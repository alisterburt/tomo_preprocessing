from pathlib import Path
from typing import Optional

import pandas as pd
import starfile
import rich
import typer
from rich.progress import track

from .._cli import cli
from ... import utils
from ...utils.relion import relion_pipeline_job

console = rich.console.Console(record=True)

@cli.command(name='Split')
@relion_pipeline_job
def split_tomograms(
    tilt_series_star_file: Path = typer.Option(...),
    output_directory: Path = typer.Option(...),
):
    """Align one or multiple tilt-series in AreTomo using RELION tilt-series metadata.

    Parameters
    ----------
    tilt_series_star_file: RELION tilt-series STAR file.
    output_directory: directory in which results will be stored.

    Returns
    -------
    A tilt-series .star file (denoiser_split.star) to use for generating tomograms with the RELION generate tomograms function
    prior to denoising with cryoCare/care4relion.
    """
    if not tilt_series_star_file.exists():
        e = 'Could not find tilt series star file'
        console.log(f'ERROR: {e}')
        raise RuntimeError(e)    
     
    #NEW IDEA: duplicate global star with: pd.concat([star['global']]*2, ignore_index=True);
    # like Write_Aligned_Star loop (see below) through each tomo_name but add _h1 (only loop 1st half)
    # loop again thru 2nd half with _h2 via df.head([LENGTH OF DF /2]).iterrows()
    # repeat with TS star location
        
    tilt_series_metadata = utils.star.iterate_tilt_series_metadata(
        tilt_series_star_file=tilt_series_star_file,
        tilt_series_id=None
    )
    
    for tilt_series_id, _, _ in tilt_series_metadata:
        
	split_tilt_series
                 

    #EXAMPLE BELOW
   
    #df = starfile.read(tilt_series_star_file, always_dict=True)['global']

    # update individual tilt series star files
    #df['rlnTomoTiltSeriesStarFile'] = [
    #    job_directory / 'tilt_series' / f'{tilt_series_id}.star'
    #    for tilt_series_id in df['rlnTomoName']
    #]
    # check which output files were succesfully generated, take only those
    #df = df[df['rlnTomoTiltSeriesStarFile'].apply(lambda x: x.exists())]
    #starfile.write({'global': df}, job_directory / 'aligned_tilt_series.star')        
        
    
    #Write new global star (denoiser_split.star) with all tomograms
    
    console.save_html(str(output_directory / 'log.html'), clear=False)
    console.save_text(str(output_directory / 'log.txt'), clear=False)
