# TRS-80 Color Computer BASIC Emulator Test Suite

This directory contains the comprehensive test suite for the TRS-80 Color Computer BASIC emulator, organized into unit tests and integration tests.

## Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=emulator --cov-report=term-missing

# Run unit tests only
python -m pytest tests/unit/ -v

# Run integration tests only
python -m pytest tests/integration/ -v

# Run a specific test file
python -m pytest tests/unit/test_print_command.py -v

# Run tests matching a pattern
python -m pytest -k "test_for" -v
```

## Test Structure

### Unit Tests (`unit/`)
Tests individual components in isolation using pytest fixtures:
- `test_ast_parser.py` - Abstract syntax tree parsing
- `test_command_*.py` - Individual BASIC command implementations
- `test_expressions.py` - Expression evaluation
- `test_functions.py` - Built-in BASIC functions
- `test_variables.py` - Variable management
- `test_error_*.py` - Error handling and context management
- `test_graphics_commands.py` - Graphics system components
- `test_output_manager.py` - Output streaming and management
- `test_direct_emulator.py` - Direct emulator unit testing
- `test_program_management_commands.py` - DIR, FILES, DRIVE, SAVE, CLOAD, CSAVE commands
- `test_renum_command.py` - RENUM line renumbering functionality
- `test_on_commands.py` - ON GOTO and ON GOSUB multi-way branching
- `test_if_then_comprehensive.py` - IF THEN statement variations
- `test_file_commands.py` - File system command testing
- And more...

### Integration Tests (`integration/`)
Tests multiple components working together:

#### Core Integration
- `test_comprehensive_program.py` - Complex program execution
- `test_cross_command_interactions.py` - Command interaction testing
- `test_for_loops.py` - Loop execution testing
- `test_program_execution_flow.py` - Program flow control
- `test_state_isolation.py` - State management between sessions
- `test_websocket_completion_signals.py` - WebSocket communication
- `test_complex_if_then.py` - Complex conditional logic

#### CLI Tests (`integration/cli/`)
- `test_cli_with_pexpect.py` - Interactive CLI testing
- `test_cli_logged.py` - CLI with logging verification

#### End-to-End Tests (`integration/e2e/`)
- `test_minimal.py` - Basic functionality verification
- `test_step_by_step.py` - Step-by-step execution testing
- `test_manual_lunar.py` - Complex lunar lander program
- `test_complete_lunar.py` - Full lunar lander execution
- `test_complex_lunar.py` - Advanced lunar lander scenarios
- `test_complex_lunar_fixed.py` - Lunar lander with fixes

## Test Framework

Tests use **pytest** with shared fixtures defined in `conftest.py`:
- `basic` fixture — provides a fresh `CoCoBasic` emulator instance
- `helpers` fixture — provides `TestHelpers` with utility methods for executing programs and checking output

### Example Test Structure
```python
class TestMyCommand:
    def test_basic_functionality(self, basic, helpers):
        """Test basic command functionality"""
        result = basic.process_command('MY_COMMAND "TEST"')
        text_outputs = helpers.get_text_output(result)
        assert 'EXPECTED' in ' '.join(text_outputs)

    def test_program_context(self, basic, helpers):
        """Test command in program context"""
        program = [
            '10 MY_COMMAND "HELLO"',
            '20 END'
        ]
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        assert 'HELLO' in ' '.join(text_outputs)
```

## Development Guidelines

### Adding Tests
1. Place unit tests in `unit/`, integration tests in `integration/`
2. Use pytest fixtures (`basic`, `helpers`) for emulator setup
3. Follow naming convention: `test_[component].py` for files, `test_[behavior]` for methods
4. Include both positive and negative test cases
5. Keep unit tests fast (< 100ms each)

### Test Quality
- Each test should test one specific behavior
- Use descriptive assertion messages
- Avoid testing implementation details
- Focus on user-visible behavior
