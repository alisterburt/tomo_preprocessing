from pathlib import Path
from typing import Optional

import typer
from yet_another_imod_wrapper import run_fiducial_based_alignment

import tomography_preprocessing.tilt_series_alignment.aretomo._utils
from .alignment import align_single_tilt_series
from .._cli import cli
from ... import utils
from ...utils.relion import relion_pipeline_job


@cli.command(name='IMOD:fiducials')
@relion_pipeline_job
def batch_fiducials(
        tilt_series_star_file: Path = typer.Option(...),
        output_directory: Path = typer.Option(...),
        tomogram_name: Optional[str] = typer.Option(None),
        nominal_fiducial_diameter_nanometres: float = typer.Option(...),
):
    """Align one or multiple tilt-series with fiducials in IMOD.

    Parameters
    ----------
    tilt_series_star_file: RELION tilt-series STAR file.
    output_directory: directory in which results will be stored.
    tomogram_name: 'rlnTomoName' in RELION tilt-series metadata.
    nominal_fiducial_diameter_nanometres: nominal fiducial diameter in nanometers.
    """
    tilt_series_metadata = utils.star.iterate_tilt_series_metadata(
        tilt_series_star_file=tilt_series_star_file,
        tilt_series_id=tomogram_name
    )
    for tilt_series_id, tilt_series_df, tilt_image_df in tilt_series_metadata:
        align_single_tilt_series(
            tilt_series_id=tilt_series_id,
            tilt_series_df=tilt_series_df,
            tilt_image_df=tilt_image_df,
            alignment_function=run_fiducial_based_alignment,
            alignment_function_kwargs={
                'fiducial_size': nominal_fiducial_diameter_nanometres
            },
            output_directory=output_directory,
        )
    if tomogram_name is None:  # write out STAR file for set of tilt-series
        tomography_preprocessing.tilt_series_alignment.aretomo._utils.write_aligned_tilt_series_star_file(
            original_tilt_series_star_file=tilt_series_star_file,
            output_directory=output_directory
        )