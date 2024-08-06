## `WLDS N, F, A`

------------------

`WLDS` will load frequency and amplitude control values into the selected SIN LFO (0 or 1). This instruction is intended to setup the selected SIN LFO which is typically done within the first sample iteration after a new program is loaded. As a result `WLDS` will in most cases be used in combination with a `SKP RUN` instruction. For a more detailed description regarding the frequency and amplitude control values see application note AN­0001.

### Operation
`See description`

### Parameters
| Name  | Width | Entry formats, range                |
|-------|-------|-------------------------------------|
| N     | 1 Bit | SIN LFO select: (0, 1)              |
| F     | 9 Bit | Decimal (0 - 511)<br>Hex ($000 - $1FF)<br>Symbolic  |
| A     | 15 Bit| Decimal (0 - 32767)<br>Hex ($0000 - $7FFF)<br>Symbolic  |


### Instruction Coding
**00NFFFFFFFFFAAAAAAAAAAAAAAA10010**

### Example
```assembly
Amp EQU 8194            ; Amplitude for a 4097 sample delay line
Freq EQU 51             ; Apx. 2Hz at 32kHz sampling rate
;------------------------

; Setup SIN LFO 0       ;
    skp run,start       ; Skip next instruction if not first iteration
    wlds 0,Freq,Amp     ; Setup SIN LFO 0

start: sof 0,0          ;
    ....                ;
    ....                ;
```

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*