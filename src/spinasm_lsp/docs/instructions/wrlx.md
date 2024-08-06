## `WRLX ADDR, C`

------------------

First, the current ACC value is stored into the register pointed to by ADDR, then ACC is subtracted from the previous content of ACC (PACC). The difference is then multiplied by C and finally PACC is added to the result. WRLX is an extremely powerful instruction in that when combined with RDFX, it forms a single order low-pass shelving filter.

### Operation
`ACC -> REG[ADDR], (PACC - ACC) * C + PACC`

### Parameters

| Name  | Width  | Entry formats, range                                                                 |
|-------|--------|---------------------------------------------------------------------------------------|
| ADDR  | 6 Bit  | Decimal (0 - 63)<br>Hex ($0 - $3F)<br>Symbolic                                              |
| C     | 16 Bit | Real (S1.14)<br>Hex ($8000 - $0000 - $7FFF)<br>Symbolic                                     |

In order to simplify the WRLX syntax, see the list of predefined symbols for all registers within the FV-1 register file.

### Instruction Coding
**CCCCCCCCCCCCCCCC00000AAAAAA01000**

### Example
```assembly
; Single order LP shelving filter
Tmp_LP EQU 32       ; Temporary register for first order LP

;----------------------------------------

    sof 0,0         ; Clear ACC
    rdax ADCL,1.0   ; Read left ADC
    rdfx Tmp_LP,x.x ; First order LP...
    wrlx Tmp_LP,y.y ; ...shelving filter
    wrax DACL,1.0   ; Result to DACL and clear ACC
```

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*