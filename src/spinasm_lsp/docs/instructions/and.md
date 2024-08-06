## `AND M`

------------------

AND will perform a bit wise "and" of the current ACC and the 24-­bit MASK specified within the instruction word. The instruction might be used to load a constant into ACC provided ACC contains $FFFFFF or to clear ACC if MASK equals $000000. (see also the pseudo opcode section)

### Operation
`ACC & MASK`

### Parameters
| Name  | Width | Entry formats, range                |
|-------|-------|-------------------------------------|
| M     | 24 Bit| Binary<br>Hex ($000000 - $FFFFFF)<br>Symbolic |

### Instruction Coding
**MMMMMMMMMMMMMMMMMMMMMMMM000001110**

### Example
```assembly
AMASK EQU $F0FFFF

;----------------------------------------
    or ­­­­­­­­­­­­­­­­­­$FFFFFF                        ; Set all bits within ACC
    and $FFFFFE                       ; Clear LSB
    and %01111111_11111111_11111111   ; Clear MSB
    and AMASK                         ; Clear ACC[19..16]
    and $0                            ; Clear ACC
```

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*