# Changelog

All notable changes to the TRS-80 Color Computer BASIC Emulator are documented here.

## March 2026

### Complete AST Execution Migration
- Migrated all 12 core commands to AST-based execution: END, GOTO, LET, PRINT, GOSUB, RETURN, FOR, EXIT FOR, WHILE, DO, IF, INPUT
- Two-tier dispatch architecture: AST-first execution via `_try_ast_execute()` with command registry fallback
- Signal-based control flow with `List[Dict]` return format across all visitors
- Added `visit_*` methods in `ASTEvaluator` for stateful command execution
- Multi-line IF handler in `process_statement()` for bare `IF condition THEN` blocks
- Fixed AST PRINT parser to handle parenthesized expressions correctly
- Removed all legacy `execute_*` methods for migrated commands (~716 lines removed)
- All 619 tests passing throughout the migration

### Post-Migration Cleanup
- Removed vestigial `_execute_via_ast()` from core.py (superseded by `_try_ast_execute()`)
- Removed 3 dead methods from io.py: `_split_print_arguments()`, `_split_print_arguments_with_separators()`, `_is_valid_variable_name()`
- Removed dead `_is_valid_variable_name()` from variables.py
- Removed dead `BaseTestCase` imports from 5 test files
- Removed vestigial `test_base.py`, `run_tests.py`, `run_unit_tests.py`, `run_integration_tests.py`
- Removed `dev_tests/test_old_code_paths.py` (referenced functions that no longer exist)
- Removed 29 test artifact `.bas` files from `programs/` directory
- Fixed test isolation: file command tests now use autouse temp directory fixtures

## February 2026

### Public Release Preparation
- Fixed stack initialization and flaky timestamp test
- Removed dead code and wrapper boilerplate
- Narrowed exception handlers to specific types
- Removed duplicate state clearing in `execute_new` and `run_program`
- Removed stale comments and fixed misleading docstrings
- Cleaned up documentation for public release

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
