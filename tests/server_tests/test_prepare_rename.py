from __future__ import annotations

import lsprotocol.types as lsp
import pytest
from pytest_lsp import LanguageClient

from ..conftest import PATCH_DIR, TestCase


class PrepareRenameTestCase(TestCase):
    """A dictionary to record prepare rename results for a symbol."""

    position: lsp.Position
    result: bool
    message: str | None
    uri: str


PREPARE_RENAMES: list[PrepareRenameTestCase] = [
    {
        "name": "mem",
        "position": lsp.Position(line=8, character=0),
        "result": None,
        "message": "Can't rename non-user defined token MEM.",
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
    },
    {
        "name": "reg0",
        "position": lsp.Position(line=22, character=10),
        "result": None,
        "message": "Can't rename non-user defined token REG0.",
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
    },
    {
        "name": "ap1",
        "position": lsp.Position(line=8, character=4),
        "result": lsp.PrepareRenameResult_Type2(default_behavior=True),
        "message": None,
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
    },
    {
        "name": "endclr",
        "position": lsp.Position(line=37, character=10),
        "result": lsp.PrepareRenameResult_Type2(default_behavior=True),
        "message": None,
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
    },
]


@pytest.mark.parametrize("test_case", PREPARE_RENAMES, ids=lambda x: x["name"])
@pytest.mark.asyncio()
async def test_prepare_rename(test_case: PrepareRenameTestCase, client: LanguageClient):
    """Test that prepare rename prevents renaming non-user defined tokens."""
    result = await client.text_document_prepare_rename_async(
        params=lsp.PrepareRenameParams(
            position=test_case["position"],
            text_document=lsp.TextDocumentIdentifier(uri=test_case["uri"]),
        )
    )

    assert result == test_case["result"]

    if test_case["message"]:
        assert test_case["message"] in client.log_messages[0].message
        assert client.log_messages[0].type == lsp.MessageType.Info
    else:
        assert not client.log_messages
