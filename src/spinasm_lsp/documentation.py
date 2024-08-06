from __future__ import annotations

from collections import UserDict
from importlib import resources
from pathlib import Path
from typing import Any

DOC_DIR = resources.files("spinasm_lsp.docs")


class MarkdownFile:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.name = self.path.stem

    def read(self) -> str:
        with self.path.open() as src:
            return src.read()


class DocMap(UserDict):
    """A mapping of instructions to markdown documentation strings."""

    def __init__(self, folder: str):
        self.dir = Path(str(DOC_DIR.joinpath(folder)))
        self.data = self.load_markdown()

    @staticmethod
    def to_lower(s: Any) -> Any:
        """Attempt to convert a value to lowercase, or return unchanged."""
        return s.lower() if hasattr(s, "lower") else s

    def __getitem__(self, key: Any) -> Any:
        """Get item with case-insensitive keys."""
        return super().__getitem__(self.to_lower(key))

    def __contains__(self, key):
        """Contains with case-insensitive keys."""
        return self.to_lower(key) in self.data

    def load_markdown(self) -> dict[str, str]:
        data = {}
        files = self.dir.glob("*.md")
        for file in files:
            md = MarkdownFile(file)
            # Store with lowercase keys to allow case-insensitive searches
            data[md.name.lower()] = md.read()

        return data


if __name__ == "__main__":
    instructions = DocMap(folder="instructions")
    print(instructions["RDAX"])
