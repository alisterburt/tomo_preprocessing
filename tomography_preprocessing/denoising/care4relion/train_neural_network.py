from pathlib import Path

import pandas as pd
import starfile
import rich
import typer
import subprocess
from rich.progress import track

from ._utils import *
from .constants import train_data_config_prefix, model_name, train_config_prefix

console = rich.console.Console(record=True)

def train_neural_network(
        tilt_series_star_file: Path = typer.Option(...),
        output_directory: Path = typer.Option(...),
        training_tomograms: str = typer.Option(...),
        even_tomos: List = typer.Option(...),
        odd_tomos: List = typer.Option(...),
        training_dir: Path = typer.Option(...),
):
    train_data_config_json = generate_train_data_config_json(
        even_tomos=even_tomos,
        odd_tomos=odd_tomos,
        training_dir=training_dir,
    )  
        
    save_json(
        training_dir=training_dir,
        output_json=train_data_config_json,
	json_prefix=train_data_config_prefix,
    )

    cmd = f"cryoCARE_extract_train_data.py --conf {training_dir}/{train_data_config_prefix}.json"
    subprocess.run(cmd, shell=True)
    #subprocess.run(['echo','cryoCARE_extract_train_data.py','--conf',f'{training_dir}/{train_data_config_prefix}.json']) ###
            
    train_config_json = generate_train_config_json(
        training_dir=training_dir,
	model_name=model_name,
    )    
        
    save_json(
        training_dir=training_dir,
        output_json=train_config_json,
	json_prefix=train_config_prefix,
    )
    
    cmd = f"cryoCARE_train.py --conf {training_dir}/{train_config_prefix}.json"
    subprocess.run(cmd, shell=True)
    #subprocess.run(['echo','cryoCARE_train.py','--conf',f'{training_dir}/{train_config_prefix}.json']) ###
    
    return model_name
