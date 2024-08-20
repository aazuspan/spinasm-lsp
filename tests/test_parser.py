"""Test the parsing of SPINAsm programs."""

from __future__ import annotations

import json
from pathlib import Path

import jsonpickle
import pytest

from spinasm_lsp.parser import SPINAsmParser

from .conftest import TEST_PATCHES


@pytest.fixture(scope="session")
def original_datadir() -> Path:
    """Override the data directory used by pytest-regressions."""
    return Path(__file__).parent / "output"


def serialize_parser_output(parser: SPINAsmParser) -> dict:
    """Serialize the output of the parser for testing."""

    # Grab the relevant attributes from the parser. Others are mostly intermediate
    # results or internal to asfv1.
    output_attrs = {
        # Check the list of tokens rather than the token lookup
        "evaluated_tokens": list(parser.evaluated_tokens),
        "semantic_encoding": parser.semantic_encoding,
        "diagnostics": parser.diagnostics,
    }

    return json.loads(jsonpickle.encode(output_attrs, make_refs=True))


@pytest.mark.parametrize("patch", TEST_PATCHES, ids=lambda x: x.stem)
def test_example_patches(patch, data_regression):
    """Test that the example patches from SPINAsm are parsable."""
    with open(patch, encoding="utf-8") as f:
        source = f.read()

    parser = SPINAsmParser(source)
    assert list(parser.evaluated_tokens)

    encoded = serialize_parser_output(parser)

    data_regression.check(encoded)
