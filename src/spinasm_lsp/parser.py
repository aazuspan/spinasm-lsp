"""The SPINAsm language parser."""

from __future__ import annotations

import bisect
import copy
from typing import Generator, Generic, Literal, TypedDict, TypeVar, overload

import lsprotocol.types as lsp
from asfv1 import fv1parse

T = TypeVar("T", bound="ParsedToken")

# Token types assigned by asfv1. Note that we exclude EOF tokens, as they are ignored by
# the LSP.
TokenType = Literal[
    "ASSEMBLER",
    "INTEGER",
    "LABEL",
    "TARGET",
    "MNEMONIC",
    "OPERATOR",
    "FLOAT",
    "ARGSEP",
]


class ASFV1Token(TypedDict):
    """Raw token metadata parsed by asfv1."""

    type: TokenType
    txt: str
    stxt: str
    val: int | float | None


class ParsedToken:
    """
    Token metadata including its position.

    Parameters
    ----------
    type : TokenType
        The type of token identified by asfv1.
    stxt : str
        The name assigned to the token, always uppercase.
    range : lsp.Range
        The position of the token in the source code.
    """

    def __init__(self, type: TokenType, stxt: str, range: lsp.Range):
        self.type = type
        self.stxt = stxt
        self.range = range

    def __repr__(self) -> str:
        return f"{self.stxt} [{self.type}] at {self.range}"

    def _clone(self: T) -> T:
        """Return a clone of the token to avoid mutating the original."""
        return copy.deepcopy(self)

    def without_address_modifier(self: T) -> T:
        """
        Create a clone of the token with the address modifier removed.
        """
        if not self.stxt.endswith("#") and not self.stxt.endswith("^"):
            return self

        clone = self._clone()
        clone.stxt = clone.stxt[:-1]
        clone.range.end.character -= 1

        return clone

    def concatenate(self: T, other: T) -> T:
        """
        Concatenate by merging with another token, in place.

        In practice, this is used for the multi-word opcodes that are parsed as separate
        tokens: CHO RDA, CHO RDAL, and CHO SOF.
        """
        self.stxt += f" {other.stxt}"
        self.range.end = other.range.end
        return self

    @classmethod
    def from_asfv1_token(
        cls, token: ASFV1Token, start: lsp.Position, end: lsp.Position | None = None
    ) -> ParsedToken:
        if end is None:
            width = len(token["stxt"])
            end = lsp.Position(line=start.line, character=start.character + width)

        return cls(
            type=token["type"],
            stxt=token["stxt"],
            range=lsp.Range(start=start, end=end),
        )


class EvaluatedToken(ParsedToken):
    """
    A parsed token with additional evaluated metadata like its value and semantic type.
    """

    def __init__(
        self,
        type: TokenType,
        stxt: str,
        range: lsp.Range,
        value: float | int | None = None,
        defined: lsp.Range | None = None,
        semantic_modifiers: list[lsp.SemanticTokenModifiers] | None = None,
        semantic_type: lsp.SemanticTokenTypes | None = None,
    ):
        super().__init__(type=type, stxt=stxt, range=range)

        self.defined = defined
        """The range where the token is defined, if applicable."""

        self.value = value
        """The numeric value of the evaluated token, if applicable."""

        self.semantic_modifiers = semantic_modifiers or []
        """The semantic modifiers relevant to the token."""

        self.semantic_type = semantic_type
        """The semantic type of the token."""

    @classmethod
    def from_parsed_token(
        cls,
        token: ParsedToken,
        value: float | int | None = None,
        defined: lsp.Range | None = None,
        semantic_modifiers: list[lsp.SemanticTokenModifiers] | None = None,
        semantic_type: lsp.SemanticTokenTypes | None = None,
    ) -> EvaluatedToken:
        return EvaluatedToken(
            type=token.type,
            stxt=token.stxt,
            range=token.range,
            value=value,
            defined=defined,
            semantic_modifiers=semantic_modifiers,
            semantic_type=semantic_type,
        )


class TokenLookup(Generic[T]):
    """A lookup table for tokens by position and name."""

    def __init__(self):
        self._prev_token: T | None = None
        self._line_lookup: dict[int, list[T]] = {}
        self._name_lookup: dict[str, list[T]] = {}

    def __iter__(self) -> Generator[T, None, None]:
        """Yield all tokens."""
        for line in self._line_lookup.values():
            yield from line

    @overload
    def get(self, *, position: lsp.Position) -> T | None: ...
    @overload
    def get(self, *, name: str) -> list[T]: ...
    @overload
    def get(self, *, line: int) -> list[T]: ...

    def get(
        self,
        *,
        position: lsp.Position | None = None,
        name: str | None = None,
        line: int | None = None,
    ) -> T | list[T] | None:
        ...
        """Retrieve a token by position, name, or line."""
        # Raise if more than one argument is provided
        if sum(arg is not None for arg in (position, name, line)) > 1:
            raise ValueError("Only one of position, name, or line may be provided")

        if position is not None:
            return self._token_at_position(position)
        if line is not None:
            return self._line_lookup.get(line, [])
        if name is not None:
            return self._name_lookup.get(name.upper(), [])
        raise ValueError("Either a position, name, or line must be provided.")

    def add_token(self, token: T) -> None:
        """Store a token for future lookup."""
        # Handle multi-word CHO instructions by merging the second token with the first
        # and skipping the second token.
        if (
            self._prev_token
            and self._prev_token.stxt == "CHO"
            and token.stxt in ("RDA", "RDAL", "SOF")
        ):
            self._prev_token.concatenate(token)  # type: ignore
            return

        # Store the token on its line
        self._line_lookup.setdefault(token.range.start.line, []).append(token)
        self._prev_token = token

        # Store user-defined tokens together by name. Other token types could be stored,
        # but currently there's no use case for retrieving their positions.
        if token.type in ("LABEL", "TARGET"):
            # Tokens are stored by name without address modifiers, so that e.g. Delay#
            # and Delay can be retrieved with the same query. This allows for renaming
            # all instances of a memory token.
            base_token = token.without_address_modifier()
            self._name_lookup.setdefault(base_token.stxt, []).append(base_token)

    def _token_at_position(self, position: lsp.Position) -> T | None:
        """Retrieve the token at the given position."""
        if position.line not in self._line_lookup:
            return None

        line_tokens = self._line_lookup[position.line]
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

    sym: ASFV1Token | None

    def __init__(self, source: str):
        self.diagnostics: list[lsp.Diagnostic] = []
        """A list of diagnostic messages generated during parsing."""
        # Mapping of token names to where they're defined
        self._definitions: dict[str, lsp.Range] = {}
        # Intermediate lookup for tokens that are parsed but not evaluated yet
        self._parsed_tokens: TokenLookup[ParsedToken] = TokenLookup()

        self.current_character: int = 0
        """The current column in the source file."""

        self.previous_character: int = 0
        """The last visitied column in the source file."""

        self.evaluated_tokens: TokenLookup[EvaluatedToken] = TokenLookup()
        """Tokens with additional metadata after evaluation."""

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

        token = ParsedToken.from_asfv1_token(
            self.sym,
            start=lsp.Position(self.current_line, character=self.current_character),
        )
        self._parsed_tokens.add_token(token)

        base_token = token.without_address_modifier()
        is_user_definable = base_token.type in ("LABEL", "TARGET")
        is_defined = base_token.stxt in self.jmptbl or base_token.stxt in self.symtbl

        if (
            is_user_definable
            and not is_defined
            # Labels appear before their target definition, so override when the target
            # is defined.
            or base_token.type == "TARGET"
        ):
            self._definitions[base_token.stxt] = base_token.range

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

    def _evaluate_token(self, token: ParsedToken) -> EvaluatedToken:
        """Evaluate a parsed token to determine its value and semantics."""
        print(f"Evaluating {token.stxt}")
        value = None
        semantic_type = None
        defined_range = None
        semantic_modifiers = []

        # Set semantic type and modifiers
        if token.type == "MNEMONIC":
            semantic_type = lsp.SemanticTokenTypes.Function
        elif token.type in ("INTEGER", "FLOAT"):
            semantic_type = lsp.SemanticTokenTypes.Number
        elif token.type in ("OPERATOR", "ASSEMBLER", "ARGSEP"):
            semantic_type = lsp.SemanticTokenTypes.Operator
        elif token.type == "LABEL":
            semantic_type = lsp.SemanticTokenTypes.Variable
            if token.stxt in self.constants:
                semantic_modifiers = [
                    lsp.SemanticTokenModifiers.Readonly,
                    lsp.SemanticTokenModifiers.DefaultLibrary,
                ]

        if token.stxt in self.jmptbl:
            semantic_type = lsp.SemanticTokenTypes.Namespace
            value = self.jmptbl[token.stxt]
        elif token.stxt in self.symtbl:
            value = self.symtbl[token.stxt]

        # Definitions are based on the base token without address modifiers
        base_token = token.without_address_modifier()
        if base_token.stxt in self._definitions:
            defined_range = self._definitions[base_token.stxt]
            if defined_range == base_token.range:
                semantic_modifiers = lsp.SemanticTokenModifiers.Definition

        return EvaluatedToken.from_parsed_token(
            token=token,
            value=value,
            defined=defined_range,
            semantic_type=semantic_type,
            semantic_modifiers=semantic_modifiers,
        )

    def parse(self) -> SPINAsmParser:
        """Parse and evaluate all tokens."""
        super().parse()

        for token in self._parsed_tokens:
            evaluated_token = self._evaluate_token(token)
            self.evaluated_tokens.add_token(evaluated_token)

        return self
