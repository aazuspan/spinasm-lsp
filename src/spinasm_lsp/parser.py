"""The SPINAsm language parser."""

from __future__ import annotations

import bisect
import copy
from typing import Literal, TypedDict

import lsprotocol.types as lsp
from asfv1 import fv1parse


class Symbol(TypedDict):
    """
    The token specification used by asfv1.

    Note that we exclude EOF tokens, as they are ignored by the LSP.
    """

    type: Literal[
        "ASSEMBLER",
        "INTEGER",
        "LABEL",
        "TARGET",
        "MNEMONIC",
        "OPERATOR",
        "FLOAT",
        "ARGSEP",
    ]
    txt: str
    stxt: str
    val: int | float | None


class Token:
    """
    A parsed token.

    Parameters
    ----------
    symbol : Symbol
        The symbol parsed by asfv1 representing the token.
    start : lsp.Position
        The start position of the token in the source file.
    end : lsp.Position, optional
        The end position of the token in the source file. If not provided, the end
        position is calculated based on the width of the symbol's stxt.

    Attributes
    ----------
    symbol : Symbol
        The symbol parsed by asfv1 representing the token.
    range : lsp.Range
        The location range of the token in the source file.
    """

    def __init__(
        self, symbol: Symbol, start: lsp.Position, end: lsp.Position | None = None
    ):
        if end is None:
            width = len(symbol["stxt"])
            end = lsp.Position(line=start.line, character=start.character + width)

        self.symbol: Symbol = symbol
        self.range: lsp.Range = lsp.Range(start=start, end=end)

    def __repr__(self) -> str:
        return self.symbol["stxt"]

    def concatenate(self, other: Token) -> Token:
        """
        Concatenate by merging with another token, in place.

        In practice, this is used for the multi-word opcodes that are parsed as separate
        tokens: CHO RDA, CHO RDAL, and CHO SOF.
        """
        if any(
            symbol_type not in ("MNEMONIC", "LABEL")
            for symbol_type in (self.symbol["type"], other.symbol["type"])
        ):
            raise TypeError("Only MNEMONIC and LABEL symbols can be concatenated.")

        self.symbol["txt"] += f" {other.symbol['txt']}"
        self.symbol["stxt"] += f" {other.symbol['stxt']}"
        self.range.end = other.range.end
        return self

    def _clone(self) -> Token:
        """Return a clone of the token to avoid mutating the original."""
        return copy.deepcopy(self)

    def without_address_modifier(self) -> Token:
        """
        Create a clone of the token with the address modifier removed.
        """
        if not str(self).endswith("#") and not str(self).endswith("^"):
            return self

        token = self._clone()
        token.symbol["stxt"] = token.symbol["stxt"][:-1]
        token.range.end.character -= 1

        return token


class TokenRegistry:
    """A registry of tokens and their positions in a source file."""

    def __init__(self, tokens: list[Token] | None = None) -> None:
        self._prev_token: Token | None = None

        """A dictionary mapping program lines to all Tokens on that line."""
        self._tokens_by_line: dict[int, list[Token]] = {}

        """A dictionary mapping token names to all matching Tokens in the program."""
        self._tokens_by_name: dict[str, list[Token]] = {}

        for token in tokens or []:
            self.register_token(token)

    def register_token(self, token: Token) -> None:
        """Add a token to the registry."""
        # Handle multi-word CHO instructions by merging the second token with the first
        # and skipping the second token.
        if str(self._prev_token) == "CHO" and str(token) in ("RDA", "RDAL", "SOF"):
            self._prev_token.concatenate(token)  # type: ignore
            return

        if token.range.start.line not in self._tokens_by_line:
            self._tokens_by_line[token.range.start.line] = []

        # Store the token on its line
        self._tokens_by_line[token.range.start.line].append(token)
        self._prev_token = token

        # Store user-defined tokens together by name. Other token types could be stored,
        # but currently there's no use case for retrieving their positions.
        if token.symbol["type"] in ("LABEL", "TARGET"):
            # Tokens are stored by name without address modifiers, so that e.g. Delay#
            # and Delay can be retrieved with the same query. This allows for renaming
            # all instances of a memory token.
            token = token.without_address_modifier()

            if str(token) not in self._tokens_by_name:
                self._tokens_by_name[str(token)] = []

            self._tokens_by_name[str(token)].append(token)

    def get_matching_tokens(self, token_name: str) -> list[Token]:
        """Retrieve all tokens with a given name in the program."""
        return self._tokens_by_name.get(token_name.upper(), [])

    def get_token_at_position(self, position: lsp.Position) -> Token | None:
        """Retrieve the token at the given position."""
        if position.line not in self._tokens_by_line:
            return None

        line_tokens = self._tokens_by_line[position.line]
        token_starts = [t.range.start.character for t in line_tokens]
        token_ends = [t.range.end.character for t in line_tokens]

        idx = bisect.bisect_left(token_starts, position.character)

        # The index returned by bisect_left points to the start value >= character. This
        # will either be the first character of the token or the start of the next
        # token. First check if we're out of bounds, then shift left unless we're at the
        # first character of the token.
        if idx == len(line_tokens) or token_starts[idx] != position.character:
            idx -= 1

        # If the col falls after the end of the token, we're not inside a token.
        if position.character > token_ends[idx]:
            return None

        return line_tokens[idx]


class SPINAsmParser(fv1parse):
    """A modified version of fv1parse optimized for use with LSP."""

    sym: Symbol | None

    def __init__(self, source: str):
        self.diagnostics: list[lsp.Diagnostic] = []
        """A list of diagnostic messages generated during parsing."""

        self.definitions: dict[str, lsp.Range] = {}
        """A dictionary mapping symbol names to their definition location."""

        self.current_character: int = 0
        """The current column in the source file."""

        self.previous_character: int = 0
        """The last visitied column in the source file."""

        self.token_registry = TokenRegistry()
        """A registry of tokens and their positions in the source file."""

        super().__init__(
            source=source,
            clamp=True,
            spinreals=False,
            # Ignore the callbacks in favor of overriding their callers
            wfunc=lambda *args, **kwargs: None,
            efunc=lambda *args, **kwargs: None,
        )

        # Track which symbols were defined at initialization, e.g. registers and LFOs
        self.constants: list[str] = list(self.symtbl.keys())
        # Keep an unchanged copy of the original source
        self._source: list[str] = self.source.copy()

    def __mkopcodes__(self):
        """
        No-op.

        Generating opcodes isn't needed for LSP functionality, so we'll skip it.
        """

    def _record_diagnostic(
        self, msg: str, line: int, character: int, severity: lsp.DiagnosticSeverity
    ):
        """Record a diagnostic message for the LSP."""
        self.diagnostics.append(
            lsp.Diagnostic(
                range=lsp.Range(
                    start=lsp.Position(line, character=character),
                    end=lsp.Position(line, character=character),
                ),
                message=msg,
                severity=severity,
                source="SPINAsm",
            )
        )

    def parseerror(self, msg: str, line: int | None = None):
        """Override to record parsing errors as LSP diagnostics."""
        if line is None:
            line = self.prevline

        # Offset the line from the parser's 1-indexed line to the 0-indexed line
        self._record_diagnostic(
            msg,
            line=line - 1,
            character=self.current_character,
            severity=lsp.DiagnosticSeverity.Error,
        )

    def scanerror(self, msg: str):
        """Override to record scanning errors as LSP diagnostics."""
        self._record_diagnostic(
            msg,
            line=self.current_line,
            character=self.current_character,
            severity=lsp.DiagnosticSeverity.Error,
        )

    def parsewarn(self, msg: str, line: int | None = None):
        """Override to record parsing warnings as LSP diagnostics."""
        if line is None:
            line = self.prevline

        # Offset the line from the parser's 1-indexed line to the 0-indexed line
        self._record_diagnostic(
            msg,
            line=line - 1,
            character=self.current_character,
            severity=lsp.DiagnosticSeverity.Warning,
        )

    @property
    def sline(self):
        return self._sline

    @sline.setter
    def sline(self, value):
        """Update the current line and reset the column."""
        self._sline = value

        # Reset the column to 0 when we move to a new line
        self.previous_character = self.current_character
        self.current_character = 0

    @property
    def current_line(self):
        """Get the zero-indexed current line."""
        return self.sline - 1

    @property
    def previous_line(self):
        """Get the zero-indexed previous line."""
        return self.prevline - 1

    def __next__(self):
        """Parse the next symbol and update the column and definitions."""
        super().__next__()
        if self.sym["type"] == "EOF":
            return

        self._update_column()

        token = Token(
            symbol=self.sym,
            start=lsp.Position(
                line=self.current_line, character=self.current_character
            ),
        )
        self.token_registry.register_token(token)

        base_token = token.without_address_modifier()
        is_user_definable = base_token.symbol["type"] in ("LABEL", "TARGET")
        is_defined = str(base_token) in self.jmptbl or str(base_token) in self.symtbl

        if (
            is_user_definable
            and not is_defined
            # Labels appear before their target definition, so override when the target
            # is defined.
            or base_token.symbol["type"] == "TARGET"
        ):
            self.definitions[str(base_token)] = base_token.range

    def _update_column(self):
        """Set the current column based on the last parsed symbol."""
        current_line_txt = self._source[self.current_line]
        current_symbol = self.sym.get("txt", None) or ""

        self.previous_character = self.current_character
        try:
            # Start at the current column to skip previous duplicates of the symbol
            self.current_character = current_line_txt.index(
                current_symbol, self.current_character
            )
        except ValueError:
            self.current_character = 0

    def parse(self) -> SPINAsmParser:
        """Parse and return the parser."""
        super().parse()
        return self
