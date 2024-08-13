from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal


class MarkdownDocumentationGenerator(ABC):
    @property
    @abstractmethod
    def markdown(self) -> str:
        """A markdown documentation string."""

    def __str__(self) -> str:
        return self.markdown


class MarkdownTable:
    def __init__(
        self,
        cols: list[str],
        rows: list[list[str]],
        justify: list[Literal["left", "center", "right"]] | None = None,
    ):
        ncol = len(cols)
        if any([len(row) != ncol for row in rows]):
            raise ValueError(f"All row lengths must match col length of {ncol}.")
        if justify is not None and len(justify) != ncol:
            raise ValueError("There must be one justify position per column.")

        if justify is None:
            self.justify = ["left"] * ncol
        self.cols = cols
        self.rows = rows

    def __str__(self) -> str:
        header = " | ".join(self.cols)

        separators = []
        for just in self.justify:
            if just == "left":
                separators.append(":-")
            elif just == "right":
                separators.append("-:")
            else:
                separators.append(":-:")
        separator = " | ".join(separators)
        rows = "\n".join([" | ".join(row) for row in self.rows])

        return f"{header}\n{separator}\n{rows}"


class MarkdownString:
    def __init__(self):
        self._content = ""

    def __str__(self):
        return self._content

    def _add_line(self, s: str):
        self._content += f"\n{s}\n"

    def add_heading(self, title: str, level: int):
        if level < 1 or level > 4:
            raise ValueError("Level must be > 0 and < 5.")
        self._add_line(f"{'#' * level} {title}")

    def add_horizontal_rule(self):
        self._add_line("-" * 24)

    def add_paragraph(self, s: str):
        self._add_line(s)

    def add_table(self, cols: list[str], rows: list[list[str]]):
        self._add_line(str(MarkdownTable(cols, rows)))

    def add_codeblock(self, source: str, language: str | None = None):
        block = f"```{language}\n{source}\n```"
        self._add_line(block)
