# SPINAsm LSP Server

A Language Server Protocol (LSP) server to provide language support for the [SPINAsm assembly language](http://www.spinsemi.com/Products/datasheets/spn1001-dev/SPINAsmUserManual.pdf). The LSP is built on an extended version of the [asfv1](https://github.com/ndf-zz/asfv1) parser.

## Features

- **Diagnostics**: Reports the location of syntax errors and warnings.
- **Hover**: Shows opcode documentation and assigned values on hover.
- **Completion**: Provides suggestions for opcodes, labels, and defined values.
- **Renaming**: Allows renaming of labels and defined values.
- **Go to definition**: Jumps to the definition of a label or defined value.

------

*This project is unaffiliated with Spin Semiconductor. Included documentation and examples are Copyright © 2018 Spin Semiconductor.*
