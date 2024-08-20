from __future__ import annotations

import itertools
import tempfile
from dataclasses import dataclass

import lsprotocol.types as lsp
import pytest
from pytest_lsp import LanguageClient

from ..conftest import TestCase, parametrize_cases


@dataclass
class SemanticTestCase(TestCase):
    """A dictionary to record prepare rename results for a symbol."""

    source: str
    encoding: list[int]


# fmt: off
TEST_CASES: list[SemanticTestCase] = [
    SemanticTestCase(
        name="variable definition",
        source="""Delay MEM REG0""",
        encoding=[
            0, 0, 5, 8, 0b10, # variable, definition
            0, 6, 3, 21, 0b0, # operator
            0, 4, 4, 8, 0b1000000100, # variable, constant readonly
        ],
    ),
    SemanticTestCase(
        name="label and opcode",
        source="""start:\nsof 0,0""",
        encoding=[ 
            0, 0, 5, 0, 0b10, # namespace, definition
            1, 0, 3, 12, 0b0, # function
            0, 4, 1, 19, 0b0, # number
            0, 1, 1, 21, 0b0, # argsep
            0, 1, 1, 19, 0b0, # number
        ], 
    ),
]
# fmt: on


@parametrize_cases(TEST_CASES)
@pytest.mark.asyncio()
async def test_semantic_tokens(
    test_case: SemanticTestCase, client: LanguageClient
) -> None:
    def batched(iterable, n):
        """
        Partial back port of itertools.batched from Python 3.12.

        https://docs.python.org/3/library/itertools.html#itertools.batched
        """
        iterator = iter(iterable)
        while batch := tuple(itertools.islice(iterator, n)):
            yield batch

    tmp = tempfile.NamedTemporaryFile()
    with open(tmp.name, "w") as dst:
        dst.write(test_case.source)

    response = await client.text_document_semantic_tokens_full_async(
        params=lsp.SemanticTokensParams(
            text_document=lsp.TextDocumentIdentifier(
                uri=f"file:///{tmp.name}",
            ),
        )
    )

    assert len(response.data) == len(test_case.encoding), "Unexpected encoding length"

    # Compare encodings 1 token at a time to make it easier to diagnose issues
    for got, expected in zip(batched(response.data, 5), batched(test_case.encoding, 5)):
        assert got == expected
