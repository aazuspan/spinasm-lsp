## `LDAX ADDR`

------------------

Loads the accumulator with the contents of the addressed register.

### Operation
`REG[ADDR]­> ACC`

### Parameters
| Name  | Width | Entry formats, range                |
|-------|-------|-------------------------------------|
| ADDR  | 6 Bit | Decimal (0 - 63)<br>Hex ($0 - $3F)<br>Symbolic |

### Instruction Coding
**00000000000000000000000000000101**

### Example
```assembly
    ldax adcl       ; ADC left input -> ACC
```

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*