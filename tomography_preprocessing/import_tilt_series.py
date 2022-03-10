from os import PathLike
from pathlib import Path
from typing import Optional, List

import mdocfile
import numpy as np
import pandas as pd
import starfile
from thefuzz import process

from .utils import basename


def import_tilt_series_from_serial_em(
        tilt_image_movie_wildcard: str,
        mdoc_file_wildcard: str,
        nominal_tilt_axis_angle: float,
        nominal_pixel_size: float,
        voltage: float,
        spherical_aberration: float,
        amplitude_contrast: float,
        output_directory: PathLike,
        dose_per_tilt_image: Optional[float] = None,
        prefix: Optional[str] = None,
        mtf_file: Optional[PathLike] = None,
) -> Path:
    """Import tilt-image movies and tilt-series metadata for CCP-EM pipeliner.

    Parameters
    ----------
    tilt_image_movie_wildcard : Set of filenames with wildcard characters
        for tilt image movie files.
    mdoc_file_wildcard : Set of filenames with wildcard characters for
        mdoc files containing tilt-series metadata.
    nominal_tilt_axis_angle : Nominal tilt axis angle in the images.
    nominal_pixel_size : Nominal pixel spacing of the tilt-images in angstroms.
    voltage : Acceleration voltage (keV)
    spherical_aberration : Spherical aberration (mm)
    amplitude_contrast : Amplitude contrast fraction (e.g. 0.1)
    dose_per_tilt_image : dose in electrons per square angstrom in each tilt image.
        If set, this will override the values from the mdoc file
    prefix : a prefix which will be added to the tilt-series name.
        This avoids name collisions when processing data from multiple collection
        sessions.

    Returns
    -------
    tilt_series_star_file : a text file pointing to a bunch of files containing actual data
    """
    tilt_image_files = list(Path().glob(tilt_image_movie_wildcard))
    mdoc_files = list(Path().glob(mdoc_file_wildcard))
    tilt_series_directory = Path(output_directory) / 'tilt_series'
    tilt_series_directory.mkdir(parents=True, exist_ok=True)

    tomogram_ids = [construct_tomogram_id(mdoc_file, prefix) for mdoc_file in mdoc_files]
    tilt_series_star_files = [f"{tilt_series_directory}/{tomogram_id}.star" for tomogram_id in tomogram_ids]

    global_data = {
        'rlnTomoName': tomogram_ids,
        'rlnTomoTiltSeriesStarFile': tilt_series_star_files,
        'rlnOpticsGroup': [1 for _ in mdoc_files]
    }
    global_df = pd.DataFrame(global_data)

    optics_data = {
        'rlnOpticsGroupName': [prefix],
        'rlnOpticsGroup': [1],
        'rlnVoltage': [voltage],
        'rlnSphericalAberration': [spherical_aberration],
        'rlnAmplitudeContrast': [amplitude_contrast],
        'rlnMicrographOriginalPixelSize': [nominal_pixel_size],
    }
    optics_df = pd.DataFrame(optics_data)

    if mtf_file is not None:
        optics_df['rlnMtfFileName'] = mtf_file

    global_star_file = Path(output_directory) / 'tilt_series.star'
    starfile.write(
        data={'optics': optics_df, 'global': global_df},
        filename=global_star_file,
        overwrite=True
    )

    for mdoc_file, output_filename in zip(mdoc_files, tilt_series_star_files):
        write_tilt_series_star_file(
            mdoc_file=mdoc_file,
            tilt_image_files=tilt_image_files,
            dose_per_tilt_image=dose_per_tilt_image,
            prefix=prefix,
            nominal_tilt_axis_angle=nominal_tilt_axis_angle,
            output_file=output_filename
        )


def construct_tomogram_id(mdoc_file: str, prefix: str) -> str:
    return f'{prefix}_{basename(mdoc_file)}'


def write_tilt_series_star_file(
        mdoc_file: Path,
        tilt_image_files: List[Path],
        prefix: str,
        nominal_tilt_axis_angle: float,
        dose_per_tilt_image: Optional[float],
        output_file: PathLike
):
    tilt_series_id = construct_tomogram_id(mdoc_file, prefix)

    df = mdocfile.read(mdoc_file, camel_to_snake=True)
    df = df.sort_values(by="date_time", ascending=True)
    df = add_pre_exposure_dose(mdoc_df=df, dose_per_tilt=dose_per_tilt_image)
    df = df.sort_values(by="tilt_angle", ascending=True)
    df = match_tilt_image_filenames(tilt_image_files, mdoc_df=df)
    df['tilt_series_id'] = tilt_series_id
    df['nominal_tilt_axis_angle'] = nominal_tilt_axis_angle
    df['optics_group'] = 1

    output_data = {
        'rlnTomoName': df['tilt_series_id'],
        'rlnTomoTiltMovieFile': df['matched_filename'],
        'rlnTomoTiltMovieFrameCount': df['num_sub_frames'],
        'rlnTomoTiltMovieIndex': df['z_value'],
        'rlnTomoNominalStageTiltAngle': df['tilt_angle'],
        'rlnTomoNominalTiltAxisAngle': df['nominal_tilt_axis_angle'],
        'rlnOpticsGroup': df['optics_group'],
        'rlnTomoNominalDefocus': df['target_defocus'],
        'rlnMicrographPreExposure': df['pre_exposure_dose'],
    }
    output_df = pd.DataFrame(output_data)
    starfile.write({'tilt_images': output_df}, output_file, overwrite=True)


def add_pre_exposure_dose(
    mdoc_df: pd.DataFrame, dose_per_tilt: Optional[float] = None
) -> pd.DataFrame:
    if dose_per_tilt is not None:
        pre_exposure_dose = dose_per_tilt * np.arange(len(mdoc_df))
    else:  # all zeros if exposure dose values not present in mdoc
        pre_exposure_dose = [0] * len(mdoc_df)

    if "exposure_dose" not in mdoc_df.columns or dose_per_tilt is not None:
        mdoc_df["pre_exposure_dose"] = pre_exposure_dose
    else:
        mdoc_df["pre_exposure_dose"] = np.cumsum(mdoc_df["exposure_dose"].to_numpy())
    return mdoc_df


def match_tilt_image_filenames(
    tilt_image_files: List[PathLike], mdoc_df: pd.DataFrame
) -> pd.DataFrame:
    tilt_image_file_basenames = [Path(f).stem for f in tilt_image_files]
    mdoc_df["mdoc_tilt_image_basename"] = mdoc_df["sub_frame_path"].apply(
        lambda x: Path(str(x).split("\\")[-1]).stem
    )
    tilt_image_basename_to_full = {
        tilt_image_file_basenames[i]: tilt_image_files[i]
        for i in range(len(tilt_image_files))
    }
    matched_filenames = []
    for mdoc_tilt_image_filename in mdoc_df["mdoc_tilt_image_basename"]:
        match, _ = process.extractOne(
            query=mdoc_tilt_image_filename,
            choices=tilt_image_file_basenames,
        )
        matched_file = tilt_image_basename_to_full[match]
        matched_filenames.append(matched_file)
    mdoc_df["matched_filename"] = matched_filenames
    return mdoc_df
