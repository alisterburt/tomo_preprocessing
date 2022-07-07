from pathlib import Path

import pandas as pd
import starfile
import rich
import typer
import subprocess
from rich.progress import track

from ._utils import *
from .._cli import cli
from ...utils.relion import relion_pipeline_job

console = rich.console.Console(record=True)

@cli.command(name='Care4Relion')
@relion_pipeline_job
def care4relion(
    tilt_series_star_file: Path = typer.Option(...),
    output_directory: Path = typer.Option(...),
    training_tomograms: str = typer.Option(...),
):
    """CARE

    Parameters
    ----------
    tilt_series_star_file: RELION tilt-series STAR file.
    output_directory: directory in which results will be stored.
    training_tomograms: tomograms which are to be used for denoising neural network training.
        User should enter tomogram names as rlnTomoName, separated by colons, e.g. TS_1:TS_2

    Returns
    -------
    CARE
    """
    if not tilt_series_star_file.exists():
        e = 'Could not find tilt series star file'
        console.log(f'ERROR: {e}')
        raise RuntimeError(e)    
      
    global_star = starfile.read(tilt_series_star_file, always_dict=True)['global']
    
    if not 'rlnTomoTomogramHalvesForDenoising' in global_star.columns:
        e = 'Could not find rlnTomoTomogramHalvesForDenoising in tilt series star file.'
        console.log(f'ERROR: {e}')
        raise RuntimeError(e)
    
    training_dir, tomogram_dir, tilt_series_dir = \
        create_denoised_tomograms_dir(output_directory)
    
    training_tomograms = parse_training_tomograms(training_tomograms)

    training_tomograms_star = generate_training_tomograms_star(
        global_star=global_star,
        training_tomograms=training_tomograms,
    )
    
    even_tomos, odd_tomos = find_tomogram_halves(training_tomograms_star)
    
    

    ########LATER: Add other user defined options ###########

    

    train_data_config_json = generate_train_data_config_json(
        even_tomos=even_tomos,
        odd_tomos=odd_tomos,
        training_dir=training_dir,
    )  
    
    train_data_config_prefix = 'train_data_config'
    
    save_json(
        training_dir=training_dir,
        output_json=train_data_config_json,
	json_prefix=train_data_config_prefix,
    )

    subprocess.run(["echo","cryoCARE_extract_train_data.py","--conf",f"{training_dir}/{train_data_config_prefix}.json"])
        
    
    
    #########LATER:Create other json files and run ############
    
    
    
    
    
    
    save_tilt_series_stars(
        global_star=global_star,
        tilt_series_dir=tilt_series_dir,
    )
    
    save_global_star(
        global_star=global_star,
        tomogram_dir=tomogram_dir,
        output_directory=output_directory,
    )    
    
    console.save_html(str(output_directory / 'log.html'), clear=False)
    console.save_text(str(output_directory / 'log.txt'), clear=False)
