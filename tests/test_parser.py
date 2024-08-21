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


def test_parsing_as_typed():
    """Test that the parser is fault tolerant for partially entered programs."""

    # Example program from SPINAsm documentation. Iteratively parsing at each character
    # is slow, so we use a small sample program here rather than parameterizing over the
    # larger test patches.
    source = """
    ; Example program from SPINAsm documentation
    Attn EQU 0.5
    Tmp_Reg EQU 63
    Tmp_Del EQU $2000

    sof 0,0
    rda Tmp_Del,Attn
    wrax Tmp_Reg,1.0
    wrax DACL
    """
    source_chars = list(source)
    for i in range(len(source_chars)):
        partial_source = "".join(source_chars[:i])
        assert SPINAsmParser(partial_source)
