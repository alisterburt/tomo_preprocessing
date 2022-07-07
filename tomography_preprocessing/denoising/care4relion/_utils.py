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
    even_tomos = [f'{rows.rlnTomoTomogramHalvesForDenoising}_even.mrc' for idx,rows in training_tomograms_star.iterrows()]
    odd_tomos = [f'{rows.rlnTomoTomogramHalvesForDenoising}_odd.mrc' for idx,rows in training_tomograms_star.iterrows()]
    return even_tomos, odd_tomos

def generate_train_data_config_json(
        even_tomos: List,
        odd_tomos: List,
        training_dir: Path,
    ) -> Dict:
    train_data_config_json = json.loads(f'{{"even": {json.dumps(even_tomos)}, "odd": {json.dumps(odd_tomos)}, "patch_shape": [72, 72, 72], \
    "num_slices": 250, "split": 0.9, "tilt_axis": "Y", "n_normalization_samples": 50, "path": "{training_dir}"}}')
    return train_data_config_json

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
    
