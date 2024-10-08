from __future__ import annotations

from dataclasses import dataclass

import lsprotocol.types as lsp
import pytest
from pytest_lsp import LanguageClient

from ..conftest import PATCH_DIR, TestCase, parametrize_cases


@dataclass
class SymbolDefinitionTestCase(TestCase):
    """A dictionary to record definition locations for a symbol."""

    range: lsp.Range
    kind: lsp.SymbolKind
    uri: str


TEST_CASES: list[SymbolDefinitionTestCase] = [
    SymbolDefinitionTestCase(
        name="apout",
        kind=lsp.SymbolKind.Variable,
        uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
        range=lsp.Range(
            start=lsp.Position(line=23, character=4),
            end=lsp.Position(line=23, character=9),
        ),
    ),
    SymbolDefinitionTestCase(
        name="lap2a",
        kind=lsp.SymbolKind.Variable,
        uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
        range=lsp.Range(
            start=lsp.Position(line=16, character=4),
            end=lsp.Position(line=16, character=9),
        ),
    ),
    SymbolDefinitionTestCase(
        name="endclr",
        kind=lsp.SymbolKind.Module,
        uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
        range=lsp.Range(
            start=lsp.Position(line=41, character=0),
            end=lsp.Position(line=41, character=6),
        ),
    ),
]


@parametrize_cases(TEST_CASES)
@pytest.mark.asyncio()
async def test_symbol_definitions(
    test_case: SymbolDefinitionTestCase, client: LanguageClient
):
    """Test that the definitions of all symbols in the document are returned."""
    result = await client.text_document_document_symbol_async(
        params=lsp.DocumentSymbolParams(
            text_document=lsp.TextDocumentIdentifier(uri=test_case.uri),
        )
    )

    matching = [item for item in result if item.name == test_case.name.upper()]
    assert matching, f"Symbol {test_case.name.upper()} not in document symbols"

    item = matching[0]
    assert item.kind == test_case.kind
    assert item.range == test_case.range
