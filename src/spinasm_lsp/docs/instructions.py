"""Markdown documentation generation for SpinASM instructions."""

# ruff: noqa: E501

from __future__ import annotations

from spinasm_lsp.docs.markdown import Arg, ArgList, Instruction

INSTRUCTIONS: dict[str, Instruction] = {
    "ABSA": Instruction(
        name="ABSA",
        args=ArgList([]),
        description="""**`ABSA`** loads the accumulator with the absolute value of the accumulator.""",
        parameter_description=None,
        operation="|ACC| ­> ACC",
        coding="00000000000000000000000000001001",
        example="""    absa            ; Absolute value of ACC -> ACC
""",
    ),
    "AND": Instruction(
        name="AND",
        args=ArgList(
            [
                Arg("MASK", 24, ["Binary", "Hex ($000000-$FFFFFF)", "Symbolic"]),
            ]
        ),
        description="""**`AND MASK`** will perform a bit wise "and" of the current `ACC` and the 24-­bit `MASK` specified within the instruction word. The instruction might be used to load a constant into `ACC` provided `ACC` contains `$FFFFFF` or to clear `ACC` if `MASK` equals `$000000`. (see also the pseudo opcode section)""",
        parameter_description=None,
        operation="ACC & MASK",
        coding="MMMMMMMMMMMMMMMMMMMMMMMM000001110",
        example="""AMASK EQU $F0FFFF

;----------------------------------------
    or ­­­­­­­­­­­­­­­­­­$FFFFFF                        ; Set all bits within ACC
    and $FFFFFE                       ; Clear LSB
    and %01111111_11111111_11111111   ; Clear MSB
    and AMASK                         ; Clear ACC[19..16]
    and $0                            ; Clear ACC
""",
    ),
    "CHO RDA": Instruction(
        name="CHO RDA",
        args=ArgList(
            [
                Arg("N", 2, ["LFO select: SIN0,SIN1,RMP0,RMP1"]),
                Arg("C", 6, ["Binary", "Bit flags"]),
                Arg("D", 16, ["Real (S.15)", "Symbolic"]),
            ]
        ),
        description="""**`CHO RDA, N, C, D`**, like the `RDA` instruction, will read a sample from the delay ram, multiply it by a coefficient and add the product to the previous content of `ACC`. However, in contrast to `RDA` the coefficient is not explicitly embedded within the instruction and the effective delay ram address is not solely determined by the address parameter. Instead, both values are modulated by the selected LFO at run time, for an in depth explanation please consult the FV­1 datasheet alongside with application note AN­0001. `CHO RDA` is a very flexible and powerful instruction, especially useful for delay line modulation effects such as chorus or pitch shifting.

The coefficient field of the `CHO` instructions are used as control bits to select various aspects of the LFO. These bits can be set using predefined flags that are `OR`ed together to create the required bit field. For a sine wave LFO (`SIN0` or `SIN1`), valid flags are:

`SIN COS REG COMPC COMPA`

While for a ramp LFO (RMP0 and RMP1), valid flags are:

`REG COMPC COMPA RPTR2 NA`

These flags are defined as:

| Flag  | HEX value | Description                                              |
| ----- | --------- | -------------------------------------------------------- |
| SIN   | $0        | Select SIN output (default) (Sine LFO only)              |
| COS   | $1        | Select COS output (Sine LFO only)                        |
| REG   | $2        | Save the output of the LFO into an internal LFO register |
| COMPC | $4        | Complement the coefficient (1-coeff)                     |
| COMPA | $8        | Complement the address offset from the LFO               |
| RPTR2 | $10       | Select the ramp+1/2 pointer (Ramp LFO only)              |
| NA    | $20       | Select x-fade coefficient and do not add address offset  |""",
        parameter_description=None,
        operation="See description",
        coding="00CCCCCC0NNAAAAAAAAAAAAAAAA10100",
        example="""; A chorus
Delay MEM 4097                          ; Chorus delay line
Amp EQU 8195                            ; Amplitude for a 4097 sample delay line
Freq EQU 51                             ; Apx. 2Hz at 32kHz sampling rate

; Setup SIN LFO 0
    skp run,cont                        ; Skip if not first iteration
    wldr 0,Freq,Amp                     ; Setup SIN LFO 0

cont:
    sof 0,0                             ; Clear ACC
    rdax ADCL,1.0                       ; Read left ADC * 1.0
    wra Delay,0                         ; Write to delay line, clear ACC
    cho rda,RMP0,COMPC|REG,Delay        ; See application note AN-0001
    cho rda,RMP0,,Delay+1               ; for detailed examples and explanation
    wra Temp,0                          ;
    cho rda,RMP0,COMPC|RPTR2,Delay      ;
    cho rda,RMP0,RPTR2,Delay+1          ;
    cho sof,RMP0,NA|COMPC,0             ;
    cho rda,RMP0,NA,Temp                ;
    wrax DACL,0                         ; Result to DACL and clear ACC
""",
    ),
    "CHO RDAL": Instruction(
        name="CHO RDAL",
        args=ArgList(
            [
                Arg("N", 2, ["LFO select: SIN0,COS0,SIN1,COS1,RMP0,RMP1"]),
            ]
        ),
        description="""**`CHO RDAL, N`** will read the current value of the selected LFO into `ACC`.""",
        parameter_description=None,
        operation="LFO * 1 ­> ACC",
        coding="110000100NN000000000000000010100",
        example="""cho rdal,SIN0           ; Read LFO S0 into ACC
wrax DACL,0             ; Result to DACL and clear ACC
""",
    ),
    "CHO SOF": Instruction(
        name="CHO SOF",
        args=ArgList(
            [
                Arg("N", 2, ["LFO select: SIN0,SIN1,RMP0,RMP1"]),
                Arg("C", 6, ["Binary", "Bit flags"]),
                Arg("D", 16, ["Real (S.15)", "Symbolic"]),
            ]
        ),
        description="""**`CHO SOF, N, C, D`**, like the `SOF` instruction, will multiply ACC by a coefficient and add the constant `D` to the result. However, in contrast to `SOF` the coefficient is not explicitly embedded within the instruction. Instead, based on the selected LFO and the 6 bit vector `C`, the coefficient is picked from a list of possible coefficients available within the LFO block of the FV­1. For an in depth explanation please consult the FV­-1 datasheet alongside with application note AN­0001. `CHO SOF` is a very flexible and powerful instruction, especially useful for the cross fading portion of pitch shift algorithms.

Please see `CHO RDA` for a description of field flags.""",
        parameter_description=None,
        operation="See description",
        coding="10CCCCCC0NNDDDDDDDDDDDDDDDD10100",
        example="""; Pitch shift
Delay MEM 4096                          ; Pitch shift delay line
Temp MEM 1                              ; Temporary storage
Amp EQU 4096                            ; RAMP LFO amplitude (4096 samples)
Freq EQU -8192                          ; RAMP LFO frequency

; Setup RAMP LFO 0
    skp run,cont                        ; Skip if not first iteration
    wldr 0,Freq,Amp                     ; Setup RAMP LFO 0

cont:
    sof 0,0                             ; Clear ACC
    rdax ADCL,1.0                       ; Read left ADC * 1.0
    wra Delay,0                         ; Write to delay line, clear ACC
    cho rda,RMP0,COMPC|REG,Delay        ; See application note AN-0001
    cho rda,RMP0,,Delay+1               ; for detailed examples and explanation
    wra Temp,0                          ;
    cho rda,RMP0,COMPC|RPTR2,Delay      ;
    cho rda,RMP0,RPTR2,Delay+1          ;
    cho sof,RMP0,NA|COMPC,0             ;
    cho rda,RMP0,NA,Temp                ;
    wrax DACL,0                         ; Result to DACL and clear ACC
""",
    ),
    "CLR": Instruction(
        name="CLR",
        args=ArgList([]),
        description="""**`CLR`** will clear the accumulator.""",
        parameter_description=None,
        operation="0 ­> ACC",
        coding="00000000000000000000000000001110",
        example="""    clr                 ; Clear ACC
    rdax ADCL,1.0       ; Read left ADC
                        ;-----------------
    ....                ; ...Left channel processing...
                        ;-----------------
    wrax DACL,0         ; Result to DACL and clear ACC
""",
    ),
    "EXP": Instruction(
        name="EXP",
        args=ArgList(
            [
                Arg("C", 16, ["Real (S1.14)", "Hex ($0000-$FFFF)", "Symbolic"]),
                Arg("D", 11, ["Real (S.10)", "Symbolic"]),
            ]
        ),
        description="""**`EXP C, D`** will multiply `2^ACC` with `C` and add the constant `D` to the result.

Since `ACC` (in it’s role as the destination for the `EXP` instruction) is limited to linear values from 0 to
+0.99999988, the `EXP` instruction is limited to logarithmic `ACC` values (in it’s role as the source operand
for the `EXP` instruction) from –16 to 0. Like the LOG instruction, `EXP` will treat the `ACC` content as a
S4.19 number. Positive logarithmic `ACC` values will be clipped to +0.99999988 which is the most positive
linear value that can be represented within the accumulator.

`D` is intended to allow the linear `ACC` to be offset by a constant in the range from –1 to +0.9990234375""",
        parameter_description=None,
        operation="C * EXP(ACC) + D",
        coding="CCCCCCCCCCCCCCCCDDDDDDDDDDD01100",
        example="""exp 0.8,0
""",
    ),
    "JAM": Instruction(
        name="JAM",
        args=ArgList(
            [
                Arg("N", 1, ["RAMP LFO select: (0, 1)"]),
            ]
        ),
        description="""**`JAM N`** will reset the selected RAMP LFO to its starting point.""",
        parameter_description=None,
        operation="0 ­> RAMP LFO N",
        coding="0000000000000000000000001N010011",
        example="""jam 0           ; Force ramp 0 LFO to it's starting position
""",
    ),
    "LDAX": Instruction(
        name="LDAX",
        args=ArgList(
            [
                Arg("ADDR", 6, ["Decimal (0-63)", "Hex ($0-$3F)", "Symbolic"]),
            ]
        ),
        description="""**`LDAX ADDR`** loads `ACC` with the contents of the addressed register `ADDR`.""",
        parameter_description=None,
        operation="REG[ADDR]­> ACC",
        coding="00000000000000000000000000000101",
        example="""    ldax adcl       ; ADC left input -> ACC
""",
    ),
    "LOG": Instruction(
        name="LOG",
        args=ArgList(
            [
                Arg("C", 16, ["Real (S1.14)", "Hex ($0000-$FFFF)", "Symbolic"]),
                Arg("D", 11, ["Real (S4.6)", "Symbolic"]),
            ]
        ),
        description="""**`LOG C, D`** will multiply the Base2 `LOG` of the current absolute value in `ACC` with `C` and add the constant `D` to the result.

It is important to note that the `LOG` function returns a fixed point number in `S4.19` format instead of the standard `S.23` format, which in turn means that the most negative Base2 `LOG` value is -16.

The `LOG` instruction can handle absolute linear accumulator values from 0.99999988 to 0.00001526 which translates to a dynamic range of apx. 96dB.

`D` is an offset to be added to the logarithmic value in the range of -16 to + 15.999998.""",
        parameter_description=None,
        operation="C * LOG(|ACC|) + D",
        coding="CCCCCCCCCCCCCCCCDDDDDDDDDDD01011",
        example="""log 1.0,0
""",
    ),
    "MAXX": Instruction(
        name="MAXX",
        args=ArgList(
            [
                Arg("ADDR", 6, ["Decimal (0-63)", "Hex ($0-$3F)", "Symbolic"]),
                Arg("C", 16, ["Real (S1.14)", "Hex ($8000-$0000-$7FFF)", "Symbolic"]),
            ]
        ),
        description="""**`MAXX ADDR, C`** will compare the absolute value of `ACC` versus C times the absolute value of the register pointed to by `ADDR`. If the absolute value of `ACC` is larger `ACC` will be loaded with `|ACC|`, otherwise the accumulator becomes overwritten by `|REG[ADDR] * C|`.""",
        parameter_description="""In order to simplify the MAXX syntax, see the list of predefined symbols for all registers within the FV-1 register file.""",
        operation="MAX( |REG[ADDR] * C| , |ACC| )",
        coding="CCCCCCCCCCCCCCCC00000AAAAAA01001",
        example="""; Peak follower
;
Peak EQU 32          ; Peak hold register

    sof 0,0          ; Clear ACC 
    rdax ADCL,1.0    ; Read left ADC
    maxx Peak,1.0    ; Keep larger absolute value in ACC

; For a peak meter insert decay code here...

    wrax Peak,0.0    ; Save (new) peak and clear ACC
""",
    ),
    "MULX": Instruction(
        name="MULX",
        args=ArgList(
            [
                Arg("ADDR", 6, ["Decimal (0-63)", "Hex ($0-$3F)", "Symbolic"]),
            ]
        ),
        description="""**`MULX ADDR`** will multiply `ACC` by the value of the register pointed to by `ADDR`. An important application of the `MULX` instruction is squaring the content of `ACC`, which combined with a single order LP is especially useful in calculating the RMS value of an arbitrary waveform.""",
        parameter_description="""In order to simplify the `MULX` syntax, see the list of predefined symbols for all registers within the FV-1 register file.""",
        operation="ACC * REG[ADDR]",
        coding="000000000000000000000AAAAAA01010",
        example="""; RMS conversion
Tmp_LP EQU 32        ; Temporary register for first order LP

    sof 0,0          ; Clear ACC 
    rdax ADCL,1.0    ; Read left ADC
                     ; RMS calculation = ACC^2 -> first order LP

    mulx ADCL        ; ACC^2
    rdfx Tmp_LP,x.x  ; First order...
    wrax Tmp_LP,1.0  ; ...LP filter

; At this point ACC holds the RMS value of the input
""",
    ),
    "NOT": Instruction(
        name="NOT",
        args=ArgList([]),
        description="""**`NOT`** will negate all bit positions within accumulator thus performing a 1’s complement.""",
        parameter_description=None,
        operation="/ACC ­> ACC",
        coding="11111111111111111111111100010000",
        example="""    not             ; 1's comp ACC
""",
    ),
    "OR": Instruction(
        name="OR",
        args=ArgList(
            [
                Arg("MASK", 24, ["Binary", "Hex ($000000-$FFFFFF)", "Symbolic"]),
            ]
        ),
        description="""**`OR MASK`** will perform a bit wise "or" of the current `ACC` and the 24-­bit `MASK` specified within the instruction word. The instruction might be used to load a constant into `ACC` provided `ACC` contains `$000000`.""",
        parameter_description=None,
        operation="ACC | MASK",
        coding="MMMMMMMMMMMMMMMMMMMMMMMM000001111",
        example="""0MASK EQU $0F0000

;----------------------------------------
    sof 0,0                           ; Clear all bits within ACC
    or $1                             ; Set LSB
    or %10000000_00000000_00000000    ; Set MSB
    or 0MASK                          ; Set ACC[19..16]
    and %S=[15..8]                    ; Set ACC[15..8]
""",
    ),
    "RDA": Instruction(
        name="RDA",
        args=ArgList(
            [
                Arg(
                    "ADDR",
                    (1) + 15,
                    ["Decimal (0-32767)", "Hex ($0-$7FFF)", "Symbolic"],
                ),
                Arg("C", 11, ["Real (S1.9)", "Hex ($400-$000-$3FF)", "Symbolic"]),
            ]
        ),
        description="""**`RDA ADDR, C`** will fetch the sample [ADDR] from the delay RAM, multiply it by `C`, and add the result to the previous content of `ACC`. This multiply-accumulate operation is probably the most popular operation found in DSP algorithms.""",
        parameter_description=None,
        operation="SRAM[ADDR] * C + ACC",
        coding="CCCCCCCCCCCAAAAAAAAAAAAAAAA00000",
        example="""Delay MEM 1024 
Coeff EQU 1.55
Tmp   EQU $2000

    rda 1000,1.9
    rda Delay+20,Coeff
    rda Tmp,-2
    rda $7FFF,$7FF
""",
    ),
    "RDAX": Instruction(
        name="RDAX",
        args=ArgList(
            [
                Arg("ADDR", 6, ["Decimal (0-63)", "Hex ($0-$3F)", "Symbolic"]),
                Arg("C", 16, ["Real (S1.14)", "Hex ($8000-$0000-$7FFF)", "Symbolic"]),
            ]
        ),
        description="""**`RDAX ADDR, C`** will fetch the value contained in `[ADDR]` from the register file, multiply it with `C` and add the result to the previous content of `ACC`. This multiply accumulate is probably the most popular operation found in DSP algorithms.""",
        parameter_description="""In order to simplify the `RDAX` syntax, see the list of predefined symbols for all registers within the FV-1 register file.""",
        operation="C * REG[ADDR] + ACC",
        coding="CCCCCCCCCCCCCCCC00000AAAAAA00100",
        example="""; Crude mono 
;
    sof 0,0          ; Clear ACC 
    rdax ADCL,0.5    ; Get ADCL value and divide it by two 
    rdax ADCR,0.5    ; Get ADCR value, divide it by two 
                     ; and add to the half of ADCL 
    wrax DACL,1.0    ; Result to DACL 
    wrax DACR,0      ; Result to DACR and clear ACC
""",
    ),
    "RDFX": Instruction(
        name="RDFX",
        args=ArgList(
            [
                Arg("ADDR", 6, ["Decimal (0-63)", "Hex ($0-$3F)", "Symbolic"]),
                Arg("C", 16, ["Real (S1.14)", "Hex ($8000-$0000-$7FFF)", "Symbolic"]),
            ]
        ),
        description="""**`RDFX ADDR, C`** will subtract the value of the register pointed to by `ADDR` from `ACC`, multiply the result by `C` and then add the value of the register pointed to by `ADDR`. `RDFX` is an extremely powerful instruction in that it represents the major portion of a single order low pass filter.""",
        parameter_description="""In order to simplify the `RDFX` syntax, see the list of predefined symbols for all registers within the FV-1 register file.""",
        operation="(ACC­REG[ADDR])*C + REG[ADDR]",
        coding="CCCCCCCCCCCCCCCC00000AAAAAA00101",
        example="""; Single order LP filter
Tmp_LP EQU 32        ; Temporary register for first order LP

    ldax ADCL        ; Read left ADC
    rdfx Tmp_LP,x.x  ; First order...
    wrax Tmp_LP,1.0  ; ...LP filter
    wrax DACL,0      ; Result to DACL and clear ACC
""",
    ),
    "RMPA": Instruction(
        name="RMPA",
        args=ArgList(
            [
                Arg("C", 11, ["Real (S1.9)", "Hex ($400-$000-$3FF)", "Symbolic"]),
            ]
        ),
        description="""**`RMPA C`** provides indirect delay line addressing in that the delay line address of the sample to be multiplied by `C` is not explicitly given in the instruction itself but contained within the pointer register `ADDR_PTR` (absolute address 24 within the internal register file.)

`RMPA` will fetch the indirectly addressed sample from the delay ram, multiply it by `C` and add the result to the previous content of `ACC`.""",
        parameter_description=None,
        operation="SRAM[PNTR[N]] * C + ACC",
        coding="CCCCCCCCCCC000000000001100000001",
        example="""; Crude variable delay line addressing
    sof 0,0             ; Clear ACC
    rdax POT1,1.0       ; Read POT1 value
    wrax ADDR_PTR,0     ; Write value to pointer register, clear ACC
    rmpa 1.0            ; Read sample from delay line
    wrax DACL,0         ; Result to DACL and clear ACC
""",
    ),
    "SKP": Instruction(
        name="SKP",
        args=ArgList(
            [
                Arg("CMASK", 5, ["Binary", "Hex ($00-$1F)", "Symbolic"]),
                Arg("N", 6, ["Decimal (1-63)", "Label"]),
            ]
        ),
        description="""**`SKP CMASK, N`** allows conditional program execution. The FV-1 features five condition flags that can be used to conditionally skip the next `N` instructions. The selection of which condition flag(s) must be asserted in order to skip the next `N` instructions is made by the five-bit condition mask `CMASK`. Only if all condition flags that correspond to a logic "1" within `CMASK` are asserted are the following `N` instructions skipped. The individual bits within `CMASK` correspond to the FV-1 condition flags as follows:

| CMASK | Flag | Description                                                                                                                                                                                                                                                                                             |
| ----- | ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| b4    | RUN  | The RUN flag is cleared after the program has executed for the first time after it was loaded into the internal program memory. The purpose of the RUN flag is to allow the program to initialize registers and LFOs during the first sample iteration then to skip those initializations from then on. |
| b3    | ZRC  | The ZRC flag is asserted if the sign of ACC and PACC is different, a condition that indicates a Zero Crossing.                                                                                                                                                                                          |
| b2    | ZRO  | Z is asserted if ACC = 0                                                                                                                                                                                                                                                                                |
| b1    | GEZ  | GEZ is asserted if ACC >= 0                                                                                                                                                                                                                                                                             |
| b0    | NEG  | N is asserted if ACC is negative                                                                                                                                                                                                                                                                        |""",
        parameter_description="""Maybe the most efficient way to define the condition mask is using its symbolic representation. In order to simplify the `SKP` syntax, SPINAsm has a predefined set of symbols which correspond to the name of the individual condition flags. (RUN, ZRC, ZRO, GEZ, NEG). Although most of the condition flags are mutually exclusive, SPINAsm allows you to specify more than one condition flag to become evaluated simply by separating multiple predefined symbols by the "|" character. Accordingly, `skp ZRC|N, 6` would skip the following six instructions in case of a zero crossing to a negative value.""",
        operation="CMASK N",
        coding="CCCCCNNNNNN000000000000000010001",
        example="""; A bridge rectifier
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
""",
    ),
    "SOF": Instruction(
        name="SOF",
        args=ArgList(
            [
                Arg("C", 16, ["Real (S1.14)", "Hex ($0000-$FFFF)", "Symbolic"]),
                Arg("D", 11, ["Real (S.10)", "Symbolic"]),
            ]
        ),
        description="""**`SOF C, D`** will multiply the current value in `ACC` with `C` and will then add the constant `D` to the result.

Please note the absence of an integer entry format for `D`. This is not by mistake but it should emphasize that `D` is not intended to become used for integer arithmetic. The reason for this instruction is that the 11 bit constant `D` would be placed into `ACC` left justified or in other words 13 bits shifted to the left. `D` is intended to offset `ACC` by a constant in the range from -1 to +0.9990234375.""",
        parameter_description=None,
        operation="C * ACC + D",
        coding="CCCCCCCCCCCCCCCCDDDDDDDDDDD01101",
        example="""Off EQU 1.0

; Halve way rectifier­­­
    sof 0,0                 ; Clear ACC
    rdax ADCL,1.0           ; Read from left ADC channel
    sof 1.0,­-Off            ; Subtract offset
    sof 1.0,Off             ; Add offset
""",
    ),
    "WLDR": Instruction(
        name="WLDR",
        args=ArgList(
            [
                Arg("N", 1, ["RAMP LFO select: (0, 1)"]),
                Arg(
                    "F",
                    16,
                    [
                        "Decimal (-16384-32768)",
                        "Hex ($4000-$000-$7FFF)",
                        "Symbolic",
                    ],
                ),
                Arg("A", 2, ["Decimal (512, 1024, 2048, 4096)", "Symbolic"]),
            ]
        ),
        description="""**`WLDR N, F, A`** will load frequency and amplitude control values into the selected RAMP LFO. (0 or 1) This instruction is intended to setup the selected RAMP LFO which is typically done within the first sample iteration after a new program became loaded. As a result `WLDR` will in most cases be used in combination with a `SKP RUN` instruction. For a more detailed description regarding the frequency and amplitude control values see application note AN­0001.""",
        parameter_description=None,
        operation="See description",
        coding="01NFFFFFFFFFFFFFFFF000000AA10010",
        example="""Amp EQU 4096            ; LFO will module a 4096 sample delay line
Freq EQU $100           ; 
;------------------------

; Setup RAMP LFO 0       ;
    skp run,start       ; Skip next instruction if not first iteration
    wldr 0,Freq,Amp     ; Setup RAMP LFO 0

start: and 0,0          ;
    ....                ;
    ....                ;
""",
    ),
    "WLDS": Instruction(
        name="WLDS",
        args=ArgList(
            [
                Arg("N", 1, ["SIN LFO select: (0, 1)"]),
                Arg("F", 9, ["Decimal (0-511)", "Hex ($000-$1FF)", "Symbolic"]),
                Arg("A", 15, ["Decimal (0-32767)", "Hex ($0000-$7FFF)", "Symbolic"]),
            ]
        ),
        description="""**`WLDS N, F, A`** will load frequency and amplitude control values into the selected SIN LFO (0 or 1). This instruction is intended to setup the selected SIN LFO which is typically done within the first sample iteration after a new program is loaded. As a result `WLDS` will in most cases be used in combination with a `SKP RUN` instruction. For a more detailed description regarding the frequency and amplitude control values see application note AN­0001.""",
        parameter_description=None,
        operation="See description",
        coding="00NFFFFFFFFFAAAAAAAAAAAAAAA10010",
        example="""Amp EQU 8194            ; Amplitude for a 4097 sample delay line
Freq EQU 51             ; Apx. 2Hz at 32kHz sampling rate
;------------------------

; Setup SIN LFO 0       ;
    skp run,start       ; Skip next instruction if not first iteration
    wlds 0,Freq,Amp     ; Setup SIN LFO 0

start: sof 0,0          ;
    ....                ;
    ....                ;
""",
    ),
    "WRA": Instruction(
        name="WRA",
        args=ArgList(
            [
                Arg(
                    "ADDR",
                    (1) + 15,
                    ["Decimal (0-32767)", "Hex ($0-$7FFF)", "Symbolic"],
                ),
                Arg("C", 11, ["Real (S1.9)", "Hex ($400-$000-$3FF)", "Symbolic"]),
            ]
        ),
        description="""**`WRA ADDR, C`** will store `ACC` to the delay ram location addressed by `ADDR` and then multiply `ACC` by `C`.""",
        parameter_description=None,
        operation="ACC­>SRAM[ADDR], ACC * C",
        coding="CCCCCCCCCCCAAAAAAAAAAAAAAAA00010",
        example="""Delay MEM 1024 
Coeff EQU 0.5

    sof 0,0             ; Clear ACC
    rdax ADCL,1.0       ; Read left ADC
    wra Delay,Coeff     ; Write to start of delay line, halve ACC
    rda Delay#,Coeff    ; Add half of the sample from the end of the delay line
    wrax DACL,0         ; Result to DACL and clear ACC
""",
    ),
    "WRAP": Instruction(
        name="WRAP",
        args=ArgList(
            [
                Arg(
                    "ADDR",
                    (1) + 15,
                    ["Decimal (0-32767)", "Hex ($0-$7FFF)", "Symbolic"],
                ),
                Arg("C", 11, ["Real (S1.9)", "Hex ($400-$000-$3FF)", "Symbolic"]),
            ]
        ),
        description="""**`WRAP ADDR, C`** will store `ACC` to the delay ram location addressed by `ADDR` then multiply `ACC` by `C` and finally add the content of the `LR` register to the product. Please note that the `LR` register contains the last sample value read from the delay ram memory. This instruction is typically used for all­pass filters in a reverb program.""",
        parameter_description=None,
        operation="ACC­>SRAM[ADDR], (ACC*C) + LR",
        coding="CCCCCCCCCCCAAAAAAAAAAAAAAAA00011",
        example="""    rda ap1#,kap        ; Read output of all-pass 1 and multiply it by kap
    wrap ap1,-kap       ; Write ACC to input of all-pass 1 and do
                        ; ACC*(-kap)+ap1# (ap1# is in LR register)
""",
    ),
    "WRAX": Instruction(
        name="WRAX",
        args=ArgList(
            [
                Arg("ADDR", 6, ["Decimal (0-63)", "Hex ($0-$3F)", "Symbolic"]),
                Arg("C", 16, ["Real (S1.14)", "Hex ($8000-$0000-$7FFF)", "Symbolic"]),
            ]
        ),
        description="""**`WRAX ADDR, C`** will save the current value in `ACC` to `[ADDR]` and then multiply `ACC` by `C`. This instruction can be used to write `ACC` to one DAC channel while clearing `ACC` for processing the next audio channel.""",
        parameter_description="""In order to simplify the `WRAX` syntax, see the list of predefined symbols for all registers within the FV­1.""",
        operation="ACC­>REG[ADDR], C * ACC",
        coding="CCCCCCCCCCCCCCCC00000AAAAAA00110",
        example="""; Stereo processing
;
    rdax ADCL,1.0    ; Read left ADC into previously cleared ACC
                     ;---------------
    ....             ; ...left channel processing
                     ;---------------
    wrax DACL,0      ; Result to DACL and clear ACC for right channel processing
    rdax ADCR,1.0    ; Read right ADC into previously cleared ACC
                     ;---------------
    ....             ; ...right channel processing
                     ;---------------
    wrax DACR,0      ; Result to DACR and clear ACC for left channel processing
""",
    ),
    "WRHX": Instruction(
        name="WRHX",
        args=ArgList(
            [
                Arg("ADDR", 6, ["Decimal (0-63)", "Hex ($0-$3F)", "Symbolic"]),
                Arg("C", 16, ["Real (S1.14)", "Hex ($8000-$0000-$7FFF)", "Symbolic"]),
            ]
        ),
        description="""**`WRHX ADDR, C`** stores the current `ACC` value in the register pointed to by `ADDR`, then multiplies `ACC` by `C`. Finally, the previous content of `ACC` (`PACC`) is added to the product. `WRHX` is an extremely powerful instruction; when combined with `RDFX`, it forms a single order high pass shelving filter.""",
        parameter_description="""In order to simplify the `WRHX` syntax, see the list of predefined symbols for all registers within the FV-1 register file.""",
        operation="ACC -> REG[ADDR], (ACC * C) + PACC",
        coding="CCCCCCCCCCCCCCCC00000AAAAAA00111",
        example="""; Single order HP shelving filter
Tmp_HP EQU 32       ; Temporary register for first order HP

;----------------------------------------

    sof 0,0         ; Clear ACC
    rdax ADCL,1.0   ; Read left ADC
    rdfx Tmp_HP,x.x ; First order HP...
    wrhx Tmp_HP,y.y ; ...shelving filter
    wrax DACL,0     ; Result to DACL and clear ACC
""",
    ),
    "WRLX": Instruction(
        name="WRLX",
        args=ArgList(
            [
                Arg("ADDR", 6, ["Decimal (0-63)", "Hex ($0-$3F)", "Symbolic"]),
                Arg("C", 16, ["Real (S1.14)", "Hex ($8000-$0000-$7FFF)", "Symbolic"]),
            ]
        ),
        description="""**`WRLX ADDR, C`** stores the current `ACC` value into the register pointed to by `ADDR`, then subtracts `ACC` from the previous content of `ACC` (`PACC`). The difference is then multiplied by C and finally `PACC` is added to the result. `WRLX` is an extremely powerful instruction in that when combined with `RDFX`, it forms a single order low-pass shelving filter.""",
        parameter_description="""In order to simplify the `WRLX` syntax, see the list of predefined symbols for all registers within the FV-1 register file.""",
        operation="ACC -> REG[ADDR], (PACC-ACC) * C + PACC",
        coding="CCCCCCCCCCCCCCCC00000AAAAAA01000",
        example="""; Single order LP shelving filter
Tmp_LP EQU 32       ; Temporary register for first order LP

;----------------------------------------

    sof 0,0         ; Clear ACC
    rdax ADCL,1.0   ; Read left ADC
    rdfx Tmp_LP,x.x ; First order LP...
    wrlx Tmp_LP,y.y ; ...shelving filter
    wrax DACL,1.0   ; Result to DACL and clear ACC
""",
    ),
    "XOR": Instruction(
        name="XOR",
        args=ArgList(
            [
                Arg("MASK", 24, ["Binary", "Hex ($000000-$FFFFFF)", "Symbolic"]),
            ]
        ),
        description="""**`XOR MASK`** will perform a bit wise "xor" of the current `ACC` and the 24­-bit `MASK` specified within the instruction word. The instruction will invert `ACC` provided `MASK` equals `$FFFFFF`. (see also the pseudo opcode section).""",
        parameter_description=None,
        operation="ACC ^ MASK",
        coding="MMMMMMMMMMMMMMMMMMMMMMMM000010000",
        example="""XMASK EQU $AAAAAA

;----------------------------------------
    sof 0,0                           ; Clear all bits within ACC
    xor $0                            ; Set all ACC bits
    xor %01010101_01010101_01010101   ; Invert all even numbered bits
    xor XMASK                          ; Invert all odd numbered bits
""",
    ),
}
