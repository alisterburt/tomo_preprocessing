from pathlib import Path
from typing import Optional

import typer
from lil_aretomo.aretomo import run_aretomo_alignment

from ._cli import cli
from .. import utils
from ..utils.relion import relion_pipeline_job

ARETOMO_ALIGNMENT_COMMAND_NAME = 'AreTomo'

@cli.command(name=ARETOMO_ALIGNMENT_COMMAND_NAME)
@relion_pipeline_job
def aretomo_function(
        tilt_series_star_file: Path = typer.Option(...),
        output_directory: Path = typer.Option(...),
        aretomo_executable: Path = typer.Option(...),	
        local_align: Optional[bool] = typer.Option(False),
        target_pixel_size: Optional[float] = typer.Option(10),
        n_patches_x: Optional[float] = typer.Option(5),
        n_patches_y: Optional[float] = typer.Option(4),
        correct_tilt_angle_offset: Optional[bool] = typer.Option(False),
        thickness_for_alignment: Optional[float] = typer.Option(800),	
        tomogram_name: Optional[str] = typer.Option(None)
):
    tilt_series_metadata = utils.star.iterate_tilt_series_metadata(
        tilt_series_star_file=tilt_series_star_file,
        tilt_series_id=tomogram_name
    )
    for tilt_series_id, tilt_series_df, tilt_image_df in tilt_series_metadata:
        utils.aretomo.align_single_tilt_series(
            tilt_series_id=tilt_series_id,
            tilt_series_df=tilt_series_df,
            tilt_image_df=tilt_image_df,
            alignment_function=run_aretomo_alignment,
            alignment_function_kwargs={'aretomo_executable': aretomo_executable,
	    'local_align': local_align,
	    'target_pixel_size': target_pixel_size,
	    'n_patches_x': n_patches_x,
	    'n_patches_y': n_patches_y,
	    'correct_tilt_angle_offset': correct_tilt_angle_offset,
            'thickness_for_alignment': thickness_for_alignment
	    },
            output_directory=output_directory,
        )
    if tomogram_name is None:  # write out STAR file for set of tilt-series
        utils.aretomo.write_aligned_tilt_series_star_file(
            original_tilt_series_star_file=tilt_series_star_file,
            output_directory=output_directory
        )

