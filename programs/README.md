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

### Rubik's Cube
- **rubiks_cube.bas** - 3D Rubik's cube in isometric projection (MERGEs `lib_rubiks_faces.bas`)
- **rubiks_cube_rotate.bas**, **rubiks_subcubes.bas** - self-contained rotation / subcube rendering demos
- **rubiks_scramble.bas** - animated scramble (MERGEs `lib_rubiks_engine.bas`)
- **rubiks_interactive.bas** - turn faces from the keyboard (MERGEs `lib_rubiks_engine.bas`)
- **rubiks_solve.bas** - scrambles, then solves with the 7-step beginner's method, animated (MERGEs the engine and `lib_rubiks_solver.bas`)
- **rubiks_test_moves.bas** - move-engine test harness

### Libraries (`lib_*`)
Shared code that other programs pull in with `MERGE`. Libraries use labels (`DrawCube:`) and no line numbers — LOAD/MERGE/CHAIN auto-number unnumbered lines — and are not meant to be RUN on their own.
- **lib_rubiks_faces.bas** - face drawing
- **lib_rubiks_engine.bas** - cube state, moves, `DoMoves`, animation
- **lib_rubiks_solver.bas** - solver steps (see `docs/rubiks_solver_plan.md`)

## Loading Programs

Use the `LOAD` command in the CLI or web interface:

```basic
LOAD "lunar_lander"        # Loads lunar_lander.bas (auto-adds .bas extension)
LOAD "lunar_lander.bas"    # Explicit filename
LIST                       # View the loaded program
RUN                        # Execute the program
```

## File Search Order

File commands are sandboxed: names are resolved inside the `programs/` directory (absolute paths, `~` and `..` are rejected). LOAD, MERGE and CHAIN look in:
1. The current `CD` directory inside the writable `programs/` directory
2. The bundled project `programs/` directory

SAVE, KILL and OPEN-for-output only ever touch the writable directory.

## Creating New Programs

1. Create a new `.bas` file in this directory
2. Use line numbers (10, 20, 30, etc.), or omit them and use labels — unnumbered lines are auto-numbered on load
3. Save and load with the `LOAD` command

Or use the SAVE command from the emulator:
```basic
10 PRINT "HELLO, WORLD!"
20 END
SAVE "myprogram"
```

## Supported BASIC Features

See the main project README for a complete list of implemented BASIC commands and functions.
