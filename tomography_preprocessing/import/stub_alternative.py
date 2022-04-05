"""Stub alternative CLI command for import job."""

from ._cli import cli


@cli.command(name='alternative')
def stub():
    """Stub for an alternative to SerialEM tomo metadata import."""
    pass
