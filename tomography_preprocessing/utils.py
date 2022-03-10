from pathlib import Path

def basename(path: Path):
    while path.stem != str(path):
        path = Path(path.stem)
    return path