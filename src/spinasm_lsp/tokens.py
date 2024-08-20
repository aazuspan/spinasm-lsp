"""Data structures for storing and retrieving parsed tokens."""

from __future__ import annotations

import bisect
import copy
from dataclasses import dataclass
from typing import Generator, Generic, Literal, TypeVar, overload

import lsprotocol.types as lsp

_ParsedTokenT = TypeVar("_ParsedTokenT", bound="ParsedToken")
_EvaluatedTokenT = TypeVar("_EvaluatedTokenT", bound="EvaluatedToken")

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


@dataclass
class ASFV1Token:
    """Raw token metadata parsed by asfv1."""

    type: TokenType
    txt: str
    stxt: str
    val: int | float | None

    def at_position(
        self, start: lsp.Position, end: lsp.Position | None = None
    ) -> ParsedToken:
        """Create a parsed token with this token's metadata at a position."""
        if end is None:
            width = len(self.stxt)
            end = lsp.Position(line=start.line, character=start.character + width)

        return ParsedToken(
            type=self.type,
            stxt=self.stxt,
            range=lsp.Range(start=start, end=end),
        )


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

    def _clone(self: _ParsedTokenT) -> _ParsedTokenT:
        """Return a clone of the token to avoid mutating the original."""
        return copy.deepcopy(self)

    def without_address_modifier(self: _ParsedTokenT) -> _ParsedTokenT:
        """
        Create a clone of the token with the address modifier removed.
        """
        if not self.stxt.endswith("#") and not self.stxt.endswith("^"):
            return self

        clone = self._clone()
        clone.stxt = clone.stxt[:-1]
        clone.range.end.character -= 1

        return clone

    def concatenate(self: _ParsedTokenT, other: _ParsedTokenT) -> _ParsedTokenT:
        """
        Concatenate by merging with another token, in place.

        In practice, this is used for the multi-word opcodes that are parsed as separate
        tokens: CHO RDA, CHO RDAL, and CHO SOF.
        """
        self.stxt += f" {other.stxt}"
        self.range.end = other.range.end
        return self


class EvaluatedToken(ParsedToken):
    """
    A parsed token that has been evaluated to determine its value and other metadata.
    """

    def __init__(
        self,
        type: TokenType,
        stxt: str,
        range: lsp.Range,
        value: float | int | None = None,
        defined: lsp.Range | None = None,
        is_constant: bool = False,
        is_label: bool = False,
    ):
        super().__init__(type=type, stxt=stxt, range=range)

        self.value = value
        """The numeric value of the evaluated token, if applicable."""

        self.defined = defined
        """The range where the token is defined, if applicable."""

        self.is_constant = is_constant
        self.is_label = is_label
        self.is_opcode = self.type == "MNEMONIC"

    @classmethod
    def from_parsed_token(
        cls: type[_EvaluatedTokenT],
        token: ParsedToken,
        *,
        value: float | int | None = None,
        defined: lsp.Range | None = None,
        is_constant: bool = False,
        is_label: bool = False,
    ) -> _EvaluatedTokenT:
        """Create an evaluated token from a parsed token."""
        return cls(
            type=token.type,
            stxt=token.stxt,
            range=token.range,
            value=value,
            defined=defined,
            is_constant=is_constant,
            is_label=is_label,
        )


class SemanticTokenMixin(EvaluatedToken):
    """A mixin for evaluated tokens with semantic information."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.semantic_type, self.semantic_modifiers = self._infer_semantics()

    def _infer_semantics(
        self,
    ) -> tuple[lsp.SemanticTokenTypes, list[lsp.SemanticTokenModifiers]]:
        """Infer the semantic type and modifiers for the token."""
        # Crosswalk asfv1 token types to LSP semantic token types
        type_semantics = {
            "MNEMONIC": lsp.SemanticTokenTypes.Function,
            "INTEGER": lsp.SemanticTokenTypes.Number,
            "FLOAT": lsp.SemanticTokenTypes.Number,
            "ASSEMBLER": lsp.SemanticTokenTypes.Operator,
            "ARGSEP": lsp.SemanticTokenTypes.Operator,
            "LABEL": lsp.SemanticTokenTypes.Variable,
            "TARGET": lsp.SemanticTokenTypes.Namespace,
        }

        semantic_type = type_semantics.get(self.type)
        if self.is_label:
            semantic_type = lsp.SemanticTokenTypes.Namespace

        semantic_modifiers = []
        if self.is_constant and self.type != "MNEMONIC":
            semantic_modifiers += [
                lsp.SemanticTokenModifiers.Readonly,
                lsp.SemanticTokenModifiers.DefaultLibrary,
            ]

        if self.stxt.endswith("#") or self.stxt.endswith("^"):
            semantic_modifiers.append(lsp.SemanticTokenModifiers.Modification)

        if self.defined == self.range:
            semantic_modifiers.append(lsp.SemanticTokenModifiers.Definition)

        return semantic_type, semantic_modifiers

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
        modifier_bitmask = sum(1 << i for i in token_modifiers)  # type: ignore

        return [
            delta_line,
            delta_start_char,
            len(self.stxt),
            token_type,
            modifier_bitmask,
        ]


class LSPTokenMixin(EvaluatedToken):
    """A mixin for evaluated tokens with LSP information."""

    @property
    def completion_detail(self) -> str:
        """A description of the token used in completions and hover."""
        type_str = (
            "opcode"
            if self.is_opcode
            else "label"
            if self.is_label
            else "constant"
            if self.is_constant
            else "variable"
        )
        value_type = "Offset" if self.is_label else "Literal"

        return (
            f"({type_str})" + f" {self.stxt}: {value_type}[{self.value}]"
            if not self.is_opcode
            else ""
        )

    @property
    def completion_kind(self) -> lsp.CompletionItemKind:
        return (
            lsp.CompletionItemKind.Function
            if self.is_opcode
            else lsp.CompletionItemKind.Constant
            if self.is_constant
            else lsp.CompletionItemKind.Module
            if self.is_label
            else lsp.CompletionItemKind.Variable
        )

    @property
    def completion_item(self) -> lsp.CompletionItem:
        """Create a completion item for the token."""

        return lsp.CompletionItem(
            label=self.stxt,
            kind=self.completion_kind,
            detail=self.completion_detail,
            documentation=None,
        )

    @property
    def symbol_kind(self) -> lsp.SymbolKind:
        return (
            lsp.SymbolKind.Function
            if self.is_opcode
            else lsp.SymbolKind.Constant
            if self.is_constant
            else lsp.SymbolKind.Module
            if self.is_label
            else lsp.SymbolKind.Variable
        )

    @property
    def document_symbol(self) -> lsp.DocumentSymbol:
        """Create a document symbol for the token."""
        return lsp.DocumentSymbol(
            name=self.stxt,
            kind=self.symbol_kind,
            range=self.defined,
            selection_range=self.defined,
        )


class LSPToken(LSPTokenMixin, SemanticTokenMixin):
    """An evaluated token with semantic and LSP information."""


class TokenLookup(Generic[_ParsedTokenT]):
    """A lookup table for tokens by position and name."""

    def __init__(self):
        self._prev_token: _ParsedTokenT | None = None
        self._line_lookup: dict[int, list[_ParsedTokenT]] = {}
        self._name_lookup: dict[str, list[_ParsedTokenT]] = {}

    def __iter__(self) -> Generator[_ParsedTokenT, None, None]:
        """Yield all tokens in order."""
        for line in self._line_lookup.values():
            yield from line

    @overload
    def get(self, *, position: lsp.Position) -> _ParsedTokenT | None: ...
    @overload
    def get(self, *, name: str) -> list[_ParsedTokenT]: ...
    @overload
    def get(self, *, line: int) -> list[_ParsedTokenT]: ...

    def get(
        self,
        *,
        position: lsp.Position | None = None,
        name: str | None = None,
        line: int | None = None,
    ) -> _ParsedTokenT | list[_ParsedTokenT] | None:
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

    def add_token(self, token: _ParsedTokenT) -> None:
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

    def _token_at_position(self, position: lsp.Position) -> _ParsedTokenT | None:
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
