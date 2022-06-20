from typing import Tuple

def gpu_ids_string2tuple(
        gpu_ids: str
    ) -> Tuple:
    """Convert GPU  ID input from colon spaced (1:2:3) to no space inbetween GPU IDs (123)"""
    return tuple(map(int, gpu_ids.strip().replace(':','')))
