from pathlib import Path
from typing import Tuple, Callable

import numpy as np
import pandas as pd
import rich
import starfile

from .. import utils


def get_tilt_series_alignment_parameters(
        imod_directory: Path,
        tilt_series_id: str
) -> Tuple[np.ndarray, np.ndarray]:
    """Get the tilt-series alignment parameters from an IMOD directory.

    Shifts are in pixels and should be applied before rotations.
    Rotations are ZYZ intrinsic Euler angles which transform the volume
    """
    tilt_angles = utils.imod.read_tlt(imod_directory / f'{tilt_series_id}.tlt')
    xf = utils.imod.read_xf(imod_directory / f'{tilt_series_id}.xf')
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
    tlt_angles = euler_angles[:, 1]
    idx_min = []
    for angle in tlt_angles:
        arr_diff = abs(star_angles - angle)
        # If difference between nominal tilt and tlt file is less than 0.5, assume same tilt
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


def align_single_tilt_series(
        tilt_series_id: str,
        tilt_series_df: pd.DataFrame,
        tilt_image_df: pd.DataFrame,
        alignment_function: Callable,
        aretomo_executable: Path,
        local_align: bool,
        target_pixel_size: float,
        n_patches_xy: tuple[int, int],
        correct_tilt_angle_offset: bool,
        thickness_for_alignment: float,
        output_directory: Path,
):
    console = rich.console.Console(record=True)
    # Create output directory structure
    tilt_series_directory, imod_alignments_directory = \
        utils.imod.create_job_directory_structure(output_directory)
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
    console.log('Creating tilt series stack')
    utils.image.stack_image_files(
        image_files=tilt_image_df['rlnMicrographName'],
        output_image_file=tilt_series_path
    )
    console.log('Running AreTomo')
    alignment_function(
        tilt_series_file=tilt_series_path,
        tilt_angles=tilt_image_df['rlnTomoNominalStageTiltAngle'],
        pixel_size=tilt_series_df['rlnMicrographOriginalPixelSize'],
        nominal_rotation_angle=tilt_image_df['rlnTomoNominalTiltAxisAngle'][0],
        output_directory=imod_directory,
        aretomo_executable=aretomo_executable,
        local_align=local_align,
        target_pixel_size=target_pixel_size,
        n_patches_xy=n_patches_xy,
        correct_tilt_angle_offset=correct_tilt_angle_offset,
        thickness_for_alignment=thickness_for_alignment,
    )
    console.log('Writing alignment .star')
    utils.aretomo.write_relion_tilt_series_alignment_output(
        tilt_image_df=tilt_image_df,
        tilt_series_id=tilt_series_id,
        pixel_size=tilt_series_df['rlnMicrographOriginalPixelSize'],
        imod_directory=imod_directory,
        output_star_file=tilt_image_metadata_star_path
    )
