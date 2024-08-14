"""Test the formatting of the documentation files."""

from __future__ import annotations

import json

import mistletoe
import pytest
from mistletoe.ast_renderer import ASTRenderer

from spinasm_lsp.docs import ASSEMBLERS, INSTRUCTIONS, MULTI_WORD_INSTRUCTIONS


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


def validate_example(example: dict) -> None:
    """Validate a Markdown example contains an assembly code block."""
    assert example["type"] == "CodeFence"
    assert example["language"] == "assembly", "Language should be 'assembly'"
    assert len(example["children"]) == 1


def test_instructions_are_unique():
    """Test that no unique fields are duplicated between instructions."""
    operations = {}
    examples = {}

    for name, content in INSTRUCTIONS.items():
        ast = json.loads(mistletoe.markdown(content.markdown, renderer=ASTRenderer))

        children = ast["children"]
        headings = [child for child in children if child["type"] == "Heading"]
        operation, _, example = headings

        operation_content = children[children.index(operation) + 1]
        example_content = children[children.index(example) + 1]

        operations[name] = operation_content["children"][0]["children"][0]["content"]
        examples[name] = example_content["children"][0]["content"]

    def value_duplicated(value, d: dict) -> bool:
        """
        Check if a value shows up in a dictionary more than once. If so, return all the
        keys that contain that value.
        """
        matches = {k: v for k, v in d.items() if v == value}
        return list(matches.keys()) if len(matches) > 1 else None

    for operation in operations.values():
        duplicate_keys = value_duplicated(operation, operations)
        if operation == "See description":
            continue
        assert not duplicate_keys, f"Operation duplicated between {duplicate_keys}"

    for example in examples.values():
        duplicate_keys = value_duplicated(example, examples)
        assert not duplicate_keys, f"Example duplicated between {duplicate_keys}"


@pytest.mark.parametrize("assembler", ASSEMBLERS.items(), ids=lambda x: x[0])
def test_assembler_formatting(assembler):
    """Test that all assembler markdown files follow the correct format."""
    _, doc = assembler

    ast = json.loads(mistletoe.markdown(doc.markdown, renderer=ASTRenderer))
    children = ast["children"]
    headings = [child for child in children if child["type"] == "Heading"]

    # Check that the description starts with the assembler name, formatted as bold
    # inline code.
    description = children[0]
    assert description["type"] == "Paragraph"
    assert find_content(description) == doc.name
    assert description["children"][0]["type"] == "Strong"
    assert description["children"][0]["children"][0]["type"] == "InlineCode"

    # Check all headings are the correct level
    for heading in headings:
        name = find_content(heading)
        assert heading["level"] == 4, f"Subheading {name} should be level 4"

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
    _, doc = instruction
    ast = json.loads(mistletoe.markdown(doc.markdown, renderer=ASTRenderer))

    children = ast["children"]
    headings = [child for child in children if child["type"] == "Heading"]

    description = children[0]
    assert description["type"] == "Paragraph"

    # Check that the description starts with the instruction signature, formatted as
    # bold inline code.
    if doc.name in MULTI_WORD_INSTRUCTIONS:
        # Multi-word instructions are documented with their first argument as part of
        # the opcode name, but the formatting should correctly list it as an argument.
        name_words = doc.name.split(" ")
        name = name_words[0]
        args = [name_words[1], *[arg.name for arg in doc.args]]
    else:
        name = doc.name
        args = [arg.name for arg in doc.args]
    arg_str = f" {', '.join(args)}" if args else ""
    assert find_content(description) == f"{name}{arg_str}"
    assert description["children"][0]["type"] == "Strong"
    assert description["children"][0]["children"][0]["type"] == "InlineCode"

    # Check subheadings
    expected_headings = ("Operation", "Parameters", "Example")
    for i, heading in enumerate(headings):
        name = find_content(heading)
        expected = expected_headings[i]
        assert name == expected, f"Heading `{name}` should be `{expected}`."
        assert heading["level"] == 4, f"Subheading {name} should be level 4"

    operation, parameters, example = headings

    # Check the operation
    operation_content = children[children.index(operation) + 1]
    assert (
        operation_content["children"][0]["type"] == "InlineCode"
    ), "Operation should be formatted as inline code"

    # Check the parameter table
    parameters_content = children[children.index(parameters) + 1]
    if not doc.args:
        msg = "Instructions without parameters should list None."
        assert parameters_content["type"] == "Paragraph", msg
        assert find_content(parameters_content) == "None.", msg
    else:
        msg = "Instructions with parameters should list them in a table."
        assert parameters_content["type"] == "Table"

    # Check example code block
    example_content = children[children.index(example) + 1]
    validate_example(example_content)

    # Check copyright footnote
    footnote = children[-1]["children"][0]
    validate_copyright(footnote)
