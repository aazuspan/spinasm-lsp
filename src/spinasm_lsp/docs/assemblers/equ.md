## `EQU`

------------------

The `EQU` statement allows one to define symbolic operands in order to increase the readability of the source code. Technically an `EQU` statement such as:

```assembly
Name EQU Value [;Comment]
```

will cause SPINAsm to replace any occurrence of the literal "Name" by the literal "Value" within each instruction line during the assembly process excluding the comment portion of an instruction line.

With the exception of blanks, any printable character is allowed within the literal "Name". However there are restrictions: "Name" must be an unique string, is limited to 32 characters and the first character must be a letter excluding the "+" and "­" signs and the "!" character.

The reason for not allowing these characters being the first character of "Name" is that any symbolic operand may be prefixed with a sign or the "!" negation operator within the instruction line. The assembler will then perform the required conversion of the operand while processing the individual instruction lines.

There is another, not syntax related, restriction when using symbolic operands defined by an `EQU` statement: Predefined symbols. As given in the end of the manual there is a set of predefined symbolic operands which should be omitted as "Name" literals within an `EQU` statement. It is not that these predefined symbols are prohibited, it is just that using them within an `EQU` statement will overwrite their predefined value.

With the literal "Value" things are slightly more complicated since its format has to comply with the syntactical rules defined for the operand type it is to represent. Although it is suggested to place `EQU` statements at the beginning of the source code file, this is not mandatory. However, the `EQU` statement has to be defined before the literal "Name" can be used as a symbolical operand within an instruction line.

### Remark
SPINAsm has no way of performing range checking while processing the EQU statement. This is because the operand type of value is not known to SPINAsm at the time the EQU statement is processed. As a result, range checking is performed when assembling the instruction line in which "Name" is to be replaced by "Value".

### Example
```assembly
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
```

If `Tmp_Del` was accidentally replaced by `Tmp_Reg` within the `rda` instruction line, SPINAsm would not detect this semantic error – simply because using `Tmp_Reg` would be syntactically correct.

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*