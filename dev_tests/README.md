# Development Tests & Verification Scripts

This directory contains focused development test scripts for immediate feedback during feature development and debugging.

## Purpose

These scripts provide **quick verification** and **feature demonstration** during active development, separate from the comprehensive test suites.

## Files

### Development Verification Scripts
- **`smoke_test.py`** - Comprehensive smoke testing suite
  - Post-deployment and pre-commit verification
  - Quick validation of core emulator functionality
  - Supports quick mode: `python smoke_test.py --quick`
  - Full test: `python smoke_test.py`

- **`debug_test_failures.py`** - Test failure debugging tool
  - Reproduces and isolates specific test failure scenarios
  - Tests DRAW commands, INKEY$, FOR loops, expressions
  - Valuable for debugging failing test cases
  - Run: `python debug_test_failures.py`

## Usage

### Quick Development Feedback
```bash
# Comprehensive smoke test (recommended first step)
python dev_tests/smoke_test.py --quick

# Check for regressions after refactoring
python dev_tests/smoke_test.py

# Debug specific test failures
python dev_tests/debug_test_failures.py
```

## Relationship to Other Test Directories

- **`dev_tests/`** (this directory) - Immediate development feedback and architectural validation
- **`tests/unit/`** - Comprehensive unit tests with full coverage
- **`tests/integration/`** - Multi-component integration testing
- **Main test runner**: `python -m pytest` (includes all directories)

## Development Workflow

1. **Quick Health Check**: `python dev_tests/smoke_test.py --quick` (30 seconds)
2. **During Development**: Run relevant `dev_tests/` scripts for immediate feedback
3. **Pre-Commit Verification**: `python dev_tests/smoke_test.py` (full smoke test)
4. **Before Push**: `python -m pytest` for comprehensive validation
5. **Debugging**: Use `debug_test_failures.py` for isolating specific failures

## Removed Files

The following files were removed as they were redundant with existing unit/integration tests:

- **`test_expression_evaluator.py`** - Functionality fully covered by `tests/unit/test_functions.py`
- **`test_regression.py`** - Functionality covered by `tests/unit/test_dim_command.py` and `tests/unit/test_inkey_command.py`
- **`test_enhanced_errors.py`** - Functionality covered by `tests/unit/test_error_context.py` and `tests/unit/test_error_handling.py`
- **`test_help_command.py`** - Functionality covered by `tests/unit/test_command_registry.py`
- **`test_streaming_output.py`** - Functionality covered by `tests/unit/test_output_manager.py`

The development test scripts provide fast iteration feedback while the comprehensive test suites ensure production quality.