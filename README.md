# TRS-80 Color Computer BASIC Emulator

A comprehensive TRS-80 Color Computer BASIC interpreter with revolutionary dual monitor web interface and standalone CLI client, featuring authentic graphics emulation, real-time streaming output, and modern educational tools.

![Production Ready](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Test Coverage](https://img.shields.io/badge/Tests-32%20Integration%20Tests-brightgreen)
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
- **Math Functions**: ABS, INT, SQR, SIN, COS, TAN, ATN, EXP, LOG, RND (with domain/range error detection)
- **String Functions**: LEN, LEFT$, RIGHT$, MID$, CHR$, ASC, STR$, VAL (with detailed error guidance)
- **Arrays**: DIM with multi-dimensional support and authentic TRS-80 bounds behavior
- **Modern Enhancements**: PAUSE command for precise timing control

### Advanced Graphics & Sound
- **Graphics Modes**: PMODE 0-4 with authentic MC6847 VDG emulation
- **Drawing Commands**: PSET, PRESET, LINE, CIRCLE with dual syntax support
- **Advanced Graphics**: PAINT (flood fill), GET/PUT (sprite operations), DRAW (turtle graphics)
- **Color Support**: Authentic 9-color Color Computer palette
- **Dynamic Sound**: SOUND command with Web Audio API and position-based frequency modulation
- **Audio Effects**: Real-time tone generation with reflection-triggered sound inflection

### Interactive Features
- **Dual Monitor Mode**: Revolutionary split-screen interface with persistent REPL and dedicated graphics display
- **Multi-Tab Support**: Independent BASIC sessions with separate programs and variables
- **INKEY$**: Non-blocking keyboard input with web interface integration  
- **Real-time Display**: HTML5 Canvas with authentic CRT styling and pixel-perfect cursor alignment
- **WebSocket Communication**: Interactive keyboard and display updates with Ctrl+C interrupt support
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
   Then navigate to `http://localhost:5000` for the dual monitor interface
   
   **CLI Client (Terminal-based):**
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

### Graphics Programming (Dual Monitor Mode)
```basic
10 PMODE 4,1: SCREEN 1,1  # High-resolution graphics mode
20 PCLS                   # Clear graphics display
30 CX = 128: CY = 96      # Center coordinates
40 FOR R = 1 TO 150 STEP 3
50   FOR A = 0 TO 360 STEP 15
60     X = CX + R * COS(A * 3.14159 / 180)
70     Y = CY + R * SIN(A * 3.14159 / 180) 
80     C = INT(A / 45) MOD 8 + 1
90     PSET(X,Y),C         # Colorful spiral
100    PAUSE 0.05          # Smooth animation
110  NEXT A
120 NEXT R
130 PRINT "SPIRAL COMPLETE!"
RUN
```

### Simple Blue Circle
```basic
10 PMODE 4,1: SCREEN 1,1: CIRCLE(128,96),50,3
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

### Comprehensive Error System  
The emulator provides **145+ educational, context-aware error messages** across all modules that help users learn:

```basic
# Enhanced DIM error with specific guidance:
DIM A(
> Missing closing parenthesis in DIM coordinates at line 0
> Suggestions:
>   - Correct syntax: DIM array_name(dimensions)
>   - Example: DIM A(10), B$(5,10)  
>   - Make sure parentheses are properly matched

# Graphics error with detailed explanation:
PSET(100
> Missing closing parenthesis in PSET coordinates at line 0
> Suggestions:
>   - Correct syntax: PSET(x,y) or PSET(x,y),color
>   - Example: PSET(100,50)
>   - Make sure parentheses are properly matched

# Mathematical domain error with educational context:
PRINT SQR(-4)
> Cannot calculate square root of negative number: -4.0 at line 0
> Details: Operation: SQR(n)
> Suggestions:
>   - Square root is only defined for non-negative numbers
>   - Use ABS() if you want the square root of the absolute value
>   - Example: SQR(ABS(-9)) returns 3

# INPUT error with syntax guidance:
INPUT "Enter value; X
> Missing closing quote in INPUT prompt at line 0
> Suggestions:
>   - Correct syntax: INPUT "prompt"; variable
>   - Example: INPUT "Enter value"; X
>   - Make sure prompt string has closing quote
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
- **Modular Architecture**: Clean separation of concerns across specialized modules with unified patterns
- **CoCoBasic Class**: Main interpreter with clear internal method naming (`process_*` for system, `execute_*` for commands)
- **Advanced Parser**: Parentheses-aware parsing with complex expression evaluation and AST generation
- **Expression Evaluator**: Sophisticated expression parsing with function registry integration
- **Command Registry**: Plugin-like architecture for extensible command handling with metadata
- **Unified Error System**: 145+ educational error messages with detailed context, suggestions, and categorization across all modules
- **Output Manager**: Streaming output management with filtering and buffering capabilities
- **Graphics Engine**: HTML5 Canvas with authentic MC6847 VDG emulation and nested function support
- **Variable Manager**: Comprehensive variable and array handling with enhanced error guidance
- **I/O System**: Multi-variable INPUT support with educational error messages and interactive keyboard integration
- **Web Interface**: Flask-SocketIO for real-time communication and responsive display
- **CLI Client**: Standalone terminal interface with real-time streaming output and program management

### File Structure
```
trs80/
├── app.py                 # Flask web application server with real-time streaming
├── cli_client.py          # Standalone CLI client with terminal interface
├── emulator/             # Core emulator modules with unified architecture
│   ├── core.py           # Main CoCoBasic interpreter with process_*/execute_* method separation
│   ├── parser.py         # Command parsing, tokenization, and AST generation
│   ├── expressions.py    # Expression evaluation with function registry
│   ├── functions.py      # BASIC function implementations with enhanced error messages (43 patterns)
│   ├── commands.py       # Command registry and plugin architecture
│   ├── error_context.py  # Unified error reporting system with educational suggestions
│   ├── output_manager.py # Output streaming and management
│   ├── graphics.py       # Graphics commands with enhanced error guidance (17 patterns)
│   ├── variables.py      # Variable and array management with detailed error messages (12 patterns)
│   └── io.py            # Input/output commands with educational error handling (6 patterns)
├── programs/             # BASIC program files directory
│   ├── README.md         # Program directory documentation
│   ├── bounce_realtime.bas # Real-time bouncing star animation
│   ├── qix_beam.bas      # Qix-style bouncing beam with dynamic sound
│   └── test_streaming.bas  # Streaming output test program
├── templates/
│   └── dual_monitor.html # Primary web interface
├── static/
│   ├── dual_monitor.css  # Interface styling with authentic CRT effects
│   ├── dual_monitor.js   # Interface with tab management and graphics
│   └── audio.js          # Web Audio API sound support
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

### Latest Update: Enhanced Error System & Architecture Refinement (September 2025) 🔧
**🎯 Major Code Quality Milestone: Unified error handling and improved internal architecture**

- **🎯 Comprehensive Error System Migration**: Fully unified error handling across all modules
  - **Educational Error Messages**: All 145+ error patterns now provide helpful suggestions and examples
  - **Consistent Error Format**: Unified error context system with detailed explanations and fix suggestions
  - **No Legacy Patterns**: Eliminated all "SYNTAX ERROR" messages in favor of specific, actionable guidance
  - **Enhanced User Experience**: Error messages now teach BASIC programming while helping debug issues

- **🏗️ Internal Architecture Improvements**: Clean separation between system and command methods
  - **Process vs Execute Naming**: Internal system methods use `process_*` (process_command, process_line, process_statement)
  - **Command Method Clarity**: User BASIC commands use `execute_*` (execute_if, execute_goto, execute_print)
  - **Backwards Compatibility**: External API unchanged - `execute_command()` still works for all existing code
  - **Better Maintainability**: Clear architectural distinction between internal processing and user commands

- **🧹 Code Quality Enhancements**: Eliminated technical debt and improved codebase clarity
  - **Deprecated Code Removal**: Cleaned up 79 lines of unused duplicate DIM implementation
  - **Architecture Consistency**: All modules follow unified patterns for better developer experience
  - **Zero Breaking Changes**: Comprehensive testing confirms all functionality preserved
  - **Cleaner Codebase**: Removed confusing dead code that could mislead developers

### Previous Update: Dynamic Sound and Interactive Graphics (September 2025) 🎵
**🎯 Enhanced Audio-Visual Experience: Qix-style bouncing beam with real-time positional audio**

- **🎮 Qix-Style Graphics Demo**: Complete implementation of classic Qix-style bouncing color beam
  - **Dynamic Trail Effects**: Elegant line fading showing only the last 25 beam segments
  - **Color Cycling**: Gradual color transitions creating rainbow effects over time
  - **Authentic Physics**: Proper angle of incidence = angle of reflection bouncing mechanics
  - **Dual-Point Animation**: Two independently bouncing endpoints creating complex geometric patterns

- **🎵 Revolutionary Sound Integration**: Position-based dynamic audio generation
  - **Positional Sound**: Frequencies modulated by X,Y coordinates creating spatial audio effects
  - **Phase Sweeping**: Continuous RF phase modulation creating authentic 8-bit sound aesthetics
  - **Reflection Audio**: Distinct high-frequency "pings" triggered at wall collisions
  - **Multi-Point Audio**: Different frequencies for each bouncing point creating rich soundscapes
  - **INKEY$ Integration**: Seamless program termination with proper audio cleanup

- **🎨 8-Bit Aesthetic**: Authentic retro computing experience with modern enhancements
  - **Classic Sound Design**: Position-based frequency modulation mimicking vintage arcade games  
  - **Visual Effects**: Smooth color transitions and trail effects creating mesmerizing displays
  - **Interactive Control**: Real-time keyboard input for program control during execution
  - **Educational Value**: Demonstrates physics, mathematics, and audio programming concepts

### Phase 2.0 Complete: Revolutionary Dual Monitor Interface ✨
**🎯 Major Milestone: World's first web-based dual monitor TRS-80 Color Computer BASIC environment**

- **🖥️ Dual Monitor Architecture**: Revolutionary split-screen interface with persistent REPL and dedicated graphics display
  - **Left Panel**: Full-featured BASIC REPL with 48-row terminal and perfect cursor alignment
  - **Right Panel**: Dedicated graphics display with authentic MC6847 VDG emulation  
  - **Resizable Panels**: Drag splitter to customize layout preferences
  - **Unified Experience**: Graphics programming without losing command line access

- **🔄 Multi-Tab Support**: Independent BASIC sessions with complete state isolation
  - **Separate Sessions**: Each tab maintains its own programs, variables, and display state
  - **Visual State Management**: Terminal content saved/restored when switching tabs
  - **Professional Workflow**: Multiple program development with tab-based organization

- **⌨️ Enhanced User Experience**: Modern interface with authentic feel  
  - **Rainbow Cursor**: Authentic TRS-80 CoCo rainbow cursor with cycling colors integrated into canvas rendering
  - **Command Line Editing**: Tab completion and Emacs key bindings (Ctrl+A, Ctrl+E, Ctrl+K, etc.)
  - **Ctrl+C Interrupt**: Robust break execution with proper race condition handling
  - **DELETE Command**: Remove program lines with line number syntax
  - **MOD Operator**: Complete mathematical expression support including modulo operations

- **🎮 Working Graphics System**: Complete graphics pipeline with perfect alignment
  - **All Graphics Modes**: PMODE 0-4 with accurate resolutions and color palettes
  - **Drawing Commands**: PSET, PRESET, LINE, CIRCLE with proper coordinate mapping
  - **Real-time Animation**: PAUSE command works seamlessly with graphics operations
  - **Export Capabilities**: PNG/SVG export functionality for sharing graphics

- **🔧 Production-Ready Stability**: Professional-grade reliability and error handling
  - **Race Condition Fixes**: Eliminated Ctrl+C timing issues that caused confusing error messages
  - **Pause Timer Management**: Clean cancellation of pause timers during program interruption
  - **Execution Context Awareness**: Proper distinction between program breaks and direct command cancellation
  - **Error Message Polish**: Silent handling of stray execution calls prevents user confusion

### Phase 1.6 Complete: Enhanced Architecture & Test Coverage  
- **Expanded Test Suite**: 383 comprehensive tests (up from 339) with 100% success rate
- **Advanced AST Parser**: Abstract Syntax Tree generation for complex expression evaluation
- **Enhanced Error System**: Educational error messages with proper categorization and context-aware suggestions
- **Plugin Architecture**: Extensible command registry with metadata and help system
- **Streaming Output Manager**: Real-time output filtering and buffering capabilities
- **Robust Expression Engine**: Sophisticated math and string expression evaluation
- **Comprehensive Function Library**: Complete implementation of all BASIC functions with detailed error handling
- **IF/THEN Statement Enhancement**: Full support for multi-statement THEN clauses

### Latest Critical Fixes (September 2025) - CLI Now Fully Functional ✅
**🎯 Major Milestone: The CLI client has transformed from "impressive demo" to "genuinely useful programming environment" for real TRS-80 BASIC development.**

- **🚀 CLI Client Reliability**: Complete program management workflow now works seamlessly
  - **Real-time Animations**: PAUSE command now works reliably for educational programming and game development
  - **File Operations**: SAVE, LOAD, FILES, and KILL commands work smoothly with proper confirmation prompts
  - **Program Execution**: No more mysterious crashes during program runs - consistent, predictable behavior
  - **Error Handling**: Clean, helpful error messages that don't confuse users with technical artifacts

- **🔧 Core Architecture Stabilization**: Fixed fundamental program counter tuple/int handling bugs
  - **PAUSE Command**: Eliminated TypeError crashes in program continuation after PAUSE operations
  - **INPUT Command**: Resolved program counter transitions in multi-variable INPUT scenarios  
  - **Program Execution**: Fixed execution loop comparison errors affecting all program runs
  - **Position Management**: Established consistent tuple-based program counter architecture across 6 locations

- **✅ Production-Ready Testing**: Comprehensive WebSocket integration test suite (32 tests, 100% success)
  - **Full Command Coverage**: Graphics, sound, I/O, file operations, and error handling
  - **Content Verification**: Tests validate actual output content and behavior, not just completion signals
  - **Regression Prevention**: Architectural guardrails prevent future program counter bugs

- **🎯 User Experience Polish**: Professional error messages and interface improvements
  - **Clear Error Messages**: "SYNTAX ERROR" instead of confusing "SYNTAX ERROR IN 0" for direct commands
  - **Context-Aware**: Still shows line numbers when errors occur during actual program execution
  - **Clean Codebase**: Removed debug statements for professional production deployment

### Previous Enhancements (January 2025)
- **🎯 Enhanced Error Messages**: Comprehensive error system with educational guidance and proper error categorization
  - **Arithmetic Errors**: Domain/range violations (e.g., SQR(-4), LOG(-5)) with mathematical explanations
  - **Type Errors**: Data type mismatches (e.g., ABS("text")) with conversion suggestions
  - **Syntax Errors**: Argument count and format issues with usage examples
  - **Context-Aware Suggestions**: Detailed guidance for fixing common programming mistakes
- **Fixed Arithmetic Error Detection**: Mathematical functions now correctly distinguish between domain errors and type errors
- **Enhanced Function Library**: All 20+ BASIC functions now provide detailed error messages with examples and suggestions
- **Test Organization**: Separated development utilities into `dev_tests/` directory for better organization

## 🧪 Testing

The emulator features **comprehensive WebSocket integration testing** with **32 integration tests** achieving **100% success rate**.

### WebSocket Integration Testing
```bash
# Run comprehensive WebSocket integration tests (requires server running)
python tests/integration/test_websocket_completion_signals.py

# These tests cover:
# - All graphics commands (PMODE, SCREEN, PSET, LINE, CIRCLE, PCLS, COLOR)
# - Sound commands (SOUND) 
# - Program execution (FOR loops, variable operations)
# - File operations (LOAD, SAVE, FILES, KILL confirmation)
# - Input/output (PRINT, INPUT, multi-variable INPUT)
# - Error handling (syntax errors, runtime errors, file errors)
# - WebSocket completion signals for CLI synchronization
```

### Development Testing
```bash
# Fast smoke test for essential functionality  
python dev_tests/smoke_test.py

# Quick mode for rapid verification
python dev_tests/smoke_test.py --quick

# Run all available test suites with detailed reporting
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
- **Teaching BASIC programming** with 145+ educational error messages providing specific guidance and examples
- **Computer history education** demonstrating 1980s computing with modern educational enhancements
- **Retro programming projects** with modern web accessibility and comprehensive error guidance
- **Learning computer graphics** through simple BASIC commands with detailed syntax explanations
- **Programming error debugging** with context-aware suggestions that teach proper coding practices
- **Real-time animations** and interactive programming demonstrations with enhanced feedback
- **Terminal-based development** with the standalone CLI client and improved error messages
- **Mathematics education** through BASIC functions with detailed domain/range error explanations
- **Software architecture learning** through clean separation of internal vs external method interfaces

## 🎓 Example Programs

### Qix-Style Bouncing Beam with Dynamic Sound
```basic
# Load and run the included Qix demo with positional audio:
LOAD "qix_beam"
SAFETY OFF      # Allow unlimited iterations for smooth animation
RUN
# Features: Dynamic color cycling, trail effects, position-based sound
# Press any key to stop the animation
```

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

### Sound and Graphics Animation
```basic
10 PMODE 4,1: SCREEN 1,1: PCLS
20 FOR A = 0 TO 360 STEP 10
30 X = 160 + 100 * COS(A * 3.14159 / 180)
40 Y = 96 + 60 * SIN(A * 3.14159 / 180)  
50 C = INT(A / 45) MOD 8 + 1
60 PSET(X,Y),C
70 F = 200 + A * 2  # Position-based frequency
80 SOUND F, 5       # Dynamic sound effect
90 PAUSE 0.1
100 NEXT A
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