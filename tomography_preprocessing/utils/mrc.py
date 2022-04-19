import os

import mrcfile
import numpy as np


def read_mrc(filename: os.PathLike) -> np.ndarray:
    with mrcfile.open(filename, permissive=True) as mrc:
        data = mrc.data
    return data