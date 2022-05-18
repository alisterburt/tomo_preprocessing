from pathlib import Path
from typing import Tuple


def create_alignment_job_directory_structure(output_directory: Path) -> Tuple[Path, Path]:
    """Create directory structure for an IMOD alignment job."""
    tilt_series_directory = output_directory / 'tilt_series'
    tilt_series_directory.mkdir(parents=True, exist_ok=True)

    imod_alignments_directory = output_directory / 'alignments'
    imod_alignments_directory.mkdir(parents=True, exist_ok=True)
    return tilt_series_directory, imod_alignments_directory
