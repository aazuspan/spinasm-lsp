from __future__ import annotations

from dataclasses import dataclass

import lsprotocol.types as lsp
import pytest
from pytest_lsp import LanguageClient

from ..conftest import PATCH_DIR, TestCase, parametrize_cases


@dataclass
class CompletionTestCase(TestCase):
    """A dictionary to track an expected completion result."""

    label: str
    detail: str
    kind: lsp.CompletionItemKind
    doc_contains: str | None
    uri: str


TEST_CASES: list[CompletionTestCase] = [
    CompletionTestCase(
        name="variable",
        label="APOUT",
        detail="(variable) APOUT: Literal[33]",
        kind=lsp.CompletionItemKind.Variable,
        doc_contains=None,
        uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
    ),
    CompletionTestCase(
        name="constant",
        label="REG0",
        detail="(constant) REG0: Literal[32]",
        kind=lsp.CompletionItemKind.Constant,
        doc_contains=None,
        uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
    ),
    CompletionTestCase(
        name="multi-word opcode",
        label="CHO RDA",
        detail="(opcode)",
        kind=lsp.CompletionItemKind.Function,
        doc_contains="`CHO RDA, N, C, D`",
        uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
    ),
    CompletionTestCase(
        name="assembler",
        label="EQU",
        detail="(assembler)",
        kind=lsp.CompletionItemKind.Operator,
        doc_contains="**`EQU`** allows one to define symbolic operands",
        uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
    ),
]


@parametrize_cases(TEST_CASES)
@pytest.mark.asyncio()
async def test_completions(test_case: CompletionTestCase, client: LanguageClient):
    """Test that expected completions are shown with details and documentation."""
    results = await client.text_document_completion_async(
        params=lsp.CompletionParams(
            position=lsp.Position(line=0, character=0),
            text_document=lsp.TextDocumentIdentifier(uri=test_case.uri),
        )
    )
    assert results is not None, "Expected completions"

    matches = [item for item in results.items if item.label == test_case.label]

    assert (
        len(matches) == 1
    ), f"Expected 1 matching label `{test_case.label}`, got {len(matches)}."
    match = matches[0]

    assert match.detail == test_case.detail
    assert match.kind == test_case.kind
    if test_case.doc_contains is not None:
        assert test_case.doc_contains in str(match.documentation)
