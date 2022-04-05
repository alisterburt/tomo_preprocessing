from os import PathLike
from pathlib import Path
from typing import List, Tuple

import mrcfile
import numpy as np
import starfile
from yet_another_imod_wrapper import align_using_fiducials, align_using_patch_tracking
from . import utils


def batch_align_tilt_series_with_fiducials(
        tilt_series_star_file: Path,
        output_directory: Path,
        nominal_fiducial_diameter_nanometres: float,
):
    star = starfile.read(tilt_series_star_file)
    for _, tilt_series_df in star['global'].iterrows():
        tilt_series_metadata_star_file = tilt_series_df['rlnTomoTiltSeriesStarFile']
        tilt_series_metadata = starfile.read(tilt_series_metadata_star_file)
        tomogram_id = tilt_series_df['rlnTomoName']
        optics_group = tilt_series_df['rlnOpticsGroup']
        pixel_size = star['optics'].set_index('rlnOpticsGroup').loc[optics_group, 'rlnMicrographPixelSize']
        tilt_image_files = tilt_series_metadata['rlnMicrographName']
        tilt_angles = tilt_series_metadata['rlnTomoNominalStageTiltAngle']
        rotation_angle = tilt_series_metadata['rlnTomoNominalTiltAxisAngle'][0]
        tilt_series_file = output_directory / f'{tomogram_id}.mrc'
        utils.image.stack_image_files(tilt_image_files, tilt_series_file)
        align_using_fiducials(
            tilt_series_file=tilt_series_file,
            tilt_angles=tilt_angles,
            pixel_size=pixel_size,
            fiducial_size=nominal_fiducial_diameter_nanometres,
            nominal_rotation_angle=rotation_angle,
            output_directory=output_directory / tomogram_id,
        )


def batch_align_tilt_series_with_patch_tracking(
        tilt_series_star_file: Path,
        output_directory: Path,
        unbinned_patch_size_pixels: Tuple[int, int],
        patch_overlap_percent: float
    ):
    star = starfile.read(tilt_series_star_file)
    for _, row in star['global'].iterrows():
        tilt_series_metadata_star_file = row['rlnTomoTiltSeriesStarFile']
        tilt_series_metadata = starfile.read(tilt_series_metadata_star_file)
        tomogram_id = row['rlnTomoName']
        tilt_series_filename = output_directory / f'{tomogram_id}.mrc'
        tilt_image_files = tilt_series_metadata['rlnMicrographName']
        utils.image.stack_image_files(tilt_image_files, tilt_series_filename)
        optics_group = row['rlnOpticsGroup']
        pixel_size = star['optics'].set_index('rlnOpticsGroup').loc[optics_group, 'rlnMicrographPixelSize']


        rotation_angle = tilt_series_metadata['rlnTomoNominalTiltAxisAngle'][0]


        align_using_patch_tracking(
            tilt_series_file=tilt_series_filename,
            tilt_angles=tilt_series_metadata['rlnTomoNominalStageTiltAngle'],
            nominal_rotation_angle=rotation_angle,
            pixel_size=pixel_size,
            patch_size_xy=unbinned_patch_size_pixels,
            patch_overlap_percentage=patch_overlap_percent,
            output_directory=output_directory / tomogram_id,
        )




