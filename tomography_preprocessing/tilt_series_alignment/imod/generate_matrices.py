from pathlib import Path
from typing import Tuple

import numpy as np
import starfile
import typer

from .._cli import cli
from .._job_utils import create_alignment_job_directory_structure, \
    relion_tilt_series_alignment_parameters_to_relion_matrix
from ... import utils


@cli.command(name='IMOD:generate-matrices')
def generate_imod_matrices(
        tilt_series_star_file: Path = typer.Option(...),
        tomogram_dimensions: Tuple[int, int, int] = typer.Option(...),
        output_directory: Path = typer.Option(...),
):
    tilt_series_metadata = utils.star.iterate_tilt_series_metadata(
        tilt_series_star_file=tilt_series_star_file,
    )
    image_directory, alignments_directory = \
        create_alignment_job_directory_structure(output_directory)
    tilt_image_star_files = []

    for tilt_series_id, tilt_series_df, tilt_image_df in tilt_series_metadata:
        euler_angles = tilt_image_df[['rlnTomoXTilt', 'rlnTomoYTilt', 'rlnTomoZRot']]
        shifts = tilt_image_df[['rlnTomoXShiftAngst', 'rlnTomoYShiftAngst']]
        shifts /= tilt_series_df['rlnMicrographOriginalPixelSize']
        matrices = relion_tilt_series_alignment_parameters_to_relion_matrix(
            specimen_shifts=shifts,
            euler_angles=euler_angles,
            tilt_image_dimensions=utils.mrc.get_image_dimensions(
                tilt_image_df['rlnMicrographName'][0])[:2],
            tomogram_dimensions=np.array(tomogram_dimensions)
        )
        tilt_image_star_file = image_directory / f'{tilt_series_id}.star'
        tilt_image_star_files.append(tilt_image_star_file)
        projection_matrix_labels = [f'rlnTomoProj{ax}' for ax in 'XYZW']
        for idx, label in enumerate(projection_matrix_labels):
            rows = matrices[:, idx, :]
            tilt_image_df[label] = [
                f'[{r[0]:.13g},{r[1]:.13g},{r[2]:.13g},{r[3]:.13g}]'
                for r in rows
            ]
        starfile.write({tilt_series_id: tilt_image_df}, tilt_image_star_file)

    star = starfile.read(tilt_series_star_file, always_dict=True)
    star['global']['rlnTomoTiltSeriesStarFile'] = tilt_image_star_files
    star['global'][['rlnTomoSizeX', 'rlnTomoSizeY', 'rlnTomoSizeZ']] = tomogram_dimensions
    star['global']['rlnTomoHand'] = 1
    starfile.write(star, output_directory / 'aligned_tilt_series_with_matrices.star')


@cli.command(name='IMOD:generate-matrices-ali')
def generate_imod_matrices(
        tilt_series_star_file: Path = typer.Option(...),
        tomogram_dimensions: Tuple[int, int, int] = typer.Option(...),
        output_directory: Path = typer.Option(...),
):
    tilt_series_metadata = utils.star.iterate_tilt_series_metadata(
        tilt_series_star_file=tilt_series_star_file,
    )
    image_directory, alignments_directory = \
        create_alignment_job_directory_structure(output_directory)
    tilt_image_star_files = []

    for tilt_series_id, tilt_series_df, tilt_image_df in tilt_series_metadata:
        euler_angles = tilt_image_df[['rlnAngleRot', 'rlnAngleTilt', 'rlnAnglePsi']]
        shifts = tilt_image_df[['rlnOriginXAngst', 'rlnOriginYAngst']]
        shifts /= tilt_series_df['rlnMicrographOriginalPixelSize']
        print('is up to date')
        matrices = relion_tilt_series_alignment_parameters_to_relion_matrix(
            specimen_shifts=np.zeros((len(euler_angles), 2)),
            euler_angles=euler_angles,
            tilt_image_dimensions=utils.mrc.get_image_dimensions(
                tilt_image_df['rlnMicrographName'][0])[:2],
            tomogram_dimensions=np.array(tomogram_dimensions)
        )
        tilt_image_star_file = image_directory / f'{tilt_series_id}.star'
        tilt_image_star_files.append(tilt_image_star_file)
        projection_matrix_labels = [f'rlnTomoProj{ax}' for ax in 'XYZW']
        for idx, label in enumerate(projection_matrix_labels):
            rows = matrices[:, idx, :]
            tilt_image_df[label] = [
                f'[{r[0]:.13g},{r[1]:.13g},{r[2]:.13g},{r[3]:.13g}]'
                for r in rows
            ]
        starfile.write({tilt_series_id: tilt_image_df}, tilt_image_star_file)

    star = starfile.read(tilt_series_star_file, always_dict=True)
    star['global']['rlnTomoTiltSeriesStarFile'] = tilt_image_star_files
    star['global'][['rlnTomoSizeX', 'rlnTomoSizeY', 'rlnTomoSizeZ']] = tomogram_dimensions
    star['global']['rlnTomoHand'] = 1
    starfile.write(star, output_directory / 'aligned_tilt_series_with_matrices.star')