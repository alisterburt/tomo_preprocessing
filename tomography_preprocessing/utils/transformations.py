import einops
import numpy as np


def Rx(angles_degrees: np.ndarray) -> np.ndarray:
    """Affine matrices for rotations around the X-axis."""
    angles_degrees = np.array(angles_degrees).reshape(-1)
    c = np.cos(np.deg2rad(angles_degrees))
    s = np.sin(np.deg2rad(angles_degrees))
    matrices = einops.repeat(
        np.eye(4), 'i j -> n i j', n=len(angles_degrees)
    )
    matrices[:, 1, 1] = c
    matrices[:, 1, 2] = -s
    matrices[:, 2, 1] = s
    matrices[:, 2, 2] = c
    return np.squeeze(matrices)


def Ry(angles_degrees: np.ndarray) -> np.ndarray:
    """Affine matrices for a rotations around the Y-axis."""
    angles_degrees = np.array(angles_degrees).reshape(-1)
    c = np.cos(np.deg2rad(angles_degrees))
    s = np.sin(np.deg2rad(angles_degrees))
    matrices = einops.repeat(
        np.eye(4), 'i j -> n i j', n=len(angles_degrees)
    )
    matrices[:, 0, 0] = c
    matrices[:, 0, 2] = s
    matrices[:, 2, 0] = -s
    matrices[:, 2, 2] = c
    return np.squeeze(matrices)


def Rz(angles_degrees: float) -> np.ndarray:
    """Affine matrix for a rotation around the Z-axis."""
    angle_degrees = np.array(angles_degrees).reshape(-1)
    c = np.cos(np.deg2rad(angle_degrees))
    s = np.sin(np.deg2rad(angle_degrees))
    matrices = einops.repeat(
        np.eye(4), 'i j -> n i j', n=len(angle_degrees)
    )
    matrices[:, 0, 0] = c
    matrices[:, 0, 1] = -s
    matrices[:, 1, 0] = s
    matrices[:, 1, 1] = c
    return np.squeeze(matrices)


def S(xyz_shifts: np.ndarray) -> np.ndarray:
    """Affine matrices for xyz-shifts."""
    xyz_shifts = np.array(xyz_shifts).reshape((-1, 3))
    n = xyz_shifts.shape[0]
    matrices = einops.repeat(np.eye(4), 'i j -> n i j', n=n)
    matrices[:, 0:3, 3] = xyz_shifts
    return np.squeeze(matrices)
