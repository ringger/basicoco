# BasiCoCo

An educational BASIC programming environment inspired by the TRS-80 Color Computer. Type BASIC, see what happens, and learn from mistakes — every error message tells you what went wrong and how to fix it.

This is not a hardware emulator. If you want to run real CoCo software, see [Related Projects](#related-projects). This project is for learning BASIC in a CoCo-flavored dialect with a modern interface and helpful feedback.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-blue)

## Why This Exists

The original TRS-80 Color Computer responded to mistakes with `?SN ERROR` — two cryptic characters and a question mark. Forty years later, we can do better.

This environment keeps the CoCo BASIC dialect but replaces the frustration with 145+ educational error messages:

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

The dual-monitor web interface puts your REPL and graphics side by side — something the original hardware couldn't do with a single composite video output.

## Quick Start

```bash
git clone https://github.com/ringger/basicoco.git
cd basicoco
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open `http://localhost:5001` for the dual monitor interface.

For a standalone terminal REPL (no server needed): `python basicoco.py`

For the CLI client (requires server): start the server in one terminal and run `python cli_client.py` in another.

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
30 X = 128 + 100 * COS(A * 3.14159 / 180)
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

## Language

The dialect is based on Extended Color BASIC as shipped with the CoCo 1 and CoCo 2, with modern quality-of-life additions.

### From Extended Color BASIC
- **Core**: NEW, RUN, LIST, END, STOP, CONT, CLEAR, LOAD, SAVE, FILES, KILL, TRON/TROFF
- **I/O**: PRINT (with separators), INPUT (with prompts, multi-variable), CLS, INKEY$
- **Variables**: Numeric and string variables, operators (+, -, *, /, ^, comparisons)
- **Control Flow**: FOR/NEXT (with STEP), IF/THEN, GOTO, GOSUB/RETURN, ON GOTO/GOSUB, ON ERROR GOTO/RESUME
- **Data**: DATA/READ/RESTORE
- **Math**: ABS, INT, SGN, SQR, SIN, COS, TAN, ATN, EXP, LOG, RND, RANDOMIZE, TIMER
- **Strings**: LEN, LEFT$, RIGHT$, MID$, CHR$, ASC, STR$, VAL, STRING$, INSTR, SPACE$, HEX$, OCT$
- **Arrays**: DIM with multi-dimensional support (DIM A(10) creates indices 0-10, as on the real CoCo)
- **Graphics**: PMODE, SCREEN, PCLS, PSET, PRESET, PPOINT, LINE, CIRCLE, PAINT, GET/PUT, DRAW (with B/N/S modifiers)
- **File I/O**: OPEN, CLOSE, PRINT#, INPUT#, LINE INPUT, EOF
- **Sound**: SOUND command (note: accepts frequency in Hz rather than the CoCo's 1-255 pitch table)

### Modern Extensions
These were not in Extended Color BASIC but make the environment more learner-friendly:

- **MOD** operator for modular arithmetic
- **EXIT FOR** to break out of FOR/NEXT loops early
- **WHILE/WEND** and **DO/LOOP** (with WHILE/UNTIL) structured loop constructs
- **IF/THEN/ELSE/ENDIF** multi-line conditional blocks
- **PAUSE** *n* — delay execution for *n* seconds (real CoCo used busy loops)
- **Single-line compound statements** like `IF A=1 THEN FOR I=1 TO 3: PRINT I: NEXT I`

### Not Yet Implemented
See [ISSUES.md](ISSUES.md) for the full list. Highlights: PEEK/POKE, PCLEAR, random-access file I/O (FIELD/GET/PUT).

## Interfaces

- **Dual Monitor Web UI**: Split-screen with persistent REPL (left) and dedicated graphics display (right), resizable panels, multi-tab support with independent sessions
- **CLI Client**: Terminal-based interface with real-time streaming output
- **Rainbow Cursor**: CoCo-style color cycling
- **Keyboard**: Command line editing with Emacs bindings, Ctrl+C interrupt, tab completion

## Differences from Real Hardware

This is a BASIC interpreter, not a hardware emulator. It doesn't emulate the 6809 CPU, MC6847 VDG, or memory map. Notable differences:

- **Error messages** are educational rather than authentic (`?SN ERROR`)
- **Graphics** are VDG-inspired but simplified — no CSS-based 4-color set switching, approximate PMODE 0/2 resolutions
- **SOUND** accepts frequency in Hz (1-4095) rather than the CoCo's pitch table values (1-255)
- **PRINT** spacing doesn't exactly match hardware behavior (number padding, 16-column comma zones)
- **Modern extensions** (MOD, EXIT FOR, WHILE/WEND, DO/LOOP, PAUSE) are additions beyond the original ROM
- Can't run real CoCo binaries, cassette images, or disk images

## Related Projects

If you're looking for authentic hardware emulation or other BASIC environments:

### CoCo Hardware Emulators
- **[XRoar](http://www.6809.org.uk/xroar/)** — The standard Dragon/CoCo emulator. Cycle-accurate 6809 emulation, runs real ROM images and software. Available as [XRoar Online](https://colorcomputerarchive.com/xroar-online/) in the browser via WebAssembly.
- **[trs80gp](http://48k.ca/trs80gp.html)** — Emulates nearly every TRS-80 variant including CoCo 1/2/3.
- **[Color Computer Archive](https://colorcomputerarchive.com/repo/Emulators/)** — Repository of CoCo emulators, ROM images, and software.

### Other BASIC Interpreters
- **[EndBASIC](https://www.endbasic.dev/)** — Educational BASIC in the browser (Rust/WASM). Modern dialect with a retro-styled terminal.
- **[RetroBASIC](https://github.com/maurymarkowitz/RetroBASIC)** — C-based interpreter that runs 1970s/80s BASIC programs across many dialects (MS-BASIC, Dartmouth, HP).

### Community
- **[CoCopedia](https://www.cocopedia.com/wiki/index.php/Emulators)** — The Color Computer wiki with comprehensive emulator listings.
- **[Glenside Color Computer Club](https://www.glensideccc.com/)** — Active CoCo community with online emulator links.

## Architecture

```
basicoco/
├── app.py                  # Flask web server
├── basicoco.py             # Standalone CLI REPL (no server needed)
├── cli_client.py           # Terminal-based CLI client
├── emulator/
│   ├── core.py             # Main CoCoBasic interpreter and command dispatch
│   ├── program_executor.py # Program execution loop and flow control
│   ├── file_manager.py     # File I/O: LOAD, SAVE, DIR, KILL, CD
│   ├── parser.py           # Command parsing and tokenization
│   ├── ast_parser.py       # AST node types, parser, and evaluator
│   ├── ast_converter.py    # Single-line to multi-line control structure conversion
│   ├── expressions.py      # Function registry
│   ├── functions.py        # BASIC function implementations (all registered here)
│   ├── commands.py         # Command registry
│   ├── graphics.py         # Graphics commands and VDG-inspired emulation
│   ├── file_io.py          # Sequential file I/O (OPEN, CLOSE, PRINT#, INPUT#, EOF)
│   ├── variables.py        # Variable/array management (DIM, array access)
│   ├── error_context.py    # Educational error reporting
│   └── output_manager.py   # Output streaming
├── programs/               # BASIC program files (.bas)
├── templates/              # HTML templates (dual monitor interface)
├── static/                 # CSS, JavaScript, audio support
└── tests/
    ├── unit/               # Unit tests
    └── integration/        # Integration and e2e tests
```

The interpreter is implemented in Python and is designed to be readable. If you're interested in how interpreters work — AST parsing, expression evaluation, control flow stacks — the codebase is a working example at a manageable scale.

### Command Dispatch

BASIC's syntax is deeply context-dependent — `A(5)` could be an array or a function call, `LINE` could be graphics or `LINE INPUT`, and `PRINT#` uses a `#` that has no meaning elsewhere. The interpreter handles this with a layered dispatch model that balances static analysis with runtime flexibility:

1. **Runtime intercepts** catch constructs the parser can't handle structurally — bare multi-line `IF...THEN`, file I/O with `#` syntax (`PRINT#`, `INPUT#`), and `LINE INPUT` (which would otherwise match the graphics `LINE` command).
2. **AST parsing** handles the core control flow and I/O commands (IF, FOR, WHILE, DO, GOTO, GOSUB, PRINT, INPUT, LET, END) — these are fully parsed into typed AST nodes and executed by the evaluator.
3. **Command registry** handles everything else — loop closers (NEXT, WEND, LOOP), data commands (DATA, READ, RESTORE), graphics, sound, and system commands. These use string-based argument splitting before passing to `evaluate_expression()`.

Single-line compound statements like `IF A=1 THEN B=2: C=3` are expanded into multi-line form at store-time by the AST converter, then executed as multi-line code. See [ISSUES.md](ISSUES.md) for planned improvements to this pipeline.

## Testing

1086 tests passing.

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=emulator --cov-report=term-missing

# Run unit tests only
python -m pytest tests/unit/ -v
```

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
- The CoCo community for keeping this platform alive four decades on
