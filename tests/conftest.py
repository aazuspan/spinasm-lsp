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
    uri: str


class SymbolDefinitionDict(TypedDict):
    """A dictionary to record definition locations for a symbol."""

    symbol: str
    range: lsp.Range
    kind: lsp.SymbolKind
    uri: str


class HoverDict(TypedDict):
    """A dictionary to record hover information for a symbol."""

    symbol: str
    position: lsp.Position
    contains: str | None
    uri: str


class PrepareRenameDict(TypedDict):
    """A dictionary to record prepare rename results for a symbol."""

    symbol: str
    position: lsp.Position
    result: bool
    message: str | None
    uri: str


class ReferenceDict(TypedDict):
    """A dictionary to record reference locations for a symbol."""

    symbol: str
    position: lsp.Position
    references: list[lsp.Location]
    uri: str


class RenameDict(TypedDict):
    """A dictionary to record rename results for a symbol."""

    symbol: str
    rename_to: str
    position: lsp.Position
    changes: list[lsp.TextEdit]
    uri: str


class SignatureHelpDict(TypedDict):
    """A dictionary to record signature help information for at a position."""

    symbol: str
    position: lsp.Position
    active_parameter: int | None
    param_contains: str | None
    doc_contains: str | None
    uri: str


REFERENCES: list[ReferenceDict] = [
    {
        # Variable
        "symbol": "apout",
        "position": lsp.Position(line=23, character=4),
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
        "references": [
            lsp.Location(
                uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
                range=lsp.Range(
                    start=lsp.Position(line=23, character=4),
                    end=lsp.Position(line=23, character=9),
                ),
            ),
            lsp.Location(
                uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
                range=lsp.Range(
                    start=lsp.Position(line=57, character=5),
                    end=lsp.Position(line=57, character=10),
                ),
            ),
            lsp.Location(
                uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
                range=lsp.Range(
                    start=lsp.Position(line=60, character=5),
                    end=lsp.Position(line=60, character=10),
                ),
            ),
            lsp.Location(
                uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
                range=lsp.Range(
                    start=lsp.Position(line=70, character=5),
                    end=lsp.Position(line=70, character=10),
                ),
            ),
        ],
    },
    {
        "symbol": "ap1",
        "position": lsp.Position(line=8, character=4),
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
        "references": [
            lsp.Location(
                uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
                range=lsp.Range(
                    start=lsp.Position(line=8, character=4),
                    end=lsp.Position(line=8, character=7),
                ),
            ),
            lsp.Location(
                uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
                range=lsp.Range(
                    start=lsp.Position(line=51, character=4),
                    end=lsp.Position(line=51, character=7),
                ),
            ),
            lsp.Location(
                uri=f"file:///{PATCH_DIR / 'Basic.spn'}",
                range=lsp.Range(
                    start=lsp.Position(line=52, character=5),
                    end=lsp.Position(line=52, character=8),
                ),
            ),
        ],
    },
]


SYMBOL_DEFINITIONS: list[SymbolDefinitionDict] = [
    {
        # Variable
        "symbol": "apout",
        "kind": lsp.SymbolKind.Variable,
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
        "range": lsp.Range(
            start=lsp.Position(line=23, character=4),
            end=lsp.Position(line=23, character=9),
        ),
    },
    {
        # Memory
        "symbol": "lap2a",
        "kind": lsp.SymbolKind.Variable,
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
        "range": lsp.Range(
            start=lsp.Position(line=16, character=4),
            end=lsp.Position(line=16, character=9),
        ),
    },
    {
        # Label
        "symbol": "endclr",
        "kind": lsp.SymbolKind.Module,
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
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
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
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
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
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
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
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
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
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
        "contains": "`MEM`",
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
    },
    {
        "symbol": "skp",
        "position": lsp.Position(line=37, character=2),
        "contains": "`SKP CMASK, N`",
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
    },
    {
        "symbol": "endclr",
        "position": lsp.Position(line=37, character=13),
        "contains": "(label) ENDCLR: Offset[4]",
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
    },
    {
        "symbol": "mono",
        "position": lsp.Position(line=47, character=5),
        "contains": "(variable) MONO: Literal[32]",
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
    },
    {
        "symbol": "reg0",
        "position": lsp.Position(line=22, character=9),
        "contains": "(constant) REG0: Literal[32]",
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
    },
    {
        "symbol": "lap2b#",
        "position": lsp.Position(line=73, character=4),
        "contains": "(variable) LAP2B#: Literal[9802]",
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
    },
    {
        # CHO RDA, hovering over CHO
        "symbol": "CHO_rda",
        "position": lsp.Position(line=85, character=0),
        "contains": "`CHO RDA, N, C, D`",
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
    },
    {
        # CHO RDA, hovering over RDA
        "symbol": "cho_RDA",
        "position": lsp.Position(line=85, character=4),
        "contains": "`CHO RDA, N, C, D`",
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
    },
    {
        # Hovering over an int, which should return no hover info
        "symbol": "None",
        "position": lsp.Position(line=8, character=8),
        "contains": None,
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
    },
]


PREPARE_RENAMES: list[PrepareRenameDict] = [
    {
        "symbol": "mem",
        "position": lsp.Position(line=8, character=0),
        "result": None,
        "message": "Can't rename non-user defined token MEM.",
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
    },
    {
        "symbol": "reg0",
        "position": lsp.Position(line=22, character=10),
        "result": None,
        "message": "Can't rename non-user defined token REG0.",
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
    },
    {
        "symbol": "ap1",
        "position": lsp.Position(line=8, character=4),
        "result": lsp.PrepareRenameResult_Type2(default_behavior=True),
        "message": None,
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
    },
    {
        "symbol": "endclr",
        "position": lsp.Position(line=37, character=10),
        "result": lsp.PrepareRenameResult_Type2(default_behavior=True),
        "message": None,
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
    },
]


RENAMES: list[RenameDict] = [
    {
        "symbol": "ap1",
        "rename_to": "FOO",
        "position": lsp.Position(line=8, character=4),
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
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
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
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
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
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

SIGNATURE_HELPS: list[SignatureHelpDict] = [
    {
        # No opcode on this line, so the signature help should be None
        "symbol": "no_opcode",
        "position": lsp.Position(line=8, character=3),
        "active_parameter": None,
        "doc_contains": None,
        "param_contains": None,
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
    },
    {
        "symbol": "skp_first_arg",
        "position": lsp.Position(line=37, character=3),
        "active_parameter": 0,
        "doc_contains": "**`SKP CMASK, N`** allows conditional program execution",
        "param_contains": "CMASK: Binary | Hex ($00-$1F) | Symbolic",
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
    },
    {
        "symbol": "skp_second_arg",
        "position": lsp.Position(line=37, character=8),
        "active_parameter": 1,
        "doc_contains": "**`SKP CMASK, N`** allows conditional program execution",
        "param_contains": "N: Decimal (1-63) | Label",
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
    },
    {
        # You should still get the last argument even if you're well beyond it
        "symbol": "skp_out_of_bounds",
        "position": lsp.Position(line=37, character=45),
        "active_parameter": 1,
        "doc_contains": "**`SKP CMASK, N`** allows conditional program execution",
        "param_contains": "N: Decimal (1-63) | Label",
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
    },
    {
        # The "first" argument of CHO RDA should be N, not RDA
        "symbol": "cho_rda",
        "position": lsp.Position(line=85, character=8),
        "active_parameter": 0,
        "doc_contains": "**`CHO RDA, N, C, D`**, like the `RDA` instruction",
        "param_contains": "N: LFO select: SIN0,SIN1,RMP0,RMP1",
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
    },
    {
        # Triggering signature help before finishing the opcode should return None
        "symbol": "cho_rda",
        "position": lsp.Position(line=85, character=0),
        "active_parameter": None,
        "doc_contains": None,
        "param_contains": None,
        "uri": f"file:///{PATCH_DIR / 'Basic.spn'}",
    },
]
