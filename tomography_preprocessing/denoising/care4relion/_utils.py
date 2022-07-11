from pathlib import Path
from typing import Tuple, List, Dict

import pandas as pd
import starfile
import typer
import json
import shutil

def create_denoised_tomograms_dir(
        output_directory: Path
) -> Tuple[Path, Path, Path]:
    training_dir = output_directory / 'external' / 'training' 
    training_dir.mkdir(parents=True, exist_ok=True)
    tomogram_dir = output_directory / 'tomograms'
    tomogram_dir.mkdir(parents=True, exist_ok=True)
    tilt_series_dir = output_directory / 'tilt_series'
    tilt_series_dir.mkdir(parents=True, exist_ok=True)
    return training_dir, tomogram_dir, tilt_series_dir
    
def parse_training_tomograms(
        training_tomograms: str
) -> List:
    training_tomograms = training_tomograms.strip().split(':')
    return training_tomograms

def generate_training_tomograms_star(
        global_star: pd.DataFrame,
        training_tomograms: List,
) -> pd.DataFrame:
    training_tomograms_idx = pd.DataFrame(global_star.rlnTomoName.tolist()).isin(training_tomograms).values
    if not any(training_tomograms_idx):
        e = f"Could not user specified training tomograms ({', '.join(str(x) for x in training_tomograms)}) in tilt series star file"
        console.log(f'ERROR: {e}')
        raise RuntimeError(e)
    training_tomograms_star = global_star[training_tomograms_idx]
    return training_tomograms_star
    
def find_tomogram_halves(
        training_tomograms_star: pd.DataFrame,
) -> Tuple[List, List]:
    even_tomos = [f'{rows.rlnTomoTomogramHalvesForDenoisingEven}' for idx,rows in training_tomograms_star.iterrows()]
    odd_tomos = [f'{rows.rlnTomoTomogramHalvesForDenoisingOdd}' for idx,rows in training_tomograms_star.iterrows()]
    return even_tomos, odd_tomos

def generate_train_data_config_json(
        even_tomos: List,
        odd_tomos: List,
        training_dir: Path,
) -> Dict:
    train_data_config_json = json.loads(f'{{"even": {json.dumps(even_tomos)}, "odd": {json.dumps(odd_tomos)}, "patch_shape": [72, 72, 72], \
    "num_slices": 250, "split": 0.9, "tilt_axis": "Y", "n_normalization_samples": 50, "path": "{training_dir}"}}')
    return train_data_config_json

def generate_train_config_json(
        training_dir: Path,
	model_name: str,
) -> Dict:
    train_config_json = json.loads(f'{{"train_data": "{training_dir}", "epochs": 100, "steps_per_epoch": 200, "batch_size": 16, "unet_kern_size": 3, \
    "unet_n_depth": 3, "unet_n_first": 16, "learning_rate": 0.0004, "model_name": "{model_name}", "path": "{training_dir}"}}')
    return train_config_json

def generate_predict_json(
        even_tomos: List,
        odd_tomos: List,
	training_dir: Path,
	model_name: str or Path,
        output_directory: Path,
        n_tiles: Tuple[int,int,int],
) -> Dict:
    if type(model_name) is str: model_name = f"{training_dir / model_name}.tar.gz" 
    predict_json = json.loads(f'{{"path": "{model_name}", "even": {json.dumps(even_tomos)}, \
    "odd": {json.dumps(odd_tomos)}, "n_tiles": {list(n_tiles)}, "output": "{output_directory / "tomograms"}"}}')
    return predict_json

def save_json(
        training_dir: Path,
        output_json: Dict,
	json_prefix: str,
):
    with open(f'{training_dir}/{json_prefix}.json', 'w') as outfile:
        json.dump(output_json, outfile, indent=4) 
	
def save_tilt_series_stars(
        global_star: pd.DataFrame,
        tilt_series_dir: Path,
):
    for idx,row in global_star.iterrows():
        shutil.copyfile(f"{row['rlnTomoTiltSeriesStarFile']}", f'{tilt_series_dir}/{row["rlnTomoName"]}.star')
    global_star['rlnTomoTiltSeriesStarFile'] = global_star.apply(lambda x: f'{tilt_series_dir}/{x["rlnTomoName"]}.star', axis=1)

def save_global_star(
        global_star: pd.DataFrame,
        tomogram_dir: Path,
        output_directory: Path,
):
    global_star['rlnTomoDenoisedTomogram'] = global_star.apply(lambda x: f'{tomogram_dir}/rec_{x["rlnTomoName"]}.mrc', axis=1)
    starfile.write({'global': global_star}, f'{output_directory}/tomograms.star')
    
def rename_predicted_tomograms(
    even_tomos: List,
    tomogram_dir: Path,
    even_suffix: str,
):
    even_tomos = [Path(tomo) for tomo in even_tomos]
    even_tomos = [Path(f"{tomogram_dir}/{tomo.name}") for tomo in even_tomos]
    [tomo.rename(Path(f"{tomogram_dir}/{tomo.stem.replace(even_suffix,'')}{tomo.suffix}")) for tomo in even_tomos]
