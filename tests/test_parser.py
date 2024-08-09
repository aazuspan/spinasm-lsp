"""Test the parsing of SPINAsm programs."""

from __future__ import annotations

import pytest

from spinasm_lsp.parser import SPINAsmParser

from .conftest import TEST_PATCHES


@pytest.mark.parametrize("patch", TEST_PATCHES, ids=lambda x: x.stem)
def test_example_patches(patch):
    """Test that the example patches from SPINAsm are parsable."""
    with open(patch, encoding="utf-8") as f:
        assert SPINAsmParser(f.read())
