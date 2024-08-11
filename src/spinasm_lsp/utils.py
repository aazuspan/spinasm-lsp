from __future__ import annotations

import bisect
import copy
from dataclasses import dataclass
from typing import Literal, TypedDict, cast

import lsprotocol.types as lsp

# Types of tokens defined by asfv1
TokenType = Literal[
    "ASSEMBLER",
    "EOF",
    "INTEGER",
    "LABEL",
    "TARGET",
    "MNEMONIC",
    "OPERATOR",
    "FLOAT",
    "ARGSEP",
]


class Symbol(TypedDict):
    """The token specification used by asfv1."""

    type: TokenType
    txt: str | None
    stxt: str | None
    val: int | float | None


@dataclass
class Token:
    """A token and its position in a source file."""

    symbol: Symbol
    range: lsp.Range
    next_token: Token | None = None
    prev_token: Token | None = None

    def __str__(self):
        return self.symbol["stxt"] or "Empty token"

    def __repr__(self):
        return str(self)

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
        token.symbol["stxt"] = cast(str, token.symbol["stxt"])[:-1]
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
        # TODO: Maybe handle multi-word CHO instructions here, by merging with the next
        # token? The tricky part is that the next token would still end up getting
        # registered unless we prevent it... If we end up with overlapping tokens, that
        # will break `get_token_at_position`. I could check if prev token was CHO when
        # I register RDAL, SOF, or RDA, and if so register them as one and unregister
        # the previous?
        if token.range.start.line not in self._tokens_by_line:
            self._tokens_by_line[token.range.start.line] = []

        # Record the previous and next token for each token to allow traversing
        if self._prev_token:
            token.prev_token = self._prev_token
            self._prev_token.next_token = token

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
