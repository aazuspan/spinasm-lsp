"""Markdown documentation generation for SpinASM assemblers."""

# ruff: noqa: E501

from __future__ import annotations

from spinasm_lsp.docs.markdown import Assembler

ASSEMBLERS: dict[str, Assembler] = {
    "EQU": Assembler(
        name="EQU",
        description="""**`EQU`** allows one to define symbolic operands in order to increase the readability of the source code. Technically an `EQU` statement such as:

```assembly
Name EQU Value [;Comment]
```

will cause SPINAsm to replace any occurrence of the literal "Name" by the literal "Value" within each instruction line during the assembly process excluding the comment portion of an instruction line.

With the exception of blanks, any printable character is allowed within the literal "Name". However there are restrictions: "Name" must be an unique string, is limited to 32 characters and the first character must be a letter excluding the "+" and "­" signs and the "!" character.

The reason for not allowing these characters being the first character of "Name" is that any symbolic operand may be prefixed with a sign or the "!" negation operator within the instruction line. The assembler will then perform the required conversion of the operand while processing the individual instruction lines.

There is another, not syntax related, restriction when using symbolic operands defined by an `EQU` statement: Predefined symbols. As given in the end of the manual there is a set of predefined symbolic operands which should be omitted as "Name" literals within an `EQU` statement. It is not that these predefined symbols are prohibited, it is just that using them within an `EQU` statement will overwrite their predefined value.

With the literal "Value" things are slightly more complicated since its format has to comply with the syntactical rules defined for the operand type it is to represent. Although it is suggested to place `EQU` statements at the beginning of the source code file, this is not mandatory. However, the `EQU` statement has to be defined before the literal "Name" can be used as a symbolical operand within an instruction line.

#### Remark
SPINAsm has no way of performing range checking while processing the EQU statement. This is because the operand type of value is not known to SPINAsm at the time the EQU statement is processed. As a result, range checking is performed when assembling the instruction line in which "Name" is to be replaced by "Value".
""",
        example="""
Attn      EQU 0.5      ; 0.5 = -6dB attenuation
Tmp_Reg   EQU 63       ; Temporary register within register file
Tmp_Del   EQU $2000    ; Temporary memory location within delay ram
;
;------------------------------
sof       0,0          ; Clear ACC
rda       Tmp_Del,Attn ; Load sample from delay ram $2000,
                       ; multiply it by 0.5 and add ACC content
wrax      Tmp_Reg,1.0  ; Save result to Tmp_Reg but keep it in ACC
wrax      DACL,0       ; Move ACC to DAC left (predefined symbol)
                       ; and then clear ACC
""",
        example_remarks="""If `Tmp_Del` was accidentally replaced by `Tmp_Reg` within the `rda` instruction line, SPINAsm would not detect this semantic error – simply because using `Tmp_Reg` would be syntactically correct.""",
    ),
    "MEM": Assembler(
        name="MEM",
        description="""**`MEM`** allows the user to partition the delay ram memory into individual blocks. A memory block declared by the statement

```assembly
Name `MEM` Size [;Comment]
```

can be referenced by `Name` from within an instruction line. `Name` has to comply with the same syntactical rules previously defined with the EQU statement, "Size" is an unsigned integer in the range of 1 to 32768 which might be entered either in decimal or in hexadecimal.

Besides the explicit identifier `Name` the assembler defines two additional implicit identifiers, `Name#` and `Name^`. `Name` refers to the first memory location within the memory block, whereas `Name#` refers to the last memory location. The identifier `Name^` references the middle of the memory block, or in other words its center. If a memory block of size 1 is defined, all three identifiers will address the same memory location. In case the memory block is of size 2, `Name` and `Name^` will address the same memory location, if the size is an even number the memory block cannot exactly be halved – the midpoint `Name^` will be calculated as: `size MOD 2`.

Optionally all three identifiers can be offset by a positive or negative integer which is entered in decimal. Although range checking is performed when using offsets, there is no error generated if the result of the address calculation exceeds the address range of the memory block. This is also true for those cases in which the result will "wrap around" the physical 32k boundary of the delay memory. However, a warning will be issued in order to alert the user regarding the out of range condition.

Mapping the memory blocks to their physical delay ram addresses is solely handled by SPINAsm. The user has no possibility to explicitly force SPINAsm to place a certain memory block to a specific physical address range. This of course does not mean that the user has no control over the layout of the delay ram at all: Knowing that SPINAsm will map memory blocks in the order they become defined within the source file, the user can implicitly control the memory map of the delay ram.
""",
        example="""DelR      MEM  1024    ; Right channel delay line
DelL      MEM  1024    ; Left channel delay line
                       ;
;------------------------------
sof       0,0          ; Clear ACC
rdax      ADCL,1.0     ; Read in left ADC
wra       DelL,0.25    ; Save it to the start of the left delay
                       ; line and keep a -12dB replica in ACC
rdax      DelL^+20,0.25; Add sample from "center of the left delay
                       ; line + 20 samples" times 0.25 to ACC
rdax      DelL#,0.25   ; Add sample from "end of the left delay
                       ; line" times 0.25 to ACC
rdax      DelL-512,0.25; Add sample from "start of the left delay
                       ; line - 512 samples" times 0.25 to ACC
""",
        example_remarks="""#### Remark
At this point the result of the address calculation will reference a sample from outside the `DelL` memory block. While being syntactically correct, the instruction might not result in what the user intended. In order to make the user aware of that potential semantic error, a warning will be issued.

```assembly
wrax      DACL,0       ; Result to DACL, clear ACC
                       ;
rdax      ADCR,1.0     ; Read in right ADC
wra       DelR,0.25    ; Save it to the start of the right delay
                       ; line and keep a -12dB replica in ACC
rdax      DelR^-20,0.25; Add sample from center of the right delay
                       ; line - 20 samples times 0.25 to ACC
rdax      DelR#,0.25   ; Add sample from end of the right delay line
                       ; times 0.25 to ACC
rdax      DelR-512,0.25; Add sample from start of the right delay
                       ; line - 512 samples times 0.25 to ACC
```

#### Remark
At this point the result of the address calculation will reference a sample from outside the `DelR` memory block. And even worse than the previous case: This time the sample be fetched from delay ram address 32256 which will contain a sample that is apx. 1 second old!

Again, syntactically correct but most likely a semantic error – warnings will be issued.

```assembly
wrax DACR,0         ; Result to DACR, clear ACC
```
""",
    ),
}
