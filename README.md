# tomography_preprocessing

[![License](https://img.shields.io/pypi/l/tomography_preprocessing.svg?color=green)](https://github.com/alisterburt/tomography_preprocessing/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/tomography_preprocessing.svg?color=green)](https://pypi.org/project/tomography_preprocessing)
[![Python Version](https://img.shields.io/pypi/pyversions/tomography_preprocessing.svg?color=green)](https://python.org)
[![CI](https://github.com/alisterburt/tomography_preprocessing/actions/workflows/ci.yml/badge.svg)](https://github.com/alisterburt/tomography_preprocessing/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/alisterburt/tomography_preprocessing/branch/main/graph/badge.svg)](https://codecov.io/gh/alisterburt/tomography_preprocessing)

A cryo-ET tilt-series data preprocessing workflow for RELION 4.0

# Installation
In a virtual environment

```sh
git clone https://github.com/alisterburt/tomo_preprocessing.git
cd tomo_preprocessing
pip install -e .
```

# Programs

| Job Type  | Program |
| ------------- | ------------- |
| Import  | `relion_tomo_import SerialEM`  |
| Tilt-series alignment  | `relion_tomo_align_tilt_series IMOD:fiducials`  |
| Tilt-series alignment  | `relion_tomo_align_tilt_series IMOD:patch-tracking`  |
| Tilt-series alignment   | `relion_tomo_align_tilt_series AreTomo`  |
| Denoising (cryoCARE)   | `relion_tomo_denoise`  |

A helptext can be found for each program with

```shell
<program_name> --help
```
