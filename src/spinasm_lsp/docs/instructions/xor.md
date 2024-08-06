## `XOR M`

------------------

`XOR` will perform a bit wise "xor" of the current `ACC` and the 24­-bit MASK specified within the instruction word. The instruction will invert `ACC` provided `MASK` equals `$FFFFFF`. (see also the pseudo opcode section).

### Operation
`ACC ^ MASK`

### Parameters
| Name  | Width | Entry formats, range                |
|-------|-------|-------------------------------------|
| M     | 24 Bit| Binary<br>Hex ($000000 - $FFFFFF)<br>Symbolic |

### Instruction Coding
**MMMMMMMMMMMMMMMMMMMMMMMM000010000**

### Example
```assembly
XMASK EQU $AAAAAA

;----------------------------------------
    sof 0,0                           ; Clear all bits within ACC
    xor $0                            ; Set all ACC bits
    xor %01010101_01010101_01010101   ; Invert all even numbered bits
    xor XMASK                          ; Invert all odd numbered bits
```

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*