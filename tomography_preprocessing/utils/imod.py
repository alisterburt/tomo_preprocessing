import os
from functools import lru_cache
from pathlib import Path
from typing import Tuple, Callable, Dict, Any

import numpy as np
import pandas as pd
import starfile

from .. import utils
from ..utils.transformations import S, Rx, Ry, Rz


def read_xf(file: os.PathLike) -> np.ndarray:
    """Read an IMOD xf file into an (n, 6) numpy array.

    The file with alignment transforms (option OutputTransformFile) contains one
    line per view, each with a linear transformation specified by six numbers:
        A11 A12 A21 A22 DX DY
    where the coordinate (X, Y) is transformed to (X', Y') by:
        X' = A11 * X + A12 * Y + DX
        Y' = A21 * X + A22 * Y + DY
    """
    return np.loadtxt(fname=file, dtype=float).reshape((-1, 6))


def read_tlt(file: os.PathLike) -> np.ndarray:
    """Read an IMOD tlt file into an (n, ) numpy array."""
    return np.loadtxt(fname=file, dtype=float).reshape(-1)


def get_xf_shifts(xf: np.ndarray) -> np.ndarray:
    """Extract XY shifts from IMOD xf data.

    Output is an (n, 2) numpy array of shifts which center tilt-images.
    """
    transformation_matrices = get_xf_transformation_matrices(xf)
    post_transformation_shifts = xf[:, -2:].reshape((-1, 2, 1))
    pre_transformation_shifts = transformation_matrices @ post_transformation_shifts
    return pre_transformation_shifts.reshape((-1, 2))


def get_xf_transformation_matrices(xf: np.ndarray) -> np.ndarray:
    """Extract the 2D transformation matrix from IMOD xf data.

    Output is an (n, 2, 2) numpy array of matrices.
    """
    return xf[:, :4].reshape((-1, 2, 2))


def get_xf_in_plane_rotations(xf: np.ndarray) -> np.ndarray:
    """Extract the in plane rotation angle from IMOD xf data.

    Output is an (n, ) numpy array of angles in degrees. This function assumes
    that the transformation in the xf file is a simple 2D rotation.
    """
    transformation_matrices = get_xf_transformation_matrices(xf)
    cos_theta = transformation_matrices[:, 0, 0]
    return np.rad2deg(np.arccos(cos_theta))


@lru_cache(maxsize=100)
def get_etomo_basename(imod_directory: Path) -> str:
    """Get the tilt-series stack basename from an Etomo directory."""
    edf_files = list(imod_directory.glob('*.edf'))
    if len(edf_files) != 1:
        raise RuntimeError('singular Etomo directive file not found')
    return edf_files[0].stem


def get_xf_file(imod_directory: Path) -> Path:
    """Get the xf file containing image transforms from an IMOD directory."""
    return imod_directory / f'{get_etomo_basename(imod_directory)}.xf'


def get_tlt_file(imod_directory: Path) -> Path:
    """Get the tlt file containing tilt angles from an IMOD directory."""
    return imod_directory / f'{get_etomo_basename(imod_directory)}.tlt'


def get_edf_file(imod_directory: Path) -> Path:
    """Get the Etomo directive file from an IMOD directory."""
    return imod_directory / f'{get_etomo_basename(imod_directory)}.edf'


def get_tilt_series_alignment_parameters(
        imod_directory: Path
) -> Tuple[np.ndarray, np.ndarray]:
    """Get the tilt-series alignment parameters from an IMOD directory.

    Shifts are in pixels and should be applied before rotations.
    Rotations are ZYZ intrinsic Euler angles which transform the volume
    """
    xf = read_xf(get_xf_file(imod_directory))
    shifts_px = get_xf_shifts(xf)
    in_plane_rotations = get_xf_in_plane_rotations(xf)
    tilt_angles = read_tlt(get_tlt_file(imod_directory))
    euler_angles = np.zeros(shape=(len(tilt_angles), 3))
    euler_angles[:, 1] = tilt_angles
    euler_angles[:, 2] = in_plane_rotations
    return shifts_px, euler_angles


def write_relion_tilt_series_alignment_output(
        tilt_image_df: pd.DataFrame,
        tilt_series_id: str,
        pixel_size: float,
        imod_directory: Path,
        output_star_file: Path,
):
    shifts_px, euler_angles = get_tilt_series_alignment_parameters(imod_directory)
    tilt_image_df[['rlnOriginXAngst', 'rlnOriginYAngst']] = shifts_px * pixel_size
    tilt_image_df[['rlnAngleRot', 'rlnAngleTilt', 'rlnAnglePsi']] = euler_angles
    starfile.write({tilt_series_id: tilt_image_df}, output_star_file)


def relion_tilt_series_alignment_to_relion_matrix(
        shifts: np.ndarray,
        euler_angles: np.ndarray,
        tilt_image_dimensions: np.ndarray,
        tomogram_dimensions: np.ndarray,
):
    x, y, z = tomogram_dimensions
    tilt_image_center = (tilt_image_dimensions - 1) / 2
    n_tilt_images = shifts.shape[0]
    shifts = np.c_(shifts, np.zeros(n_tilt_images))  # promote (n, 2) to (n, 3)

    ## Generate affine matrix components
    # rotations
    in_plane_rotation = Rz(euler_angles['rlnAnglePsi'])
    tilt = Ry(euler_angles['rlnAngleTilt'])
    Rx90 = Rx(-90)

    # offsets
    tomogram_offset_vector = -tomogram_dimensions / 2
    tomogram_origin_offset = S(tomogram_offset_vector)
    tilt_image_offset_vector = np.append(tilt_image_center, 0)

    # compose matrices





def create_job_directory_structure(output_directory: Path) -> Tuple[Path, Path]:
    """Create directory structure for an IMOD alignment job."""
    tilt_series_directory = output_directory / 'tilt_series'
    tilt_series_directory.mkdir(parents=True, exist_ok=True)

    imod_alignments_directory = output_directory / 'imod_alignments'
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
    utils.imod.write_relion_tilt_series_alignment_output(
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
    df['EtomoDirectiveFile'] = [
        output_directory / 'imod_alignments' / tilt_series_id / f'{tilt_series_id}.edf'
        for tilt_series_id, _, _ in tilt_series_metadata
    ]

    # check which output files were succesfully generated, take only those
    df = df[df['rlnTomoTiltSeriesStarFile'].apply(lambda x: x.exists())]

    starfile.write({'global': df}, output_directory / 'aligned_tilt_series.star')
