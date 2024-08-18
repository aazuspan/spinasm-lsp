"""The SPINAsm language parser."""

from __future__ import annotations

import lsprotocol.types as lsp
from asfv1 import fv1parse

from spinasm_lsp.tokens import ASFV1Token, LSPToken, ParsedToken, TokenLookup


class SPINAsmPositionParser(fv1parse):
    """An SPINAsm parser that tracks zero-indexed parsing position."""

    def __init__(self, *args, **kwargs):
        # Current position during parsing
        self._current_character: int = 0
        self._previous_character: int = 0

        super().__init__(*args, **kwargs)

        # Store an unmodified version of the source for future reference
        self._source: list[str] = self.source.copy()

    @property
    def sline(self) -> int:
        return self._sline

    @sline.setter
    def sline(self, value):
        """Update the current line and reset the column."""
        self._sline = value

        # Reset the column to 0 when we move to a new line
        self._previous_character = self._current_character
        self._current_character = 0

    @property
    def _current_line(self) -> int:
        """Get the zero-indexed current line."""
        return self.sline - 1

    @property
    def position(self) -> lsp.Position:
        """The current position of the parser in the source code."""
        return lsp.Position(line=self._current_line, character=self._current_character)

    @property
    def parsed_symbol(self) -> ASFV1Token:
        """Get the last parsed symbol."""
        return ASFV1Token(**self.sym)

    def __next__(self) -> None:
        """Parse the next token and update the current character and line."""
        super().__next__()
        current_line_txt = self._source[self._current_line]
        current_symbol = self.parsed_symbol.txt

        self._previous_character = self._current_character
        # Start at the current column to skip previous duplicates of the symbol
        self._current_character = current_line_txt.index(
            current_symbol, self._current_character
        )


class SPINAsmDiagnosticParser(SPINAsmPositionParser):
    """An SPINAsm parser that logs warnings and errors as LSP diagnostics."""

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            # Ignore the callbacks in favor of overriding their callers
            wfunc=lambda *args, **kwargs: None,
            efunc=lambda *args, **kwargs: None,
            **kwargs,
        )

        self.diagnostics: list[lsp.Diagnostic] = []
        """A list of diagnostic messages generated during parsing."""

    def _record_diagnostic(
        self, msg: str, *, position: lsp.Position, severity: lsp.DiagnosticSeverity
    ):
        """Record a diagnostic message for the LSP."""
        self.diagnostics.append(
            lsp.Diagnostic(
                range=lsp.Range(start=position, end=position),
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
            position=lsp.Position(line=line - 1, character=self._current_character),
            severity=lsp.DiagnosticSeverity.Error,
        )

    def scanerror(self, msg: str):
        """Override to record scanning errors as LSP diagnostics."""
        self._record_diagnostic(
            msg,
            position=lsp.Position(
                line=self._current_line, character=self._current_character
            ),
            severity=lsp.DiagnosticSeverity.Error,
        )

    def parsewarn(self, msg: str, line: int | None = None):
        """Override to record parsing warnings as LSP diagnostics."""
        if line is None:
            line = self.prevline

        # Offset the line from the parser's 1-indexed line to the 0-indexed line
        self._record_diagnostic(
            msg,
            position=lsp.Position(line=line - 1, character=self._current_character),
            severity=lsp.DiagnosticSeverity.Warning,
        )


class SPINAsmParser(SPINAsmDiagnosticParser):
    """An SPINAsm parser with position, diagnostics, and additional LSP features."""

    def __init__(self, source: str):
        # Intermediate token definitions and lookups set during parsing
        self._definitions: dict[str, lsp.Range] = {}
        self._parsed_tokens: TokenLookup[ParsedToken] = TokenLookup()

        super().__init__(
            source=source,
            clamp=True,
            spinreals=False,
        )

        # Store built-in constants that were defined at initialization.
        self._constants: list[str] = list(self.symtbl.keys())

        self.evaluated_tokens: TokenLookup[LSPToken] = TokenLookup()
        """Tokens with additional metadata after evaluation."""

    def __mkopcodes__(self):
        """
        No-op.

        Generating opcodes isn't needed for LSP functionality, so we'll skip it.
        """

    def __next__(self):
        """Parse the next symbol and update the column and definitions."""
        super().__next__()
        if self.parsed_symbol.type == "EOF":
            return

        token = self.parsed_symbol.at_position(
            start=lsp.Position(self._current_line, character=self._current_character),
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

    def _evaluate_token(self, token: ParsedToken) -> LSPToken:
        """Evaluate a parsed token to determine its value and metadata."""
        value = self.jmptbl.get(token.stxt, self.symtbl.get(token.stxt, None))
        defined_range = self._definitions.get(token.without_address_modifier().stxt)

        return LSPToken.from_parsed_token(
            token=token,
            value=value,
            defined=defined_range,
            is_constant=token.stxt in self._constants,
            is_label=token.stxt in self.jmptbl,
        )

    def parse(self) -> SPINAsmParser:
        """Parse and evaluate all tokens."""
        super().parse()

        for token in self._parsed_tokens:
            evaluated_token = self._evaluate_token(token)
            self.evaluated_tokens.add_token(evaluated_token)

        return self
