## `SKP CMASK,N`

------------------

The SKP instruction allows conditional program execution. The FV-1 features five condition flags that can be used to conditionally skip the next N instructions. The selection of which condition flag(s) must be asserted in order to skip the next N instructions is made by the five-bit condition mask "CMASK". Only if all condition flags that correspond to a logic "1" within CMASK are asserted are the following N instructions skipped. The individual bits within CMASK correspond to the FV-1 condition flags as follows:

| CMASK | Flag | Description |
| --- | --- | --- |
| b4 | RUN | The RUN flag is cleared after the program has executed for the first time after it was loaded into the internal program memory. The purpose of the RUN flag is to allow the program to initialize registers and LFOs during the first sample iteration then to skip those initializations from then on. |
| b3 | ZRC | The ZRC flag is asserted if the sign of ACC and PACC is different, a condition that indicates a Zero Crossing. |
| b2 | ZRO | Z is asserted if ACC = 0 |
| b1 | GEZ | GEZ is asserted if ACC >= 0 |
| b0 | NEG | N is asserted if ACC is negative |

### Operation
`CMASK N`

### Parameters
| Name | Width | Entry formats, range |
| --- | --- | --- |
| CMASK | 5 Bit | Binary<br>Hex ($00 - $1F)<br>Symbolic |
| N | 6 Bit | Decimal (1 - 63)<br>Label |

Maybe the most efficient way to define the condition mask is using its symbolic representation. In order to simplify the SKP syntax, SPINAsm has a predefined set of symbols which correspond to the name of the individual condition flags. (RUN, ZRC, ZRO, GEZ, NEG). Although most of the condition flags are mutually exclusive, SPINAsm allows you to specify more than one condition flag to become evaluated simply by separating multiple predefined symbols by the "|" character. Accordingly, "skp ZRC|N, 6" would skip the following six instructions in case of a zero crossing to a negative value.

### Instruction Coding
**CCCCCNNNNNN000000000000000010001**

### Example
```assembly
; A bridge rectifier
;
    sof 0,0          ; Clear ACC 
    rdax ADCL,1.0    ; Read from left ADC channel
    skp GEZ,pos      ; Skip next instruction if ACC >= 0
    sof -1.0,0       ; Make ACC positive
pos:
    wrax DACL,0      ; Result to DACL, clear ACC
    rdax ADCL,1.0    ; Read from left ADC channel
    skp N,neg        ; Skip next instruction if ACC < 0
    sof -1.0,0       ; Make ACC negative
neg:
    wrax 0,DACR      ; Result to DACR, clear
```

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*