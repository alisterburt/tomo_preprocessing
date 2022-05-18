from pathlib import Path

import pandas as pd
from lil_aretomo.aretomo import run_aretomo_alignment
from rich.console import Console

from ._utils import write_relion_tilt_series_alignment_output
from .._job_utils import create_alignment_job_directory_structure
from ... import utils


def align_single_tilt_series(
        tilt_series_id: str,
        tilt_series_df: pd.DataFrame,
        tilt_image_df: pd.DataFrame,
        aretomo_executable: Path,
        do_local_alignments: bool,
        alignment_pixel_size: float,
        n_patches_xy: tuple[int, int],
        alignment_thickness_px: float,
        output_directory: Path,
):
    """Align a single tilt-series in AreTomo using RELION tilt-series metadata.

    Parameters
    ----------
    tilt_series_id: 'rlnTomoName' in RELION tilt-series metadata.
    tilt_series_df: master file for tilt-series metadata.
    tilt_image_df: file containing information for images in a single tilt-series.
    aretomo_executable: path to executable for AreTomo.
    do_local_alignments: flag to enable local alignments.
    alignment_pixel_size: pixel size for alignments in angstroms per pixel.
    n_patches_xy: number of patches in x and y for local alignments
    alignment_thickness_px: thickness of intermediate reconstruction during alignments.
    output_directory: directory in which results will be stored.
    """
    console = Console(record=True)

    # Create output directory structure
    image_directory, all_alignments_dir = \
        create_alignment_job_directory_structure(output_directory)
    alignment_dir = all_alignments_dir / tilt_series_id
    alignment_dir.mkdir(parents=True, exist_ok=True)

    # Establish filenames
    tilt_series_filename = f'{tilt_series_id}.mrc'
    tilt_image_metadata_filename = f'{tilt_series_id}.star'

    # Order is important in IMOD, sort by tilt angle
    tilt_image_df = tilt_image_df.sort_values(by='rlnTomoNominalStageTiltAngle', ascending=True)

    # Create tilt-series stack and align using IMOD
    # implicit assumption - one tilt-axis angle per tilt-series
    console.log('Creating tilt series stack')
    image_file_path = image_directory / tilt_series_filename
    utils.image.stack_image_files(
        image_files=tilt_image_df['rlnMicrographName'],
        output_image_file=image_file_path
    )
    console.log('Running AreTomo')
    run_aretomo_alignment(
        tilt_series_file=image_file_path,
        tilt_angles=tilt_image_df['rlnTomoNominalStageTiltAngle'],
        pixel_size=tilt_series_df['rlnMicrographOriginalPixelSize'],
        nominal_rotation_angle=tilt_image_df['rlnTomoNominalTiltAxisAngle'][0],
        output_directory=alignment_dir,
        aretomo_executable=aretomo_executable,
        local_align=do_local_alignments,
        target_pixel_size=alignment_pixel_size,
        n_patches_xy=n_patches_xy,
        correct_tilt_angle_offset=False,
        thickness_for_alignment=alignment_thickness_px,
    )
    console.log('Writing STAR file for aligned tilt-series')
    write_relion_tilt_series_alignment_output(
        tilt_image_df=tilt_image_df,
        tilt_series_id=tilt_series_id,
        pixel_size=tilt_series_df['rlnMicrographOriginalPixelSize'],
        imod_directory=alignment_dir,
        output_star_file=image_directory / tilt_image_metadata_filename,
    )
    console.save_text(alignment_dir / 'log.txt', clear=False)
    console.save_html(alignment_dir / 'log.html')