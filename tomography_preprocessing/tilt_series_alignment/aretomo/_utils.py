from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
import starfile

from ..imod import _utils as imod_utils

def get_tilt_series_alignment_parameters(
        alignment_directory: Path,
        tilt_series_id: str
) -> np.ndarray:
    """Get tilt-series alignment parameters from an AreTomo alignment directory.

    Shifts are in pixels and should be applied before rotations.
    Rotations are ZYZ intrinsic Euler angles which transform the volume.
    """
    xf = imod_utils.read_xf(alignment_directory / f'{tilt_series_id}.xf')
    tlt = imod_utils.read_tlt(alignment_directory / f'{tilt_series_id}.tlt')
    shifts_px = imod_utils.calculate_specimen_shifts(xf)
    return shifts_px, xf, tlt


def write_relion_tilt_series_alignment_output(
        tilt_image_df: pd.DataFrame,
        tilt_series_id: str,
        pixel_size: float,
        imod_directory: Path,
        output_star_file: Path,
):
    """Write output from a tilt-series alignment experiment."""
    shifts_px, xf, tlt = get_tilt_series_alignment_parameters(imod_directory, tilt_series_id)
    tilt_image_df[['rlnTomoXShiftAngst', 'rlnTomoYShiftAngst']] = shifts_px * pixel_size
    tilt_image_df[['rlnTomoXTilt', 'rlnTomoYTilt', 'rlnTomoZRot']] = \
        imod_utils.get_xyz_extrinsic_euler_angles(xf, tlt)
    
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
