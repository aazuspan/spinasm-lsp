"""The SPINAsm Language Server Protocol implementation."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from lsprotocol import types as lsp
from pygls.server import LanguageServer

from . import __version__
from .documentation import DocMap
from .parser import SPINAsmParser


@lru_cache(maxsize=1)
def _parse_document(source: str) -> SPINAsmParser:
    """
    Parse a document and return the parser.

    Parser are cached based on the source code to speed up subsequent parsing.
    """
    return SPINAsmParser(source).parse()


class SPINAsmLanguageServer(LanguageServer):
    def __init__(self, *args, **kwargs) -> None:
        self._prev_parser: SPINAsmParser | None = None
        self.documentation = DocMap(folders=["instructions", "assemblers"])

        super().__init__(*args, name="spinasm-lsp", version=__version__, **kwargs)

    def debug(self, msg: Any) -> None:
        """Log a debug message."""
        # MessageType.Debug is a proposed feature of 3.18.0, and isn't fully supported
        # yet.
        self.show_message_log(str(msg), lsp.MessageType.Log)

    def info(self, msg: Any) -> None:
        """Log an info message."""
        self.show_message_log(str(msg), lsp.MessageType.Info)

    def warning(self, msg: Any) -> None:
        """Log a warning message."""
        self.show_message_log(str(msg), lsp.MessageType.Warning)

    def error(self, msg: Any) -> None:
        """Log an error message."""
        self.show_message_log(str(msg), lsp.MessageType.Error)

    async def get_parser(self, uri: str) -> SPINAsmParser:
        """Return a parser for the document, caching if possible."""
        document = self.workspace.get_text_document(uri)
        parser = _parse_document(document.source)

        # Skip publishing diagnostics if the parser is unchanged
        if parser is not self._prev_parser:
            self.publish_diagnostics(document.uri, parser.diagnostics)
            self._prev_parser = parser

        return parser


server = SPINAsmLanguageServer(max_workers=5)


@server.feature(lsp.TEXT_DOCUMENT_DID_CHANGE)
async def did_change(
    ls: SPINAsmLanguageServer, params: lsp.DidChangeTextDocumentParams
):
    """Run diagnostics on changed document."""
    await ls.get_parser(params.text_document.uri)


@server.feature(lsp.TEXT_DOCUMENT_DID_SAVE)
async def did_save(ls: SPINAsmLanguageServer, params: lsp.DidSaveTextDocumentParams):
    """Run diagnostics on saved document."""
    await ls.get_parser(params.text_document.uri)


@server.feature(lsp.TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls: SPINAsmLanguageServer, params: lsp.DidOpenTextDocumentParams):
    """Run diagnostics on open document."""
    await ls.get_parser(params.text_document.uri)


@server.feature(lsp.TEXT_DOCUMENT_DID_CLOSE)
def did_close(
    ls: SPINAsmLanguageServer, params: lsp.DidCloseTextDocumentParams
) -> None:
    """Clear the diagnostics on close."""
    ls.publish_diagnostics(params.text_document.uri, [])


@server.feature(lsp.TEXT_DOCUMENT_HOVER)
async def hover(ls: SPINAsmLanguageServer, params: lsp.HoverParams) -> lsp.Hover | None:
    """Retrieve documentation from symbols on hover."""
    parser = await ls.get_parser(params.text_document.uri)

    if (token := parser.token_registry.get_token_at_position(params.position)) is None:
        return None

    token_val = token.symbol["stxt"]
    token_type = token.symbol["type"]

    hover_msg = None
    if token_type in ("LABEL", "TARGET"):
        # Label definitions and targets
        if token_val in parser.jmptbl:
            hover_definition = parser.jmptbl[token_val.upper()]
            hover_msg = f"(label) {token_val}: Offset[**{hover_definition}**]"
        # Variable and memory definitions
        elif token_val in parser.symtbl:
            hover_definition = parser.symtbl[token_val.upper()]
            hover_msg = f"(constant) {token_val}: Literal[**{hover_definition}**]"
    # Opcodes and assignments
    elif token_type in ("ASSEMBLER", "MNEMONIC"):
        hover_msg = ls.documentation.get(token_val, "")

    return (
        None
        if not hover_msg
        else lsp.Hover(
            contents=lsp.MarkupContent(kind=lsp.MarkupKind.Markdown, value=hover_msg),
        )
    )


@server.feature(lsp.TEXT_DOCUMENT_COMPLETION)
async def completions(
    ls: SPINAsmLanguageServer, params: lsp.CompletionParams
) -> lsp.CompletionList:
    """Returns completion items."""
    parser = await ls.get_parser(params.text_document.uri)

    opcodes = [k.upper() for k in ls.documentation]
    symbols = list(parser.symtbl.keys())
    labels = list(parser.jmptbl.keys())
    mem = list(parser.mem.keys())

    opcode_items = [
        lsp.CompletionItem(
            label=k,
            kind=lsp.CompletionItemKind.Function,
            documentation=lsp.MarkupContent(
                kind=lsp.MarkupKind.Markdown, value=ls.documentation[k.upper()]
            ),
        )
        for k in opcodes
    ]
    # TODO: Set details for all the completions below using the same info as the hover.
    symbol_items = [
        lsp.CompletionItem(label=k, kind=lsp.CompletionItemKind.Constant)
        for k in symbols
    ]
    label_items = [
        lsp.CompletionItem(label=k, kind=lsp.CompletionItemKind.Reference)
        for k in labels
    ]
    mem_items = [
        lsp.CompletionItem(label=k, kind=lsp.CompletionItemKind.Variable) for k in mem
    ]

    return lsp.CompletionList(
        is_incomplete=False, items=opcode_items + mem_items + symbol_items + label_items
    )


@server.feature(lsp.TEXT_DOCUMENT_DEFINITION)
async def definition(
    ls: SPINAsmLanguageServer, params: lsp.DefinitionParams
) -> lsp.Location | None:
    """Returns the definition location of a symbol."""
    parser = await ls.get_parser(params.text_document.uri)

    document = ls.workspace.get_text_document(params.text_document.uri)

    if (token := parser.token_registry.get_token_at_position(params.position)) is None:
        return None

    # Definitions should be checked against the base token name, ignoring address
    # modifiers.
    base_token = token.without_address_modifier()

    if str(base_token) not in parser.definitions:
        return None

    return lsp.Location(
        uri=document.uri,
        range=parser.definitions[str(base_token)],
    )


@server.feature(lsp.TEXT_DOCUMENT_PREPARE_RENAME)
async def prepare_rename(ls: SPINAsmLanguageServer, params: lsp.PrepareRenameParams):
    """Called by the client to determine if renaming the symbol at the given location
    is a valid operation."""
    parser = await ls.get_parser(params.text_document.uri)

    if (token := parser.token_registry.get_token_at_position(params.position)) is None:
        return None

    # Renaming is checked against the base token name, ignoring address modifiers.
    base_token = token.without_address_modifier()

    # Only user-defined labels should support renaming
    if str(base_token) not in parser.definitions:
        ls.info(f"Can't rename non-user defined token {base_token}.")
        return None

    return lsp.PrepareRenameResult_Type2(default_behavior=True)


@server.feature(
    lsp.TEXT_DOCUMENT_RENAME, options=lsp.RenameOptions(prepare_provider=True)
)
async def rename(ls: SPINAsmLanguageServer, params: lsp.RenameParams):
    parser = await ls.get_parser(params.text_document.uri)

    if (token := parser.token_registry.get_token_at_position(params.position)) is None:
        return None

    # Ignore address modifiers so that e.g. we can rename `Delay` by renaming `Delay#`
    base_token = token.without_address_modifier()
    matching_tokens = parser.token_registry.get_matching_tokens(str(base_token))

    edits = [lsp.TextEdit(t.range, new_text=params.new_name) for t in matching_tokens]
    return lsp.WorkspaceEdit(changes={params.text_document.uri: edits})


def start() -> None:
    server.start_io()


if __name__ == "__main__":
    start()
