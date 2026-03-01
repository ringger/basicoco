# Changelog

All notable changes to the TRS-80 Color Computer BASIC Emulator are documented here.

## September 2025

### AST Integration Architecture Stabilization
- Resolved 49 test failures from AST architecture conflicts
- Reverted `execute_let`, `execute_end`, and `execute_input` from AST to legacy implementation for correct stateful behavior
- Added EXIT and ON as recognized AST keywords
- Enhanced AST converter to handle expression-based jumps
- Removed unused AST visitors for GOSUB, RETURN, INPUT per architecture guidelines
- All 519 tests passing, 0 failures

### Vestigial Code Cleanup
- Removed dead code and unused imports across `app.py`, `test_utilities.py`, and `cli_client.py`
- Eliminated obsolete methods including `parse_function_arguments()`
- Added pytest-cov integration with coverage tracking

### Single-Line Control Structure Support
- Complete support for complex single-line BASIC statements in both immediate and program modes
- AST-based conversion of single-line IF/THEN, FOR/NEXT, WHILE/WEND, DO/LOOP to multi-line equivalents
- New `ast_converter.py` module for statement normalization

### Pytest Migration
- Migrated all 47 test files from unittest to pytest
- Fixed 121+ tests during conversion
- Added pytest.ini, conftest.py, and shared fixtures

### Unified Error System
- All 145+ error messages now provide educational suggestions and examples
- Unified error context system replacing generic "SYNTAX ERROR" messages
- Four error types: syntax, runtime, type, and arithmetic errors

### Internal Architecture Improvements
- Clear method naming: `process_*` for internal system, `execute_*` for user commands
- Removed 79 lines of duplicate DIM implementation

### Dynamic Sound and Interactive Graphics
- Qix-style bouncing beam demo with positional audio
- SOUND command with Web Audio API and position-based frequency modulation
- INKEY$ integration for real-time keyboard input during execution

### Dual Monitor Interface (Phase 2.0)
- Split-screen web interface with persistent REPL and dedicated graphics display
- Multi-tab support with independent BASIC sessions
- Rainbow cursor with authentic TRS-80 CoCo color cycling
- Command line editing with Emacs key bindings
- Ctrl+C interrupt with proper race condition handling
- PNG/SVG graphics export

### Enhanced Architecture and Test Coverage (Phase 1.6)
- Expanded test suite from 339 to 383 tests
- Advanced AST parser for complex expression evaluation
- Plugin-based command registry with metadata
- Streaming output manager
- Multi-statement IF/THEN clause support

### CLI Client Stabilization
- Fixed program counter tuple/int handling bugs affecting PAUSE, INPUT, and program execution
- WebSocket integration test suite (32 tests)
- Context-aware error messages (line numbers shown only during program execution)

## January 2025

### Enhanced Error Messages
- Educational error system with domain/range violation explanations
- Type mismatch detection with conversion suggestions
- Argument count and format validation with usage examples
- Separated development utilities into `dev_tests/` directory
