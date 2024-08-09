from __future__ import annotations

import bisect
from collections import UserDict
from dataclasses import dataclass
from typing import Callable, Literal, TypedDict

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


class CallbackDict(UserDict):
    """A dictionary that fires a callback when an item is set."""

    def __init__(self, dict=None, /, callback: Callable | None = None, **kwargs):
        self.callback = callback or (lambda key: None)
        super().__init__(dict, **kwargs)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.callback(key)


class TokenValue(TypedDict):
    """The token specification used by asfv1."""

    type: TokenType
    txt: str | None
    stxt: str | None
    val: int | float | None


# TODO: Probably use lsp.Position and lsp.Range to define the token location
@dataclass
class Token:
    """A token and its position in a source file."""

    value: TokenValue
    line: int
    col_start: int
    col_end: int
    next_token: Token | None = None
    prev_token: Token | None = None

    def __str__(self):
        return self.value["stxt"] or "Empty token"

    def __repr__(self):
        return str(self)


class TokenRegistry:
    """A registry of tokens and their positions in a source file."""

    def __init__(self, tokens: list[Token] | None = None) -> None:
        self._prev_token: Token | None = None

        """A dictionary mapping program lines to all Tokens on that line."""
        self.lines: dict[int, list[Token]] = {}

        """A dictionary mapping token names to all matching Tokens in the program."""
        self.directory: dict[str, list[Token]] = {}

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
        if token.line not in self.lines:
            self.lines[token.line] = []

        # Record the previous and next token for each token to allow traversing
        if self._prev_token:
            token.prev_token = self._prev_token
            self._prev_token.next_token = token

        # Store the token on its line
        self.lines[token.line].append(token)
        self._prev_token = token

        # Store user-defined tokens in the registry. Other token types could be stored,
        # but currently there's no use case for retrieving their positions.
        if token.value["type"] in ("LABEL", "TARGET"):
            if str(token) not in self.directory:
                self.directory[str(token)] = []
            self.directory[str(token)].append(token)

    def get_matching_tokens(self, token_name: str) -> list[Token]:
        """Retrieve all tokens with a given name in the program."""
        return self.directory.get(token_name.upper(), [])

    def get_token_at_position(self, line: int, col: int) -> Token | None:
        """Retrieve the token at the given line and column index."""
        if line not in self.lines:
            return None

        line_tokens = self.lines[line]
        token_starts = [t.col_start for t in line_tokens]
        token_ends = [t.col_end for t in line_tokens]

        pos = bisect.bisect_left(token_starts, col)

        # The index returned by bisect_left points to the start value >= col. This will
        # either be the first character of the token or the start of the next token.
        # First check if we're out of bounds, then shift left unless we're at the first
        # character of the token.
        if pos == len(line_tokens) or token_starts[pos] != col:
            pos -= 1

        # If the col falls after the end of the token, we're not inside a token.
        if col > token_ends[pos]:
            return None

        return line_tokens[pos]
