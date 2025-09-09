# TRS-80 Color Computer BASIC Emulator

A comprehensive TRS-80 Color Computer BASIC interpreter with both web interface and standalone CLI client, featuring authentic graphics emulation, real-time streaming output, and modern educational tools.

![Production Ready](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Test Coverage](https://img.shields.io/badge/Tests-339%2F339%20Passing-brightgreen)
![Success Rate](https://img.shields.io/badge/Success%20Rate-100%25-brightgreen)
![CLI Client](https://img.shields.io/badge/CLI-Real--time%20Streaming-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-blue)

## 🚀 Features

### Complete BASIC Language Support
- **Core Commands**: NEW, RUN, LIST, END, STOP, CONT, CLEAR, LOAD
- **I/O Operations**: PRINT (with separators), INPUT (with prompts), CLS
- **Variables & Math**: Numeric and string variables, all operators (+, -, *, /, ^, =, <, >, <=, >=, <>)
- **Control Flow**: FOR/NEXT loops (with STEP), IF/THEN, GOTO, GOSUB/RETURN, ON GOTO/GOSUB
- **Data Processing**: DATA/READ/RESTORE for structured data
- **Math Functions**: ABS, INT, SQR, SIN, COS, TAN, ATN, EXP, LOG, RND
- **String Functions**: LEN, LEFT$, RIGHT$, MID$, CHR$, ASC, STR$, VAL
- **Arrays**: DIM with multi-dimensional support and authentic TRS-80 bounds behavior
- **Modern Enhancements**: PAUSE command for precise timing control

### Advanced Graphics & Sound
- **Graphics Modes**: PMODE 0-4 with authentic MC6847 VDG emulation
- **Drawing Commands**: PSET, PRESET, LINE, CIRCLE with dual syntax support
- **Advanced Graphics**: PAINT (flood fill), GET/PUT (sprite operations), DRAW (turtle graphics)
- **Color Support**: Authentic 9-color Color Computer palette
- **Sound**: SOUND command with Web Audio API

### Interactive Features
- **INKEY$**: Non-blocking keyboard input with web interface integration
- **Real-time Display**: HTML5 Canvas with authentic CRT styling
- **WebSocket Communication**: Interactive keyboard and display updates
- **Standalone CLI Client**: Terminal-based interface with real-time streaming output
- **Program Management**: LOAD command with smart file discovery from programs/ directory
- **Real-time Animations**: Carriage return support and inline PRINT for smooth animations

## 🎯 Quick Start

### Prerequisites
- Python 3.8+
- Flask
- Flask-SocketIO

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd trs80
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install flask flask-socketio
   ```

4. **Run the emulator**
   
   **Web Interface:**
   ```bash
   python app.py
   ```
   Then navigate to `http://localhost:5000` in your browser
   
   **CLI Client (Alternative):**
   ```bash
   # In terminal 1 - Start server
   python app.py
   
   # In terminal 2 - Start CLI client
   python cli_client.py
   ```

## 💻 Usage Examples

### Basic Programming
```basic
10 PRINT "HELLO, WORLD!"
20 FOR I = 1 TO 5
30 PRINT "COUNT: "; I
40 NEXT I
50 END
RUN
```

### Graphics Programming
```basic
10 PMODE 1, 1: PCLS
20 CIRCLE 128, 96, 50
30 PAINT 128, 96, 2
40 FOR X = 0 TO 255 STEP 5
50 PSET X, 96, 3
60 NEXT X
RUN
```

### Array Operations
```basic
10 DIM NUMBERS(10)
20 FOR I = 0 TO 10
30 NUMBERS(I) = I * I
40 PRINT "SQUARE OF "; I; " IS "; NUMBERS(I)
50 NEXT I
RUN
```

### Interactive Input
```basic
10 INPUT "WHAT IS YOUR NAME"; NAME$
20 PRINT "HELLO, "; NAME$; "!"
30 INPUT "ENTER A NUMBER"; NUM
40 PRINT "THE SQUARE ROOT OF "; NUM; " IS "; SQR(NUM)
RUN
```

### Multi-Variable Input
```basic
10 INPUT "NAME, AGE, SCORE"; N$, A, S
20 PRINT N$; " IS "; A; " YEARS OLD"
30 PRINT "SCORED "; S; " POINTS"
RUN
```

### Program File Management
```basic
# Save your programs as .bas files in the programs/ directory
# Then load and run them:

LOAD "bounce_realtime"      # Load a program file
LIST                        # View the loaded program
RUN                        # Execute it

# Programs automatically searched in:
# - Current directory
# - programs/ subdirectory
```

### Real-Time Animation
```basic
10 REM BOUNCING STAR ANIMATION
20 CLS: POS = 1: DIR = 1
30 FOR I = 1 TO 20
40 PRINT "          "; CHR$(13);  # Clear line
50 LINE$ = ""
60 FOR J = 1 TO 10
70 IF J = POS THEN LINE$ = LINE$ + "*"
80 IF J <> POS THEN LINE$ = LINE$ + " "
90 NEXT J
100 PRINT LINE$; CHR$(13);       # Print star position
110 PAUSE 0.3                    # Real-time pause
120 POS = POS + DIR
130 IF POS = 10 THEN DIR = -1
140 IF POS = 1 THEN DIR = 1
150 NEXT I
RUN
```

## 🏗️ Architecture

### Core Components
- **Modular Architecture**: Clean separation of concerns across specialized modules
- **CoCoBasic Class**: Main interpreter orchestrating program storage and execution with real-time streaming
- **Advanced Parser**: Parentheses-aware parsing with complex expression evaluation and AST generation
- **Expression Evaluator**: Sophisticated expression parsing with function registry integration
- **Command Registry**: Plugin-like architecture for extensible command handling with metadata
- **Error Context System**: Structured error reporting with line numbers and suggestions
- **Output Manager**: Streaming output management with filtering and buffering capabilities
- **Graphics Engine**: HTML5 Canvas with authentic MC6847 VDG emulation and nested function support
- **Variable Manager**: Comprehensive variable and array handling with type validation
- **I/O System**: Multi-variable INPUT support and interactive keyboard integration
- **Web Interface**: Flask-SocketIO for real-time communication and responsive display
- **CLI Client**: Standalone terminal interface with real-time streaming output and program management

### File Structure
```
trs80/
├── app.py                 # Flask web application server with real-time streaming
├── cli_client.py          # Standalone CLI client with terminal interface
├── emulator/             # Core emulator modules
│   ├── core.py           # Main CoCoBasic interpreter class with streaming support
│   ├── parser.py         # Command parsing, tokenization, and AST generation
│   ├── expressions.py    # Expression evaluation with function registry
│   ├── functions.py      # BASIC function implementations (math, string, system)
│   ├── commands.py       # Command registry and plugin architecture
│   ├── error_context.py  # Structured error reporting system
│   ├── output_manager.py # Output streaming and management
│   ├── graphics.py       # Graphics commands and canvas operations
│   ├── variables.py      # Variable and array management
│   └── io.py            # Input/output command handling with inline PRINT support
├── programs/             # BASIC program files directory
│   ├── README.md         # Program directory documentation
│   ├── bounce_realtime.bas # Real-time bouncing star animation
│   └── test_streaming.bas  # Streaming output test program
├── templates/
│   └── index.html        # Web interface
├── static/
│   ├── style.css         # Styling with authentic CRT effects
│   └── script.js         # Client-side JavaScript
├── tests/
│   ├── unit/            # Unit tests for individual commands and components
│   ├── integration/     # Integration tests for complex programs
│   └── test_base.py     # Test framework base class with comprehensive assertions
├── dev_tests/           # Development and debugging utilities
│   ├── README.md        # Development test documentation
│   ├── smoke_test.py    # Quick functionality verification
│   └── debug_test_failures.py # Test debugging utilities
├── docs/
│   └── claude-code-architecture-reference.md  # Development tools reference
├── run_tests.py         # Comprehensive test runner
├── CLAUDE.md            # Development guide and roadmap
└── README.md           # This file
```

## 🚀 Recent Enhancements

### Phase 1.6 Complete: Enhanced Architecture & Test Coverage
- **Expanded Test Suite**: 339 comprehensive tests (up from 229) with 100% success rate
- **Advanced AST Parser**: Abstract Syntax Tree generation for complex expression evaluation
- **Enhanced Error Reporting**: Structured error context with line numbers and helpful suggestions
- **Plugin Architecture**: Extensible command registry with metadata and help system
- **Streaming Output Manager**: Real-time output filtering and buffering capabilities
- **Robust Expression Engine**: Sophisticated math and string expression evaluation
- **Comprehensive Function Library**: Complete implementation of all BASIC functions
- **IF/THEN Statement Enhancement**: Full support for multi-statement THEN clauses

### Latest Bug Fixes (January 2025)
- **Fixed IF/THEN Multi-Statement Parsing**: Resolved command registry detection issue for complex IF/THEN statements
- **Enhanced Command Registry**: Improved multi-statement detection with special case handling for IF statements
- **Test Organization**: Separated development utilities into `dev_tests/` directory for better organization

## 🧪 Testing

The emulator features **comprehensive test coverage** with **339 tests** achieving **100% success rate**.

### Quick Verification
```bash
# Fast smoke test for essential functionality
python dev_tests/smoke_test.py

# Quick mode for rapid verification
python dev_tests/smoke_test.py --quick
```

### Comprehensive Testing
```bash
# Run all test suites with detailed reporting
python run_tests.py

# Run with verbose output
python run_tests.py -v
```

### Specific Test Suites
```bash
python tests/unit/test_print_command.py
python tests/unit/test_graphics_commands.py
python tests/integration/test_complex_programs.py
```

### Test Categories
- **Unit Tests**: Individual command functionality (graphics, variables, I/O, parsing)
- **Integration Tests**: Complex program execution and multi-feature interaction
- **Architecture Tests**: Core component functionality (AST parser, command registry, error context)
- **Expression Tests**: Mathematical and string expression evaluation
- **Function Tests**: BASIC function implementations (math, string, system)
- **Error Recovery**: State consistency and error handling
- **Development Tests**: Debugging utilities and smoke tests

### Test Infrastructure
- **Base Framework**: Comprehensive assertion methods and utilities (`tests/test_base.py`)
- **Mock Systems**: Graphics, sound, and input simulation for isolated testing
- **Automated Discovery**: Recursive test file detection and execution
- **Detailed Reporting**: Success rates, failure analysis, and progress tracking

## 🎮 Authentic TRS-80 Behavior

This emulator faithfully recreates TRS-80 Color Computer BASIC behavior:

- **Array Dimensioning**: `DIM A(10)` creates 11 elements (indices 0-10)
- **Error Messages**: Authentic error messages (SYNTAX ERROR, OUT OF DATA, etc.)
- **Graphics Modes**: Accurate MC6847 VDG graphics modes and resolutions
- **PRINT Formatting**: Correct semicolon and comma separator behavior
- **String Handling**: Authentic string function behavior and formatting

## 🛠️ Development

### Adding New Features
1. Implement the feature in the `CoCoBasic` class
2. Add corresponding tests in `tests/unit/` or `tests/integration/`
3. Run the test suite to ensure no regressions
4. Update documentation

### Code Style
- Follow existing patterns and conventions
- Use descriptive variable names
- Add comments for complex logic
- Ensure all tests pass before committing

### Testing Guidelines
- Write tests for all new functionality
- Test both success and error cases
- Verify authentic TRS-80 behavior
- Maintain 100% test success rate

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for your changes
4. Ensure all tests pass
5. Submit a pull request

## 📚 Educational Use

This emulator is perfect for:
- **Teaching BASIC programming** with authentic vintage experience
- **Computer history education** demonstrating 1980s computing
- **Retro programming projects** with modern web accessibility and CLI convenience
- **Learning computer graphics** through simple BASIC commands
- **Real-time animations** and interactive programming demonstrations
- **Terminal-based development** with the standalone CLI client

## 🎓 Example Programs

### Graphics Demo
```basic
10 PMODE 1, 1: PCLS
20 FOR I = 1 TO 50
30 X = RND(256): Y = RND(192)
40 C = RND(4) + 1
50 CIRCLE X, Y, RND(20) + 5, C
60 NEXT I
RUN
```

### Data Processing
```basic
10 DATA "ALICE", 85, "BOB", 92, "CHARLIE", 78
20 TOTAL = 0: COUNT = 0
30 READ NAME$, SCORE
40 PRINT NAME$; ": "; SCORE
50 TOTAL = TOTAL + SCORE
60 COUNT = COUNT + 1
70 GOTO 30
80 PRINT "AVERAGE: "; TOTAL / COUNT
RUN
```

## 🔧 System Requirements

### Server Requirements
- Python 3.8 or higher
- 50MB disk space
- 256MB RAM minimum

### Browser Requirements (Web Interface)
- Modern web browser with WebSocket support
- HTML5 Canvas support
- Web Audio API support (for sound)

### CLI Client Requirements
- Terminal with ANSI escape sequence support
- Python readline library (usually included)
- Socket.IO client support (automatically installed)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Original TRS-80 Color Computer designers at Tandy/Radio Shack
- Microsoft BASIC-69 language specification
- MC6847 VDG chip documentation
- Modern web technologies: Flask, SocketIO, HTML5 Canvas

## 📞 Support

For questions, issues, or contributions:
- Create an issue in the project repository
- Check existing documentation and test cases
- Review the comprehensive test suite for usage examples

---

**Experience authentic 1980s computing with modern web accessibility!** 🖥️✨