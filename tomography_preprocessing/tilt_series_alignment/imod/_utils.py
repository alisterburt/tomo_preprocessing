import os
from functools import lru_cache
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
import starfile

from tomography_preprocessing import utils
from tomography_preprocessing.utils.transformations import S, Ry, Rz


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


def get_pre_rotation_shifts(xf: np.ndarray) -> np.ndarray:
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


def get_xf_in_plane_rotations(xf: np.ndarray) -> np.ndarray:
    """Extract the in plane rotation angle from IMOD xf data.

    Output is an (n, ) numpy array of angles in degrees. This function assumes
    that the transformation in the xf file is a simple 2D rotation.
    """
    transformation_matrices = get_xf_transformation_matrices(xf)
    cos_theta = transformation_matrices[:, 0, 0]
    return np.rad2deg(np.arccos(cos_theta))


@lru_cache(maxsize=100)
def get_etomo_basename(imod_directory: Path) -> str:
    """Get the tilt-series stack basename from an Etomo directory."""
    edf_files = list(imod_directory.glob('*.edf'))
    if len(edf_files) != 1:
        raise RuntimeError('singular Etomo directive file not found')
    return edf_files[0].stem


def get_xf_file(imod_directory: Path) -> Path:
    """Get the xf file containing image transforms from an IMOD directory."""
    return imod_directory / f'{get_etomo_basename(imod_directory)}.xf'


def get_tlt_file(imod_directory: Path) -> Path:
    """Get the tlt file containing tilt angles from an IMOD directory."""
    return imod_directory / f'{get_etomo_basename(imod_directory)}.tlt'


def get_edf_file(imod_directory: Path) -> Path:
    """Get the Etomo directive file from an IMOD directory."""
    return imod_directory / f'{get_etomo_basename(imod_directory)}.edf'


def get_tilt_series_alignment_parameters(
        imod_directory: Path
) -> Tuple[np.ndarray, np.ndarray]:
    """Get the tilt-series alignment parameters from an IMOD directory.

    Shifts are in pixels and should be applied before rotations.
    Rotations are ZYZ intrinsic Euler angles which transform the volume.
    """
    xf = read_xf(get_xf_file(imod_directory))
    shifts_px = get_pre_rotation_shifts(xf)
    in_plane_rotations = get_xf_in_plane_rotations(xf)
    tilt_angles = read_tlt(get_tlt_file(imod_directory))
    euler_angles = np.zeros(shape=(len(tilt_angles), 3))
    euler_angles[:, 1] = tilt_angles
    euler_angles[:, 2] = in_plane_rotations
    return shifts_px, euler_angles


def write_relion_tilt_series_alignment_output(
        tilt_image_df: pd.DataFrame,
        tilt_series_id: str,
        pixel_size: float,
        imod_directory: Path,
        output_star_file: Path,
):
    shifts_px, euler_angles = get_tilt_series_alignment_parameters(imod_directory)
    tilt_image_df[['rlnOriginXAngst', 'rlnOriginYAngst']] = shifts_px * pixel_size
    tilt_image_df[['rlnAngleRot', 'rlnAngleTilt', 'rlnAnglePsi']] = euler_angles

    starfile.write({tilt_series_id: tilt_image_df}, output_star_file)


def relion_tilt_series_alignment_parameters_to_relion_matrix(
        shifts: pd.DataFrame,
        euler_angles: pd.DataFrame,
        tilt_image_dimensions: np.ndarray,
        tomogram_dimensions: np.ndarray,
):
    """shifts need to be in px at this point"""
    tilt_image_center = (tilt_image_dimensions - 1) / 2
    n_tilt_images = shifts.shape[0]
    shifts = np.c_[shifts, np.zeros(n_tilt_images)]  # zero-fill (n, 2) to (n, 3)
    tomogram_center_to_origin = -tomogram_dimensions / 2
    tilt_image_corner_to_center_vector = np.append(tilt_image_center, 0)

    # Generate affine matrices for each component of the final transformation
    # first the rotations
    in_plane_rotation = Rz(euler_angles['rlnAnglePsi'])
    tilt = Ry(euler_angles['rlnAngleTilt'])

    # offsets
    tomogram_origin_offset = S(tomogram_center_to_origin)
    tilt_image_corner_to_center = S(tilt_image_corner_to_center_vector)
    tilt_image_centering_shift = S(shifts)

    # compose matrices
    volume_transforms = in_plane_rotation @ tilt @ tomogram_origin_offset
    image_transforms = tilt_image_corner_to_center @ tilt_image_centering_shift
    return np.squeeze(image_transforms @ volume_transforms)


def write_aligned_tilt_series_star_file(
        original_tilt_series_star_file: Path,
        output_directory: Path,
):
    df = starfile.read(original_tilt_series_star_file, always_dict=True)['global']
    tilt_series_metadata = list(utils.star.iterate_tilt_series_metadata(
        tilt_series_star_file=original_tilt_series_star_file
    ))
    # update individual tilt series star files
    df['rlnTomoTiltSeriesStarFile'] = [
        output_directory / 'tilt_series' / f'{tilt_series_id}.star'
        for tilt_series_id, _, _ in tilt_series_metadata
    ]
    df['EtomoDirectiveFile'] = [
        output_directory / 'alignments' / tilt_series_id / f'{tilt_series_id}.edf'
        for tilt_series_id, _, _ in tilt_series_metadata
    ]
    etomo_dir_exist = any(df['EtomoDirectiveFile'].apply(lambda x: Path(x).exists()))
    if etomo_dir_exist is False:
        df = df.drop(columns=['EtomoDirectiveFile'])
    # check which output files were succesfully generated, take only those
    df = df[df['rlnTomoTiltSeriesStarFile'].apply(lambda x: x.exists())]
    starfile.write({'global': df}, output_directory / 'aligned_tilt_series.star')
