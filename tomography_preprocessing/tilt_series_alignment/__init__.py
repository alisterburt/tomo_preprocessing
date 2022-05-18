# Import decorated batch alignment functions first
from .aretomo import batch_aretomo as _batch_aretomo
from .imod import batch_fiducials as _batch_imod_fiducials
from .imod import batch_patch_tracking as _batch_imod_patch_tracking

# Then import the cli, it will be decorated with all programs
from ._cli import cli
