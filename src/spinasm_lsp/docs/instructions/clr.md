## `CLR`

------------------

`CLR` will clear the accumulator.

### Operation
`0 ­> ACC`

### Parameters

None.

### Instruction Coding
**00000000000000000000000000001110**

### Example
```assembly
    clr                 ; Clear ACC
    rdax ADCL,1.0       ; Read left ADC
                        ;-----------------
    ....                ; ...Left channel processing...
                        ;-----------------
    wrax DACL,0         ; Result to DACL and clear ACC
```

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*