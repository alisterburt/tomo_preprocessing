# Design:
# relion_tomo_train_denoise Split --i global.star --tn [names of tomos to train]
# --o output_dir; then use reconstruct tomograms; relion_tomo_train_denoise CryoCare --i split.star
# --o output_dir;

###########

### This is template script for generating multiple tomograms, this should be program independent

###########

from pathlib import Path

import pandas as pd
import starfile
import typer

#def split_global_star(
#    global_star: Path,
#    output_directory: Path,
#):
#    star = starfile.read(global_star)
    
    #for each line, take rln name, add _h1, add line to df, change to new TS star, repeat with _h2
    
#    starfile.write({f'global': star}, output_directory / 'split_tilt_series.star')
    
#def split_tilt_series_star(
#    tilt_series_star: Path,
#    rln_tomo_name: str,
#    output_directory: Path,
#): 
#    star = starfile.read(tilt_series_star)

#    star_h1 = star.iloc[::2,:]
#    star_h2 = star.iloc[1::2,:]

#    starfile.write({f'{rln_tomo_name}_h1': star_h1}, output_directory / 'f{rln_tomo_name}_h1.star')
#    starfile.write({f'{rln_tomo_name}_h2': star_h2}, output_directory / 'f{rln_tomo_name}_h2.star')
    

