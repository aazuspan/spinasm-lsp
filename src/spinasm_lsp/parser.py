"""The SPINAsm language parser."""

from __future__ import annotations

import lsprotocol.types as lsp
from asfv1 import fv1parse

from spinasm_lsp.tokens import ASFV1Token, EvaluatedToken, ParsedToken, TokenLookup


class SPINAsmParser(fv1parse):
    """A modified version of fv1parse optimized for use with LSP."""

    sym: ASFV1Token | None

    def __init__(self, source: str):
        self.diagnostics: list[lsp.Diagnostic] = []
        """A list of diagnostic messages generated during parsing."""
        # Intermediate token definitions and lookups set during parsing
        self._definitions: dict[str, lsp.Range] = {}
        self._parsed_tokens: TokenLookup[ParsedToken] = TokenLookup()

        # Current position during parsing
        self._current_character: int = 0
        self._previous_character: int = 0

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
            character=self._current_character,
            severity=lsp.DiagnosticSeverity.Error,
        )

    def scanerror(self, msg: str):
        """Override to record scanning errors as LSP diagnostics."""
        self._record_diagnostic(
            msg,
            line=self._current_line,
            character=self._current_character,
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
            character=self._current_character,
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
        self._previous_character = self._current_character
        self._current_character = 0

    @property
    def _current_line(self):
        """Get the zero-indexed current line."""
        return self.sline - 1

    def __next__(self):
        """Parse the next symbol and update the column and definitions."""
        super().__next__()
        if self.sym["type"] == "EOF":
            return

        self._update_column()

        token = ParsedToken.from_asfv1_token(
            self.sym,
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

    def _update_column(self):
        """Set the current column based on the last parsed symbol."""
        current_line_txt = self._source[self._current_line]
        current_symbol = self.sym.get("txt", None) or ""

        self._previous_character = self._current_character
        try:
            # Start at the current column to skip previous duplicates of the symbol
            self._current_character = current_line_txt.index(
                current_symbol, self._current_character
            )
        except ValueError:
            self._current_character = 0

    def _evaluate_token(self, token: ParsedToken) -> EvaluatedToken:
        """Evaluate a parsed token to determine its value and semantics."""
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
                semantic_modifiers = [lsp.SemanticTokenModifiers.Definition]

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
