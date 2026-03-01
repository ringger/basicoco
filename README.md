# TRS-80 Color Computer BASIC Emulator

A TRS-80 Color Computer BASIC interpreter with a dual monitor web interface, standalone CLI client, authentic MC6847 VDG graphics emulation, and 145+ educational error messages.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-blue)

## Features

### BASIC Language Support
- **Core Commands**: NEW, RUN, LIST, END, STOP, CONT, CLEAR, LOAD, SAVE, FILES, KILL
- **I/O**: PRINT (with separators), INPUT (with prompts, multi-variable), CLS, INKEY$
- **Variables and Math**: Numeric and string variables, all operators (+, -, *, /, ^, MOD, comparisons)
- **Control Flow**: FOR/NEXT (with STEP), IF/THEN, GOTO, GOSUB/RETURN, ON GOTO/GOSUB, EXIT FOR, WHILE/WEND, DO/LOOP
- **Single-Line Control Structures**: Complex statements like `IF A=1 THEN FOR I=1 TO 3: PRINT I: NEXT I` automatically converted via AST
- **Data Processing**: DATA/READ/RESTORE
- **Math Functions**: ABS, INT, SQR, SIN, COS, TAN, ATN, EXP, LOG, RND
- **String Functions**: LEN, LEFT$, RIGHT$, MID$, CHR$, ASC, STR$, VAL
- **Arrays**: DIM with multi-dimensional support and authentic TRS-80 bounds behavior
- **Timing**: PAUSE command for animations and real-time programs

### Graphics and Sound
- **Graphics Modes**: PMODE 0-4 with authentic MC6847 VDG emulation
- **Drawing**: PSET, PRESET, LINE, CIRCLE, PAINT (flood fill), GET/PUT (sprites), DRAW (turtle graphics)
- **Color**: Authentic 9-color Color Computer palette
- **Sound**: SOUND command with Web Audio API and position-based frequency modulation

### Interfaces
- **Dual Monitor Web UI**: Split-screen with persistent REPL (left) and dedicated graphics display (right), resizable panels, multi-tab support with independent sessions
- **CLI Client**: Terminal-based interface with real-time streaming output
- **Rainbow Cursor**: Authentic TRS-80 CoCo color cycling
- **Keyboard**: Command line editing with Emacs bindings, Ctrl+C interrupt, tab completion

### Educational Error Messages
145+ context-aware error messages that teach BASIC programming:

```
DIM A(
> Missing closing parenthesis in DIM coordinates at line 0
> Suggestions:
>   - Correct syntax: DIM array_name(dimensions)
>   - Example: DIM A(10), B$(5,10)
>   - Make sure parentheses are properly matched

PRINT SQR(-4)
> Cannot calculate square root of negative number: -4.0 at line 0
> Suggestions:
>   - Square root is only defined for non-negative numbers
>   - Use ABS() if you want the square root of the absolute value
>   - Example: SQR(ABS(-9)) returns 3
```

## Quick Start

```bash
git clone https://github.com/ringger/trs80.git
cd trs80
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open `http://localhost:5000` for the dual monitor interface.

For the CLI client, start the server in one terminal and run `python cli_client.py` in another.

## Usage Examples

```basic
10 PRINT "HELLO, WORLD!"
20 FOR I = 1 TO 5
30 PRINT "COUNT: "; I
40 NEXT I
50 END
RUN
```

```basic
10 PMODE 4,1: SCREEN 1,1: PCLS
20 FOR A = 0 TO 360 STEP 10
30 X = 160 + 100 * COS(A * 3.14159 / 180)
40 Y = 96 + 60 * SIN(A * 3.14159 / 180)
50 C = INT(A / 45) MOD 8 + 1
60 PSET(X,Y),C
70 SOUND 200 + A * 2, 5
80 PAUSE 0.1
90 NEXT A
RUN
```

```basic
10 INPUT "WHAT IS YOUR NAME"; NAME$
20 PRINT "HELLO, "; NAME$; "!"
30 INPUT "ENTER A NUMBER"; NUM
40 PRINT "THE SQUARE ROOT OF "; NUM; " IS "; SQR(NUM)
RUN
```

Programs can be saved as `.bas` files in the `programs/` directory and loaded with `LOAD "filename"`.

## Architecture

```
trs80/
├── app.py                  # Flask web server
├── cli_client.py           # Terminal-based CLI client
├── emulator/
│   ├── core.py             # Main CoCoBasic interpreter
│   ├── parser.py           # Command parsing and tokenization
│   ├── ast_parser.py       # AST parser, node types, and ASTEvaluator for command execution
│   ├── ast_converter.py    # Single-line to multi-line control structure conversion
│   ├── expressions.py      # Expression evaluation
│   ├── functions.py        # BASIC function implementations
│   ├── commands.py         # Command registry
│   ├── error_context.py    # Educational error reporting
│   ├── output_manager.py   # Output streaming
│   ├── graphics.py         # Graphics commands and MC6847 VDG emulation
│   ├── variables.py        # Variable/array management (DIM, array access)
│   └── io.py               # I/O helpers (print formatting, argument splitting)
├── programs/               # BASIC program files (.bas)
├── templates/              # HTML templates (dual monitor interface)
├── static/                 # CSS, JavaScript, audio support
├── tests/
│   ├── unit/               # Unit tests
│   └── integration/        # Integration and e2e tests
└── dev_tests/              # Development utilities and smoke tests
```

## Testing

619 tests passing, 32 skipped (WebSocket tests require a running server).

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=emulator --cov-report=term-missing

# Run unit tests only
python -m pytest tests/unit/ -v

# Quick smoke test
python dev_tests/smoke_test.py --quick
```

## Authentic TRS-80 Behavior

- `DIM A(10)` creates 11 elements (indices 0-10)
- Authentic error messages (SYNTAX ERROR, OUT OF DATA, etc.)
- Accurate MC6847 VDG graphics modes and resolutions
- Correct PRINT semicolon and comma separator behavior
- Authentic string function behavior

## Roadmap

### Phase 1: State Management Architecture Enhancement
- Specialized state managers for variables, execution, I/O, and graphics
- Refactored state clearing policies for NEW, LOAD, RUN

### Phase 2: Disk BASIC File Operations
- OPEN/CLOSE for sequential and random access files
- FIELD, GET, PUT for random file access

### Phase 3: System Functions and Memory Simulation
- PEEK/POKE with simulated TRS-80 memory map
- VARPTR, MEM, TIMER, FRE(0), RANDOMIZE
- Machine language: EXEC, USR, LOADM, SAVEM

### Phase 4: Enhanced Disk BASIC Commands
- MERGE, RENAME, COPY, CLOADM/CSAVEM

### Phase 5: Error Handling and Recovery
- ON ERROR GOTO / RESUME, ERR, ERL

### Not Yet Implemented
HEX$, OCT$, PCLEAR, PPOINT, EOF, LOC, LOF, FREE, BACKUP, DSKINI, VERIFY, EDIT, LLIST, TRON/TROFF

See [CHANGELOG.md](CHANGELOG.md) for release history.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for your changes
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License. See [LICENSE](LICENSE) for details.

## Acknowledgments

- Original TRS-80 Color Computer designers at Tandy/Radio Shack
- Microsoft Color BASIC / Extended Color BASIC language specification
- MC6847 VDG chip documentation
