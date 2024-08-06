## `SOF C, D`

------------------

SOF will multiply the current value in ACC with C and will then add the constant D to the result.

Please note the absence of an integer entry format for D. This is not by mistake but it should emphasize that D is not intended to become used for integer arithmetic. The reason for this instruction is that the 11 bit constant D would be placed into ACC left justified or in other words 13 bits shifted to the left. D is intended to offset ACC by a constant in the range from -1 to +0.9990234375.

### Operation
`C * ACC + D`

### Parameters
| Name | Width | Entry formats, range |
|---|---|---|
| C | 16 Bit | Real (S1.14)<br>Hex ($0000 - $FFFF)<br>Symbolic |
| D | 11 Bit | Real (S.10)<br>Symbolic |

### Instruction Coding
**CCCCCCCCCCCCCCCCDDDDDDDDDDD01101**

### Example
```assembly
Off EQU 1.0

; Halve way rectifier­­­
    sof 0,0                 ; Clear ACC
    rdax ADCL,1.0           ; Read from left ADC channel
    sof 1.0,­-Off            ; Subtract offset
    sof 1.0,Off             ; Add offset
```

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*