from __future__ import annotations

from dataclasses import dataclass

import lsprotocol.types as lsp
import pytest
from pytest_lsp import LanguageClient

from ..conftest import TestCase, parametrize_cases


@dataclass
class DiagnosticTestCase(TestCase):
    """A dictionary to record prepare rename results for a symbol."""

    source: str
    expected: list[lsp.Diagnostic]


TEST_CASES: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        name="undefined label",
        source="""SOF 0, a\n""",
        expected=[
            lsp.Diagnostic(
                range=lsp.Range(
                    start=lsp.Position(line=0, character=7),
                    end=lsp.Position(line=0, character=7),
                ),
                message="Undefined label a",
                severity=lsp.DiagnosticSeverity.Error,
                source="SPINAsm",
            ),
        ],
    ),
    DiagnosticTestCase(
        name="redefined constant",
        source="""REG0 EQU 4\n""",
        expected=[
            lsp.Diagnostic(
                range=lsp.Range(
                    start=lsp.Position(line=0, character=9),
                    end=lsp.Position(line=0, character=9),
                ),
                message="Label REG0 re-defined",
                severity=lsp.DiagnosticSeverity.Warning,
                source="SPINAsm",
            ),
        ],
    ),
    DiagnosticTestCase(
        name="out of range",
        source="""MULX 100\n""",
        expected=[
            lsp.Diagnostic(
                range=lsp.Range(
                    start=lsp.Position(line=0, character=5),
                    end=lsp.Position(line=0, character=5),
                ),
                message="Register 0x64 out of range for MULX",
                severity=lsp.DiagnosticSeverity.Error,
                source="SPINAsm",
            ),
        ],
    ),
    DiagnosticTestCase(
        name="out of range (without newline)",
        source="""MULX 100""",
        expected=[
            lsp.Diagnostic(
                range=lsp.Range(
                    start=lsp.Position(line=0, character=5),
                    end=lsp.Position(line=0, character=5),
                ),
                message="Register 0x64 out of range for MULX",
                severity=lsp.DiagnosticSeverity.Error,
                source="SPINAsm",
            ),
        ],
    ),
]


@parametrize_cases(TEST_CASES)
@pytest.mark.asyncio()
async def test_diagnostic_parsing_errors(
    test_case: DiagnosticTestCase, client: LanguageClient
):
    """Test that parsing errors and warnings are correctly reported by the server."""
    # We need a URI to associate with the source, but it doesn't need to be a real file.
    test_uri = "dummy_uri"

    client.text_document_did_open(
        lsp.DidOpenTextDocumentParams(
            text_document=lsp.TextDocumentItem(
                uri=test_uri,
                language_id="spinasm",
                version=1,
                text=test_case.source,
            )
        )
    )

    await client.wait_for_notification(lsp.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)

    returned = client.diagnostics[test_uri]
    assert len(returned) == len(
        test_case.expected
    ), "Expected number of diagnostics does not match"

    for expected, actual in zip(test_case.expected, returned):
        assert actual == expected, "Diagnostic does not match expected"
