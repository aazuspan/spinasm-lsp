## `MEM`

------------------

The `MEM` Statement allows the user to partition the delay ram memory into individual blocks. A memory block declared by the statement

```assembly
Name `MEM` Size [;Comment]
```

can be referenced by `Name` from within an instruction line. `Name` has to comply with the same syntactical rules previously defined with the EQU statement, "Size" is an unsigned integer in the range of 1 to 32768 which might be entered either in decimal or in hexadecimal.

Besides the explicit identifier `Name` the assembler defines two additional implicit identifiers, `Name#` and `Name^`. `Name` refers to the first memory location within the memory block, whereas `Name#` refers to the last memory location. The identifier `Name^` references the middle of the memory block, or in other words its center. If a memory block of size 1 is defined, all three identifiers will address the same memory location. In case the memory block is of size 2, `Name` and `Name^` will address the same memory location, if the size is an even number the memory block cannot exactly be halved – the midpoint `Name^` will be calculated as: `size MOD 2`.

Optionally all three identifiers can be offset by a positive or negative integer which is entered in decimal. Although range checking is performed when using offsets, there is no error generated if the result of the address calculation exceeds the address range of the memory block. This is also true for those cases in which the result will "wrap around" the physical 32k boundary of the delay memory. However, a warning will be issued in order to alert the user regarding the out of range condition.

Mapping the memory blocks to their physical delay ram addresses is solely handled by SPINAsm. The user has no possibility to explicitly force SPINAsm to place a certain memory block to a specific physical address range. This of course does not mean that the user has no control over the layout of the delay ram at all: Knowing that SPINAsm will map memory blocks in the order they become defined within the source file, the user can implicitly control the memory map of the delay ram.

### Example
```assembly
DelR      MEM  1024    ; Right channel delay line
DelL      MEM  1024    ; Left channel delay line
                       ;
;------------------------------
sof       0,0          ; Clear ACC
rdax      ADCL,1.0     ; Read in left ADC
wra       DelL,0.25    ; Save it to the start of the left delay
                       ; line and keep a -12dB replica in ACC
rdax      DelL^+20,0.25; Add sample from "center of the left delay
                       ; line + 20 samples" times 0.25 to ACC
rdax      DelL#,0.25   ; Add sample from "end of the left delay
                       ; line" times 0.25 to ACC
rdax      DelL-512,0.25; Add sample from "start of the left delay
                       ; line - 512 samples" times 0.25 to ACC
```

### Remark
At this point the result of the address calculation will reference a sample from outside the `DelL` memory block. While being syntactically correct, the instruction might not result in what the user intended. In order to make the user aware of that potential semantic error, a warning will be issued.

```assembly
wrax      DACL,0       ; Result to DACL, clear ACC
                       ;
rdax      ADCR,1.0     ; Read in right ADC
wra       DelR,0.25    ; Save it to the start of the right delay
                       ; line and keep a -12dB replica in ACC
rdax      DelR^-20,0.25; Add sample from center of the right delay
                       ; line - 20 samples times 0.25 to ACC
rdax      DelR#,0.25   ; Add sample from end of the right delay line
                       ; times 0.25 to ACC
rdax      DelR-512,0.25; Add sample from start of the right delay
                       ; line - 512 samples times 0.25 to ACC
```

### Remark
At this point the result of the address calculation will reference a sample from outside the `DelR` memory block. And even worse than the previous case: This time the sample be fetched from delay ram address 32256 which will contain a sample that is apx. 1 second old!

Again, syntactically correct but most likely a semantic error – warnings will be issued.

```assembly
wrax DACR,0         ; Result to DACR, clear ACC
```

------------------
*Adapted from Spin Semiconductor SPINAsm & FV-1 Instruction Set reference manual. Copyright 2008 by Spin Semiconductor.*