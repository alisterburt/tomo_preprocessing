import os
from pathlib import Path

import starfile

from tomography_preprocessing.import_tilt_series.serialem import import_tilt_series_from_serial_em


def test_import_tilt_series_from_serial_em(test_data_directory, project_directory, tmpdir):
    test_data_directory = test_data_directory.relative_to(project_directory)
    os.chdir(project_directory)

    mdoc_file_pattern = f"{str(test_data_directory / 'mdoc')}/*.mdoc"
    tilt_image_movie_pattern = f"{str(test_data_directory)}/*.mrc"
    output_directory = Path(tmpdir)
    import_tilt_series_from_serial_em(
        tilt_image_movie_pattern=tilt_image_movie_pattern,
        mdoc_file_pattern=mdoc_file_pattern,
        nominal_pixel_size=1.35,
        amplitude_contrast=0.07,
        voltage=300,
        spherical_aberration=2.7,
        nominal_tilt_axis_angle=85.3,
        output_directory=output_directory,
        dose_per_tilt_image=3.01,
        prefix='my_prefix'
    )

    assert output_directory.exists()
    tilt_series_star_file = (output_directory / 'tilt_series.star')
    assert tilt_series_star_file.exists()
    df = starfile.read(tilt_series_star_file)
    assert 'rlnTomoName' in df.keys()
    assert 'rlnTomoTiltSeriesStarFile' in df.keys()
    for file in df['rlnTomoTiltSeriesStarFile']:
        star = starfile.read(file)
        assert 'optics' in star.keys()
        assert 'tilt_images' in star.keys()
