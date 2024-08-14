# SPINAsm LSP Server

A Language Server Protocol (LSP) server to provide language support for the [SPINAsm assembly language](http://www.spinsemi.com/Products/datasheets/spn1001-dev/SPINAsmUserManual.pdf). The LSP is built on an extended version of the [asfv1](https://github.com/ndf-zz/asfv1) parser.

## Features

- **Diagnostics**: Reports the location of syntax errors and warnings.
- **Signature help**: Shows parameter hints as instructions are entered.
- **Hover**: Shows documentation and values on hover.
- **Completion**: Provides suggestions for opcodes, labels, and variables.
- **Renaming**: Allows renaming labels and variables.
- **Go to definition**: Jumps to the definition of a label, memory address, or variable.

------

*This project is unaffiliated with Spin Semiconductor. Included documentation is Copyright © 2018 Spin Semiconductor.*
