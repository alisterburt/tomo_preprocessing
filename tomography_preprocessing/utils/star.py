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
    star = starfile.read(tilt_series_star_file, always_dict=True)
    for _, tilt_series_df in star['global'].iterrows():
        tilt_series_id = tilt_series_df['rlnTomoName']
        tilt_image_df = starfile.read(
            tilt_series_df['rlnTomoTiltSeriesStarFile'], always_dict=True
        )[tilt_series_id]
        yield tilt_series_id, tilt_series_df, tilt_image_df


def get_pixel_size(optics_df: pd.DataFrame, optics_group: int) -> float:
    """Get pixel size for an optics group from an optics dataframe."""
    return optics_df.set_index('rlnOpticsGroup').loc[optics_group, 'rlnMicrographPixelSize']
