## `WRA ADDR, C`

------------------

`WRA` will store `ACC` to the delay ram location addressed by `ADDR` and then multiply `ACC` by `C`.

### Operation
`ACC­>SRAM[ADDR], ACC * C`

### Parameters

| Name  | Width | Entry formats, range                |
|-------|-------|-------------------------------------|
| ADDR  | (1)+15 Bit| Decimal (0 - 32767)<br>Hex ($0 - $7FFF)<br>Symbolic |
| C     | 11 Bit    | Real (S1.9)<br>Hex ($400 - $000 - $3FF)<br>Symbolic  |

### Instruction Coding
**CCCCCCCCCCCAAAAAAAAAAAAAAAA00010**

### Example
```assembly
Delay MEM 1024 
Coeff EQU 0.5

    sof 0,0             ; Clear ACC
    rdax ADCL,1.0       ; Read left ADC
    wra Delay,Coeff     ; Write to start of delay line, halve ACC
    rda Delay#,Coeff    ; Add half of the sample from the end of the delay line
    wrax DACL,0         ; Result to DACL and clear ACC
```

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*