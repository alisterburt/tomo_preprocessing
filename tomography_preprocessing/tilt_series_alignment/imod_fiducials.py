from pathlib import Path

import typer
from yet_another_imod_wrapper import run_fiducial_based_alignment

from ._cli import cli
from .. import utils

FIDUCIAL_ALIGNMENT_COMMAND_NAME = 'IMOD:fiducials'


@cli.command(name=FIDUCIAL_ALIGNMENT_COMMAND_NAME)
def align_single_tilt_series_in_imod_using_fiducials(
        tilt_series_star_file: Path = typer.Option(...),
        output_directory: Path = typer.Option(...),
        tomogram_name: str = typer.Option(..., '--tn'),
        nominal_fiducial_diameter_nanometres: float = typer.Option(...),
):
    tilt_series_directory = output_directory / 'tilt_series'
    tilt_series_directory.mkdir(parents=True, exist_ok=True)

    imod_alignments_directory = output_directory / 'imod_alignments'
    imod_alignments_directory.mkdir(parents=True, exist_ok=True)

    tilt_series_id, tilt_series_df, tilt_image_df = \
        utils.star.get_tilt_series_metadata(tilt_series_star_file, tomogram_name)

    tilt_series_filename = f'{tilt_series_id}.mrc'
    tilt_image_metadata_filename = f'{tilt_series_id}.star'
    tilt_series_path = tilt_series_directory / tilt_series_filename
    tilt_image_metadata_star_path = tilt_series_directory / tilt_image_metadata_filename

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
    run_fiducial_based_alignment(
        tilt_series_file=tilt_series_path,
        tilt_angles=tilt_image_df['rlnTomoNominalStageTiltAngle'],
        pixel_size=tilt_series_df['rlnMicrographOriginalPixelSize'],
        fiducial_size=nominal_fiducial_diameter_nanometres,
        nominal_rotation_angle=tilt_image_df['rlnTomoNominalTiltAxisAngle'][0],
        output_directory=imod_directory
    )
    utils.imod.write_relion_tilt_series_alignment_output(
        tilt_image_df=tilt_image_df,
        tilt_series_id=tilt_series_id,
        pixel_size=tilt_series_df['rlnMicrographOriginalPixelSize'],
        imod_directory=imod_directory,
        output_star_file=tilt_image_metadata_star_path
    )
