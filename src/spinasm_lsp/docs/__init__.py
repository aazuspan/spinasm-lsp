from __future__ import annotations

from spinasm_lsp.docs.assemblers import ASSEMBLERS
from spinasm_lsp.docs.instructions import INSTRUCTIONS
from spinasm_lsp.docs.markdown import Instruction, MarkdownGenerator

# Opcodes where the first argument is considered part of the instruction rather than
# an argument, which requires some special handling.
MULTI_WORD_INSTRUCTIONS = ("CHO RDA", "CHO RDAL", "CHO SOF")


class DocumentationManager:
    """A manager for case-insensitive documentation lookups."""

    instructions = INSTRUCTIONS
    assemblers = ASSEMBLERS
    data: dict[str, MarkdownGenerator] = {**INSTRUCTIONS, **ASSEMBLERS}

    def __getitem__(self, key: str) -> str:
        return str(self.data[key.upper()])

    def get_markdown(self, key: str, default: str = "") -> str:
        return str(self.data.get(key.upper(), default))

    def get_instruction(self, key: str) -> Instruction | None:
        return self.instructions.get(key.upper(), None)

    def __contains__(self, key: str) -> bool:
        return self.data.__contains__(key.upper())

    def __iter__(self):
        return iter(self.data)


__all__ = ["DocumentationManager"]
