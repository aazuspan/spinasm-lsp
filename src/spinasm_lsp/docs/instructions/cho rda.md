## `CHO RDA N, C, D`

------------------

Like the `RDA` instruction, `CHO RDA` will read a sample from the delay ram, multiply it by a coefficient and add the product to the previous content of ACC. However, in contrast to `RDA` the coefficient is not explicitly embedded within the instruction and the effective delay ram address is not solely determined by the address parameter. Instead, both values are modulated by the selected LFO at run time, for an in depth explanation please consult the FV­1 datasheet alongside with application note AN­0001. `CHO RDA` is a very flexible and powerful instruction, especially useful for delay line modulation effects such as chorus or pitch shifting.

The coefficient field of the `CHO` instructions are used as control bits to select various aspects of the LFO. These bits can be set using predefined flags that are `OR`ed together to create the required bit field. For a sine wave LFO (SIN0 or SIN1), valid flags are:

`SIN COS REG COMPC COMPA`

While for a ramp LFO (RMP0 and RMP1), valid flags are:

`REG COMPC COMPA RPTR2 NA`

These flags are defined as:

| Flag | HEX value | Description |
| --- | --- | --- |
| SIN | $0 | Select SIN output (default) (Sine LFO only) |
| COS | $1 | Select COS output (Sine LFO only) |
| REG | $2 | Save the output of the LFO into an internal LFO register |
| COMPC | $4 | Complement the coefficient (1-coeff) |
| COMPA | $8 | Complement the address offset from the LFO |
| RPTR2 | $10 | Select the ramp+1/2 pointer (Ramp LFO only) |
| NA | $20 | Select x-fade coefficient and do not add address offset |

### Operation
`See description`

### Parameters
| Name | Width | Entry formats, range |
|---|---|---|
| N     | 2 Bit | LFO select: SIN0,SIN1,RMP0,RMP1|
| C | 6 Bit | Binary<br>Bit flags |
| D | 16 Bit | Real (S.15)<br>Symbolic |

### Instruction Coding
**00CCCCCC0NNAAAAAAAAAAAAAAAA10100**

### Example
```assembly
; A chorus
Delay MEM 4097                          ; Chorus delay line
Amp EQU 8195                            ; Amplitude for a 4097 sample delay line
Freq EQU 51                             ; Apx. 2Hz at 32kHz sampling rate

; Setup SIN LFO 0
    skp run,cont                        ; Skip if not first iteration
    wldr 0,Freq,Amp                     ; Setup SIN LFO 0

cont:
    sof 0,0                             ; Clear ACC
    rdax ADCL,1.0                       ; Read left ADC * 1.0
    wra Delay,0                         ; Write to delay line, clear ACC
    cho rda,RMP0,COMPC|REG,Delay        ; See application note AN-0001
    cho rda,RMP0,,Delay+1               ; for detailed examples and explanation
    wra Temp,0                          ;
    cho rda,RMP0,COMPC|RPTR2,Delay      ;
    cho rda,RMP0,RPTR2,Delay+1          ;
    cho sof,RMP0,NA|COMPC,0             ;
    cho rda,RMP0,NA,Temp                ;
    wrax DACL,0                         ; Result to DACL and clear ACC
```

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*