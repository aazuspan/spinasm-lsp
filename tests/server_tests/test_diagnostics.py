import lsprotocol.types as lsp
import pytest
from pytest_lsp import LanguageClient


@pytest.mark.asyncio()
async def test_diagnostic_parsing_errors(client: LanguageClient):
    """Test that parsing errors and warnings are correctly reported by the server."""
    source_with_errors = """
; Undefined symbol a
SOF 0,a

; Label REG0 re-defined
REG0 EQU 4

; Register out of range
MULX 100
"""

    # We need a URI to associate with the source, but it doesn't need to be a real file.
    test_uri = "dummy_uri"
    client.text_document_did_open(
        lsp.DidOpenTextDocumentParams(
            text_document=lsp.TextDocumentItem(
                uri=test_uri,
                language_id="spinasm",
                version=1,
                text=source_with_errors,
            )
        )
    )

    await client.wait_for_notification(lsp.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)

    expected = [
        lsp.Diagnostic(
            range=lsp.Range(
                start=lsp.Position(line=2, character=6),
                end=lsp.Position(line=2, character=6),
            ),
            message="Undefined label a",
            severity=lsp.DiagnosticSeverity.Error,
            source="SPINAsm",
        ),
        lsp.Diagnostic(
            range=lsp.Range(
                start=lsp.Position(line=5, character=9),
                end=lsp.Position(line=5, character=9),
            ),
            message="Label REG0 re-defined",
            severity=lsp.DiagnosticSeverity.Warning,
            source="SPINAsm",
        ),
        lsp.Diagnostic(
            range=lsp.Range(
                start=lsp.Position(line=8, character=0),
                end=lsp.Position(line=8, character=0),
            ),
            message="Register 0x64 out of range for MULX",
            severity=lsp.DiagnosticSeverity.Error,
            source="SPINAsm",
        ),
    ]

    returned = client.diagnostics[test_uri]
    extra = len(returned) - len(expected)
    assert extra == 0, f"Expected {len(expected)} diagnostics, got {len(returned)}."

    for i, diag in enumerate(expected):
        assert diag == returned[i], f"Diagnostic {i} does not match expected"
