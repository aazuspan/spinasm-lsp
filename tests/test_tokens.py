from __future__ import annotations

from dataclasses import dataclass, field

import lsprotocol.types as lsp
import pytest

from spinasm_lsp.parser import SPINAsmParser
from spinasm_lsp.tokens import ASFV1Token, LSPToken, TokenLookup

from .conftest import PATCH_DIR, TestCase, parametrize_cases


@dataclass
class TokenSemanticsTestCase(TestCase):
    """A dictionary to record prepare rename results for a symbol."""

    token: LSPToken
    encoding: list[int]
    type: lsp.SemanticTokenTypes
    modifiers: list[lsp.SemanticTokenModifiers] = field(default_factory=list)
    prev_token_start: lsp.Position = field(
        default_factory=lambda: lsp.Position(line=0, character=0)
    )


TOKEN_SEMANTICS: list[TokenSemanticsTestCase] = [
    TokenSemanticsTestCase(
        name="skp at start",
        token=LSPToken(
            type="MNEMONIC",
            stxt="SKP",
            range=lsp.Range(lsp.Position(0, 0), lsp.Position(0, 2)),
        ),
        encoding=[0, 0, 3, 12, 0b0],
        type=lsp.SemanticTokenTypes.Function,
    ),
    TokenSemanticsTestCase(
        name="variable on newline",
        token=LSPToken(
            type="LABEL",
            stxt="TMP",
            range=lsp.Range(lsp.Position(10, 0), lsp.Position(10, 2)),
        ),
        encoding=[9, 0, 3, 8, 0b0],
        type=lsp.SemanticTokenTypes.Variable,
        prev_token_start=lsp.Position(line=1, character=8),
    ),
    TokenSemanticsTestCase(
        name="constant after token",
        token=LSPToken(
            type="LABEL",
            stxt="REG0",
            range=lsp.Range(lsp.Position(3, 15), lsp.Position(3, 2)),
            is_constant=True,
        ),
        encoding=[0, 5, 4, 8, 0b1000000100],
        type=lsp.SemanticTokenTypes.Variable,
        modifiers=[
            lsp.SemanticTokenModifiers.Readonly,
            lsp.SemanticTokenModifiers.DefaultLibrary,
        ],
        prev_token_start=lsp.Position(line=3, character=10),
    ),
]


@parametrize_cases(TOKEN_SEMANTICS)
def test_semantic_tokens(test_case: TokenSemanticsTestCase):
    """Test that the semantic tokens are correctly generated."""
    encoding = test_case.token.semantic_encoding(test_case.prev_token_start)

    assert test_case.token.semantic_type == test_case.type
    assert test_case.token.semantic_modifiers == test_case.modifiers
    assert encoding == test_case.encoding


@pytest.fixture()
def sentence_token_lookup() -> tuple[str, TokenLookup]:
    """A sentence with a token registry for each word."""
    sentence = "This   is a line    with words."

    # Build a list of word tokens, ignoring whitespace. We'll build the tokens
    # consistently with asfv1 parsed tokens.
    words = list(filter(lambda x: x, sentence.split(" ")))
    token_vals = [ASFV1Token(type="LABEL", txt=w, stxt=w, val=None) for w in words]
    tokens = []
    col = 0

    lookup = TokenLookup()
    for t in token_vals:
        start = sentence.index(t.txt, col)
        parsed_token = t.at_position(lsp.Position(line=0, character=start))
        eval_token = LSPToken.from_parsed_token(parsed_token)

        col = eval_token.range.end.character + 1

        tokens.append(eval_token)
        lookup.add_token(parsed_token)

    return sentence, lookup


def test_get_token_from_registry(sentence_token_lookup: tuple[str, TokenLookup]):
    """Test that tokens are correctly retrieved by position from a registry."""
    sentence, lookup = sentence_token_lookup

    # Manually build a mapping of column indexes to expected token words. Note that
    # each word includes the whitespace immediately after it, which is consistent with
    # other LSPs, and that all other whitespace is None.
    token_positions = {i: None for i in range(len(sentence))}
    for i in range(0, 5):
        token_positions[i] = "This"
    for i in range(7, 10):
        token_positions[i] = "is"
    for i in range(10, 12):
        token_positions[i] = "a"
    for i in range(12, 17):
        token_positions[i] = "line"
    for i in range(20, 25):
        token_positions[i] = "with"
    for i in range(25, 32):
        token_positions[i] = "words."

    for i, word in token_positions.items():
        found_tok = lookup.get(position=lsp.Position(line=0, character=i))
        found_val = found_tok.stxt if found_tok is not None else found_tok
        msg = f"Expected token `{word}` at col {i}, found `{found_val}`"
        assert found_val == word, msg


def test_get_token_at_invalid_position_returns_none(sentence_token_lookup):
    """Test that retrieving tokens from out of bounds always returns None."""
    _, lookup = sentence_token_lookup

    assert lookup.get(position=lsp.Position(line=99, character=99)) is None


def test_get_token_positions():
    """Test getting all positions of a token from a registry."""
    patch = PATCH_DIR / "Basic.spn"
    with open(patch) as fp:
        source = fp.read()

    parser = SPINAsmParser(source).parse()

    all_matches = parser.evaluated_tokens.get(name="apout")
    assert len(all_matches) == 4
    assert [t.range.start.line for t in all_matches] == [23, 57, 60, 70]


def test_concatenate_cho_rdal_tokens():
    """Test that CHO and RDAL tokens are concatenated correctly into CHO RDAL."""
    cho = ASFV1Token(type="MNEMONIC", txt="CHO", stxt="CHO", val=None).at_position(
        start=lsp.Position(line=0, character=0)
    )

    # Put whitespace between CHO and RDAL to test that range is calculated
    rdal = ASFV1Token(type="LABEL", txt="RDAL", stxt="RDAL", val=None).at_position(
        start=lsp.Position(line=0, character=10)
    )

    cho_rdal = cho.concatenate(rdal)

    assert cho_rdal.stxt == "CHO RDAL"
    assert cho_rdal.type == "MNEMONIC"
    assert cho_rdal.range == lsp.Range(
        start=lsp.Position(line=0, character=0), end=lsp.Position(line=0, character=14)
    )
