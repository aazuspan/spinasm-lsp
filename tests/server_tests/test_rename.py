from __future__ import annotations

import lsprotocol.types as lsp
import pytest
from pytest_lsp import LanguageClient

from ..conftest import PATCH_DIR, TestCase


class RenameTestCase(TestCase):
    """A dictionary to record rename results for a symbol."""

    rename_to: str
    position: lsp.Position
    changes: list[lsp.TextEdit]
    uri: str


RENAMES: list[RenameTestCase] = [
    {
        "name": "ap1",
        "rename_to": "FOO",
        "position": lsp.Position(line=8, character=4),
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
        "changes": [
            lsp.TextEdit(
                range=lsp.Range(start=lsp.Position(8, 4), end=lsp.Position(8, 7)),
                new_text="FOO",
            ),
            # This symbol is `ap1#``, and should be matched when renaming `ap1`
            lsp.TextEdit(
                range=lsp.Range(start=lsp.Position(51, 4), end=lsp.Position(51, 7)),
                new_text="FOO",
            ),
            lsp.TextEdit(
                range=lsp.Range(start=lsp.Position(52, 5), end=lsp.Position(52, 8)),
                new_text="FOO",
            ),
        ],
    },
    {
        "name": "endclr",
        "rename_to": "END",
        "position": lsp.Position(line=41, character=0),
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
        "changes": [
            lsp.TextEdit(
                range=lsp.Range(start=lsp.Position(37, 8), end=lsp.Position(37, 14)),
                new_text="END",
            ),
            lsp.TextEdit(
                range=lsp.Range(start=lsp.Position(41, 0), end=lsp.Position(41, 6)),
                new_text="END",
            ),
        ],
    },
    {
        "name": "lap1a#",
        "rename_to": "FOO",
        "position": lsp.Position(line=61, character=4),
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
        "changes": [
            # Renaming `lap1a#` should also rename `lap1a`
            lsp.TextEdit(
                range=lsp.Range(start=lsp.Position(12, 4), end=lsp.Position(12, 9)),
                new_text="FOO",
            ),
            lsp.TextEdit(
                range=lsp.Range(start=lsp.Position(61, 4), end=lsp.Position(61, 9)),
                new_text="FOO",
            ),
            lsp.TextEdit(
                range=lsp.Range(start=lsp.Position(62, 5), end=lsp.Position(62, 10)),
                new_text="FOO",
            ),
        ],
    },
]


@pytest.mark.parametrize("test_case", RENAMES, ids=lambda x: x["name"])
@pytest.mark.asyncio()
async def test_rename(test_case: RenameTestCase, client: LanguageClient):
    """Test that renaming a symbol suggests the correct edits."""
    result = await client.text_document_rename_async(
        params=lsp.RenameParams(
            position=test_case["position"],
            new_name=test_case["rename_to"],
            text_document=lsp.TextDocumentIdentifier(uri=test_case["uri"]),
        )
    )

    assert result.changes[test_case["uri"]] == test_case["changes"]
