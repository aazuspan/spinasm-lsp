from __future__ import annotations

from pathlib import Path
from typing import TypedDict

import lsprotocol.types as lsp
import pytest_lsp
from pytest_lsp import ClientServerConfig, LanguageClient

PATCH_DIR = Path(__file__).parent / "patches"
TEST_PATCHES = list(PATCH_DIR.glob("*.spn"))
assert TEST_PATCHES, "No test patches found in the patches directory."


@pytest_lsp.fixture(
    params=["neovim", "visual_studio_code"],
    config=ClientServerConfig(server_command=["spinasm-lsp"]),
)
async def client(request, lsp_client: LanguageClient):
    """A client fixture for LSP tests."""
    params = lsp.InitializeParams(
        capabilities=pytest_lsp.client_capabilities(request.param)
    )

    await lsp_client.initialize_session(params)
    yield

    await lsp_client.shutdown_session()


class TestCase(TypedDict):
    """The inputs and outputs of a test case."""

    __test__ = False

    name: str
    """The name used to identify the test case."""
