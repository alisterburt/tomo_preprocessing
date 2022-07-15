from pathlib import Path
from typing import List

import pandas as pd
import starfile
import rich
import typer
import subprocess
from rich.progress import track

from ._utils import (
    generate_train_data_config_json,
    save_json,
    generate_train_config_json,
)
from .constants import TRAIN_DATA_CONFIG_PREFIX, MODEL_NAME, TRAIN_CONFIG_PREFIX

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
	json_prefix=TRAIN_DATA_CONFIG_PREFIX,
    )

    cmd = f"cryoCARE_extract_train_data.py --conf {training_dir}/{TRAIN_DATA_CONFIG_PREFIX}.json"
    subprocess.run(cmd, shell=True)
            
    train_config_json = generate_train_config_json(
        training_dir=training_dir,
	model_name=MODEL_NAME,
    )    
        
    save_json(
        training_dir=training_dir,
        output_json=train_config_json,
	json_prefix=TRAIN_CONFIG_PREFIX,
    )
    
    cmd = f"cryoCARE_train.py --conf {training_dir}/{TRAIN_CONFIG_PREFIX}.json"
    subprocess.run(cmd, shell=True)
    
    return MODEL_NAME
