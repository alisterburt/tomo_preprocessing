# tomography_preprocessing

*this repository has been archived as these programs are to be integrated into RELION from version 4.1*

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

For CryoCARE denoising, please install this version: https://github.com/EuanPyle/cryoCARE_mpido

A helptext can be found for each program with

```shell
<program_name> --help
```
