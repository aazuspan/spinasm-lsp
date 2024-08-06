## `NOT`

------------------

`NOT` will negate all bit positions within accumulator thus performing a 1’s complement.

### Operation
`/ACC ­> ACC`

### Parameters

None.

### Instruction Coding
**11111111111111111111111100010000**

### Example
```assembly
    not             ; 1's comp ACC
```

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*