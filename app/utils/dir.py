from typing import Self
from pathlib import Path


class Dir:
    def __init__(self: Self, path: Path | str) -> None:
        self.path = Path(path)

    def is_empty(self: Self) -> bool:
        return not any(self.path.iterdir())

    def is_dir(self: Self) -> bool:
        return self.path.is_dir()
