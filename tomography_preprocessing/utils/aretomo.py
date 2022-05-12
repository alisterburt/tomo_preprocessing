import os
from functools import lru_cache
from pathlib import Path
from typing import Tuple, Callable, Dict, Any

import numpy as np
import pandas as pd
import starfile

from .. import utils
from ..utils.transformations import S, Rx, Ry, Rz

def read_tlt(file: os.PathLike) -> np.ndarray:
    """Read an IMOD tlt file into an (n, ) numpy array."""
    return np.loadtxt(fname=file, dtype=float).reshape(-1)

@lru_cache(maxsize=100)

def get_xf_file(imod_directory: Path, tilt_series_id: str) -> Path:
    """Get the xf file containing image transforms from an IMOD directory."""
    return imod_directory / f'{tilt_series_id}.xf'


def get_tlt_file(imod_directory: Path, tilt_series_id: str) -> Path:
    """Get the tlt file containing tilt angles from an IMOD directory."""
    return imod_directory / f'{tilt_series_id}.tlt'


def get_tilt_series_alignment_parameters(
        imod_directory: Path,
        tilt_series_id: str
) -> Tuple[np.ndarray, np.ndarray]:
    """Get the tilt-series alignment parameters from an IMOD directory.

    Shifts are in pixels and should be applied before rotations.
    Rotations are ZYZ intrinsic Euler angles which transform the volume
    """
    tilt_angles = read_tlt(get_tlt_file(imod_directory,tilt_series_id))  
    xf = utils.imod.read_xf(get_xf_file(imod_directory,tilt_series_id))
    shifts_px = utils.imod.get_xf_shifts(xf)
    in_plane_rotations = utils.imod.get_xf_in_plane_rotations(xf)
    euler_angles = np.zeros(shape=(len(tilt_angles), 3))
    euler_angles[:, 1] = tilt_angles
    euler_angles[:, 2] = in_plane_rotations
    return shifts_px, euler_angles,


def remove_ignored_images(
    tilt_image_df: pd.DataFrame, 
    euler_angles: np.ndarray
) -> pd.DataFrame:
    """Detect the images removed from the tilt series by AreTomo (due to poor alignment) and remove them from
    the image stack and star file
    """
    star_angles = tilt_image_df['rlnTomoNominalStageTiltAngle']
    tlt_angles = euler_angles[:,1]
    idx_min = []
    for angle in tlt_angles:
        arr_diff = abs(star_angles - angle)
        #If difference between nominal tilt and tlt file is less than 0.5, assume same tilt
        if np.min(arr_diff) < 0.5:	
            idx_min.append(np.argmin(arr_diff))
    complete_df = tilt_image_df.copy()
    complete_df = complete_df.iloc[idx_min]
    return complete_df


def write_relion_tilt_series_alignment_output(
        tilt_image_df: pd.DataFrame,
        tilt_series_id: str,
        pixel_size: float,
        imod_directory: Path,
        output_star_file: Path,
):
    shifts_px, euler_angles = get_tilt_series_alignment_parameters(imod_directory, tilt_series_id)
    tilt_image_df = remove_ignored_images(tilt_image_df, euler_angles)
    tilt_image_df[['rlnOriginXAngst', 'rlnOriginYAngst']] = shifts_px * pixel_size
    tilt_image_df[['rlnAngleRot', 'rlnAngleTilt', 'rlnAnglePsi']] = euler_angles

    starfile.write({tilt_series_id: tilt_image_df}, output_star_file)


def relion_tilt_series_alignment_parameters_to_relion_matrix(
        shifts: pd.DataFrame,
        euler_angles: pd.DataFrame,
        tilt_image_dimensions: np.ndarray,
        tomogram_dimensions: np.ndarray,
):
    """shifts need to be in px at this point"""
    tilt_image_center = (tilt_image_dimensions - 1) / 2
    n_tilt_images = shifts.shape[0]
    shifts = np.c_[shifts, np.zeros(n_tilt_images)]  # zero-fill (n, 2) to (n, 3)
    tomogram_center_to_origin = -tomogram_dimensions / 2
    tilt_image_corner_to_center_vector = np.append(tilt_image_center, 0)

    # Generate affine matrices for each component of the final transformation
    # first the rotations
    in_plane_rotation = Rz(euler_angles['rlnAnglePsi'])
    tilt = Ry(euler_angles['rlnAngleTilt'])

    # offsets
    tomogram_origin_offset = S(tomogram_center_to_origin)
    tilt_image_corner_to_center = S(tilt_image_corner_to_center_vector)
    tilt_image_centering_shift = S(shifts)

    # compose matrices
    volume_transforms = in_plane_rotation @ tilt @ tomogram_origin_offset
    image_transforms = tilt_image_corner_to_center @ tilt_image_centering_shift
    return np.squeeze(image_transforms @ volume_transforms)


def create_job_directory_structure(output_directory: Path) -> Tuple[Path, Path]:
    """Create directory structure for an AreTomo alignment job."""
    tilt_series_directory = output_directory / 'tilt_series'
    tilt_series_directory.mkdir(parents=True, exist_ok=True)

    imod_alignments_directory = output_directory / 'aretomo_alignments'
    imod_alignments_directory.mkdir(parents=True, exist_ok=True)
    return tilt_series_directory, imod_alignments_directory


def align_single_tilt_series(
        tilt_series_id: str,
        tilt_series_df: pd.DataFrame,
        tilt_image_df: pd.DataFrame,
        alignment_function: Callable,
        alignment_function_kwargs: Dict[str, Any],
        output_directory: Path,
):
    # Create output directory structure
    tilt_series_directory, imod_alignments_directory = \
        create_job_directory_structure(output_directory)
    imod_directory = imod_alignments_directory / tilt_series_id
    imod_directory.mkdir(parents=True, exist_ok=True)

    # Establish filenames
    tilt_series_filename = f'{tilt_series_id}.mrc'
    tilt_image_metadata_filename = f'{tilt_series_id}.star'
    tilt_series_path = tilt_series_directory / tilt_series_filename
    tilt_image_metadata_star_path = tilt_series_directory / tilt_image_metadata_filename

    # Order is important in IMOD, sort by tilt angle
    tilt_image_df = tilt_image_df.sort_values(by='rlnTomoNominalStageTiltAngle', ascending=True)

    # Create tilt-series stack and align using IMOD
    # implicit assumption - one tilt-axis angle per tilt-series
    utils.image.stack_image_files(
        image_files=tilt_image_df['rlnMicrographName'],
        output_image_file=tilt_series_path
    )
    alignment_function(
        tilt_series_file=tilt_series_path,
        tilt_angles=tilt_image_df['rlnTomoNominalStageTiltAngle'],
        pixel_size=tilt_series_df['rlnMicrographOriginalPixelSize'],
        nominal_rotation_angle=tilt_image_df['rlnTomoNominalTiltAxisAngle'][0],
        output_directory=imod_directory,
        **alignment_function_kwargs
    )    
    utils.aretomo.write_relion_tilt_series_alignment_output(
        tilt_image_df=tilt_image_df,
        tilt_series_id=tilt_series_id,
        pixel_size=tilt_series_df['rlnMicrographOriginalPixelSize'],
        imod_directory=imod_directory,
        output_star_file=tilt_image_metadata_star_path
    )


def write_aligned_tilt_series_star_file(
        original_tilt_series_star_file: Path,
        output_directory: Path,
):
    df = starfile.read(original_tilt_series_star_file, always_dict=True)['global']
    tilt_series_metadata = list(utils.star.iterate_tilt_series_metadata(
        tilt_series_star_file=original_tilt_series_star_file
    ))
    # update individual tilt series star files
    df['rlnTomoTiltSeriesStarFile'] = [
        output_directory / 'tilt_series' / f'{tilt_series_id}.star'
        for tilt_series_id, _, _ in tilt_series_metadata
    ]

    # check which output files were succesfully generated, take only those
    df = df[df['rlnTomoTiltSeriesStarFile'].apply(lambda x: x.exists())]

    starfile.write({'global': df}, output_directory / 'aligned_tilt_series.star')
