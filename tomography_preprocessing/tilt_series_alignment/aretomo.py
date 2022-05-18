from pathlib import Path
from typing import Optional, Callable

import pandas as pd
import rich
import typer
from lil_aretomo.aretomo import run_aretomo_alignment

from ._cli import cli
from ._alignment_utils import create_alignment_job_directory_structure
from .. import utils
from ..utils.relion import relion_pipeline_job

console = rich.console.Console(record=True)


@cli.command(name='AreTomo')
@relion_pipeline_job
def relion_batch_aretomo(
        tilt_series_star_file: Path = typer.Option(...),
        output_directory: Path = typer.Option(...),
        aretomo_executable: Path = typer.Option(...),
        local_align: Optional[bool] = typer.Option(False),
        target_pixel_size: Optional[float] = typer.Option(10),
        n_patches_xy: Optional[tuple[int, int]] = typer.Option((5, 4)),
        correct_tilt_angle_offset: Optional[bool] = typer.Option(False),
        thickness_for_alignment: Optional[float] = typer.Option(800),
        tomogram_name: Optional[str] = typer.Option(None)
):
    console.log('Extracting metadata for all tilt series.')
    tilt_series_metadata = utils.star.iterate_tilt_series_metadata(
        tilt_series_star_file=tilt_series_star_file,
        tilt_series_id=tomogram_name
    )
    for tilt_series_id, tilt_series_df, tilt_image_df in tilt_series_metadata:
        console.log(f'Aligning {tilt_series_id}...')

        utils.aretomo.align_single_tilt_series(
            tilt_series_id=tilt_series_id,
            tilt_series_df=tilt_series_df,
            tilt_image_df=tilt_image_df,
            alignment_function=run_aretomo_alignment,
            aretomo_executable=aretomo_executable,
            local_align=local_align,
            target_pixel_size=target_pixel_size,
            n_patches_xy=n_patches_xy,
            correct_tilt_angle_offset=correct_tilt_angle_offset,
            thickness_for_alignment=thickness_for_alignment,
            output_directory=output_directory,
        )
    if tomogram_name is None:  # write out STAR file for set of tilt-series
        console.log('Writing aligned_tilt_series.star')
        utils.imod.write_aligned_tilt_series_star_file(
            original_tilt_series_star_file=tilt_series_star_file,
            output_directory=output_directory
        )
    console.save_html(str(output_directory / 'log.html'), clear=False)
    console.save_text(str(output_directory / 'log.txt'), clear=False)


def align_single_tilt_series(
        tilt_series_id: str,
        tilt_series_df: pd.DataFrame,
        tilt_image_df: pd.DataFrame,
        alignment_function: Callable,
        aretomo_executable: Path,
        local_align: bool,
        target_pixel_size: float,
        n_patches_xy: tuple[int, int],
        correct_tilt_angle_offset: bool,
        thickness_for_alignment: float,
        output_directory: Path,
):
    console = rich.console.Console(record=True)
    # Create output directory structure
    tilt_series_directory, alignments_directory = \
        create_alignment_job_directory_structure(
            output_directory)
    imod_directory = alignments_directory / tilt_series_id
    imod_directory.mkdir(parents=True, exist_ok=True)

    # Establish filenames
    tilt_series_filename = f'{tilt_series_id}.mrc'
    tilt_image_metadata_filename = f'{tilt_series_id}.star'
    tilt_series_path = tilt_series_directory / tilt_series_filename
    tilt_image_metadata_star_path = tilt_series_directory / tilt_image_metadata_filename

    # Order is important in IMOD, sort by tilt angle
    tilt_image_df = tilt_image_df.sort_values(by='rlnTomoNominalStageTiltAngle', ascending=True)

    # Create tilt-series stack and align using IMOD
    # implicit assumption - one tilt-axis angle per tilt-series
    console.log('Creating tilt series stack')
    utils.image.stack_image_files(
        image_files=tilt_image_df['rlnMicrographName'],
        output_image_file=tilt_series_path
    )
    console.log('Running AreTomo')
    alignment_function(
        tilt_series_file=tilt_series_path,
        tilt_angles=tilt_image_df['rlnTomoNominalStageTiltAngle'],
        pixel_size=tilt_series_df['rlnMicrographOriginalPixelSize'],
        nominal_rotation_angle=tilt_image_df['rlnTomoNominalTiltAxisAngle'][0],
        output_directory=imod_directory,
        aretomo_executable=aretomo_executable,
        local_align=local_align,
        target_pixel_size=target_pixel_size,
        n_patches_xy=n_patches_xy,
        correct_tilt_angle_offset=correct_tilt_angle_offset,
        thickness_for_alignment=thickness_for_alignment,
    )
    console.log('Writing alignment .star')
    utils.aretomo.write_relion_tilt_series_alignment_output(
        tilt_image_df=tilt_image_df,
        tilt_series_id=tilt_series_id,
        pixel_size=tilt_series_df['rlnMicrographOriginalPixelSize'],
        imod_directory=imod_directory,
        output_star_file=tilt_image_metadata_star_path
    )
