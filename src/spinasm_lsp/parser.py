from __future__ import annotations

from asfv1 import fv1parse
from lsprotocol import types as lsp

from spinasm_lsp.utils import Symbol, Token, TokenRegistry


class SPINAsmParser(fv1parse):
    """A modified version of fv1parse optimized for use with LSP."""

    sym: Symbol | None

    def __init__(self, source: str):
        self.diagnostics: list[lsp.Diagnostic] = []
        self.definitions: dict[str, lsp.Range] = {}
        self.col: int = 0
        self.prevcol: int = 0
        self.token_registry = TokenRegistry()

        super().__init__(
            source=source,
            clamp=True,
            spinreals=False,
            # Ignore the callbacks in favor of overriding their callers
            wfunc=lambda *args, **kwargs: None,
            efunc=lambda *args, **kwargs: None,
        )

        # Keep an unchanged copy of the original source
        self._source: list[str] = self.source.copy()

    def __mkopcodes__(self):
        """
        No-op.

        Generating opcodes isn't needed for LSP functionality, so we'll skip it.
        """

    def _record_diagnostic(
        self, msg: str, line: int, col: int, severity: lsp.DiagnosticSeverity
    ):
        """Record a diagnostic message for the LSP."""
        self.diagnostics.append(
            lsp.Diagnostic(
                range=lsp.Range(
                    start=lsp.Position(line, character=col),
                    end=lsp.Position(line, character=col),
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
            msg, line - 1, col=self.col, severity=lsp.DiagnosticSeverity.Error
        )

    def scanerror(self, msg: str):
        """Override to record scanning errors as LSP diagnostics."""
        self._record_diagnostic(
            msg, self.current_line, col=self.col, severity=lsp.DiagnosticSeverity.Error
        )

    def parsewarn(self, msg: str, line: int | None = None):
        """Override to record parsing warnings as LSP diagnostics."""
        if line is None:
            line = self.prevline

        # Offset the line from the parser's 1-indexed line to the 0-indexed line
        self._record_diagnostic(
            msg, line - 1, col=self.col, severity=lsp.DiagnosticSeverity.Warning
        )

    @property
    def sline(self):
        return self._sline

    @sline.setter
    def sline(self, value):
        """Update the current line and reset the column."""
        self._sline = value

        # Reset the column to 0 when we move to a new line
        self.prevcol = self.col
        self.col = 0

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
        self._update_column()

        token_width = max(len(self.sym["txt"] or "") - 1, 0)
        token_range = lsp.Range(
            start=lsp.Position(line=self.current_line, character=self.col),
            end=lsp.Position(line=self.current_line, character=self.col + token_width),
        )
        token = Token(self.sym, range=token_range)
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

        self.prevcol = self.col
        try:
            # Start at the current column to skip previous duplicates of the symbol
            self.col = current_line_txt.index(current_symbol, self.col)
        except ValueError:
            self.col = 0

    def parse(self) -> SPINAsmParser:
        """Parse and return the parser."""
        super().parse()
        return self
