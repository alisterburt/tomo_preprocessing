from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from ._utils import write_aligned_tilt_series_star_file
from .alignment import align_single_tilt_series
from .._cli import cli
from ... import utils
from ...utils.relion import relion_pipeline_job

console = Console(record=True)


@cli.command(name='AreTomo')
@relion_pipeline_job
def batch_aretomo(
        tilt_series_star_file: Path = typer.Option(...),
        output_directory: Path = typer.Option(...),
        do_local_alignments: Optional[bool] = typer.Option(False),
        n_patches_xy: Optional[tuple[int, int]] = typer.Option((5,4)),
        alignment_resolution: Optional[float] = typer.Option(10),
        alignment_thickness: Optional[float] = typer.Option(800),
        tomogram_name: Optional[str] = typer.Option(None),
        do_tilt_angle_offset_correct: Optional[bool] = typer.Option(False),
):
    """Align one or multiple tilt-series in AreTomo using RELION tilt-series metadata.

    Parameters
    ----------
    tilt_series_star_file: RELION tilt-series STAR file.
    output_directory: directory in which results will be stored.
    do_local_alignments: flag to enable/disable local alignments in AreTomo.
    n_patches_xy: number of patches in x and y used in local alignments.
    alignment_resolution: resolution for intermediate alignments.
    alignment_thickness: thickness of intermediate reconstructions during alignments in px.
    tomogram_name: 'rlnTomoName' for a specific tilt-series.
    do_tilt_angle_offset_correct: flag to enable/disable stage tilt offset correction (-TiltCor) in AreTomo

    Returns
    -------

    """
    if not tilt_series_star_file.exists():
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
            do_local_alignments=do_local_alignments,
            alignment_resolution=alignment_resolution,
            n_patches_xy=n_patches_xy,
            alignment_thickness_px=alignment_thickness,
            do_tilt_angle_offset_correct=do_tilt_angle_offset_correct,
            output_directory=output_directory,
        )
    if tomogram_name is None:  # write out STAR file for set of tilt-series
        console.log('Writing aligned_tilt_series.star')
        write_aligned_tilt_series_star_file(
            original_tilt_series_star_file=tilt_series_star_file,
            output_directory=output_directory
        )
    console.save_html(str(output_directory / 'log.html'), clear=False)
    console.save_text(str(output_directory / 'log.txt'), clear=False)
