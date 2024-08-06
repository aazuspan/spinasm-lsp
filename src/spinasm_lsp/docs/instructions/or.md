## `OR M`

------------------

`OR` will perform a bit wise "or" of the current `ACC` and the 24-­bit MASK specified within the instruction word. The instruction might be used to load a constant into `ACC` provided `ACC` contains `$000000`.

### Operation
`ACC | MASK`

### Parameters
| Name  | Width | Entry formats, range                |
|-------|-------|-------------------------------------|
| M     | 24 Bit| Binary<br>Hex ($000000 - $FFFFFF)<br>Symbolic |

### Instruction Coding
**MMMMMMMMMMMMMMMMMMMMMMMM000001111**

### Example
```assembly
0MASK EQU $0F0000

;----------------------------------------
    sof 0,0                           ; Clear all bits within ACC
    or $1                             ; Set LSB
    or %10000000_00000000_00000000    ; Set MSB
    or 0MASK                          ; Set ACC[19..16]
    and %S=[15..8]                    ; Set ACC[15..8]
```

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*