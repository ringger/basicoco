# Development Tests & Verification Scripts

This directory contains 9 development test scripts for immediate feedback during feature development and debugging.

## Purpose

These scripts provide **quick verification** and **feature demonstration** during active development, separate from the comprehensive test suites.

## Files

### Feature Demonstration Scripts
- **`test_expression_evaluator.py`** - Demo of ExpressionEvaluator refactoring
  - Quick verification of expression parsing capabilities
  - Shows math operations, variables, and function calls
  - Run: `python test_expression_evaluator.py`

- **`test_streaming_output.py`** - Demo of StreamingOutputManager features  
  - Demonstrates real-time output streaming
  - Shows message filtering and buffering
  - Run: `python test_streaming_output.py`

- **`test_enhanced_errors.py`** - Demo of enhanced error reporting
  - Shows structured error messages with context
  - Demonstrates line number tracking and suggestions
  - Run: `python test_enhanced_errors.py`

- **`test_help_command.py`** - Demo of HELP system and command registry
  - Shows command discovery and help generation
  - Demonstrates plugin architecture capabilities
  - Run: `python test_help_command.py`

### Development Verification Scripts
- **`smoke_test.py`** - Comprehensive smoke testing suite
  - Post-deployment and pre-commit verification
  - Quick validation of core emulator functionality
  - Supports quick mode: `python smoke_test.py --quick`
  - Full test: `python smoke_test.py`

- **`test_regression.py`** - Quick regression check for refactoring
  - Smoke test for core functionality after changes
  - Ensures arrays, functions, and expressions still work
  - Run: `python test_regression.py`

- **`test_old_code_paths.py`** - Development debugging tool
  - Checks if legacy code paths are still being used
  - Helps verify refactoring completeness
  - Run: `python test_old_code_paths.py`

- **`debug_test_failures.py`** - Test failure debugging tool
  - Reproduces and isolates specific test failure scenarios
  - Tests DRAW commands, INKEY$, FOR loops, expressions
  - Valuable for debugging failing test cases
  - Run: `python debug_test_failures.py`

### Integration Scripts
- **`test_websocket.py`** - WebSocket integration testing
  - Tests real-time communication with web interface
  - Network functionality verification
  - Run: `python test_websocket.py`

## Usage

### Quick Development Feedback
```bash
# Comprehensive smoke test (recommended first step)
python dev_tests/smoke_test.py --quick

# Test expression evaluation after changes
python dev_tests/test_expression_evaluator.py

# Check for regressions after refactoring
python dev_tests/test_regression.py

# Verify streaming output works
python dev_tests/test_streaming_output.py
```

### Feature Demonstration
```bash
# Show enhanced error reporting
python dev_tests/test_enhanced_errors.py

# Demonstrate HELP system
python dev_tests/test_help_command.py
```

## Relationship to Other Test Directories

- **`dev_tests/`** (this directory) - Immediate development feedback and demos
- **`tests/unit/`** - Comprehensive unit tests with full coverage
- **`tests/integration/`** - Multi-component integration testing
- **Main test runner**: `python run_tests.py` (includes all directories)

## Development Workflow

1. **Quick Health Check**: `python dev_tests/smoke_test.py --quick` (30 seconds)
2. **During Development**: Run relevant `dev_tests/` scripts for immediate feedback
3. **Pre-Commit Verification**: `python dev_tests/smoke_test.py` (full smoke test)
4. **Before Push**: `python run_tests.py` for comprehensive validation (339 tests)
5. **Feature Demo**: Use `dev_tests/` scripts to show capabilities to stakeholders
6. **Debugging**: Use diagnostic scripts like `test_old_code_paths.py`

The development test scripts provide fast iteration feedback while the comprehensive test suites ensure production quality.