from __future__ import annotations

from dataclasses import dataclass

import lsprotocol.types as lsp
import pytest
from pytest_lsp import LanguageClient

from ..conftest import PATCH_DIR, TestCase, parametrize_cases


@dataclass
class SignatureHelpTestCase(TestCase):
    """A dictionary to record signature help information for at a position."""

    position: lsp.Position
    active_parameter: int | None
    param_contains: str | None
    doc_contains: str | None
    uri: str


TEST_CASES: list[SignatureHelpTestCase] = [
    SignatureHelpTestCase(
        name="no_opcode",
        position=lsp.Position(line=8, character=3),
        active_parameter=None,
        doc_contains=None,
        param_contains=None,
        uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
    ),
    SignatureHelpTestCase(
        name="skp_first_arg",
        position=lsp.Position(line=37, character=4),
        active_parameter=0,
        doc_contains="**`SKP CMASK, N`** allows conditional program execution",
        param_contains="CMASK: Binary | Hex ($00-$1F) | Symbolic",
        uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
    ),
    SignatureHelpTestCase(
        name="skp_second_arg",
        position=lsp.Position(line=37, character=8),
        active_parameter=1,
        doc_contains="**`SKP CMASK, N`** allows conditional program execution",
        param_contains="N: Decimal (1-63) | Label",
        uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
    ),
    SignatureHelpTestCase(
        name="skp_out_of_bounds",
        position=lsp.Position(line=37, character=45),
        active_parameter=1,
        doc_contains="**`SKP CMASK, N`** allows conditional program execution",
        param_contains="N: Decimal (1-63) | Label",
        uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
    ),
    SignatureHelpTestCase(
        name="cho_rda",
        position=lsp.Position(line=85, character=8),
        active_parameter=0,
        doc_contains="**`CHO RDA, N, C, D`**, like the `RDA` instruction",
        param_contains="N: LFO select: SIN0,SIN1,RMP0,RMP1",
        uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
    ),
    SignatureHelpTestCase(
        name="cho_rda_unfinished",
        position=lsp.Position(line=85, character=0),
        active_parameter=None,
        doc_contains=None,
        param_contains=None,
        uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
    ),
    SignatureHelpTestCase(
        name="cho_rda_before_comma",
        position=lsp.Position(line=85, character=7),
        active_parameter=None,
        doc_contains=None,
        param_contains=None,
        uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
    ),
]


@parametrize_cases(TEST_CASES)
@pytest.mark.asyncio()
async def test_signature_help(test_case: SignatureHelpTestCase, client: LanguageClient):
    result = await client.text_document_signature_help_async(
        params=lsp.SignatureHelpParams(
            context=lsp.SignatureHelpContext(
                trigger_kind=lsp.SignatureHelpTriggerKind.TriggerCharacter,
                is_retrigger=False,
            ),
            position=test_case.position,
            text_document=lsp.TextDocumentIdentifier(uri=test_case.uri),
        )
    )

    if test_case.active_parameter is None:
        assert not result
        return

    sig: lsp.SignatureInformation = result.signatures[result.active_signature]
    param: lsp.ParameterInformation = sig.parameters[result.active_parameter]

    assert test_case.active_parameter == result.active_parameter
    assert test_case.doc_contains in str(sig.documentation)
    assert test_case.param_contains in param.label
