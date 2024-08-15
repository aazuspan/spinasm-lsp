"""The SPINAsm Language Server Protocol implementation."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from lsprotocol import types as lsp
from pygls.server import LanguageServer

from spinasm_lsp import __version__
from spinasm_lsp.docs import MULTI_WORD_INSTRUCTIONS, DocumentationManager
from spinasm_lsp.parser import SPINAsmParser


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
        self.documentation = DocumentationManager()

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


def _get_defined_hover(stxt: str, parser: SPINAsmParser) -> str:
    """Get a hover message with the value of a defined variable or label."""
    # Check jmptbl first since labels are also defined in symtbl
    if stxt in parser.jmptbl:
        hover_definition = parser.jmptbl[stxt]
        return f"(label) {stxt}: Offset[{hover_definition}]"
    # Check constants next since they are also defined in symtbl
    if stxt in parser.constants:
        hover_definition = parser.symtbl[stxt]
        return f"(constant) {stxt}: Literal[{hover_definition}]"
    if stxt in parser.symtbl:
        hover_definition = parser.symtbl[stxt]
        return f"(variable) {stxt}: Literal[{hover_definition}]"

    return ""


@server.feature(lsp.TEXT_DOCUMENT_HOVER)
async def hover(ls: SPINAsmLanguageServer, params: lsp.HoverParams) -> lsp.Hover | None:
    """Retrieve documentation from symbols on hover."""
    parser = await ls.get_parser(params.text_document.uri)

    if (token := parser.token_registry.get_token_at_position(params.position)) is None:
        return None

    if token.symbol["type"] in ("LABEL", "TARGET"):
        hover_msg = _get_defined_hover(str(token), parser=parser)

        return (
            None
            if not hover_msg
            else lsp.Hover(
                # Java markdown formatting happens to give the best color-coding for
                # hover messages
                contents={"language": "java", "value": f"{hover_msg}"},
                range=token.range,
            )
        )

    if token.symbol["type"] in ("ASSEMBLER", "MNEMONIC"):
        hover_msg = ls.documentation.get_markdown(str(token))

        return (
            None
            if not hover_msg
            else lsp.Hover(
                contents=lsp.MarkupContent(
                    kind=lsp.MarkupKind.Markdown, value=hover_msg
                ),
                range=token.range,
            )
        )

    return None


@server.feature(lsp.TEXT_DOCUMENT_COMPLETION)
async def completions(
    ls: SPINAsmLanguageServer, params: lsp.CompletionParams
) -> lsp.CompletionList:
    """Returns completion items."""
    parser = await ls.get_parser(params.text_document.uri)

    symbol_completions = [
        lsp.CompletionItem(
            label=symbol,
            kind=lsp.CompletionItemKind.Constant
            if symbol in parser.constants
            else lsp.CompletionItemKind.Variable
            if symbol in parser.symtbl
            else lsp.CompletionItemKind.Module,
            detail=_get_defined_hover(symbol, parser=parser),
        )
        for symbol in {**parser.symtbl, **parser.jmptbl}
    ]

    opcode_completions = [
        lsp.CompletionItem(
            label=opcode,
            kind=lsp.CompletionItemKind.Function,
            detail="(opcode)",
            documentation=lsp.MarkupContent(
                kind=lsp.MarkupKind.Markdown,
                value=ls.documentation.get_markdown(opcode),
            ),
        )
        for opcode in [k.upper() for k in ls.documentation.instructions]
    ]

    assembler_completions = [
        lsp.CompletionItem(
            label=assembler,
            kind=lsp.CompletionItemKind.Operator,
            detail="(assembler)",
            documentation=lsp.MarkupContent(
                kind=lsp.MarkupKind.Markdown,
                value=ls.documentation.get_markdown(assembler),
            ),
        )
        for assembler in [k.upper() for k in ls.documentation.assemblers]
    ]

    return lsp.CompletionList(
        is_incomplete=False,
        items=symbol_completions + opcode_completions + assembler_completions,
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


@server.feature(lsp.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
async def document_symbol_definitions(
    ls: SPINAsmLanguageServer, params: lsp.DocumentSymbolParams
) -> list[lsp.DocumentSymbol]:
    """Returns the definitions of all symbols in the document."""
    parser = await ls.get_parser(params.text_document.uri)

    return [
        lsp.DocumentSymbol(
            name=symbol,
            kind=lsp.SymbolKind.Module
            if symbol in parser.jmptbl
            # There's no need to check for constants here since they aren't included
            # in the parser definitions.
            else lsp.SymbolKind.Variable,
            range=definition,
            selection_range=definition,
        )
        for symbol, definition in parser.definitions.items()
    ]


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
async def rename(
    ls: SPINAsmLanguageServer, params: lsp.RenameParams
) -> lsp.WorkspaceEdit:
    parser = await ls.get_parser(params.text_document.uri)

    if (token := parser.token_registry.get_token_at_position(params.position)) is None:
        return None

    # Ignore address modifiers so that e.g. we can rename `Delay` by renaming `Delay#`
    base_token = token.without_address_modifier()
    matching_tokens = parser.token_registry.get_matching_tokens(str(base_token))

    edits = [lsp.TextEdit(t.range, new_text=params.new_name) for t in matching_tokens]
    return lsp.WorkspaceEdit(changes={params.text_document.uri: edits})


@server.feature(lsp.TEXT_DOCUMENT_REFERENCES)
async def references(
    ls: SPINAsmLanguageServer, params: lsp.ReferenceParams
) -> list[lsp.Location]:
    parser = await ls.get_parser(params.text_document.uri)

    if (token := parser.token_registry.get_token_at_position(params.position)) is None:
        return []

    # Ignore address modifiers so that e.g. we can find all variations of addresses,
    # e.g. `Delay` and `Delay#`
    base_token = token.without_address_modifier()
    matching_tokens = parser.token_registry.get_matching_tokens(str(base_token))

    return [
        lsp.Location(uri=params.text_document.uri, range=t.range)
        for t in matching_tokens
    ]


@server.feature(
    lsp.TEXT_DOCUMENT_SIGNATURE_HELP,
    options=lsp.SignatureHelpOptions(
        trigger_characters=[" "], retrigger_characters=[","]
    ),
)
async def signature_help(
    ls: SPINAsmLanguageServer, params: lsp.SignatureHelpParams
) -> lsp.SignatureHelp | None:
    parser = await ls.get_parser(params.text_document.uri)

    try:
        line_tokens = parser.token_registry._tokens_by_line[params.position.line]
    # Exit on empty line
    except KeyError:
        return None

    # Find all opcodes on the line that could have triggered the signature help. Ignore
    # opcodes that appear after the cursor, to avoid showing signature help prematurely.
    opcodes = [
        t
        for t in line_tokens
        if t.symbol["type"] == "MNEMONIC"
        and t.range.start.character < params.position.character
    ]
    if not opcodes:
        return None

    # We should never have more than one opcode on a line, but just in case, grab the
    # last one entered before the cursor.
    triggered_opcode = opcodes[-1]
    opcode = ls.documentation.get_instruction(str(triggered_opcode))
    if opcode is None:
        return None

    remaining_tokens = line_tokens[line_tokens.index(triggered_opcode) + 1 :]

    argseps = [t for t in remaining_tokens if t.symbol["type"] == "ARGSEP"]
    # The first argument separator to the right of the cursor is the active arg index.
    # If there are no separators right of the cursor, we either haven't entered an arg
    # yet or we're on the last arg.
    arg_idx = 0 if not argseps else len(opcode.args) - 1
    for i, argsep in enumerate(argseps):
        if argsep.range.end.character > params.position.character:
            arg_idx = i
            break

    # Special case for multi-word instructions that treat the first argument as part of
    # the instruction name. In that case, we need to shift to the previous argument to
    # account for the extra arg separator.
    if str(triggered_opcode) in MULTI_WORD_INSTRUCTIONS and arg_idx != -1:
        arg_idx -= 1

    signature = [lsp.ParameterInformation(label=arg.markdown) for arg in opcode.args]

    return lsp.SignatureHelp(
        signatures=[
            lsp.SignatureInformation(
                label=f"{opcode.name} {opcode.args.markdown}",
                parameters=signature,
                documentation=lsp.MarkupContent(
                    kind=lsp.MarkupKind.Markdown,
                    value=opcode.markdown,
                ),
            )
        ],
        active_signature=0,
        active_parameter=arg_idx,
    )


def start() -> None:
    server.start_io()


if __name__ == "__main__":
    start()
