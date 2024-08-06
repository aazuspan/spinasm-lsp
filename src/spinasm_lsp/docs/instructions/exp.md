## `EXP C, D`

------------------

`EXP` will multiply 2^`ACC` with `C` and add the constant `D` to the result.

Since `ACC` (in it’s role as the destination for the `EXP` instruction) is limited to linear values from 0 to
+0.99999988, the `EXP` instruction is limited to logarithmic `ACC` values (in it’s role as the source operand
for the `EXP` instruction) from –16 to 0. Like the LOG instruction, `EXP` will treat the `ACC` content as a
S4.19 number. Positive logarithmic `ACC` values will be clipped to +0.99999988 which is the most positive
linear value that can be represented within the accumulator.

`D` is intended to allow the linear `ACC` to be offset by a constant in the range from –1 to +0.9990234375

### Operation
`C * EXP(ACC) + D`

### Parameters
| Name  | Width | Entry formats, range                |
|-------|-------|-------------------------------------|
| C     | 16 Bit| Real (S1.14)<br>Hex ($0000 - $FFFF)<br>Symbolic |
| D     | 11 Bit| Real (S.10)<br>Symbolic |

### Instruction Coding
**CCCCCCCCCCCCCCCCDDDDDDDDDDD01100**

### Example
```assembly
exp 0.8,0
```

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*