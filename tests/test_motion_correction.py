import os
from pathlib import Path

import starfile

from tomography_preprocessing.motion_correction import run_relion_motioncorr, create_relion_run_motioncor_input_file, create_output_corrected_star_files
#
# def test_run_relion_motioncorr(input_import_star_path: Path, project_directory: Path):
#     test_data_directory = test_data_directory.relative_to(project_directory)
#     os.chdir(project_dir)
#
#     run_relion_motioncorr(
#         tilt_series_star_file=
#     )
#

def test_create_relion_run_motioncor_input_file(test_data_directory, project_directory):
    test_data_directory = test_data_directory.relative_to(project_directory)
    os.chdir(project_directory)

    tilt_series_star_file = test_data_directory / 'import' / 'tilt_series.star'
    output_file = Path('test_output/test_motioncor_input_file.star')

    create_relion_run_motioncor_input_file(tilt_series_star_file, output_file)
    assert output_file.exists()
    output_data = starfile.read(output_file)
    assert 'optics' in output_data.keys()
    assert 'movies' in output_data.keys()
    assert output_data['movies'].shape == (41, 3)
    assert 'rlnMicrographMovieName' in output_data['movies'].columns


def test_create_output_corrected_star_files(test_data_directory, project_directory):
    test_data_directory = test_data_directory.relative_to(project_directory)
    os.chdir(project_directory)

    example_input_file = test_data_directory / 'motion_correction' / 'example_result.star'
    create_output_corrected_star_files(example_input_file, 'test_output/tilt_series_mc')