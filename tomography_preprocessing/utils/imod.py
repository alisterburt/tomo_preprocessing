import os

import numpy as np


def read_xf(file: os.PathLike) -> np.ndarray:
    """Read an IMOD xf file into a numpy array.

    The file with alignment transforms (option OutputTransformFile) contains one
    line per view, each with a linear transformation specified by six numbers:
        A11 A12 A21 A22 DX DY
    where the coordinate (X, Y) is transformed to (X', Y') by:
        X' = A11 * X + A12 * Y + DX
        Y' = A21 * X + A22 * Y + DY
    """
    return np.loadtxt(fname=file, dtype=float)


def xf_to_shifts(xf: np.ndarray):
    """Extract XY shifts from IMOD xf data."""
    return xf[:, (-2, -1)]


def xf_to_transformation_matrix(xf: np.ndarray) -> np.ndarray:
    """Extract the transformation matrix from IMOD xf data."""
    return xf[:, 0:4]
