from pathlib import Path
from typing import Optional

import pandas as pd
import starfile


def run_relion_ctffind(
        tilt_series_star_file: Path,
        output_directory: Path,
        use_noDW: bool = True,
        fft_box: int = 512,
        res_min: float = 30.0,
        res_max: float = 5.0,
        df_min: float = 5000.0,
        df_max: float = 50000.0,
        df_step: float = 150.0,

        use_ctffind4: bool = True,
        use_summed_power_spectra: bool = False,
        ctffind4_exe: str,
        exhaustive_search: bool = False,
        ctf_window: int = -1,

        use_gctf: bool = False,
        gctf_exe: str,
        ignore_searches: bool = True,
        do_EPA: bool = True
        extra_gctf_args: str = '',
        gpu_ids: str = '',

        mpi: int = 1,
        threads: int = 1,
):
    output_directory.mkdir(parents=True, exist_ok=True)
    ctffind_input_star_file = output_directory / 'relion_ctffind_input.star'
    create_relion_run_ctffind_input_file(tilt_series_star_file, ctffind_input_star_file)
    # TODO: actually run relion ctffind
    ctffind_output_star_file = output_directory / 'micrographs_ctf.star'
    create_output_star_files(ctffind_output_star_file, output_directory)



def create_relion_run_ctffind_input_file(
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
        'rlnMicrographName': df['rlnMicrographName']
    }
    micrograph_df = pd.DataFrame(data_for_relion)

    starfile.write(
        data={'optics': optics_block, 'micrographs': micrograph_df},
        filename=output_micrographs_star_file,
        force_loop=True,
        overwrite=True,
    )


def create_output_star_files(
        corrected_micrographs_star_file: Path,
        output_directory: Path
):
    star = starfile.read(corrected_micrographs_star_file)
    output_tilt_series_star_file = Path(output_directory) / 'tilt_series.star'
    per_tilt_series_directory = Path(output_directory) / 'tilt_series'

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
            force_loop=True,
        )

    global_data = {
        'rlnTomoName': tomo_ids,
        'rlnTomoTiltSeriesStarFile': output_filenames,
        'rlnOpticsGroup': optics_block['rlnOpticsGroup'],
    }
    starfile.write(data={'optics': optics_block,
                         'global': global_data},
                   filename=output_tilt_series_star_file,
                   force_loop=True,
                   overwrite=True)