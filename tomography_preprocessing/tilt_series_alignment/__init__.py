# Import decorated batch alignment functions first
from .imod import batch_fiducials as _batch_imod_fiducials
from .imod import batch_patch_tracking as _batch_imod_patch_tracking
from ._generate_matrices import generate_relion_matrices
from .aretomo import batch_aretomo as _batch_aretomo

# Then import the cli, it will be decorated with all programs
from ._cli import cli
