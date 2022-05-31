from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

from ..utils.transformations import S, Rx, Ry, Rz


def create_alignment_job_directory_structure(output_directory: Path) -> Tuple[Path, Path]:
    """Create directory structure for an IMOD alignment job."""
    tilt_series_directory = output_directory / 'tilt_series'
    tilt_series_directory.mkdir(parents=True, exist_ok=True)

    imod_alignments_directory = output_directory / 'alignments'
    imod_alignments_directory.mkdir(parents=True, exist_ok=True)
    return tilt_series_directory, imod_alignments_directory


def relion_tilt_series_alignment_parameters_to_relion_matrix(
        specimen_shifts: pd.DataFrame,
        euler_angles: pd.DataFrame,
        tilt_image_dimensions: np.ndarray,
        tomogram_dimensions: np.ndarray,
):
    """Generate affine matrices transforming points in 3D to 2D in tilt-images.

    Projection model:
    3D specimen is rotated about its center then translated such that the projection
    of points onto the XY-plane gives their position in a tilt-image.

    More specifically
    - 3D specimen is rotated about its center by
        - shifting the origin to the specimen center
        - rotated extrinsically about the Y-axis by the tilt angle
        - rotated extrinsically about the Z-axis by the in plane rotation angle
    - 3D specimen is translated to align coordinate system with tilt-image
        - move center-of-rotation of specimen to center of tilt-image
        - move center-of-rotation of specimen to rotation center in tilt-image

    Parameters
    ----------
    specimen_shifts: XY-shifts which align the projected specimen with tilt-images
    euler_angles: YZX intrinsic Euler angles which transform the specimen
    tilt_image_dimensions: XY-dimensions of tilt-series.
    tomogram_dimensions: size of tomogram in XYZ
    """
    tilt_image_center = tilt_image_dimensions / 2
    specimen_center = tomogram_dimensions / 2

    # Transformations, defined in order of application
    s0 = S(-specimen_center)  # put specimen center-of-rotation at the origin
    r0 = Rx(euler_angles['rlnTomoXTilt'])  # rotate specimen around X-axis
    r1 = Ry(euler_angles['rlnTomoYTilt'])  # rotate specimen around Y-axis
    r2 = Rz(euler_angles['rlnTomoZRot'])  # rotate specimen around Z-axis
    s1 = S(specimen_shifts)  # shift projected specimen in xy (camera) plane
    s2 = S(tilt_image_center)  # move specimen back into tilt-image coordinate system

    # compose matrices
    transformations = s2 @ s1 @ r2 @ r1 @ r0 @ s0
    return np.squeeze(transformations)