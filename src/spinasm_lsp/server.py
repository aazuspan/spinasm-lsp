from lsprotocol import types as lsp
from pygls.server import LanguageServer

from . import __version__
from .documentation import DocMap
from .logging import ServerLogger

LSP_SERVER = LanguageServer(
    name="spinasm-lsp",
    version=__version__,
    max_workers=5,
)

LOGGER = ServerLogger(LSP_SERVER)

# TODO: Probably load async as part of a custom language server subclass
INSTRUCTIONS = DocMap(folder="instructions")


@LSP_SERVER.feature(lsp.TEXT_DOCUMENT_HOVER)
def hover(ls: LanguageServer, params: lsp.HoverParams) -> lsp.Hover:
    """Retrieve documentation from symbols on hover."""
    document = ls.workspace.get_text_document(params.text_document.uri)
    pos = params.position

    # TODO: Handle multi-word instructions like CHO RDA, CHO SOF, CHO RDAL
    try:
        word = document.word_at_position(pos)
    except IndexError:
        return None

    word_docs = INSTRUCTIONS.get(word, None)
    if word_docs:
        return lsp.Hover(
            contents=lsp.MarkupContent(kind=lsp.MarkupKind.Markdown, value=word_docs),
        )

    return None


def start() -> None:
    LSP_SERVER.start_io()


if __name__ == "__main__":
    instructions = DocMap(folder="instructions")
    start()
