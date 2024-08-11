"""Test LSP utilities."""

import lsprotocol.types as lsp
import pytest

from spinasm_lsp import utils
from spinasm_lsp.parser import SPINAsmParser

from .conftest import PATCH_DIR


@pytest.fixture()
def sentence_token_registry() -> tuple[str, utils.TokenRegistry]:
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
        end = start + len(t["txt"]) - 1
        col = end + 1
        tokens.append(
            utils.Token(
                t,
                range=lsp.Range(
                    start=lsp.Position(line=0, character=start),
                    end=lsp.Position(line=0, character=end),
                ),
            )
        )

    return sentence, utils.TokenRegistry(tokens)


def test_callback_dict():
    """Test that a CallbackDict calls its callback function when values are set."""
    key_store = []
    items = {
        "foo": 42,
        "bar": 0,
        "baz": 99,
    }
    d = utils.CallbackDict(items, callback=lambda k: key_store.append(k))
    assert d == items
    assert key_store == ["foo", "bar", "baz"]


def test_get_token_from_registry(sentence_token_registry):
    """Test that tokens are correctly retrieved by position from a registry."""
    sentence, reg = sentence_token_registry

    # Manually build a mapping of column indexes to expected token words
    token_positions = {i: None for i in range(len(sentence))}
    for i in range(0, 4):
        token_positions[i] = "This"
    for i in range(7, 9):
        token_positions[i] = "is"
    for i in range(10, 11):
        token_positions[i] = "a"
    for i in range(12, 16):
        token_positions[i] = "line"
    for i in range(20, 24):
        token_positions[i] = "with"
    for i in range(25, 31):
        token_positions[i] = "words."

    for i, word in token_positions.items():
        found_tok = reg.get_token_at_position(lsp.Position(line=0, character=i))
        found_val = found_tok.value["txt"] if found_tok is not None else found_tok
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
