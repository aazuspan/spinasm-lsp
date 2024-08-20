from __future__ import annotations

from dataclasses import dataclass

import lsprotocol.types as lsp
import pytest
from pytest_lsp import LanguageClient

from ..conftest import PATCH_DIR, TestCase, parametrize_cases


@dataclass
class HoverTestCase(TestCase):
    """A dictionary to record hover information for a symbol."""

    position: lsp.Position
    contains: str | None
    uri: str


TEST_CASES: list[HoverTestCase] = [
    HoverTestCase(
        name="mem",
        position=lsp.Position(line=8, character=0),
        contains="`MEM`",
        uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
    ),
    HoverTestCase(
        name="skp",
        position=lsp.Position(line=37, character=2),
        contains="`SKP CMASK, N`",
        uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
    ),
    HoverTestCase(
        name="endclr",
        position=lsp.Position(line=37, character=13),
        contains="(label) ENDCLR: Offset[4]",
        uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
    ),
    HoverTestCase(
        name="mono",
        position=lsp.Position(line=47, character=5),
        contains="(variable) MONO: Literal[32]",
        uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
    ),
    HoverTestCase(
        name="reg0",
        position=lsp.Position(line=22, character=9),
        contains="(constant) REG0: Literal[32]",
        uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
    ),
    HoverTestCase(
        name="lap2b#",
        position=lsp.Position(line=73, character=4),
        contains="(variable) LAP2B#: Literal[9802]",
        uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
    ),
    HoverTestCase(
        name="CHO_rda",
        position=lsp.Position(line=85, character=0),
        contains="`CHO RDA, N, C, D`",
        uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
    ),
    HoverTestCase(
        name="cho_RDA",
        position=lsp.Position(line=85, character=4),
        contains="`CHO RDA, N, C, D`",
        uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
    ),
    HoverTestCase(
        name="None",
        position=lsp.Position(line=8, character=8),
        contains=None,
        uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
    ),
]


@parametrize_cases(TEST_CASES)
@pytest.mark.asyncio()
async def test_hover(test_case: HoverTestCase, client: LanguageClient):
    result = await client.text_document_hover_async(
        params=lsp.CompletionParams(
            position=test_case.position,
            text_document=lsp.TextDocumentIdentifier(uri=test_case.uri),
        )
    )

    if test_case.contains is None:
        assert result is None, "Expected no hover result"
    else:
        msg = f"Hover does not contain `{test_case.contains}`"
        assert test_case.contains in result.contents.value, msg
