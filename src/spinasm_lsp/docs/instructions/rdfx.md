## `RDFX ADDR, C`

------------------

`RDFX` will subtract the value of the register pointed to by `ADDR` from `ACC`, multiply the result by `C` and then add the value of the register pointed to by `ADDR`. `RDFX` is an extremely powerful instruction in that it represents the major portion of a single order low pass filter.

### Operation
`(ACC­REG[ADDR])*C + REG[ADDR]`

### Parameters
| Name  | Width | Entry formats, range                |
|-------|-------|-------------------------------------|
| ADDR  | 6 Bit | Decimal (0 - 63)<br>Hex ($0 - $3F)<br>Symbolic |
| C     | 16 Bit| Real (S1.14)<br>Hex ($8000 - $0000 - $7FFF)<br>Symbolic |

In order to simplify the `RDFX` syntax, see the list of predefined symbols for all registers within the FV-1 register file.

### Instruction Coding
**CCCCCCCCCCCCCCCC00000AAAAAA00101**

### Example
```assembly
; Single order LP filter
Tmp_LP EQU 32        ; Temporary register for first order LP

    ldax ADCL        ; Read left ADC
    rdfx Tmp_LP,x.x  ; First order...
    wrax Tmp_LP,1.0  ; ...LP filter
    wrax DACL,0      ; Result to DACL and clear ACC
```

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*