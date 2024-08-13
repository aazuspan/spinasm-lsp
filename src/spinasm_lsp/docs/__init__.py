from spinasm_lsp.docs.assemblers import ASSEMBLERS
from spinasm_lsp.docs.instructions import INSTRUCTIONS
from spinasm_lsp.docs.markdown import MarkdownDocumentationGenerator


class DocumentationManager:
    """A manager for case-insensitive documentation lookups."""

    data: dict[str, MarkdownDocumentationGenerator] = {**INSTRUCTIONS, **ASSEMBLERS}

    def __getitem__(self, key: str) -> str:
        return str(self.data[key.upper()])

    def get(self, key: str, default: str = "") -> str:
        return str(self.data.get(key.upper(), default))

    def __contains__(self, key: str) -> bool:
        return self.data.__contains__(key.upper())

    def __iter__(self):
        return iter(self.data)


__all__ = ["DocumentationManager"]
