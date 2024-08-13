"""Test the formatting of the documentation files."""

from __future__ import annotations

import json

import mistletoe
import mistletoe.ast_renderer
import pytest

from spinasm_lsp.docs import ASSEMBLERS, INSTRUCTIONS

VALID_ENTRY_FORMATS = (
    "Decimal (0 - 63)",
    "Decimal (1 - 63)",
    "Decimal (0 - 511)",
    "Decimal (0 - 32767)",
    "Decimal (512, 1024, 2048, 4096)",
    "Decimal (-16384 - 32768)",
    "Real (S.10)",
    "Real (S.15)",
    "Real (S4.6)",
    "Real (S1.9)",
    "Real (S1.14)",
    "Hex ($0 - $3F)",
    "Hex ($00 - $1F)",
    "Hex ($000 - $1FF)",
    "Hex ($0 - $7FFF)",
    "Hex ($400 - $000 - $3FF)",
    "Hex ($4000 - $000 - $7FFF)",
    "Hex ($000000 - $FFFFFF)",
    "Hex ($0000 - $FFFF)",
    "Hex ($0000 - $7FFF)",
    "Hex ($8000 - $0000 - $7FFF)",
    "Binary",
    "Bit flags",
    "Symbolic",
    "Label",
    "RAMP LFO select: (0, 1)",
    "SIN LFO select: (0, 1)",
    "LFO select: SIN0,SIN1,RMP0,RMP1",
    "LFO select: SIN0,COS0,SIN1,COS1,RMP0,RMP1",
)


def find_content(d: dict):
    """Eagerly grab the first content from the dictionary or its children."""
    if "content" in d:
        return d["content"]

    if "children" in d:
        return find_content(d["children"][0])

    raise ValueError("No content found.")


def validate_copyright(footnote: dict) -> None:
    """Validate a Markdown footnote contains a correctly formatted copyright."""
    copyright = (
        "Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference "
        "manual. Copyright 2008 by Spin Semiconductor."
    )
    assert footnote["type"] == "Emphasis", "Copyright is missing or incorrect."
    assert find_content(footnote) == copyright, "Copyright does not match."


def validate_title(title: dict, expected_name: str | None = None) -> None:
    """
    Validate a Markdown title is correctly formatted and optionally matches an expected
    name.
    """
    if expected_name is not None:
        assert find_content(title) == expected_name, "Title should match name"

    assert title["level"] == 2, "Title heading should be level 2"
    assert title["children"][0]["type"] == "InlineCode"
    assert title["children"][0]["children"][0]["type"] == "RawText"


def validate_example(example: dict) -> None:
    """Validate a Markdown example contains an assembly code block."""
    assert example["type"] == "CodeFence"
    assert example["language"] == "assembly", "Language should be 'assembly'"
    assert len(example["children"]) == 1


def test_instructions_are_unique():
    """Test that no unique fields are duplicated between instructions."""
    operations = {}
    codings = {}
    examples = {}
    titles = {}

    for name, content in INSTRUCTIONS.items():
        content = content.markdown
        ast = json.loads(
            mistletoe.markdown(content, renderer=mistletoe.ast_renderer.ASTRenderer)
        )

        children = ast["children"]
        headings = [child for child in children if child["type"] == "Heading"]
        title, operation, _, coding, example = headings

        operation_content = children[children.index(operation) + 1]
        coding_content = children[children.index(coding) + 1]
        example_content = children[children.index(example) + 1]

        titles[name] = title["children"][0]["children"][0]["content"]
        operations[name] = operation_content["children"][0]["children"][0]["content"]
        codings[name] = coding_content["children"][0]["children"][0]["content"]
        examples[name] = example_content["children"][0]["content"]

    def value_duplicated(value, d: dict) -> bool:
        """
        Check if a value shows up in a dictionary more than once. If so, return all the
        keys that contain that value.
        """
        matches = {k: v for k, v in d.items() if v == value}
        return list(matches.keys()) if len(matches) > 1 else None

    for title in titles.values():
        duplicate_keys = value_duplicated(title, titles)
        assert not duplicate_keys, f"Title duplicated between {duplicate_keys}"

    for operation in operations.values():
        duplicate_keys = value_duplicated(operation, operations)
        if operation == "See description":
            continue
        assert not duplicate_keys, f"Operation duplicated between {duplicate_keys}"

    for coding in codings.values():
        duplicate_keys = value_duplicated(coding, codings)
        assert not duplicate_keys, f"Coding duplicated between {duplicate_keys}"

    for example in examples.values():
        duplicate_keys = value_duplicated(example, examples)
        assert not duplicate_keys, f"Example duplicated between {duplicate_keys}"


@pytest.mark.parametrize("assembler", ASSEMBLERS.items(), ids=lambda x: x[0])
def test_assembler_formatting(assembler):
    """Test that all assembler markdown files follow the correct format."""
    assembler_name, content = assembler
    content = content.markdown

    ast = json.loads(
        mistletoe.markdown(content, renderer=mistletoe.ast_renderer.ASTRenderer)
    )
    children = ast["children"]
    headings = [child for child in children if child["type"] == "Heading"]
    title = headings[0]

    # Check title heading
    validate_title(title, expected_name=assembler_name.upper())
    assert children[1]["type"] == "ThematicBreak", "Missing break after title"

    # Check all headings are the correct level
    for heading in headings[1:]:
        name = find_content(heading)
        assert heading["level"] == 3, f"Subheading {name} should be level 3"

    # Check the Example heading exists and contains a code block
    example = [h for h in headings if find_content(h) == "Example"]
    assert len(example) == 1
    example_content = children[children.index(example[0]) + 1]
    validate_example(example_content)

    # Check copyright footnote
    footnote = children[-1]["children"][0]
    validate_copyright(footnote)


@pytest.mark.parametrize("instruction", INSTRUCTIONS.items(), ids=lambda x: x[0])
def test_instruction_formatting(instruction):
    """Test that all instruction markdown files follow the correct format."""
    instruction_name, content = instruction
    content = content.markdown

    ast = json.loads(
        mistletoe.markdown(content, renderer=mistletoe.ast_renderer.ASTRenderer)
    )
    children = ast["children"]
    headings = [child for child in children if child["type"] == "Heading"]
    title = headings[0]

    # Check title heading. The heading title won't match the instruction name because
    # it also includes args.
    validate_title(title, expected_name=None)
    assert children[1]["type"] == "ThematicBreak", "Missing break after title"

    # Parse the parameters
    title_split = find_content(title).replace(",", " ").split(" ")

    # The CHO instructions like CHO RDAL and CHO SOF use the first two words as the name
    title_end_idx = 1 if title_split[0] != "CHO" else 2
    title_name = " ".join(title_split[:title_end_idx])
    assert (
        title_name.lower() == instruction_name.lower()
    ), "Title does not match filename"
    # Everything after the instruction title is a param name
    title_param_names = [p for p in title_split[title_end_idx:] if p]

    # Check subheadings
    expected_headings = ("Operation", "Parameters", "Instruction Coding", "Example")
    for i, heading in enumerate(headings[1:]):
        name = find_content(heading)
        expected = expected_headings[i]
        assert name == expected, f"Heading `{name}` should be `{expected}`."
        assert heading["level"] == 3, f"Subheading {name} should be level 3"

    _, operation, parameters, coding, example = headings

    # Check the operation
    operation_content = children[children.index(operation) + 1]
    assert (
        operation_content["children"][0]["type"] == "InlineCode"
    ), "Operation should be formatted as inline code"

    # Check the parameter table
    parameters_content = children[children.index(parameters) + 1]

    if len(title_param_names) > 0:
        assert parameters_content["type"] == "Table"
        # Check the columns
        columns = parameters_content["header"]["children"]
        column_names = [find_content(c) for c in columns]
        assert column_names == [
            "Name",
            "Width",
            "Entry formats, range",
        ], "Incorrect parameter table columns"
        # Check the rows
        rows = parameters_content["children"]
        assert len(rows) > 0, "Parameter table must contain at least 1 row"
        table_param_names = [find_content(r) for r in rows]
        assert (
            table_param_names == title_param_names
        ), "Parameters in table do not match title."
        # Validate entry formats
        entry_formats = []
        for r in rows:
            entry_formats += find_content(r["children"][2]).split("<br>")
        for format in entry_formats:
            assert format in VALID_ENTRY_FORMATS, f"Invalid entry format {format}"
    # If the instruction has no parameters, it should just list None instead of a table.
    else:
        assert parameters_content["type"] == "Paragraph"
        assert find_content(parameters_content) == "None."

    # Check instruction coding content
    coding_content = children[children.index(coding) + 1]
    assert (
        coding_content["type"] == "Paragraph"
    ), "Missing or invalid instruction coding"
    assert (
        coding_content["children"][0]["type"] == "Strong"
    ), "Use strong format for instruction coding."

    # Check example code block
    example_content = children[children.index(example) + 1]
    validate_example(example_content)

    # Check copyright footnote
    footnote = children[-1]["children"][0]
    validate_copyright(footnote)
