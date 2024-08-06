## `JAM N`

------------------

`JAM` will reset the selected RAMP LFO to its starting point.

### Operation
`0 ­> RAMP LFO N`

### Parameters
| Name  | Width | Entry formats, range                |
|-------|-------|-------------------------------------|
| N     | 1 Bit | RAMP LFO select: (0, 1)              |

### Instruction Coding
**0000000000000000000000001N010011**

### Example
```assembly
jam 0           ; Force ramp 0 LFO to it's starting position
```

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*