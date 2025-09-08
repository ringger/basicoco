# TRS-80 Color Computer BASIC Programs

This directory contains BASIC programs for the TRS-80 Color Computer emulator.

## Available Programs

### Animation Demos
- **bounce.bas** - Bouncing star animation (10 character width)
- **simple_bounce.bas** - Alternative bouncing animation using STRING$ function
- **bounce_demo.bas** - Original bouncing demo with @() positioning

## Loading Programs

Use the `LOAD` command in the CLI or web interface:

```basic
LOAD "bounce"              # Loads bounce.bas (auto-adds .bas extension)
LOAD "bounce.bas"          # Explicit filename
LOAD "programs/bounce"     # Explicit path (also works)
LIST                       # View the loaded program
RUN                        # Execute the program
```

## File Search Order

The LOAD command searches for programs in this order:
1. Current working directory
2. `programs/` subdirectory
3. Project root directory
4. Project root `programs/` directory

## Creating New Programs

1. Create a new `.bas` file in this directory
2. Use line numbers (10, 20, 30, etc.)
3. Save and load with the `LOAD` command

Example program structure:
```basic
10 REM MY PROGRAM
20 PRINT "HELLO, WORLD!"
30 END
```

## Supported BASIC Features

See the main project README for a complete list of implemented BASIC commands and functions.