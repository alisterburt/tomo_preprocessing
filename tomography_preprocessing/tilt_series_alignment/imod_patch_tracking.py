from pathlib import Path
from typing import Tuple, Optional

import typer
from yet_another_imod_wrapper import run_patch_tracking_based_alignment

from ._cli import cli
from .. import utils

PATCH_TRACKING_COMMAND_NAME = 'IMOD:patch-tracking'


@cli.command(name=PATCH_TRACKING_COMMAND_NAME)
def align_tilt_series_in_imod_using_patch_tracking(
        tilt_series_star_file: Path = typer.Option(...),
        output_directory: Path = typer.Option(...),
        tomogram_name: Optional[str] = typer.Option(None, ),
        unbinned_patch_size_pixels: Tuple[int, int] = typer.Option(...),
        patch_overlap_percentage: float = typer.Option(...),
):
    tilt_series_metadata = utils.star.iterate_tilt_series_metadata(
        tilt_series_star_file=tilt_series_star_file,
        tilt_series_id=tomogram_name
    )
    for tilt_series_id, tilt_series_df, tilt_image_df in tilt_series_metadata:
        utils.imod.align_single_tilt_series(
            tilt_series_id=tilt_series_id,
            tilt_series_df=tilt_series_df,
            tilt_image_df=tilt_image_df,
            alignment_function=run_patch_tracking_based_alignment,
            alignment_function_kwargs={
                'patch_size_xy': unbinned_patch_size_pixels,
                'patch_overlap_percentage': patch_overlap_percentage,
            },
            output_directory=output_directory,
        )
    if tomogram_name is None:  # write out STAR file for set of tilt-series
        utils.imod.write_aligned_tilt_series_star_file(
            original_tilt_series_star_file=tilt_series_star_file,
            output_directory=output_directory
        )
