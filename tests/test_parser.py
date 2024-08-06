"""Test the parsing of the SpinASM grammar."""

from __future__ import annotations

import random

import pytest

from spinasm_lsp.parser import (
    Assignment,
    FV1Program,
    Instruction,
    Label,
)

from .conftest import TEST_PATCHES


@pytest.mark.parametrize(
    "expr",
    ["42", "42.0", "0x2A", "$2A", "%00101010", "%001_01_010"],
    ids=["i", "f", "0x", "$", "%", "%_"],
)
def test_number_representations(expr):
    """Test supported number representations."""
    assert FV1Program(f"OP {expr}").statements[0].args[0] == 42


@pytest.mark.parametrize("stmt", [None, "SOF 0", "x EQU 4"], ids=["none", "op", "equ"])
def test_parse_label(stmt: str | None):
    """Test that labels are parsed, with and without following statements."""
    prog = FV1Program(f"myLabel: {stmt}")
    assert len(prog.statements) == 2 if stmt else 1
    assert prog.statements[0] == Label("myLabel")


@pytest.mark.parametrize("n_args", [0, 1, 3], ids=lambda x: f"{x} args")
def test_parse_instruction(n_args):
    """Test that instructions with varying number of arguments are parsed correctly."""
    args = [random.randint(0, 100) for _ in range(n_args)]
    code = f"OP {','.join(map(str, args))}"
    assert FV1Program(code).statements[0] == Instruction("OP", args=args)


@pytest.mark.parametrize("type", ["equ", "mem"])
@pytest.mark.parametrize("order", ["{name} {type} {val}", "{type} {name} {val}"])
def test_assign(type: str, order: str):
    """Test that assignment with EQU and MEM work with either keyword order."""
    code = order.format(name="A", type=type, val=5)
    prog = FV1Program(code)
    assert prog.statements[0] == Assignment(f"{type}", "A", 5)


def test_parse_instruction_with_multiple_commas():
    """Test that redundant commas are ignored."""
    assert FV1Program("SOF 0,,42").statements[0] == Instruction("SOF", args=[0, 42])


def test_whitespace_ignored():
    """Test that whitespace around instructions and assignments are ignored."""
    assert FV1Program(" MULX 0  \n B EQU A*2 \n   ")


@pytest.mark.xfail()
@pytest.mark.parametrize("patch", TEST_PATCHES, ids=lambda x: x.stem)
def test_example_patches(patch):
    """Test that the example patches from SpinASM parse correctly."""
    with open(patch) as f:
        FV1Program(f.read())
