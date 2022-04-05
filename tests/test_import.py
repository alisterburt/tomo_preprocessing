import os

from tomography_preprocessing.import_tilt_series import import_tilt_series_from_serial_em


def test_import_tilt_series_from_serial_em(test_data_directory, project_directory):
    test_data_directory = test_data_directory.relative_to(project_directory)
    os.chdir(project_directory)

    mdoc_file_pattern = f"{str(test_data_directory / 'mdoc')}/*.mdoc"
    tilt_image_movie_pattern = f"{str(test_data_directory)}/*.mrc"

    import_tilt_series_from_serial_em(
        tilt_image_movie_wildcard=tilt_image_movie_pattern,
        mdoc_file_wildcard=mdoc_file_pattern,
        nominal_pixel_size=1.35,
        amplitude_contrast=0.07,
        voltage=300,
        spherical_aberration=2.7,
        nominal_tilt_axis_angle=85.3,
        output_directory='test_output',
        dose_per_tilt_image=3.01,
        prefix='my_prefix'
    )