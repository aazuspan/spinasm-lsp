## `WLDR N, F, A`

------------------

`WLDR` will load frequency and amplitude control values into the selected RAMP LFO. (0 or 1) This instruction is intended to setup the selected RAMP LFO which is typically done within the first sample iteration after a new program became loaded. As a result `WLDR` will in most cases be used in combination with a `SKP RUN` instruction. For a more detailed description regarding the frequency and amplitude control values see application note AN­0001.

### Operation
`See description`

### Parameters
| Name  | Width | Entry formats, range                |
|-------|-------|-------------------------------------|
| N     | 1 Bit | RAMP LFO select: (0, 1)              |
| F     | 16 Bit | Decimal (-16384 - 32768)<br>Hex ($4000 - $000 - $7FFF)<br>Symbolic  |
| A     | 2 Bit| Decimal (512, 1024, 2048, 4096)<br>Symbolic  |


### Instruction Coding
**01NFFFFFFFFFFFFFFFF000000AA10010**

### Example
```assembly
Amp EQU 4096            ; LFO will module a 4096 sample delay line
Freq EQU $100           ; 
;------------------------

; Setup RAMP LFO 0       ;
    skp run,start       ; Skip next instruction if not first iteration
    wldr 0,Freq,Amp     ; Setup RAMP LFO 0

start: and 0,0          ;
    ....                ;
    ....                ;
```

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*