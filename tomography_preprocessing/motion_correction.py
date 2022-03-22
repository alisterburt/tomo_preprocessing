from pathlib import Path
from typing import Optional

import pandas as pd
import starfile


def run_relion_motioncorr(
        tilt_series_star_file: Path,
        gain_reference_file: Path,
        gain_rotation: int,
        gain_flip: int,
        defect_file: Optional[Path] = None,
        first_frame_for_corrected_sum: int = 1,
        last_frame_for_corrected_sum: Optional[int] = None,
        power_spec_grouping: int = 1,
        power_spec_size_out: int = 512,
        b_factor: float = 150,
        dose_per_frame: float = 0,
        group_frames: int = 1,
        binning_factor: int = 1,
        x_patches: int = 3,
        y_patches: int = 3,
        use_relioncorr: bool = True,
        mpi: int = 1,
        threads: int = 1,
):
    pass


def create_relion_run_motioncor_input_file(
        tilt_series_star_file: Path,
        output_micrographs_star_file: Path,
):
    star = starfile.read(tilt_series_star_file)
    optics_block = star['optics']
    tilt_series_star_files = [f for f in star['global']['rlnTomoTiltSeriesStarFile']]
    df = pd.concat([starfile.read(file) for file in tilt_series_star_files])

    data_for_relion = {
        'rlnTomoName': df['rlnTomoName'],
        'rlnMicrographMovieName': df['rlnTomoTiltMovieFile'],
        'rlnOpticsGroup': df['rlnOpticsGroup'],
    }
    movie_df = pd.DataFrame(data_for_relion)

    starfile.write(
        data={'optics': optics_block, 'movies': movie_df},
        filename=output_micrographs_star_file,
        force_loop=True,
        overwrite=True,
    )


def create_output_corrected_star_files(
        corrected_micrographs_star_file: Path,
        output_directory: Path
):
    star = starfile.read(corrected_micrographs_star_file)
    output_tilt_series_star_file = Path(output_directory) / 'tilt_series.star'
    per_tilt_series_directory = Path(output_directory) / 'tilt_series'
    per_tilt_series_directory.mkdir(parents=True, exist_ok=True)

    optics_block = star['optics']
    micrographs = star['micrographs']
    tomo_ids = list(micrographs['rlnTomoName'].unique())
    grouped = micrographs.groupby(micrographs['rlnTomoName'])

    output_filenames = [
        per_tilt_series_directory / f'{tomo_id}.star'
        for tomo_id in tomo_ids
    ]
    for tomo_id, output_filename in zip(tomo_ids, output_filenames):
        starfile.write(
            data={'optics': optics_block, 'tilt_images': grouped.getgroup(tomo_id)},
            filename=output_filename,
            force_loop=True
        )

    global_data = {
        'rlnTomoName': tomo_ids,
        'rlnTomoTiltSeriesStarFile': output_filenames,
        'rlnOpticsGroup': optics_block['optics']['rlnOpticsGroup'],
    }
    starfile.write(data={'optics': optics_block,
                         'global': global_data},
                   filename=output_tilt_series_star_file,
                   force_loop=True,
                   overwrite=True)

