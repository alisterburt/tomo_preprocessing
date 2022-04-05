from pathlib import Path
import os
from typing import Tuple, List

import mrcfile
import numpy as np


def basename(path: Path):
    while path.stem != str(path):
        path = Path(path.stem)
    return path


def read_mrc(filename: os.PathLike) -> np.ndarray:
    with mrcfile.open(filename) as mrc:
        data = mrc.data
    return data


def get_pixel_size(filename: os.PathLike) -> float:
    with mrcfile.open(filename, header_only=True) as mrc:
        pixel_size = mrc.voxel_size.x
    return pixel_size


def get_image_shape(filename: os.PathLike) -> Tuple[int, int, int]:
    with mrcfile.open(filename, header_only=True) as mrc:
        nz, ny, nx = mrc.header.nz, mrc.header.ny, mrc.header.nx
    return int(nz), int(ny), int(nx)


def stack_images(image_files: List[os.PathLike], output_image_file: os.PathLike):
    n_images = len(image_files)
    _, h, w = get_image_shape(image_files[0])
    stack_shape = (n_images, h, w)
    mrc = mrcfile.new_mmap(output_image_file, shape=stack_shape, mrc_mode=2)
    for idx, image_file in enumerate(image_files):
        mrc.data[idx] = read_mrc(image_file).astype(np.float32)
    mrc.reset_header_stats()
    mrc.update_header_from_data()
    pixel_size = get_pixel_size(image_files[0])
    mrc.voxel_size = (pixel_size, pixel_size, 0)
    mrc.close()


def read_xf(filename: os.PathLike):
    Rz