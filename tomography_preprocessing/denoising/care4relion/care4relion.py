from pathlib import Path

import pandas as pd
import starfile
import rich
import typer
import json
from rich.progress import track

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
    
    #=====Function 1
    training_tomograms = training_tomograms.strip().split(':')
    #=====/Function 1
    
    #=====Function 2
    training_tomograms_idx = pd.DataFrame(global_star.rlnTomoName.tolist()).isin(training_tomograms).values
    if not any(training_tomograms_idx):
        e = f"Could not user specified training tomograms ({', '.join(str(x) for x in training_tomograms)}) in tilt series star file"
        console.log(f'ERROR: {e}')
        raise RuntimeError(e)
    training_tomograms_star = global_star[training_tomograms_idx]
    #=====/Function 2
    
    #=====Function 3
    even_tomos = [f'{rows.rlnTomoTomogramHalvesForDenoising}_even.mrc' for idx,rows in training_tomograms_star.iterrows()]
    odd_tomos = [f'{rows.rlnTomoTomogramHalvesForDenoising}_odd.mrc' for idx,rows in training_tomograms_star.iterrows()]
    #=====/Function 3
    
    #Training_dir
    training_dir = Path('test') ############
    
    #Add other user defined options, and let user define training tomograms and GPU ID

    #=====Function 4
    train_data_config_json_template = json.loads(f'{{"even": {json.dumps(even_tomos)}, "odd": {json.dumps(odd_tomos)}, "patch_shape": [72, 72, 72], \
    "num_slices": 250, "split": 0.9, "tilt_axis": "Y", "n_normalization_samples": 50, "path": "{str(training_dir)}"}}')
    #=====/Function 4
    
    with open(f'{str(training_dir)}/train_data_config.json', 'w') as outfile:
        json.dump(train_data_config_json_template, outfile, indent=4)   
    
    
    #Run config.json
    
    #Create other json files and run
    
    console.save_html(str(output_directory / 'log.html'), clear=False)
    console.save_text(str(output_directory / 'log.txt'), clear=False)
