## `RMPA C`

------------------

`RMPA` provides indirect delay line addressing in that the delay line address of the sample to be multiplied by `C` is not explicitly given in the instruction itself but contained within the pointer register `ADDR_PTR` (absolute address 24 within the internal register file.)

`RMPA` will fetch the indirectly addressed sample from the delay ram, multiply it by `C` and add the result to the previous content of `ACC`.

### Operation
`SRAM[PNTR[N]] * C + ACC`

### Parameters

| Name  | Width | Entry formats, range                |
|-------|-------|-------------------------------------|
| C     | 11 Bit    | Real (S1.9)<br>Hex ($400 - $000 - $3FF)<br>Symbolic  |

### Instruction Coding
**CCCCCCCCCCC000000000001100000001**

### Example
```assembly
; Crude variable delay line addressing
    sof 0,0             ; Clear ACC
    rdax POT1,1.0       ; Read POT1 value
    wrax ADDR_PTR,0     ; Write value to pointer register, clear ACC
    rmpa 1.0            ; Read sample from delay line
    wrax DACL,0         ; Result to DACL and clear ACC
```

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*