# TRS-80 Color Computer BASIC Programs

This directory contains BASIC programs for the TRS-80 Color Computer emulator.

## Available Programs

### Demo Programs
- **lunar_lander.bas** - Classic lunar lander game
- **simple_lunar.bas** - Simplified lunar lander
- **bounce_pause.bas** - Bouncing animation with PAUSE command
- **blue_circle.bas** - Graphics circle demo
- **qix_beam.bas** - QIX-style beam animation
- **spiral.bas** - Spiral graphics pattern

## Loading Programs

Use the `LOAD` command in the CLI or web interface:

```basic
LOAD "lunar_lander"        # Loads lunar_lander.bas (auto-adds .bas extension)
LOAD "lunar_lander.bas"    # Explicit filename
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

Or use the SAVE command from the emulator:
```basic
10 PRINT "HELLO, WORLD!"
20 END
SAVE "myprogram"
```

## Supported BASIC Features

See the main project README for a complete list of implemented BASIC commands and functions.
