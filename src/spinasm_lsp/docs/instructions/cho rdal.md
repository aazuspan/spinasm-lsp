## `CHO RDAL, N`

------------------

`CHO RDAL` will read the current value of the selected LFO into `ACC`.

### Operation
`LFO * 1 ­> ACC`

### Parameters
| Name  | Width | Entry formats, range                |
|-------|-------|-------------------------------------|
| N     | 2 Bit | LFO select: SIN0,COS0,SIN1,COS1,RMP0,RMP1|

### Instruction Coding
**110000100NN000000000000000010100**

### Example
```assembly
cho rdal,SIN0           ; Read LFO S0 into ACC
wrax DACL,0             ; Result to DACL and clear ACC
```

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*