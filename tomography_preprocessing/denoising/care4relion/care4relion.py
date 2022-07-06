from pathlib import Path

import pandas as pd
import starfile
import rich
import typer
from rich.progress import track

from .._cli import cli
from ...utils.relion import relion_pipeline_job

console = rich.console.Console(record=True)

@cli.command(name='Care4Relion')
@relion_pipeline_job
def care4relion(
    tilt_series_star_file: Path = typer.Option(...),
    output_directory: Path = typer.Option(...),
):
    """CARE

    Parameters
    ----------
    tilt_series_star_file: RELION tilt-series STAR file.
    output_directory: directory in which results will be stored.

    Returns
    -------
    CARE
    """
    if not tilt_series_star_file.exists():
        e = 'Could not find tilt series star file'
        console.log(f'ERROR: {e}')
        raise RuntimeError(e)    
      
    #Detect _rlnTomoDenoisingSplitTomogram Exists, if not, recommend split tomo must be fed to Rec Tomo and use the output of that here
    
    #Use _rlnTomoDenoisingSplitTomogram to find both halves of tomogram
    
    #Generate json file for train_data_config.json
    
    #Add other user defined options, and let user define training tomograms and GPU ID
    
    #Run config.json
    
    #Create other json files and run
    
    console.save_html(str(output_directory / 'log.html'), clear=False)
    console.save_text(str(output_directory / 'log.txt'), clear=False)
