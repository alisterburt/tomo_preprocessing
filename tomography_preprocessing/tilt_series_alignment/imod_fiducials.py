from pathlib import Path

from yet_another_imod_wrapper import align_using_fiducials as _run_fiducial_based_alignment
from .. import utils
from ..utils.star import iterate_tilt_series_metadata as _iterate_tilt_series_metadata
from ._cli import cli

import typer


@cli.command(name='IMOD:fiducials')
def align_tilt_series_in_imod_using_fiducials(
        tilt_series_star_file: Path = typer.Option(...),
        output_directory: Path = typer.Option(...),
        nominal_fiducial_diameter_nanometres: float = typer.Option(...),
):
    for tilt_series_id, optics_df, tilt_image_df in _iterate_tilt_series_metadata(tilt_series_star_file):
        tilt_series_filename = output_directory / f'{tilt_series_id}.mrc'

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




