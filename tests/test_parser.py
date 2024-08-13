"""Test the parsing of SPINAsm programs."""

from __future__ import annotations

import lsprotocol.types as lsp
import pytest

from spinasm_lsp.parser import SPINAsmParser, Token, TokenRegistry

from .conftest import PATCH_DIR, TEST_PATCHES


@pytest.mark.parametrize("patch", TEST_PATCHES, ids=lambda x: x.stem)
def test_example_patches(patch):
    """Test that the example patches from SPINAsm are parsable."""
    with open(patch, encoding="utf-8") as f:
        assert SPINAsmParser(f.read()).parse()


@pytest.fixture()
def sentence_token_registry() -> tuple[str, TokenRegistry]:
    """A sentence with a token registry for each word."""
    sentence = "This   is a line    with words."

    # Build a list of word tokens, ignoring whitespace. We'll build the tokens
    # consistently with asfv1 parsed tokens.
    words = list(filter(lambda x: x, sentence.split(" ")))
    token_vals = [{"type": "LABEL", "txt": w, "stxt": w, "val": None} for w in words]
    tokens = []
    col = 0

    for t in token_vals:
        start = sentence.index(t["txt"], col)
        token = Token(t, start=lsp.Position(line=0, character=start))
        col = token.range.end.character + 1

        tokens.append(token)

    return sentence, TokenRegistry(tokens)


def test_get_token_from_registry(sentence_token_registry):
    """Test that tokens are correctly retrieved by position from a registry."""
    sentence, reg = sentence_token_registry

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
        found_tok = reg.get_token_at_position(lsp.Position(line=0, character=i))
        found_val = found_tok.symbol["txt"] if found_tok is not None else found_tok
        msg = f"Expected token `{word}` at col {i}, found `{found_val}`"
        assert found_val == word, msg


def test_get_token_at_invalid_position_returns_none(sentence_token_registry):
    """Test that retrieving tokens from out of bounds always returns None."""
    _, reg = sentence_token_registry

    assert reg.get_token_at_position(lsp.Position(line=99, character=99)) is None


def test_get_token_positions():
    """Test getting all positions of a token from a registry."""
    patch = PATCH_DIR / "Basic.spn"
    with open(patch) as fp:
        source = fp.read()

    parser = SPINAsmParser(source).parse()

    all_matches = parser.token_registry.get_matching_tokens("apout")
    assert len(all_matches) == 4
    assert [t.range.start.line for t in all_matches] == [23, 57, 60, 70]


def test_concatenate_cho_rdal_tokens():
    """Test that CHO and RDAL tokens are concatenated correctly into CHO RDAL."""
    cho_rdal = Token(
        symbol={"type": "MNEMONIC", "txt": "cho", "stxt": "CHO", "val": None},
        start=lsp.Position(line=0, character=0),
    ).concatenate(
        Token(
            symbol={"type": "LABEL", "txt": "rdal", "stxt": "RDAL", "val": None},
            # Put whitespace between CHO and RDAL to test that range is calculated
            start=lsp.Position(line=0, character=10),
        )
    )

    assert cho_rdal.symbol == {
        "type": "MNEMONIC",
        "txt": "cho rdal",
        "stxt": "CHO RDAL",
        "val": None,
    }

    assert cho_rdal.range == lsp.Range(
        start=lsp.Position(line=0, character=0), end=lsp.Position(line=0, character=14)
    )
