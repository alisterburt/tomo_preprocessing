from __future__ import annotations

from typing import TYPE_CHECKING, Tuple

import pandas as pd
import starfile

if TYPE_CHECKING:
    import os
    from typing import Iterable

_TiltSeriesMetadata = Tuple[str, pd.DataFrame, pd.DataFrame]


def iterate_tilt_series_metadata(
        tilt_series_star_file: os.PathLike
) -> Iterable[_TiltSeriesMetadata]:
    """Iterate over metadata from a tilt series data STAR file."""
    star = starfile.read(tilt_series_star_file)
    for _, row in star['tilt_series'].iterrows():
        tilt_series_id = row['rlnTomoName']
        tilt_series_metadata = starfile.read(row['rlnTomoTiltSeriesStarFile'])
        yield tilt_series_id, tilt_series_metadata['optics'], tilt_series_metadata['tilt_images']


def get_pixel_size(optics_df: pd.DataFrame, optics_group: int) -> float:
    """Get pixel size for an optics group from an optics dataframe."""
    return optics_df.set_index('rlnOpticsGroup').loc[optics_group, 'rlnMicrographPixelSize']
