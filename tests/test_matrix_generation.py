import os
from pathlib import Path

from tomography_preprocessing.tilt_series_alignment.imod_generate_matrices import generate_imod_matrices
os.chdir('/Users/aburt/Programming/tomo_preprocessing/HIV-2TS-sjors')
generate_imod_matrices(
    tilt_series_star_file='./TiltSeriesAlign/job005/aligned_tilt_series.star',
    tomogram_dimensions=(4000, 4000, 3000),
    output_directory=Path('test_imod_matrices')
)
