## `MAXX ADDR, C`

------------------

`MAXX` will compare the absolute value of `ACC` versus C times the absolute value of the register pointed to by `ADDR`. If the absolute value of `ACC` is larger `ACC` will be loaded with `|ACC|`, otherwise the accumulator becomes overwritten by `|REG[ADDR] * C|`.

### Operation
`MAX( |REG[ADDR] * C| , |ACC| )`

### Parameters
| Name  | Width | Entry formats, range                |
|-------|-------|-------------------------------------|
| ADDR  | 6 Bit | Decimal (0 - 63)<br>Hex ($0 - $3F)<br>Symbolic |
| C     | 16 Bit| Real (S1.14)<br>Hex ($8000 - $0000 - $7FFF)<br>Symbolic |

In order to simplify the MAXX syntax, see the list of predefined symbols for all registers within the FV-1 register file.

### Instruction Coding
**CCCCCCCCCCCCCCCC00000AAAAAA01001**

### Example
```assembly
; Peak follower
;
Peak EQU 32          ; Peak hold register

    sof 0,0          ; Clear ACC 
    rdax ADCL,1.0    ; Read left ADC
    maxx Peak,1.0    ; Keep larger absolute value in ACC

; For a peak meter insert decay code here...

    wrax Peak,0.0    ; Save (new) peak and clear ACC
```

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*