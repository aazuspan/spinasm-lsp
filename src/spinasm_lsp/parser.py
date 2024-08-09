from __future__ import annotations

from asfv1 import fv1parse
from lsprotocol import types as lsp

from spinasm_lsp.utils import CallbackDict, Token, TokenRegistry


class SPINAsmParser(fv1parse):
    """A modified version of fv1parse optimized for use with LSP."""

    def __init__(self, source: str):
        self.diagnostics: list[lsp.Diagnostic] = []
        self.definitions: dict[str, lsp.Position] = {}
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

        # Wrap the dictionaries to record whenever a definition is added
        self.jmptbl: CallbackDict = CallbackDict(
            self.jmptbl, callback=self._on_definition
        )
        self.symtbl: CallbackDict = CallbackDict(
            self.symtbl, callback=self._on_definition
        )

    def _on_definition(self, label: str):
        """Record the program location when a definition is added."""
        # Don't record the position of constants that are defined at program
        # initialization.
        if self.current_line == -1:
            return

        # Due to the parsing order, the current line will be correct for labels but
        # incorrect for assignments, which need to use previous line instead.
        line = self.current_line if label in self.jmptbl else self.previous_line

        # Try to find the position of the label on the definition line. Remove address
        # modifiers from the label name, since those are defined implicitly by the
        # parser rather than in the source.
        try:
            col = (
                self._source[line]
                .upper()
                .index(label.replace("#", "").replace("^", ""))
            )
        except ValueError:
            col = 0

        self.definitions[label] = lsp.Position(line, col)

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
        """Parse the next symbol and update the column."""
        super().__next__()
        # TODO: Make sure super().__next__ can't get stuck in an infinite loop since I
        # removed the maxerr check
        self._update_column()

        token_width = len(self.sym["txt"] or "")
        token = Token(self.sym, self.current_line, self.col, self.col + token_width)
        self.token_registry.register_token(token)

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
