from pathlib import Path


class Dir:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def exists_and_is_dir(self) -> bool:
        return self.path.exists() and self.path.is_dir()

    def ensure_is_dir(self) -> None:
        if not self.path.exists():
            raise FileNotFoundError(f"Caminho inexistente: {self.path}")
        if not self.path.is_dir():
            raise NotADirectoryError(f"Não é um diretório: {self.path}")

    def is_empty(self) -> bool:
        self.ensure_is_dir()
        return not any(self.path.iterdir())
