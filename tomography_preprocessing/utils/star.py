from __future__ import annotations

from typing import TYPE_CHECKING, Tuple, Optional

import pandas as pd
import starfile

from .. import utils

if TYPE_CHECKING:
    import os
    from typing import Iterable

TiltSeriesMetadata = Tuple[str, pd.DataFrame, pd.DataFrame]


def _iterate_all_tilt_series_metadata(
        tilt_series_star_file: os.PathLike
) -> Iterable[TiltSeriesMetadata]:
    """Yield all metadata from a tilt-series data STAR file."""
    star = starfile.read(tilt_series_star_file, always_dict=True)
    for _, tilt_series_df in star['global'].iterrows():
        tilt_series_id = tilt_series_df['rlnTomoName']
        tilt_image_df = starfile.read(
            tilt_series_df['rlnTomoTiltSeriesStarFile'], always_dict=True
        )[tilt_series_id]
        yield tilt_series_id, tilt_series_df, tilt_image_df


def _extract_single_tilt_series_metadata(
        tilt_series_star_file: os.PathLike,
        tilt_series_id: str
) -> TiltSeriesMetadata:
    """Get metadata for a specific tilt-series from a tilt-series data STAR file."""
    star = starfile.read(tilt_series_star_file, always_dict=True)
    tilt_series_df = star['global'].set_index('rlnTomoName').loc[tilt_series_id, :]
    tilt_image_df = starfile.read(
        tilt_series_df['rlnTomoTiltSeriesStarFile'], always_dict=True
    )[tilt_series_id]
    return tilt_series_id, tilt_series_df, tilt_image_df


def iterate_tilt_series_metadata(
        tilt_series_star_file: os.PathLike,
        tilt_series_id: Optional[str] = None,
) -> Iterable[TiltSeriesMetadata]:
    """Yield metadata from a tilt-series data STAR file."""
    if tilt_series_id is None:  # align all tilt-series
        all_tilt_series_metadata = utils.star._iterate_all_tilt_series_metadata(tilt_series_star_file)
    else:  # do single tilt-series alignment
        all_tilt_series_metadata = [
            utils.star._extract_single_tilt_series_metadata(tilt_series_star_file, tilt_series_id)
        ]
    for tilt_series_metadata in all_tilt_series_metadata:
        yield tilt_series_metadata


def get_pixel_size(optics_df: pd.DataFrame, optics_group: int) -> float:
    """Get pixel size for an optics group from an optics dataframe."""
    return optics_df.set_index('rlnOpticsGroup').loc[optics_group, 'rlnMicrographPixelSize']
