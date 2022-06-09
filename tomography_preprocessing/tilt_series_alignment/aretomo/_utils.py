from pathlib import Path

import starfile


def write_aligned_tilt_series_star_file(
        original_tilt_series_star_file: Path,
        output_directory: Path,
):
    df = starfile.read(original_tilt_series_star_file, always_dict=True)['global']

    # update individual tilt series star files
    df['rlnTomoTiltSeriesStarFile'] = df['rlnTomoName'].apply(
        lambda tilt_series_id: output_directory / 'tilt_series' / f'{tilt_series_id}.star'
    )

    # check which output files were succesfully generated, take only those
    df = df[df['rlnTomoTiltSeriesStarFile'].apply(lambda p: p.exists())]
    starfile.write({'global': df}, output_directory / 'aligned_tilt_series.star')
