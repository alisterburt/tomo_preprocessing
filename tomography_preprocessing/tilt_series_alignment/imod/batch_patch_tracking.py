from pathlib import Path
from typing import Tuple, Optional

import typer
from yet_another_imod_wrapper import run_patch_tracking_based_alignment
from rich.console import Console

import tomography_preprocessing.tilt_series_alignment.aretomo._utils
from .alignment import align_single_tilt_series
from .._cli import cli
from ... import utils
from ...utils.relion import relion_pipeline_job

console = Console(record=True)

@cli.command(name='IMOD:patch-tracking')
@relion_pipeline_job
def batch_patch_tracking(
        tilt_series_star_file: Path = typer.Option(...),
        output_directory: Path = typer.Option(...),
        tomogram_name: Optional[str] = typer.Option(None),
        unbinned_patch_size_pixels: Tuple[int, int] = typer.Option(...),
        patch_overlap_percentage: float = typer.Option(...),
):
    """Align one or multiple tilt-series with patch-tracking in IMOD.

    Parameters
    ----------
    tilt_series_star_file: RELION tilt-series STAR file.
    output_directory: directory in which to store results.
    tomogram_name: 'rlnTomoName' in tilt-series STAR file.
    unbinned_patch_size_pixels: size of 2D patches used for alignment.
    patch_overlap_percentage: percentage of overlap between tracked patches.
    """
    #Check input paths exist
    if not Path(tilt_series_star_file).exists():
        e = 'Could not find tilt series star file'
        console.log(f'ERROR: {e}')
        raise RuntimeError(e)
    console.log('Extracting metadata for all tilt series.')
    tilt_series_metadata = utils.star.iterate_tilt_series_metadata(
        tilt_series_star_file=tilt_series_star_file,
        tilt_series_id=tomogram_name
    )
    for tilt_series_id, tilt_series_df, tilt_image_df in tilt_series_metadata:
        console.log(f'Aligning {tilt_series_id}...')
        align_single_tilt_series(
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
        console.log('Writing aligned_tilt_series.star')
        tomography_preprocessing.tilt_series_alignment.aretomo._utils.write_aligned_tilt_series_star_file(
            original_tilt_series_star_file=tilt_series_star_file,
            output_directory=output_directory
        )
    console.save_html(str(output_directory / 'log.html'), clear=False)
    console.save_text(str(output_directory / 'log.txt'), clear=False)
