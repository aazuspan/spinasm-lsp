import lsprotocol.types as lsp
import pytest
import pytest_lsp
from pytest_lsp import ClientServerConfig, LanguageClient

from .conftest import (
    DEFINITIONS,
    HOVERS,
    PATCH_DIR,
    PREPARE_RENAMES,
    REFERENCES,
    RENAMES,
    SIGNATURE_HELPS,
    SYMBOL_DEFINITIONS,
    DefinitionDict,
    PrepareRenameDict,
    ReferenceDict,
    RenameDict,
    SignatureHelpDict,
    SymbolDefinitionDict,
)


@pytest_lsp.fixture(
    params=["neovim", "visual_studio_code"],
    config=ClientServerConfig(server_command=["spinasm-lsp"]),
)
async def client(request, lsp_client: LanguageClient):
    # Setup the server
    params = lsp.InitializeParams(
        capabilities=pytest_lsp.client_capabilities(request.param)
    )

    await lsp_client.initialize_session(params)
    yield

    # Shutdown the server after the test
    await lsp_client.shutdown_session()


@pytest.mark.asyncio()
@pytest.mark.parametrize("test_case", DEFINITIONS, ids=lambda x: x["symbol"])
async def test_definition(test_case: DefinitionDict, client: LanguageClient):
    """Test that the definition location of different assignments is correct."""
    result = await client.text_document_definition_async(
        params=lsp.DefinitionParams(
            position=test_case["referenced"],
            text_document=lsp.TextDocumentIdentifier(uri=test_case["uri"]),
        )
    )

    assert result == test_case["defined"]


@pytest.mark.asyncio()
async def test_completions(client: LanguageClient):
    """Test that expected completions are shown with details and documentation."""
    patch = PATCH_DIR / "Basic.spn"

    results = await client.text_document_completion_async(
        params=lsp.CompletionParams(
            position=lsp.Position(line=0, character=0),
            text_document=lsp.TextDocumentIdentifier(uri=f"file:///{patch.absolute()}"),
        )
    )
    assert results is not None, "Expected completions"
    completions = [item.label for item in results.items]

    expected_completions = [
        # Memory locations
        "AP1",
        "LAP1A",
        "D2",
        # Variables
        "MONO",
        "APOUT",
        "KRF",
        # Constants
        "REG0",
        "SIN0",
        # Opcodes
        "SOF",
        "MULX",
        "WRAX",
    ]

    for completion in expected_completions:
        assert completion in completions, f"Expected completion {completion} not found"

    # Completions for defined values should show their literal value
    apout_completion = [item for item in results.items if item.label == "APOUT"][0]
    assert apout_completion.detail == "(variable) APOUT: Literal[33]"
    assert apout_completion.kind == lsp.CompletionItemKind.Variable
    assert apout_completion.documentation is None

    # Completions for constant values should show their literal value
    reg0_completion = [item for item in results.items if item.label == "REG0"][0]
    assert reg0_completion.detail == "(constant) REG0: Literal[32]"
    assert reg0_completion.kind == lsp.CompletionItemKind.Constant
    assert reg0_completion.documentation is None

    # Completions for opcodes should include their documentation
    cho_rda_completion = [item for item in results.items if item.label == "CHO RDA"][0]
    assert cho_rda_completion.detail == "(opcode)"
    assert cho_rda_completion.kind == lsp.CompletionItemKind.Function
    assert "`CHO RDA, N, C, D`" in str(cho_rda_completion.documentation)


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


@pytest.mark.parametrize("test_case", HOVERS, ids=lambda x: x["symbol"])
@pytest.mark.asyncio()
async def test_hover(test_case: dict, client: LanguageClient):
    result = await client.text_document_hover_async(
        params=lsp.CompletionParams(
            position=test_case["position"],
            text_document=lsp.TextDocumentIdentifier(uri=test_case["uri"]),
        )
    )

    if test_case["contains"] is None:
        assert result is None, "Expected no hover result"
    else:
        msg = f"Hover does not contain `{test_case['contains']}`"
        assert test_case["contains"] in result.contents.value, msg


@pytest.mark.parametrize("test_case", PREPARE_RENAMES, ids=lambda x: x["symbol"])
@pytest.mark.asyncio()
async def test_prepare_rename(test_case: PrepareRenameDict, client: LanguageClient):
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


@pytest.mark.parametrize("test_case", RENAMES, ids=lambda x: x["symbol"])
@pytest.mark.asyncio()
async def test_rename(test_case: RenameDict, client: LanguageClient):
    """Test that renaming a symbol suggests the correct edits."""
    result = await client.text_document_rename_async(
        params=lsp.RenameParams(
            position=test_case["position"],
            new_name=test_case["rename_to"],
            text_document=lsp.TextDocumentIdentifier(uri=test_case["uri"]),
        )
    )

    assert result.changes[test_case["uri"]] == test_case["changes"]


@pytest.mark.parametrize("test_case", SYMBOL_DEFINITIONS, ids=lambda x: x["symbol"])
@pytest.mark.asyncio()
async def test_symbol_definitions(
    test_case: SymbolDefinitionDict, client: LanguageClient
):
    """Test that the definitions of all symbols in the document are returned."""
    result = await client.text_document_document_symbol_async(
        params=lsp.DocumentSymbolParams(
            text_document=lsp.TextDocumentIdentifier(uri=test_case["uri"]),
        )
    )

    matching = [item for item in result if item.name == test_case["symbol"].upper()]
    assert matching, f"Symbol {test_case['symbol'].upper()} not in document symbols"

    item = matching[0]
    assert item.kind == test_case["kind"]
    assert item.range == test_case["range"]


@pytest.mark.parametrize("test_case", REFERENCES, ids=lambda x: x["symbol"])
@pytest.mark.asyncio()
async def test_references(test_case: ReferenceDict, client: LanguageClient):
    """Test that references to a symbol are correctly found."""
    result = await client.text_document_references_async(
        params=lsp.ReferenceParams(
            context=lsp.ReferenceContext(include_declaration=False),
            position=test_case["position"],
            text_document=lsp.TextDocumentIdentifier(uri=test_case["uri"]),
        )
    )

    assert result == test_case["references"]


@pytest.mark.parametrize("test_case", SIGNATURE_HELPS, ids=lambda x: x["symbol"])
@pytest.mark.asyncio()
async def test_signature_help(test_case: SignatureHelpDict, client: LanguageClient):
    result = await client.text_document_signature_help_async(
        params=lsp.SignatureHelpParams(
            context=lsp.SignatureHelpContext(
                trigger_kind=lsp.SignatureHelpTriggerKind.Invoked, is_retrigger=False
            ),
            position=test_case["position"],
            text_document=lsp.TextDocumentIdentifier(uri=test_case["uri"]),
        )
    )

    if test_case["active_parameter"] is None:
        assert not result
        return

    sig: lsp.SignatureInformation = result.signatures[result.active_signature]
    param: lsp.ParameterInformation = sig.parameters[result.active_parameter]

    assert test_case["active_parameter"] == result.active_parameter
    assert test_case["doc_contains"] in str(sig.documentation)
    assert test_case["param_contains"] in param.label
