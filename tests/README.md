# BasiCoCo Test Suite

This directory contains the comprehensive test suite for BasiCoCo, organized into unit tests and integration tests.

## Running Tests

```bash
# Default run: everything except tests marked `slow` (~12 s)
python -m pytest

# Everything, including slow tests (Rubik's solver, live-server, pexpect audits; ~3.5 min)
python -m pytest -m ""

# Slow tests only
python -m pytest -m slow

# Run with coverage (see "Coverage" below)
python -m pytest -m "" --cov --timeout=300

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
- `test_program_management_commands.py` - DIR, FILES, DRIVE, SAVE, CLOAD, CSAVE commands
- `test_renum_command.py` - RENUM line renumbering functionality
- `test_on_commands.py` - ON GOTO and ON GOSUB multi-way branching
- `test_if_then_comprehensive.py` - IF THEN statement variations
- `test_file_commands.py` - File system command testing
- `test_regressions_executor.py`, `test_regressions_parser.py`, `test_regressions_builtins.py` - regression tests for the Sept 2026 audit findings (each test names its task number)
- `test_line_expansion.py` - one-line IF/loop expansion (`ast_converter.expand_statements`)
- `test_numeric_semantics.py` - CoCo number formatting, VAL, operator precedence, `^` edge cases
- `test_sandbox.py` - filesystem sandbox, KILL protocol, per-session CD
- `test_comments_and_crunching.py` - `'`/REM comments, block-IF detection, crunched spacing, ERR codes
- `test_immediate_mode.py`, `test_chain_directive.py`, `test_renum_references.py`, `test_graphics_arguments.py`, `test_graphics_pixels.py`, `test_file_io_args.py`, `test_help_listing.py`, `test_app_sessions.py`
- `test_rubiks_*.py` - Rubik's cube engine and solver (slow); `test_rubiks_regressions.py` solves 100 seeded random scrambles and checks each solution in pycuber
- And more...

### Integration Tests (`integration/`)
Tests multiple components working together:

#### Core Integration
- `test_comprehensive_program.py` - Complex program execution
- `test_cross_command_interactions.py` - Command interaction testing
- `test_for_loops.py` - Loop execution testing
- `test_program_execution_flow.py` - Program flow control
- `test_state_isolation.py` - State management between sessions
- `test_websocket_completion_signals.py` - WebSocket communication (live server)
- `test_websocket_security.py` - origin checks, KILL protocol, Ctrl+C, command serialization, reconnect (live server)
- `test_complex_if_then.py` - Complex conditional logic
- `test_program_audit.py` - runs every bundled program via pexpect (in a temp working directory)
- `test_input_resume.py`, `test_array_combinations.py`, `test_single_line_control_structures.py`

#### End-to-End Tests (`integration/e2e/`)
- `test_cli_sessions.py` - drives `cli_client.py` with pexpect against a live server: store/run, INPUT round trip, and a full lunar lander game

#### Browser tests (`integration/browser/`)
- `test_browser_client.py` - the web client in headless Google Chrome (Playwright): commands typed into the real REPL, output and scrollback read back, graphics checked pixel by pixel on the real canvas
- `test_browser_ui.py` - Ctrl+C, INKEY$ key forwarding, the Copy button, the graphics info labels, PCLS with a color, SOUND note queueing
- `test_browser_reload.py` - reloading the page reconnects to the same session with every tab
- Marked `browser` and `slow`; they use the installed Chrome (`channel='chrome'`) and are skipped, with the launch error as the reason, if Chrome can't start. Run just these with `python -m pytest -m browser`
- `tests/client/dual_monitor_harness.js` (run by `unit/test_client_rendering.py`) checks the same client code in Node on a fake canvas, with no browser needed

#### Live server fixture
`tests/integration/conftest.py` provides `live_server`: it starts `app.py` on a free localhost port with its working directory set to a fresh temp directory, so anything the server writes stays out of the repo's `programs/`. Tests get `live_server.url`, `.port` and `.programs_dir`. A server that fails to start fails the test — nothing is silently skipped.

## Coverage

```bash
python -m pytest -m "" --cov --cov-report=json:coverage.json --timeout=300
python tools/diff_coverage.py coverage.json <rev>   # uncovered lines changed since <rev>
```

`.coveragerc` measures `emulator/`, `app.py`, `cli_client.py` and `basicoco.py`, including the server and CLI subprocesses the integration tests start (`patch = subprocess`; `sigterm = true` so the live server saves its data when stopped). Coverage slows the Rubik's tests past the default 30 s timeout, hence `--timeout=300`; a full run takes about 12 minutes.

Changed-but-uncovered lines left on purpose after the audit's coverage pass (#81), each with its reason:
- `app.py` `_Pretty.__repr__`: only formats DEBUG log output.
- `app.py` disconnect with no session / while a program runs: a timing race the socket tests can't set up deterministically.
- `program_files.py` KILL's `PermissionError` / `OSError`: OS failures after the sandbox check.
- `graphics.py` DRAW's final `return []`: fallthrough after every known DRAW command.
- `program_executor.py` exception with an empty message: defensive.
- `core.py` numeric INPUT overflow → 0: `basic_number_prefix` doesn't raise OverflowError for any input found.

Lines found to be buggy or possibly unreachable are tracked in TASKS.md (#92–#96).

## Test Framework

Tests use **pytest** with shared fixtures defined in `conftest.py`:
- `basic` fixture — provides a fresh `CoCoBasic` emulator instance
- `graphics_basic` fixture — an emulator already in graphics mode
- `helpers` fixture — provides `TestHelpers` with utility methods for executing programs and checking output (`load_program`, `run_to_completion`, `get_text_output`, `get_error_messages`, ...)
- `temp_programs_dir` fixture — chdir into a temp directory with a `programs/` subdirectory; **any test that creates files must use it** (never write to the real `programs/`)

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
