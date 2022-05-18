from pathlib import Path
from typing import Callable, Dict, Any

import pandas as pd

from tomography_preprocessing import utils
from ._alignment_utils import create_alignment_job_directory_structure


def align_single_tilt_series(
        tilt_series_id: str,
        tilt_series_df: pd.DataFrame,
        tilt_image_df: pd.DataFrame,
        alignment_function: Callable,
        alignment_function_kwargs: Dict[str, Any],
        output_directory: Path,
):
    # Create output directory structure
    tilt_series_directory, imod_alignments_directory = \
        create_alignment_job_directory_structure(output_directory)
    imod_directory = imod_alignments_directory / tilt_series_id
    imod_directory.mkdir(parents=True, exist_ok=True)

    # Establish filenames
    tilt_series_filename = f'{tilt_series_id}.mrc'
    tilt_image_metadata_filename = f'{tilt_series_id}.star'
    tilt_series_path = tilt_series_directory / tilt_series_filename
    tilt_image_metadata_star_path = tilt_series_directory / tilt_image_metadata_filename

    # Order is important in IMOD, sort by tilt angle
    tilt_image_df = tilt_image_df.sort_values(by='rlnTomoNominalStageTiltAngle', ascending=True)

    # Create tilt-series stack and align using IMOD
    # implicit assumption - one tilt-axis angle per tilt-series
    utils.image.stack_image_files(
        image_files=tilt_image_df['rlnMicrographName'],
        output_image_file=tilt_series_path
    )
    alignment_function(
        tilt_series_file=tilt_series_path,
        tilt_angles=tilt_image_df['rlnTomoNominalStageTiltAngle'],
        pixel_size=tilt_series_df['rlnMicrographOriginalPixelSize'],
        nominal_rotation_angle=tilt_image_df['rlnTomoNominalTiltAxisAngle'][0],
        output_directory=imod_directory,
        **alignment_function_kwargs
    )
    utils.imod.write_relion_tilt_series_alignment_output(
        tilt_image_df=tilt_image_df,
        tilt_series_id=tilt_series_id,
        pixel_size=tilt_series_df['rlnMicrographOriginalPixelSize'],
        imod_directory=imod_directory,
        output_star_file=tilt_image_metadata_star_path
    )