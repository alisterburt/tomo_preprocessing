from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
import starfile

from ..imod import _utils as imod_utils

def get_tilt_series_alignment_parameters(
        alignment_directory: Path,
        tilt_series_id: str
) -> Tuple[np.ndarray, np.ndarray]:
    """Get tilt-series alignment parameters from an AreTomo alignment directory.

    Shifts are in pixels and should be applied before rotations.
    Rotations are ZYZ intrinsic Euler angles which transform the volume.
    """
    tilt_angles = imod_utils.read_tlt(alignment_directory / f'{tilt_series_id}.tlt')
    xf = imod_utils.read_xf(alignment_directory / f'{tilt_series_id}.xf')
    shifts_px = imod_utils.get_pre_rotation_shifts(xf)
    in_plane_rotations = imod_utils.get_xf_in_plane_rotations(xf)
    euler_angles = np.zeros(shape=(len(tilt_angles), 3))
    euler_angles[:, 1] = tilt_angles
    euler_angles[:, 2] = in_plane_rotations
    return shifts_px, euler_angles,


def remove_ignored_images(
        tilt_image_df: pd.DataFrame,
        refined_tilt_angles: np.ndarray
) -> pd.DataFrame:
    """Detect the images removed from the tilt series by AreTomo (due to poor alignment) and remove them from
    the image stack and star file
    """
    nominal_tilt_angles = tilt_image_df['rlnTomoNominalStageTiltAngle']

    # setup for broadcasting:
    # _nominal shape         (n, 1)
    # _refined shape         (1, m)
    _nominal_tilt_angles = np.array(nominal_tilt_angles).reshape((-1, 1))
    _refined_tilt_angles = refined_tilt_angles.reshape((1, -1))
    
    # calculate difference between refined tilt angles and nominal tilt angles
    # deltas shape           (n, m)
    tilt_angle_deltas = np.abs(_nominal_tilt_angles - _refined_tilt_angles)

    # check all deltas are small
    all_deltas_close = np.allclose(np.min(tilt_angle_deltas, axis=0), 0, atol=0.5)
    if not all_deltas_close:
        raise RuntimeError("Could not determine which images were automatically removed.")

    # Get subset of images data with matched tilt-images
    idx = np.argmin(tilt_angle_deltas, axis=0)
    return tilt_image_df.iloc[idx]


def write_relion_tilt_series_alignment_output(
        tilt_image_df: pd.DataFrame,
        tilt_series_id: str,
        pixel_size: float,
        imod_directory: Path,
        output_star_file: Path,
):
    shifts_px, euler_angles = get_tilt_series_alignment_parameters(imod_directory, tilt_series_id)
    tilt_image_df = tilt_image_df.copy()  # working on a copy here avoids warnings
    tilt_image_df = remove_ignored_images(tilt_image_df, euler_angles[:,1])
    tilt_image_df[['rlnOriginXAngst', 'rlnOriginYAngst']] = shifts_px * pixel_size
    tilt_image_df[['rlnAngleRot', 'rlnAngleTilt', 'rlnAnglePsi']] = euler_angles
    
    starfile.write({tilt_series_id: tilt_image_df}, output_star_file)


def write_aligned_tilt_series_star_file(
        original_tilt_series_star_file: Path,
        output_directory: Path,
):
    df = starfile.read(original_tilt_series_star_file, always_dict=True)['global']

    # update individual tilt series star files
    df['rlnTomoTiltSeriesStarFile'] = df['rlnTomoName'].apply(
        lambda tilt_series_id: output_directory / 'tilt_series' / f'{tilt_series_id}.star'
    )

    # check which output files were succesfully generated, take only those
    df = df[df['rlnTomoTiltSeriesStarFile'].apply(lambda p: p.exists())]
    starfile.write({'global': df}, output_directory / 'aligned_tilt_series.star')
