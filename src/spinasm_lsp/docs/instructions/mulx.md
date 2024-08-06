## `MULX ADDR`

------------------

`MULX` will multiply `ACC` by the value of the register pointed to by `ADDR`. An important application of the `MULX` instruction is squaring the content of `ACC`, which combined with a single order LP is especially useful in calculating the RMS value of an arbitrary waveform.

### Operation
`ACC * REG[ADDR]`

### Parameters
| Name  | Width | Entry formats, range                |
|-------|-------|-------------------------------------|
| ADDR  | 6 Bit | Decimal (0 - 63)<br>Hex ($0 - $3F)<br>Symbolic |

In order to simplify the `MULX` syntax, see the list of predefined symbols for all registers within the FV-1 register file.

### Instruction Coding
**000000000000000000000AAAAAA01010**

### Example
```assembly
; RMS conversion
Tmp_LP EQU 32        ; Temporary register for first order LP

    sof 0,0          ; Clear ACC 
    rdax ADCL,1.0    ; Read left ADC
                     ; RMS calculation = ACC^2 -> first order LP

    mulx ADCL        ; ACC^2
    rdfx Tmp_LP,x.x  ; First order...
    wrax Tmp_LP,1.0  ; ...LP filter

; At this point ACC holds the RMS value of the input
```

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*