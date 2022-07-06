from pathlib import Path

import pandas as pd
import starfile
import typer

def create_splitting_job_directory_structure(output_directory: Path) -> Path:
    """Create directory structure for a tomogram splitting job."""
    metadata_directory = output_directory / 'tilt_series'
    metadata_directory.mkdir(parents=True, exist_ok=True)
    return metadata_directory
    
def write_split_tilt_series_star(
    global_star: pd.DataFrame,
    metadata_directory: Path,
):
    for idx, row in global_star.iterrows():
        tomo_star = starfile.read(row['rlnTomoTiltSeriesStarFile'])
        tomo_star_h1 = tomo_star.iloc[::2,:]
        tomo_star_h2 = tomo_star.iloc[1::2,:]	
        starfile.write({f"{row['rlnTomoName']}_h1": tomo_star_h1}, f"{metadata_directory / row['rlnTomoName']}_h1.star")
        starfile.write({f"{row['rlnTomoName']}_h2": tomo_star_h2}, f"{metadata_directory / row['rlnTomoName']}_h2.star")

def generate_split_global_star(
    global_star: pd.DataFrame,
    metadata_directory: Path,
) -> pd.DataFrame:
    #Duplicate global star
    global_star = pd.concat([global_star]*2, ignore_index=True)
    
    #Add h1 and h2 to rlnTomoName first and second halves
    star_half_length = len(global_star)//2
    global_star_copy = global_star.copy()
    global_star_copy['rlnTomoName'].iloc[0:star_half_length] = global_star_copy['rlnTomoName'].iloc[0:star_half_length].apply(lambda x: f'{x}_h1')
    global_star_copy['rlnTomoName'].iloc[star_half_length:] = global_star_copy['rlnTomoName'].iloc[star_half_length:].apply(lambda x: f'{x}_h2')
    
    #Modify TS star names to include h1 and h2
    global_star_copy['rlnTomoTiltSeriesStarFile'].iloc[0:star_half_length] = global_star_copy['rlnTomoTiltSeriesStarFile'].iloc[0:star_half_length].apply(lambda x: f'{metadata_directory}/{Path(x).stem}_h1{Path(x).suffix}')
    global_star_copy['rlnTomoTiltSeriesStarFile'].iloc[star_half_length:] = global_star_copy['rlnTomoTiltSeriesStarFile'].iloc[star_half_length:].apply(lambda x: f'{metadata_directory}/{Path(x).stem}_h2{Path(x).suffix}')
    return global_star_copy
