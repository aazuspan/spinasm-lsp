## `WRAX ADDR, C`

------------------

`WRAX` will save the current value in `ACC` to `[ADDR]` and then multiply `ACC` by `C`. This instruction can be used to write `ACC` to one DAC channel while clearing `ACC` for processing the next audio channel.

### Operation
`ACC­>REG[ADDR], C * ACC`

### Parameters
| Name  | Width | Entry formats, range                |
|-------|-------|-------------------------------------|
| ADDR  | 6 Bit | Decimal (0 - 63)<br>Hex ($0 - $3F)<br>Symbolic |
| C     | 16 Bit| Real (S1.14)<br>Hex ($8000 - $0000 - $7FFF)<br>Symbolic |

In order to simplify the `WRAX` syntax, see the list of predefined symbols for all registers within the FV­1.

### Instruction Coding
**CCCCCCCCCCCCCCCC00000AAAAAA00110**

### Example
```assembly
; Stereo processing
;
    rdax ADCL,1.0    ; Read left ADC into previously cleared ACC
                     ;---------------
    ....             ; ...left channel processing
                     ;---------------
    wrax DACL,0      ; Result to DACL and clear ACC for right channel processing
    rdax ADCR,1.0    ; Read right ADC into previously cleared ACC
                     ;---------------
    ....             ; ...right channel processing
                     ;---------------
    wrax DACR,0      ; Result to DACR and clear ACC for left channel processing
```

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*