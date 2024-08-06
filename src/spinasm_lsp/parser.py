from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from lark import Lark, Transformer, v_args
from lark.exceptions import VisitError


class ParsingError(Exception): ...


@dataclass
class Expression:
    expression: list[int | float | str]

    def __eq__(self, other):
        # If the expression has a single value, match against that
        if len(self.expression) == 1:
            return self.expression[0] == other

        # Otherwise, match the expression as a concated string of values and operators
        return " ".join(map(str, self.expression)) == other


@dataclass
class Instruction:
    opcode: str
    args: list[Expression]


@dataclass
class Assignment:
    type: Literal["equ", "mem"]
    name: str
    value: Expression


@dataclass
class Label:
    name: str


@v_args(inline=True)
class FV1ProgramTransformer(Transformer):
    local_vars: dict[str, float]
    memory: dict[str, float]

    def __init__(
        self,
        local_vars: dict[str, float],
        memory: dict[str, float],
        visit_tokens: bool = True,
    ) -> None:
        self.local_vars = local_vars
        self.memory = memory
        super().__init__(visit_tokens=visit_tokens)

    def instruction(self, opcode: str, args: list | None, _) -> Instruction:
        return Instruction(opcode, args or [])

    def assignment(self, mapping, _):
        return mapping

    def label(self, name) -> Label:
        return Label(name)

    def equ(self, name: str, value) -> Assignment:
        self.local_vars[name] = value
        return Assignment(type="equ", name=name, value=value)

    def mem(self, name: str, value) -> Assignment:
        self.memory[name] = value
        return Assignment(type="mem", name=name, value=value)

    def value(self, negative: str | None, value: float) -> float:
        """A negated value."""
        if negative:
            value *= -1

        return value

    def DEC_NUM(self, token) -> int | float:
        if "." in token:
            return float(token)
        return int(token)

    def HEX_NUM(self, token) -> int:
        # Hex numbers can be written with either $ or 0x prefix
        token = token.replace("$", "0x")
        return int(token, base=16)

    def BIT_VECTOR(self, token) -> int:
        # Remove the % prefix and optional underscores
        return int(token[1:].replace("_", ""), base=2)

    def NAME(self, name) -> str:
        # if name not in self.local_vars:
        # TODO: This doesn't work because labels can be used before they are defined.
        # Probably the simplest fix is making a special grammar for SKP since that's
        # the only instruction that uses labels. Alternatively, maybe we keep a dict
        # with all the defined and used labels and variables (separately) and their
        # line numbers, and go through and resolve them after parsing.
        # raise ParsingError(f"`{name}` is undefined.")

        # NOTE: identifiers are case-insensitive. asfv1 warns when you redefine, while
        # the original FV-1 assembler errors out. Both store labels as uppercase.
        return name.upper()
        # return self.local_vars.get(name, str(name))

    @v_args(inline=False)
    def args(self, tokens):
        return tokens

    @v_args(inline=False)
    def expr(self, tokens):
        return Expression(tokens)

    @v_args(inline=False)
    def program(self, tokens):
        return list(tokens)

    IDENT = OPERATOR = OPCODE = str


class FV1Program:
    constants = {
        "SIN0_RATE": 0x00,
        "SIN0_RANGE": 0x01,
        "SIN1_RATE": 0x02,
        "SIN1_RANGE": 0x03,
        "RMP0_RATE": 0x04,
        "RMP0_RANGE": 0x05,
        "RMP1_RATE": 0x06,
        "RMP1_RANGE": 0x07,
        "POT0": 0x10,
        "POT1": 0x11,
        "POT2": 0x12,
        "ADCL": 0x14,
        "ADCR": 0x15,
        "DACL": 0x16,
        "DACR": 0x17,
        "ADDR_PTR": 0x18,
        "REG0": 0x20,
        "REG1": 0x21,
        "REG2": 0x22,
        "REG3": 0x23,
        "REG4": 0x24,
        "REG5": 0x25,
        "REG6": 0x26,
        "REG7": 0x27,
        "REG8": 0x28,
        "REG9": 0x29,
        "REG10": 0x2A,
        "REG11": 0x2B,
        "REG12": 0x2C,
        "REG13": 0x2D,
        "REG14": 0x2E,
        "REG15": 0x2F,
        "REG16": 0x30,
        "REG17": 0x31,
        "REG18": 0x32,
        "REG19": 0x33,
        "REG20": 0x34,
        "REG21": 0x35,
        "REG22": 0x36,
        "REG23": 0x37,
        "REG24": 0x38,
        "REG25": 0x39,
        "REG26": 0x3A,
        "REG27": 0x3B,
        "REG28": 0x3C,
        "REG29": 0x3D,
        "REG30": 0x3E,
        "REG31": 0x3F,
        "SIN0": 0x00,
        "SIN1": 0x01,
        "RMP0": 0x02,
        "RMP1": 0x03,
        "RDA": 0x00,
        "SOF": 0x02,
        "RDAL": 0x03,
        "SIN": 0x00,
        "COS": 0x01,
        "REG": 0x02,
        "COMPC": 0x04,
        "COMPA": 0x08,
        "RPTR2": 0x10,
        "NA": 0x20,
        "RUN": 0x10,
        "ZRC": 0x08,
        "ZRO": 0x04,
        "GEZ": 0x02,
        "NEG": 0x01,
    }
    local_vars: dict[str, float] = {**constants}
    memory: dict[str, float] = {}

    def __init__(self, code: str):
        self.transformer = FV1ProgramTransformer(
            local_vars=self.local_vars, memory=self.memory
        )

        self.parser = Lark.open_from_package(
            package="spinasm_lsp",
            grammar_path="spinasm.lark",
            start="program",
            # parser="lalr",
            # strict=True,
            # transformer=self.transformer
        )

        # Make sure the code ends with a newline to properly parse the last line
        if not code.endswith("\n"):
            code += "\n"

        try:
            self.tree = self.parser.parse(code)
            self.statements: list[dict] = self.transformer.transform(self.tree)
        except VisitError as e:
            # Unwrap errors thrown by FV1ProgramTransformer
            if wrapped_err := e.__context__:
                raise wrapped_err from None

            raise e


if __name__ == "__main__":
    code = r"""
    Tmp EQU 4
    """

    with open("./demos/test.spn") as src:
        code = src.read()

    program = FV1Program(code)

    # print(program)
    print("program.statements =")
    for statement in program.statements:
        print("\t", statement)

    print(f"{program.local_vars = }")
    print(f"{program.memory = }")
