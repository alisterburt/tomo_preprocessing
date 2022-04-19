import os
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

import numpy as np


def read_xf(file: os.PathLike) -> np.ndarray:
    """Read an IMOD xf file into an (n, 6) numpy array.

    The file with alignment transforms (option OutputTransformFile) contains one
    line per view, each with a linear transformation specified by six numbers:
        A11 A12 A21 A22 DX DY
    where the coordinate (X, Y) is transformed to (X', Y') by:
        X' = A11 * X + A12 * Y + DX
        Y' = A21 * X + A22 * Y + DY
    """
    return np.loadtxt(fname=file, dtype=float).reshape((-1, 6))


def read_tlt(file: os.PathLike) -> np.ndarray:
    """Read an IMOD tlt file into an (n, ) numpy array."""
    return np.loadtxt(fname=file, dtype=float).reshape(-1)


def get_xf_shifts(xf: np.ndarray) -> np.ndarray:
    """Extract XY shifts from IMOD xf data.

    Output is an (n, 2) numpy array of shifts which center tilt-images.
    """
    transformation_matrices = get_xf_transformation_matrices(xf)
    post_transformation_shifts = xf[:, -2:].reshape((-1, 2, 1))
    pre_transformation_shifts = transformation_matrices @ post_transformation_shifts
    return pre_transformation_shifts.reshape((-1, 2))


def get_xf_transformation_matrices(xf: np.ndarray) -> np.ndarray:
    """Extract the 2D transformation matrix from IMOD xf data.

    Output is an (n, 2, 2) numpy array of matrices.
    """
    return xf[:, :4].reshape((-1, 2, 2))


def get_xf_rotation_angles(xf: np.ndarray) -> np.ndarray:
    """Extract the in plane rotation angle from IMOD xf data.

    Output is an (n, ) numpy array of angles in degrees. This function assumes
    that the transformation in the xf file is a simple 2D rotation.
    """
    transformation_matrices = get_xf_transformation_matrices(xf)
    cos_theta = transformation_matrices[:, 0, 0]
    return np.rad2deg(np.arccos(cos_theta))


@lru_cache(maxsize=100)
def get_stack_prefix(imod_directory: Path) -> str:
    stem_counter = defaultdict(int)
    for file in imod_directory.glob('*'):
        stem_counter[file.stem] += 1

    if len(stem_counter) == 0:
        raise RuntimeError('no files found in IMOD directory')

    max_count = 0
    for stem in stem_counter:
        if stem_counter[stem] > max_count:
            max_count = stem_counter[stem]
            highest_frequency_stem = stem
    return highest_frequency_stem


def get_xf_file(imod_directory: Path) -> Path:
    """Get the xf file containing image transforms from an IMOD directory."""
    return imod_directory / f'{get_stack_prefix(imod_directory)}.xf'


def get_tlt_file(imod_directory: Path) -> Path:
    """Get the tlt file containing tilt angles from an IMOD directory."""
    return imod_directory / f'{get_stack_prefix(imod_directory)}.xf'
