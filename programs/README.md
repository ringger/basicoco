# BasiCoCo Programs

This directory contains BASIC programs for BasiCoCo.

## Available Programs

### Games
- **guess_number.bas** - Number guessing game (GOSUB, INPUT, IF/ELSE, LEFT$, RND)
- **math_quiz.bas** - Math quiz game (WHILE/WEND, EXIT FOR, ABS, SGN, RANDOMIZE, RND)
- **lunar_lander.bas** - Classic lunar lander game
- **simple_lunar.bas** - Simplified lunar lander

### Interactive Tools
- **string_lab.bas** - String laboratory: Caesar cipher, word counter, base converter (MID$, ASC, CHR$, INSTR, VAL, STR$, SQR, RESTORE, ON...GOSUB)
- **sorting_demo.bas** - Bubble sort with subroutines (GOSUB/RETURN, DATA/READ, DIM, DO/LOOP, STRING$, ON...GOTO)
- **bar_chart.bas** - Bar chart visualization (DIM, INPUT, LEN, LEFT$, WHILE/WEND)
- **math_plotter.bas** - Math function plotter: sine, cosine, exp, sqrt, Lissajous, turtle star (SIN, COS, ATN, EXP, LOG, PMODE, SCREEN, LINE, DRAW, PAINT)

### File I/O
- **address_book.bas** - Contact manager with save/load (OPEN, CLOSE, PRINT#, INPUT#, LINE INPUT, EOF, ON ERROR GOTO)
- **graph_chart.bas** - Graphical bar chart from file data (OPEN, INPUT#, PRINT#, PMODE, LINE, PAINT, PSET, ON ERROR GOTO)

### Graphics Demos
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
