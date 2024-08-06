## `LOG C, D`

------------------

`LOG` will multiply the Base2 `LOG` of the current absolute value in `ACC` with `C` and add the constant `D` to
the result.

It is important to note that the `LOG` function returns a fixed point number in S4.19 format instead of the standard S.23 format, which in turn means that the most negative Base2 `LOG` value is -16.

The `LOG` instruction can handle absolute linear accumulator values from 0.99999988 to 0.00001526 which translates to a dynamic range of apx. 96dB.

`D` is an offset to be added to the logarithmic value in the range of -16 to + 15.999998.

### Operation
`C * LOG(|ACC|) + D`

### Parameters
| Name  | Width | Entry formats, range                |
|-------|-------|-------------------------------------|
| C     | 16 Bit| Real (S1.14)<br>Hex ($0000 - $FFFF)<br>Symbolic |
| D     | 11 Bit| Real (S4.6)<br>Symbolic |

### Instruction Coding
**CCCCCCCCCCCCCCCCDDDDDDDDDDD01011**

### Example
```assembly
log 1.0,0
```

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*