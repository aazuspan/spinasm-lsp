## `RDAX ADDR, C`

------------------

RDAX will fetch the value contained in `[ADDR]` from the register file, multiply it with `C` and add the result to the previous content of `ACC`. This multiply accumulate is probably the most popular operation found in DSP algorithms.

### Operation
`C * REG[ADDR] + ACC`

### Parameters
| Name  | Width | Entry formats, range                |
|-------|-------|-------------------------------------|
| ADDR  | 6 Bit | Decimal (0 - 63)<br>Hex ($0 - $3F)<br>Symbolic |
| C     | 16 Bit| Real (S1.14)<br>Hex ($8000 - $0000 - $7FFF)<br>Symbolic |

In order to simplify the RDAX syntax, see the list of predefined symbols for all registers within the FV-1 register file.

### Instruction Coding
**CCCCCCCCCCCCCCCC00000AAAAAA00100**

### Example
```assembly
; Crude mono 
;
    sof 0,0          ; Clear ACC 
    rdax ADCL,0.5    ; Get ADCL value and divide it by two 
    rdax ADCR,0.5    ; Get ADCR value, divide it by two 
                     ; and add to the half of ADCL 
    wrax DACL,1.0    ; Result to DACL 
    wrax DACR,0      ; Result to DACR and clear ACC
```

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*