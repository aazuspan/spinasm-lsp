from typing import Any

from lsprotocol import types as lsp
from pygls import server


class ServerLogger:
    def __init__(self, server: server.LanguageServer):
        self.server = server

    def debug(self, msg: Any) -> None:
        self.server.show_message_log(str(msg), lsp.MessageType.Debug)

    def info(self, msg: Any) -> None:
        self.server.show_message_log(str(msg), lsp.MessageType.Info)

    def warning(self, msg: Any) -> None:
        self.server.show_message_log(str(msg), lsp.MessageType.Warning)

    def error(self, msg: Any) -> None:
        self.server.show_message_log(str(msg), lsp.MessageType.Error)
