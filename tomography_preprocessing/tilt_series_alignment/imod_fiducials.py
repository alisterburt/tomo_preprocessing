from pathlib import Path

import typer
from yet_another_imod_wrapper import run_fiducial_based_alignment as _run_fiducial_based_alignment

from ._cli import cli
from .. import utils
from ..utils.star import iterate_tilt_series_metadata as _iterate_tilt_series_metadata


@cli.command(name='IMOD:fiducials')
def align_tilt_series_in_imod_using_fiducials(
        tilt_series_star_file: Path = typer.Option(...),
        output_directory: Path = typer.Option(...),
        nominal_fiducial_diameter_nanometres: float = typer.Option(...),
):
    tilt_series_directory = output_directory / 'tilt_series'
    tilt_series_directory.mkdir(parents=True, exist_ok=True)

    imod_alignments_directory = output_directory / 'imod_alignments'
    imod_alignments_directory.mkdir(parents=True, exist_ok=True)

    for tilt_series_id, optics_df, tilt_image_df in _iterate_tilt_series_metadata(
            tilt_series_star_file):
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
            output_image_file=tilt_series_filename
        )
        _run_fiducial_based_alignment(
            tilt_series_file=tilt_series_filename,
            tilt_angles=tilt_image_df['rlnTomoNominalStageTiltAngle'],
            pixel_size=utils.star.get_pixel_size(
                optics_df, optics_group=optics_df['rlnOpticsGroup'][0]
            ),
            fiducial_size=nominal_fiducial_diameter_nanometres,
            nominal_rotation_angle=tilt_image_df['rlnTomoNominalTiltAxisAngle'][0],
            output_directory=output_directory / tilt_series_id,
        )
