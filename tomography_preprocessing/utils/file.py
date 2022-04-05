from pathlib import Path
from typing import List


def basename(path: Path):
    while path.stem != str(path):
        path = Path(path.stem)
    return path


def glob(pattern: str) -> List[Path]:
    return list(Path().glob(pattern))
