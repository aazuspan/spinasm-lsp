from __future__ import annotations

import lsprotocol.types as lsp
import pytest
from pytest_lsp import LanguageClient

from ..conftest import PATCH_DIR, TestCase


class ReferenceTestCase(TestCase):
    """A dictionary to record reference locations for a symbol."""

    position: lsp.Position
    references: list[lsp.Location]
    uri: str


REFERENCES: list[ReferenceTestCase] = [
    {
        # Variable
        "name": "apout",
        "position": lsp.Position(line=23, character=4),
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
        "references": [
            lsp.Location(
                uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
                range=lsp.Range(
                    start=lsp.Position(line=23, character=4),
                    end=lsp.Position(line=23, character=9),
                ),
            ),
            lsp.Location(
                uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
                range=lsp.Range(
                    start=lsp.Position(line=57, character=5),
                    end=lsp.Position(line=57, character=10),
                ),
            ),
            lsp.Location(
                uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
                range=lsp.Range(
                    start=lsp.Position(line=60, character=5),
                    end=lsp.Position(line=60, character=10),
                ),
            ),
            lsp.Location(
                uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
                range=lsp.Range(
                    start=lsp.Position(line=70, character=5),
                    end=lsp.Position(line=70, character=10),
                ),
            ),
        ],
    },
    {
        "name": "ap1",
        "position": lsp.Position(line=8, character=4),
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
        "references": [
            lsp.Location(
                uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
                range=lsp.Range(
                    start=lsp.Position(line=8, character=4),
                    end=lsp.Position(line=8, character=7),
                ),
            ),
            lsp.Location(
                uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
                range=lsp.Range(
                    start=lsp.Position(line=51, character=4),
                    end=lsp.Position(line=51, character=7),
                ),
            ),
            lsp.Location(
                uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
                range=lsp.Range(
                    start=lsp.Position(line=52, character=5),
                    end=lsp.Position(line=52, character=8),
                ),
            ),
        ],
    },
]


@pytest.mark.parametrize("test_case", REFERENCES, ids=lambda x: x["name"])
@pytest.mark.asyncio()
async def test_references(test_case: ReferenceTestCase, client: LanguageClient):
    """Test that references to a symbol are correctly found."""
    result = await client.text_document_references_async(
        params=lsp.ReferenceParams(
            context=lsp.ReferenceContext(include_declaration=False),
            position=test_case["position"],
            text_document=lsp.TextDocumentIdentifier(uri=test_case["uri"]),
        )
    )

    assert result == test_case["references"]
