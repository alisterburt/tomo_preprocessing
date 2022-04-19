from __future__ import annotations

from typing import TYPE_CHECKING

import mrcfile

if TYPE_CHECKING:
    import os
    import numpy as np


def read_mrc(filename: os.PathLike) -> np.ndarray:
    with mrcfile.open(filename, permissive=True) as mrc:
        data = mrc.data
    return data


def write_empty_file(filename: os.PathLike) -> None:
    open(filename, mode='w').close()