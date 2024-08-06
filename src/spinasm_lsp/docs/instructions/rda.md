## `RDA ADDR, C`

------------------

RDA will fetch the sample [ADDR] from the delay RAM, multiply it by C, and add the result to the previous content of ACC. This multiply-accumulate operation is probably the most popular operation found in DSP algorithms.

### Operation
`SRAM[ADDR] * C + ACC`

### Parameters

| Name  | Width | Entry formats, range                |
|-------|-------|-------------------------------------|
| ADDR  | (1)+15 Bit| Decimal (0 - 32767)<br>Hex ($0 - $7FFF)<br>Symbolic |
| C     | 11 Bit    | Real (S1.9)<br>Hex ($400 - $000 - $3FF)<br>Symbolic  |

### Instruction Coding
**CCCCCCCCCCCAAAAAAAAAAAAAAAA00000**

### Example
```assembly
Delay MEM 1024 
Coeff EQU 1.55
Tmp   EQU $2000

    rda 1000,1.9
    rda Delay+20,Coeff
    rda Tmp,-2
    rda $7FFF,$7FF
```

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*