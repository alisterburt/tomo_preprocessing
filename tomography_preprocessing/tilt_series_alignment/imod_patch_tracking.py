from pathlib import Path
from typing import Tuple

import typer
from yet_another_imod_wrapper import run_patch_tracking_based_alignment

from ._cli import cli
from .. import utils
from ..utils.star import get_tilt_series_metadata

PATCH_TRACKING_COMMAND_NAME = 'IMOD:patch-tracking'


@cli.command(name=PATCH_TRACKING_COMMAND_NAME)
def align_single_tilt_series_in_imod_using_patch_tracking(
    tilt_series_star_file: Path = typer.Option(...),
    output_directory: Path = typer.Option(...),
    tomogram_name: str = typer.Option(...),
    unbinned_patch_size_pixels: Tuple[int, int] = typer.Option(...),
    patch_overlap_percentage: float = typer.Option(...),
):
    tilt_series_directory = output_directory / 'tilt_series'
    tilt_series_directory.mkdir(parents=True, exist_ok=True)

    imod_alignments_directory = output_directory / 'imod_alignments'
    imod_alignments_directory.mkdir(parents=True, exist_ok=True)

    tilt_series_id, tilt_series_df, tilt_image_df = get_tilt_series_metadata(
        tilt_series_star_file, tomogram_name
    )

    tilt_series_filename = f'{tilt_series_id}.mrc'
    tilt_series_path = tilt_series_directory / tilt_series_filename

    imod_directory = imod_alignments_directory / tilt_series_id
    imod_directory.mkdir(exist_ok=True, parents=True)

    # Order is important in IMOD, sort by tilt angle
    tilt_image_df = tilt_image_df.sort_values(by='rlnTomoNominalStageTiltAngle', ascending=True)

    # Create tilt-series stack and align using IMOD
    # implicit assumption - one tilt-axis angle per tilt-series
    utils.image.stack_image_files(
        image_files=tilt_image_df['rlnMicrographName'],
        output_image_file=tilt_series_path
    )
    run_patch_tracking_based_alignment(
        tilt_series_file=tilt_series_path,
        tilt_angles=tilt_image_df['rlnTomoNominalStageTiltAngle'],
        nominal_rotation_angle=tilt_image_df['rlnTomoNominalTiltAxisAngle'][0],
        pixel_size=tilt_series_df['rlnMicrographOriginalPixelSize'],
        patch_size_xy=unbinned_patch_size_pixels,
        patch_overlap_percentage=patch_overlap_percentage,
        output_directory=imod_directory,
    )
