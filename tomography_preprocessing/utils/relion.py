from pathlib import Path
from .io import write_empty_file

JOB_SUCCESS_FILENAME = 'RELION_JOB_EXIT_SUCCESS'
JOB_FAILURE_FILENAME = 'RELION_JOB_EXIT_FAILURE'
ABORT_JOB_NOW_FILENAME = 'RELION_JOB_ABORT_NOW'
JOB_ABORTED_FILENAME = 'RELION_JOB_ABORTED'


def write_job_success_file(job_directory: Path) -> None:
    """Write a file indicating job success."""
    output_file = job_directory / JOB_SUCCESS_FILENAME
    write_empty_file(output_file)


def write_job_failure_file(job_directory: Path) -> None:
    """Write a file indicating job failure."""
    output_file = job_directory / JOB_FAILURE_FILENAME
    write_empty_file(output_file)


def _check_for_abort_job_now_file(job_directory: Path) -> bool:
    """Check for the presence of a file indicating job termination."""
    output_file = job_directory / ABORT_JOB_NOW_FILENAME
    return output_file.exists()


def _write_job_aborted_file(job_directory: Path) -> None:
    """Write a file indicating that the job was succesfully terminated."""
    output_file = job_directory / JOB_ABORTED_FILENAME
    write_empty_file(output_file)


def abort_job_if_necessary(job_directory: Path) -> None:
    """Abort a job if file indicating job should be terminated is found."""
    if _check_for_abort_job_now_file(job_directory) is True:
        _write_job_aborted_file(job_directory)

