from pathlib import Path
from typing import Tuple

import typer
from yet_another_imod_wrapper import align_using_patch_tracking as _run_patch_tracking

from .. import utils
from ..utils.star import iterate_tilt_series_metadata
from ._cli import cli


@cli.command(name='IMOD:patch-tracking')
def align_tilt_series_in_imod_using_patch_tracking(
        tilt_series_star_file: Path = typer.Option(...),
        output_directory: Path = typer.Option(...),
        unbinned_patch_size_pixels: Tuple[int, int] = typer.Option(...),
        patch_overlap_percentage: float = typer.Option(...)
    ):
    for tilt_series_id, optics_df, tilt_image_df in iterate_tilt_series_metadata(tilt_series_star_file):
        tilt_series_filename = output_directory / f'{tilt_series_id}.mrc'

        # Order is important in IMOD, sort by tilt angle
        tilt_image_df = tilt_image_df.sort_values(by='rlnTomoNominalStageTiltAngle', ascending=True)

        # Create tilt-series stack and align using IMOD
        # implicit assumption - one tilt-axis angle per tilt-series
        utils.image.stack_image_files(
            image_files=tilt_image_df['rlnMicrographName'],
            output_image_file=tilt_series_filename
        )
        _run_patch_tracking(
            tilt_series_file=tilt_series_filename,
            tilt_angles=tilt_image_df['rlnTomoNominalStageTiltAngle'],
            nominal_rotation_angle=tilt_image_df['rlnTomoNominalTiltAxisAngle'][0],
            pixel_size=utils.star.get_pixel_size(
                optics_df, optics_group=optics_df['rlnOpticsGroup'][0]
            ),
            patch_size_xy=unbinned_patch_size_pixels,
            patch_overlap_percentage=patch_overlap_percentage,
            output_directory=output_directory / tilt_series_id,
        )