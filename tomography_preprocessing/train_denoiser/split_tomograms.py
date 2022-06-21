from pathlib import Path
from typing import Optional

import pandas as pd
import starfile
import rich
import typer
from rich.progress import track

from ._cli import cli
from .. import utils
from ..utils.relion import relion_pipeline_job

console = rich.console.Console(record=True)


@cli.command(name='Split')
@relion_pipeline_job
def split_tomograms(
    tilt_series_star_file: Path = typer.Option(...),
    output_directory: Path = typer.Option(...),
    tomogram_names: str = typer.Option(...),
):
"""Align one or multiple tilt-series in AreTomo using RELION tilt-series metadata.

    Parameters
    ----------
    tilt_series_star_file: RELION tilt-series STAR file.
    output_directory: directory in which results will be stored.
    tomogram_names: specify which tilt-series you wish to use to train the denoising network.
        Their names must match 'rlnTomoName' in the tilt_series_star_file. Separate each tilt-
series name with
        a comma (e.g. TS_100, TS_200, TS_300). We recommend 3-5 tomograms.

    Returns
    -------
    A split_tilt_series.star file. Use this file to generate tomograms with the RELION generat
e tomograms function.
    """
#    if not tilt_series_star_file.exists():
#        e = 'Could not find tilt series star file'
#        console.log(f'ERROR: {e}')
#        raise RuntimeError(e)
   
    console.log('Doing stuff.')

    console.save_html(str(output_directory / 'log.html'), clear=False)
    console.save_text(str(output_directory / 'log.txt'), clear=False)
