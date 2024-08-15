"""Tools for generating Markdown documentation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cached_property
from typing import List, Literal


class MarkdownGenerator(ABC):
    """An abstract class for dataclasses that can be converted into markdown strings."""

    @property
    @abstractmethod
    def markdown(self) -> str:
        """A markdown documentation string."""

    def __str__(self) -> str:
        return self.markdown


@dataclass
class Arg(MarkdownGenerator):
    """Metadata for an argument to a SPINAsm instruction."""

    name: str
    width: int
    formats: list[str]

    @property
    def markdown(self) -> str:
        return f"{self.name}: {' | '.join(self.formats)}"


class ArgList(MarkdownGenerator, List[Arg]):
    """A collection of arguments for a SPINAsm instruction."""

    @property
    def markdown(self) -> str:
        return ", ".join([arg.markdown for arg in self])


@dataclass
class Instruction(MarkdownGenerator):
    """Generatable Markdown documentation for a SPINAsm instruction."""

    name: str
    args: ArgList
    description: str
    operation: str
    coding: str
    example: str
    parameter_description: str | None = None

    @cached_property
    def markdown(self) -> str:
        """A markdown documentation string."""
        md = MarkdownString()

        md.add_paragraph(self.description.strip())

        md.add_heading("Operation", level=4)
        md.add_paragraph(f"`{self.operation}`")

        md.add_heading("Parameters", level=4)
        if not self.args:
            md.add_paragraph("None.")
        else:
            md.add_table(
                cols=["Name", "Width", "Entry formats, range"],
                rows=[
                    [arg.name, f"{arg.width} Bit", "<br>".join(arg.formats)]
                    for arg in self.args
                ],
            )
        if self.parameter_description:
            md.add_paragraph(self.parameter_description)

        md.add_heading("Example", level=4)
        md.add_codeblock(self.example.strip(), language="assembly")

        md.add_horizontal_rule()
        md.add_paragraph(
            "*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference "
            "manual. Copyright 2008 by Spin Semiconductor.*"
        )

        return str(md)


@dataclass
class Assembler(MarkdownGenerator):
    """Generatable Markdown documentation for a SPINAsm assembler."""

    name: str
    description: str
    example: str
    example_remarks: str = ""

    @cached_property
    def markdown(self) -> str:
        """A markdown documentation string."""
        md = MarkdownString()

        md.add_paragraph(self.description.strip())

        md.add_heading("Example", level=4)
        md.add_codeblock(self.example.strip(), language="assembly")

        if self.example_remarks:
            md.add_paragraph(self.example_remarks.strip())

        md.add_horizontal_rule()
        md.add_paragraph(
            "*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference "
            "manual. Copyright 2008 by Spin Semiconductor.*"
        )

        return str(md)


class MarkdownTable(MarkdownGenerator):
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

    @property
    def markdown(self) -> str:
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
