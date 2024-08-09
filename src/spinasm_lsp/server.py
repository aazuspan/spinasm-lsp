from __future__ import annotations

from typing import Any

from lsprotocol import types as lsp
from pygls.server import LanguageServer
from pygls.workspace import TextDocument

from . import __version__
from .documentation import DocMap
from .parser import SPINAsmParser


class SPINAsmLanguageServer(LanguageServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, name="spinasm-lsp", version=__version__, **kwargs)
        self.parser: SPINAsmParser = None

    def debug(self, msg: Any) -> None:
        """Log a debug message."""
        self.show_message_log(str(msg), lsp.MessageType.Debug)

    def info(self, msg: Any) -> None:
        """Log an info message."""
        self.show_message_log(str(msg), lsp.MessageType.Info)

    def warning(self, msg: Any) -> None:
        """Log a warning message."""
        self.show_message_log(str(msg), lsp.MessageType.Warning)

    def error(self, msg: Any) -> None:
        """Log an error message."""
        self.show_message_log(str(msg), lsp.MessageType.Error)

    async def parse(self, document: TextDocument) -> SPINAsmParser:
        """Parse a document and publish diagnostics."""
        try:
            self.parser = SPINAsmParser(document.source).parse()
            diagnostics = self.parser.diagnostics
        except Exception as e:
            self.error(e)
            diagnostics = []

        self.publish_diagnostics(document.uri, diagnostics)
        return self.parser


LSP_SERVER = SPINAsmLanguageServer(max_workers=5)
# TODO: Probably load async as part of a custom language server subclass
DOCUMENTATION = DocMap(folders=["instructions", "assemblers"])


@LSP_SERVER.feature(lsp.TEXT_DOCUMENT_DID_CHANGE)
async def did_change(
    ls: SPINAsmLanguageServer, params: lsp.DidChangeTextDocumentParams
):
    """Run diagnostics on changed document."""
    document = ls.workspace.get_text_document(params.text_document.uri)
    await ls.parse(document)


@LSP_SERVER.feature(lsp.TEXT_DOCUMENT_DID_SAVE)
async def did_save(ls: SPINAsmLanguageServer, params: lsp.DidSaveTextDocumentParams):
    """Run diagnostics on saved document."""
    document = ls.workspace.get_text_document(params.text_document.uri)
    await ls.parse(document)


@LSP_SERVER.feature(lsp.TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls: SPINAsmLanguageServer, params: lsp.DidOpenTextDocumentParams):
    """Run diagnostics on open document."""
    document = ls.workspace.get_text_document(params.text_document.uri)
    await ls.parse(document)


@LSP_SERVER.feature(lsp.TEXT_DOCUMENT_DID_CLOSE)
def did_close(
    ls: SPINAsmLanguageServer, params: lsp.DidCloseTextDocumentParams
) -> None:
    """Clear the diagnostics on close."""
    text_document = ls.workspace.get_text_document(params.text_document.uri)
    # Clear the diagnostics on close
    ls.publish_diagnostics(text_document.uri, [])


@LSP_SERVER.feature(lsp.TEXT_DOCUMENT_HOVER)
def hover(ls: SPINAsmLanguageServer, params: lsp.HoverParams) -> lsp.Hover | None:
    """Retrieve documentation from symbols on hover."""
    pos = params.position

    token = ls.parser.token_registry.get_token_at_position(pos.line, pos.character)
    if token is None:
        return None

    token_val = token.value["stxt"]
    token_type = token.value["type"]

    # stxt should only be None for EOF tokens, but check to be sure.
    if token_type == "EOF" or not isinstance(token_val, str):
        return None

    hover_msg = None
    if token_type in ("LABEL", "TARGET"):
        # Label definitions and targets
        if token_val in LSP_SERVER.parser.jmptbl:
            hover_definition = LSP_SERVER.parser.jmptbl[token_val.upper()]
            hover_msg = f"(label) {token_val}: Offset[**{hover_definition}**]"
        # Variable and memory definitions
        elif token_val in LSP_SERVER.parser.symtbl:
            hover_definition = LSP_SERVER.parser.symtbl[token_val.upper()]
            hover_msg = f"(constant) {token_val}: Literal[**{hover_definition}**]"
        # Special case for hovering over the second word of a CHO instruction, which
        # should be treated as part of the instruction for retrieving documentation.
        if token_val in ("SOF", "RDAL", "RDA") and str(token.prev_token) == "CHO":
            token_val = f"CHO {token_val}"
            hover_msg = DOCUMENTATION.get(token_val, "")
    # Opcodes and assignments
    elif token_type in ("ASSEMBLER", "MNEMONIC"):
        # CHO is a special opcode that treats its first argument as part of the
        # instruction, for the sake of documentation.
        if token_val == "CHO" and token.next_token is not None:
            token_val = f"CHO {str(token.next_token)}"

        hover_msg = DOCUMENTATION.get(token_val, "")

    return (
        None
        if not hover_msg
        else lsp.Hover(
            contents=lsp.MarkupContent(kind=lsp.MarkupKind.Markdown, value=hover_msg),
        )
    )


@LSP_SERVER.feature(lsp.TEXT_DOCUMENT_COMPLETION)
def completions(
    ls: SPINAsmLanguageServer, params: lsp.CompletionParams | None = None
) -> lsp.CompletionList:
    """Returns completion items."""
    opcodes = [k.upper() for k in DOCUMENTATION]
    symbols = list(ls.parser.symtbl.keys())
    labels = list(ls.parser.jmptbl.keys())
    mem = list(ls.parser.mem.keys())

    opcode_items = [
        lsp.CompletionItem(label=k, kind=lsp.CompletionItemKind.Function)
        for k in opcodes
    ]
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


@LSP_SERVER.feature(lsp.TEXT_DOCUMENT_DEFINITION)
def definition(
    ls: SPINAsmLanguageServer, params: lsp.DefinitionParams
) -> lsp.Location | None:
    """Returns the definition location of a symbol."""
    document = ls.workspace.get_text_document(params.text_document.uri)
    pos = params.position

    # TODO: Probably switch to token registry
    try:
        word = document.word_at_position(pos).upper()
    except IndexError:
        return None

    if word in ls.parser.definitions:
        return lsp.Location(
            uri=document.uri,
            range=lsp.Range(
                start=ls.parser.definitions[word],
                end=ls.parser.definitions[word],
            ),
        )

    return None


@LSP_SERVER.feature(lsp.TEXT_DOCUMENT_PREPARE_RENAME)
def prepare_rename(ls: SPINAsmLanguageServer, params: lsp.PrepareRenameParams):
    """Called by the client to determine if renaming the symbol at the given location
    is a valid operation."""
    pos = params.position

    token = ls.parser.token_registry.get_token_at_position(pos.line, pos.character)
    if token is None:
        ls.debug(f"No token to rename at {pos}.")
        return None

    # Only user-defined labels should support renaming
    if str(token) not in ls.parser.definitions:
        ls.debug(f"Can't rename non-user defined token {token}.")
        return None

    return lsp.PrepareRenameResult_Type2(default_behavior=True)


@LSP_SERVER.feature(
    lsp.TEXT_DOCUMENT_RENAME, options=lsp.RenameOptions(prepare_provider=True)
)
def rename(ls: SPINAsmLanguageServer, params: lsp.RenameParams):
    pos = params.position

    token = ls.parser.token_registry.get_token_at_position(pos.line, pos.character)
    if token is None:
        return None

    matching_tokens = ls.parser.token_registry.get_matching_tokens(str(token))

    edits = [
        lsp.TextEdit(
            range=lsp.Range(
                start=lsp.Position(t.line, t.col_start),
                end=lsp.Position(t.line, t.col_end),
            ),
            new_text=params.new_name,
        )
        for t in matching_tokens
    ]

    return lsp.WorkspaceEdit(changes={params.text_document.uri: edits})


def start() -> None:
    LSP_SERVER.start_io()


if __name__ == "__main__":
    start()
