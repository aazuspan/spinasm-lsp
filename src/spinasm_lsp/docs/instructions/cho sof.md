## `CHO SOF N, C, D`

------------------

Like the `SOF` instruction, `CHO SOF` will multiply ACC by a coefficient and add the constant `D` to the result. However, in contrast to `SOF` the coefficient is not explicitly embedded within the instruction. Instead, based on the selected LFO and the 6 bit vector `C`, the coefficient is picked from a list of possible coefficients available within the LFO block of the FV­1. For an in depth explanation please consult the FV­-1 datasheet alongside with application note AN­0001. `CHO SOF` is a very flexible and powerful instruction, especially useful for the cross fading portion of pitch shift algorithms.

Please see `CHO RDA` for a description of field flags.

### Operation
`See description`

### Parameters
| Name | Width | Entry formats, range |
|---|---|---|
| N     | 2 Bit | LFO select: SIN0,SIN1,RMP0,RMP1|
| C | 6 Bit | Binary<br>Bit flags |
| D | 16 Bit | Real (S.15)<br>Symbolic |

### Instruction Coding
**10CCCCCC0NNDDDDDDDDDDDDDDDD10100**

### Example
```assembly
; Pitch shift
Delay MEM 4096                          ; Pitch shift delay line
Temp MEM 1                              ; Temporary storage
Amp EQU 4096                            ; RAMP LFO amplitude (4096 samples)
Freq EQU -8192                          ; RAMP LFO frequency

; Setup RAMP LFO 0
    skp run,cont                        ; Skip if not first iteration
    wldr 0,Freq,Amp                     ; Setup RAMP LFO 0

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