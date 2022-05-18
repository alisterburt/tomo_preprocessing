from pathlib import Path
from typing import Tuple, Callable

import numpy as np
import pandas as pd
import rich
import starfile

import tomography_preprocessing.tilt_series_alignment._utils
from .. import utils


def get_tilt_series_alignment_parameters(
        alignment_directory: Path,
        tilt_series_id: str
) -> Tuple[np.ndarray, np.ndarray]:
    """Get tilt-series alignment parameters from an AreTomo alignment directory.

    Shifts are in pixels and should be applied before rotations.
    Rotations are ZYZ intrinsic Euler angles which transform the volume.
    """
    tilt_angles = utils.imod.read_tlt(alignment_directory / f'{tilt_series_id}.tlt')
    xf = utils.imod.read_xf(alignment_directory / f'{tilt_series_id}.xf')
    shifts_px = utils.imod.get_pre_rotation_shifts(xf)
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


