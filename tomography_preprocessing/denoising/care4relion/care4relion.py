from pathlib import Path
from typing import Optional

import pandas as pd
import starfile
import rich
import typer
import subprocess
from rich.progress import track

from .train_neural_network import train_neural_network
from ._utils import *
from .constants import predict_config_prefix, even_suffix 
from .._cli import cli
from ...utils.relion import relion_pipeline_job

console = rich.console.Console(record=True)

@cli.command(name='Care4Relion')
@relion_pipeline_job
def care4relion(
    tilt_series_star_file: Path = typer.Option(...),
    output_directory: Path = typer.Option(...),
    training_tomograms: str = typer.Option(...),
    model_name: Optional[Path] = typer.Option(None),

):
    """Denoises tomograms using cryoCARE (Thorsten Wagner version) (https://github.com/thorstenwagner/cryoCARE_mpido)
    
    Requires that two tomograms have been generated using the same sample. These can be generated via taking odd/even 
    frames during Motion Correction (optimal) or by taking odd/even tilts during tomogram reconstruction.
    The location of these tomograms should be specified in the global star file for all tilt series with the headers: 
    
     
    _rlnTomoTomogramHalvesForDenoisingEven
    
      _rlnTomoTomogramHalvesForDenoisingOdd

    Parameters
    ----------
    
    tilt_series_star_file: RELION tilt-series STAR file.
    
    output_directory: directory in which results will be stored.
    
    training_tomograms: tomograms which are to be used for denoising neural network training.
        User should enter tomogram names as rlnTomoName, separated by colons, e.g. TS_1:TS_2
	
    model_name (optional): if you have already trained a denoising neural network and want to skip the training step,
        user can provide the path to the model.tar.gz produced by a previous cryoCARE denoising job. This will skip
        straight to tomogram generation.

    Returns
    -------
    Denoised tomograms.
    """
    if not tilt_series_star_file.exists():
        e = 'Could not find tilt series star file'
        console.log(f'ERROR: {e}')
        raise RuntimeError(e)    
      
    global_star = starfile.read(tilt_series_star_file, always_dict=True)['global']
    
    if not 'rlnTomoTomogramHalvesForDenoisingEven' in global_star.columns:
        e = 'Could not find rlnTomoTomogramHalvesForDenoisingEven in tilt series star file.'
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
    
    
    
    
    if model_name is None:
        console.log('User has not provided path to a previously trained neural network, beginning to train now...')
        model_name = train_neural_network(
            tilt_series_star_file=tilt_series_star_file,
            output_directory=output_directory,
            training_tomograms=training_tomograms,
            even_tomos=even_tomos,
            odd_tomos=odd_tomos,
            training_dir=training_dir,
        )
    else:
        if not model_name.exists():
            e = f'Could not find user specified model_name ("{model_name}")'
            console.log(f'ERROR: {e}')
            raise RuntimeError(e)
    
    predict_json = generate_predict_json(
        even_tomos=even_tomos,
        odd_tomos=odd_tomos,
	training_dir=training_dir,
	model_name=model_name,
        output_directory=output_directory,
    )
    
    save_json(
        training_dir=training_dir,
        output_json=predict_json,
	json_prefix=predict_config_prefix,
    )

    console.log('Generating denoised tomograms')
    cmd = f"cryoCARE_predict.py --conf {training_dir}/{predict_config_prefix}.json"
    #subprocess.run(cmd, shell=True)
    subprocess.run(['echo','cryoCARE_predict.py','--conf',f'{training_dir}/{predict_config_prefix}.json']) ### 
            
    rename_predicted_tomograms(
    even_tomos=even_tomos,
    tomogram_dir=tomogram_dir,
    even_suffix=even_suffix,
    )
    
    console.log('Denoised tomograms successfully generated, finalising metadata')
    
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
