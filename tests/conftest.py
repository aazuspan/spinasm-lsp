from __future__ import annotations

from pathlib import Path
from typing import TypedDict

import lsprotocol.types as lsp

PATCH_DIR = Path(__file__).parent / "patches"
TEST_PATCHES = list(PATCH_DIR.glob("*.spn"))
assert TEST_PATCHES, "No test patches found in the patches directory."


class DefinitionDict(TypedDict):
    """A dictionary track where a symbol is referenced and defined."""

    symbol: str
    referenced: lsp.Position
    defined: lsp.Location


class SymbolDefinitionDict(TypedDict):
    """A dictionary to record definition locations for a symbol."""

    symbol: str
    range: lsp.Range
    kind: lsp.SymbolKind


class HoverDict(TypedDict):
    """A dictionary to record hover information for a symbol."""

    symbol: str
    position: lsp.Position
    contains: str | None


class PrepareRenameDict(TypedDict):
    """A dictionary to record prepare rename results for a symbol."""

    symbol: str
    position: lsp.Position
    result: bool
    message: str | None


class RenameDict(TypedDict):
    """A dictionary to record rename results for a symbol."""

    symbol: str
    rename_to: str
    position: lsp.Position
    changes: list[lsp.TextEdit]


SYMBOL_DEFINITIONS: list[SymbolDefinitionDict] = [
    {
        # Variable
        "symbol": "apout",
        "kind": lsp.SymbolKind.Variable,
        "range": lsp.Range(
            start=lsp.Position(line=23, character=4),
            end=lsp.Position(line=23, character=9),
        ),
    },
    {
        # Memory
        "symbol": "lap2a",
        "kind": lsp.SymbolKind.Variable,
        "range": lsp.Range(
            start=lsp.Position(line=16, character=4),
            end=lsp.Position(line=16, character=9),
        ),
    },
    {
        # Label
        "symbol": "endclr",
        "kind": lsp.SymbolKind.Module,
        "range": lsp.Range(
            start=lsp.Position(line=41, character=0),
            end=lsp.Position(line=41, character=6),
        ),
    },
]


# Example assignments from the "Basic.spn" patch, for testing definition locations
DEFINITIONS: list[DefinitionDict] = [
    {
        # Variable
        "symbol": "apout",
        "referenced": lsp.Position(line=57, character=7),
        "defined": lsp.Location(
            uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
            range=lsp.Range(
                start=lsp.Position(line=23, character=4),
                end=lsp.Position(line=23, character=9),
            ),
        ),
    },
    {
        # Memory
        "symbol": "lap2a",
        "referenced": lsp.Position(line=72, character=7),
        "defined": lsp.Location(
            uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
            range=lsp.Range(
                start=lsp.Position(line=16, character=4),
                end=lsp.Position(line=16, character=9),
            ),
        ),
    },
    {
        # Memory. Note that this has an address modifier, but still points to the
        # original definition.
        "symbol": "lap2a#",
        "referenced": lsp.Position(line=71, character=7),
        "defined": lsp.Location(
            uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
            range=lsp.Range(
                start=lsp.Position(line=16, character=4),
                end=lsp.Position(line=16, character=9),
            ),
        ),
    },
    {
        # Label
        "symbol": "endclr",
        "referenced": lsp.Position(line=37, character=9),
        "defined": lsp.Location(
            uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
            range=lsp.Range(
                start=lsp.Position(line=41, character=0),
                end=lsp.Position(line=41, character=6),
            ),
        ),
    },
]


# Example hovers from the "Basic.spn" patch, for testing hover info
HOVERS: list[HoverDict] = [
    {
        "symbol": "mem",
        "position": lsp.Position(line=8, character=0),
        "contains": "## `MEM`",
    },
    {
        "symbol": "skp",
        "position": lsp.Position(line=37, character=2),
        "contains": "## `SKP CMASK,N`",
    },
    {
        "symbol": "endclr",
        "position": lsp.Position(line=37, character=13),
        "contains": "(label) ENDCLR: Offset[4]",
    },
    {
        "symbol": "mono",
        "position": lsp.Position(line=47, character=5),
        "contains": "(variable) MONO: Literal[32]",
    },
    {
        "symbol": "reg0",
        "position": lsp.Position(line=22, character=9),
        "contains": "(constant) REG0: Literal[32]",
    },
    {
        "symbol": "lap2b#",
        "position": lsp.Position(line=73, character=4),
        "contains": "(variable) LAP2B#: Literal[9802]",
    },
    {
        # CHO RDA, hovering over CHO
        "symbol": "CHO_rda",
        "position": lsp.Position(line=85, character=0),
        "contains": "## `CHO RDA N, C, D`",
    },
    {
        # CHO RDA, hovering over RDA
        "symbol": "cho_RDA",
        "position": lsp.Position(line=85, character=4),
        "contains": "## `CHO RDA N, C, D`",
    },
    {
        # Hovering over an int, which should return no hover info
        "symbol": "None",
        "position": lsp.Position(line=8, character=8),
        "contains": None,
    },
]


PREPARE_RENAMES: list[PrepareRenameDict] = [
    {
        "symbol": "mem",
        "position": lsp.Position(line=8, character=0),
        "result": None,
        "message": "Can't rename non-user defined token MEM.",
    },
    {
        "symbol": "reg0",
        "position": lsp.Position(line=22, character=10),
        "result": None,
        "message": "Can't rename non-user defined token REG0.",
    },
    {
        "symbol": "ap1",
        "position": lsp.Position(line=8, character=4),
        "result": lsp.PrepareRenameResult_Type2(default_behavior=True),
        "message": None,
    },
    {
        "symbol": "endclr",
        "position": lsp.Position(line=37, character=10),
        "result": lsp.PrepareRenameResult_Type2(default_behavior=True),
        "message": None,
    },
]


RENAMES: list[RenameDict] = [
    {
        "symbol": "ap1",
        "rename_to": "FOO",
        "position": lsp.Position(line=8, character=4),
        "changes": [
            lsp.TextEdit(
                range=lsp.Range(start=lsp.Position(8, 4), end=lsp.Position(8, 7)),
                new_text="FOO",
            ),
            # This symbol is `ap1#``, and should be matched when renaming `ap1`
            lsp.TextEdit(
                range=lsp.Range(start=lsp.Position(51, 4), end=lsp.Position(51, 7)),
                new_text="FOO",
            ),
            lsp.TextEdit(
                range=lsp.Range(start=lsp.Position(52, 5), end=lsp.Position(52, 8)),
                new_text="FOO",
            ),
        ],
    },
    {
        "symbol": "endclr",
        "rename_to": "END",
        "position": lsp.Position(line=41, character=0),
        "changes": [
            lsp.TextEdit(
                range=lsp.Range(start=lsp.Position(37, 8), end=lsp.Position(37, 14)),
                new_text="END",
            ),
            lsp.TextEdit(
                range=lsp.Range(start=lsp.Position(41, 0), end=lsp.Position(41, 6)),
                new_text="END",
            ),
        ],
    },
    {
        "symbol": "lap1a#",
        "rename_to": "FOO",
        "position": lsp.Position(line=61, character=4),
        "changes": [
            # Renaming `lap1a#` should also rename `lap1a`
            lsp.TextEdit(
                range=lsp.Range(start=lsp.Position(12, 4), end=lsp.Position(12, 9)),
                new_text="FOO",
            ),
            lsp.TextEdit(
                range=lsp.Range(start=lsp.Position(61, 4), end=lsp.Position(61, 9)),
                new_text="FOO",
            ),
            lsp.TextEdit(
                range=lsp.Range(start=lsp.Position(62, 5), end=lsp.Position(62, 10)),
                new_text="FOO",
            ),
        ],
    },
]
