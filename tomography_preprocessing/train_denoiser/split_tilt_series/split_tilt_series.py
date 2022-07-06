from pathlib import Path

import pandas as pd
import starfile
import rich
import typer
from rich.progress import track

from .._cli import cli
from ...utils.relion import relion_pipeline_job
from ._utils import (
    create_splitting_job_directory_structure,
    write_split_tilt_series_star,
    generate_split_global_star,
)

console = rich.console.Console(record=True)

@cli.command(name='Split')
@relion_pipeline_job
def split_tilt_series(
    tilt_series_star_file: Path = typer.Option(...),
    output_directory: Path = typer.Option(...),
):
    """Splits tilt series into odd and even tilt tilt-series in order to generate half tomogram sets for denoising

    Parameters
    ----------
    tilt_series_star_file: RELION tilt-series STAR file.
    output_directory: directory in which results will be stored.

    Returns
    -------
    A tilt-series .star file (split_tilt_series.star) to use for generating tomograms with the RELION generate tomograms function
    prior to denoising.
    """
    if not tilt_series_star_file.exists():
        e = 'Could not find tilt series star file'
        console.log(f'ERROR: {e}')
        raise RuntimeError(e)    
  
    metadata_directory = create_splitting_job_directory_structure(output_directory) 
    
    global_star = starfile.read(tilt_series_star_file, always_dict=True)['global']
    
    write_split_tilt_series_star(global_star, metadata_directory)
    
    global_star = generate_split_global_star(global_star, metadata_directory)
    
    starfile.write({'global': global_star}, f"{output_directory / 'split_tilt_series.star'}")
    
    console.save_html(str(output_directory / 'log.html'), clear=False)
    console.save_text(str(output_directory / 'log.txt'), clear=False)
