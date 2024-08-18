"""Data structures for storing and retrieving parsed tokens."""

from __future__ import annotations

import bisect
import copy
from typing import Generator, Generic, Literal, TypedDict, TypeVar, cast, overload

import lsprotocol.types as lsp

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

# Map semantic type enums to integer encodings
SEMANTIC_TYPE_LEGEND = {k: i for i, k in enumerate(lsp.SemanticTokenTypes)}
SEMANTIC_MODIFIER_LEGEND = {k: i for i, k in enumerate(lsp.SemanticTokenModifiers)}


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

    def semantic_encoding(self, prev_token_start: lsp.Position) -> list[int]:
        """
        Encode the token's semantic information for the LSP.

        The output is a list of 5 ints representing:
        - The delta line from the previous token
        - The delta character from the previous token
        - The length of the token
        - The semantic type index
        - The encoded semantic modifiers

        See https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_semanticTokens
        """
        # Set the token's position relative to the previous token. If we're on a new
        # line, set the character relative to zero.
        delta_line = self.range.start.line - prev_token_start.line
        delta_start_char = (
            self.range.start.character
            if delta_line
            else self.range.start.character - prev_token_start.character
        )

        token_type = SEMANTIC_TYPE_LEGEND.get(self.semantic_type)
        token_modifiers = [
            SEMANTIC_MODIFIER_LEGEND.get(mod) for mod in self.semantic_modifiers
        ]
        # Return an empty semantic encoding if type or modifiers are unrecognized
        if token_type is None or None in token_modifiers:
            return []

        # The index of each modifier is encoded into a bitmask
        modifier_bitmask = sum(1 << i for i in cast(list[int], token_modifiers))

        return [
            delta_line,
            delta_start_char,
            len(self.stxt),
            token_type,
            modifier_bitmask,
        ]


class TokenLookup(Generic[T]):
    """A lookup table for tokens by position and name."""

    def __init__(self):
        self._prev_token: T | None = None
        self._line_lookup: dict[int, list[T]] = {}
        self._name_lookup: dict[str, list[T]] = {}

    def __iter__(self) -> Generator[T, None, None]:
        """Yield all tokens in order."""
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
