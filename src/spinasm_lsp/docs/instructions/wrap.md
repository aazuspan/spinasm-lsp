## `WRAP ADDR, C`

------------------

`WRAP` will store `ACC` to the delay ram location addressed by ADDR then multiply `ACC` by `C` and finally add the content of the `LR` register to the product. Please note that the `LR` register contains the last sample value read from the delay ram memory. This instruction is typically used for all­pass filters in a reverb program.

### Operation
`ACC­>SRAM[ADDR], (ACC*C) + LR`

### Parameters
| Name  | Width | Entry formats, range                |
|-------|-------|-------------------------------------|
| ADDR  | (1)+15 Bit| Decimal (0 - 32767)<br>Hex ($0 - $7FFF)<br>Symbolic |
| C     | 11 Bit    | Real (S1.9)<br>Hex ($400 - $000 - $3FF)<br>Symbolic  |

### Instruction Coding
**CCCCCCCCCCCAAAAAAAAAAAAAAAA00011**

### Example
```assembly
    rda ap1#,kap        ; Read output of all-pass 1 and multiply it by kap
    wrap ap1,-kap       ; Write ACC to input of all-pass 1 and do
                        ; ACC*(-kap)+ap1# (ap1# is in LR register)
```

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*