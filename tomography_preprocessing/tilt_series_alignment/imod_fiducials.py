from pathlib import Path
from typing import Optional

import typer
from yet_another_imod_wrapper import run_fiducial_based_alignment

from ._cli import cli
from .. import utils

FIDUCIAL_ALIGNMENT_COMMAND_NAME = 'IMOD:fiducials'


@cli.command(name=FIDUCIAL_ALIGNMENT_COMMAND_NAME)
def align_tilt_series_in_imod_using_fiducials(
        tilt_series_star_file: Path = typer.Option(...),
        output_directory: Path = typer.Option(...),
        tomogram_name: Optional[str] = typer.Option(None, '--tn'),
        nominal_fiducial_diameter_nanometres: float = typer.Option(...),
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
            alignment_function=run_fiducial_based_alignment,
            alignment_function_kwargs={'fiducial_size': nominal_fiducial_diameter_nanometres},
            output_directory=output_directory,
        )
    if tomogram_name is None:  # write out STAR file for set of tilt-series
        utils.imod.write_aligned_tilt_series_star_file(
            original_tilt_series_star_file=tilt_series_star_file,
            output_directory=output_directory
        )

