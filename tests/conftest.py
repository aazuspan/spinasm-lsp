from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import lsprotocol.types as lsp
import pytest
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


@dataclass
class TestCase:
    """The inputs and outputs of a test case."""

    __test__ = False

    name: str
    """The name used to identify the test case."""


def parametrize_cases(test_cases: list[TestCase]):
    """A decorator to parametrize a test function with test cases."""
    return pytest.mark.parametrize("test_case", test_cases, ids=lambda x: x.name)
