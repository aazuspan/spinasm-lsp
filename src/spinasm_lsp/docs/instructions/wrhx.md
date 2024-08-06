## `WRHX ADDR, C`

------------------

The current ACC value is stored in the register pointed to by ADDR, then ACC is multiplied by C. Finally, the previous content of ACC (PACC) is added to the product. WRHX is an extremely powerful instruction; when combined with RDFX, it forms a single order high pass shelving filter.

### Operation
`ACC -> REG[ADDR], (ACC * C) + PACC`

### Parameters
| Name  | Width  | Entry formats, range                                                     |
|-------|--------|--------------------------------------------------------------------------|
| ADDR  | 6 Bit  | Decimal (0 - 63)<br>Hex ($0 - $3F)<br>Symbolic                            |
| C     | 16 Bit | Real (S1.14)<br>Hex ($8000 - $0000 - $7FFF)<br>Symbolic                    |

In order to simplify the WRHX syntax, see the list of predefined symbols for all registers within the FV-1 register file.

### Instruction Coding
**CCCCCCCCCCCCCCCC00000AAAAAA00111**

### Example
```assembly
; Single order HP shelving filter
Tmp_HP EQU 32       ; Temporary register for first order HP

;----------------------------------------

    sof 0,0         ; Clear ACC
    rdax ADCL,1.0   ; Read left ADC
    rdfx Tmp_HP,x.x ; First order HP...
    wrhx Tmp_HP,y.y ; ...shelving filter
    wrax DACL,0     ; Result to DACL and clear ACC
```

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*