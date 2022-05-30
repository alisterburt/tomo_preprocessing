from pathlib import Path
from typing import Callable, Dict, Any

import pandas as pd
from rich.console import Console

from .._job_utils import create_alignment_job_directory_structure
from ._utils import write_relion_tilt_series_alignment_output
from ... import utils


def align_single_tilt_series(
        tilt_series_id: str,
        tilt_series_df: pd.DataFrame,
        tilt_image_df: pd.DataFrame,
        alignment_function: Callable,
        alignment_function_kwargs: Dict[str, Any],
        output_directory: Path,
):
    """Align a single tilt-series in IMOD using RELION tilt-series metadata.

    Parameters
    ----------
    tilt_series_id: 'rlnTomoName' in RELION tilt-series metadata.
    tilt_series_df: master file for tilt-series metadata.
    tilt_image_df: file containing information for images in a single tilt-series.
    alignment_function: alignment function from yet_another_imod_wrapper.
    alignment_function_kwargs: keyword arguments specific to the alignment function.
    output_directory: directory in which results will be stored.
    """
    console = Console(record=True)

    # Create output directory structure
    image_dir, all_alignments_dir = \
        create_alignment_job_directory_structure(output_directory)
    alignment_dir = all_alignments_dir / tilt_series_id
    alignment_dir.mkdir(parents=True, exist_ok=True)

    # Establish filenames
    tilt_series_filename = f'{tilt_series_id}.mrc'
    tilt_image_metadata_filename = f'{tilt_series_id}.star'

    # Order is important in IMOD, sort by tilt angle
    tilt_image_df = tilt_image_df.sort_values(by='rlnTomoNominalStageTiltAngle', ascending=True)

    # Create tilt-series stack and align using IMOD
    # implicit assumption - one tilt-axis angle per tilt-series
    console.log('Creating tilt series stack')
    image_file_path = image_dir / tilt_series_filename
    utils.image.stack_image_files(
        image_files=tilt_image_df['rlnMicrographName'],
        output_image_file=image_file_path,
    )
    if not image_file_path.exists():
        e = f'Tilt image stack {tilt_series_id}.mrc failed to generate'
        console.log(f'ERROR: {e}') 
        raise RuntimeError(e)
    console.log('Running IMOD alignment')
    alignment_function(
        tilt_series_file=image_file_path,
        tilt_angles=tilt_image_df['rlnTomoNominalStageTiltAngle'],
        pixel_size=tilt_series_df['rlnMicrographOriginalPixelSize'],
        nominal_rotation_angle=tilt_image_df['rlnTomoNominalTiltAxisAngle'][0],
        output_directory=alignment_dir,
        **alignment_function_kwargs,
    )
    #Check IMOD is producing xf files as output
    if not ((alignment_dir / tilt_series_id)).with_suffix('.xf').exists():
        e = f'{tilt_series_id}.xf failed to generate. Tilt series alignment failed.'
        console.log(f'ERROR: {e}') 
        raise RuntimeError(e)    
    console.log('Writing STAR file for aligned tilt-series')
    write_relion_tilt_series_alignment_output(
        tilt_image_df=tilt_image_df,
        tilt_series_id=tilt_series_id,
        pixel_size=tilt_series_df['rlnMicrographOriginalPixelSize'],
        imod_directory=alignment_dir,
        output_star_file=image_dir / tilt_image_metadata_filename,
    )
    #Check star file produced
    if not ((image_dir / tilt_image_metadata_filename)).exists():
        e = f'Star file for {tilt_series_id} failed to generate'
        console.log(f'ERROR: {e}') 
        raise RuntimeError(e)    
