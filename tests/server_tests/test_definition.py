from __future__ import annotations

import lsprotocol.types as lsp
import pytest
from pytest_lsp import LanguageClient

from ..conftest import PATCH_DIR, TestCase


class DefinitionTestCase(TestCase):
    """A dictionary track where a symbol is referenced and defined."""

    referenced: lsp.Position
    defined: lsp.Location
    uri: str


DEFINITIONS: list[DefinitionTestCase] = [
    {
        # Variable
        "name": "apout",
        "referenced": lsp.Position(line=57, character=7),
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
        "defined": lsp.Location(
            uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
            range=lsp.Range(
                start=lsp.Position(line=23, character=4),
                end=lsp.Position(line=23, character=9),
            ),
        ),
    },
    {
        # Memory
        "name": "lap2a",
        "referenced": lsp.Position(line=72, character=7),
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
        "defined": lsp.Location(
            uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
            range=lsp.Range(
                start=lsp.Position(line=16, character=4),
                end=lsp.Position(line=16, character=9),
            ),
        ),
    },
    {
        # Memory. Note that this has an address modifier, but still points to the
        # original definition.
        "name": "lap2a#",
        "referenced": lsp.Position(line=71, character=7),
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
        "defined": lsp.Location(
            uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
            range=lsp.Range(
                start=lsp.Position(line=16, character=4),
                end=lsp.Position(line=16, character=9),
            ),
        ),
    },
    {
        # Label
        "name": "endclr",
        "referenced": lsp.Position(line=37, character=9),
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
        "defined": lsp.Location(
            uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
            range=lsp.Range(
                start=lsp.Position(line=41, character=0),
                end=lsp.Position(line=41, character=6),
            ),
        ),
    },
]


@pytest.mark.asyncio()
@pytest.mark.parametrize("test_case", DEFINITIONS, ids=lambda x: x["name"])
async def test_definition(test_case: DefinitionTestCase, client: LanguageClient):
    """Test that the definition location of different assignments is correct."""
    result = await client.text_document_definition_async(
        params=lsp.DefinitionParams(
            position=test_case["referenced"],
            text_document=lsp.TextDocumentIdentifier(uri=test_case["uri"]),
        )
    )

    assert result == test_case["defined"]
