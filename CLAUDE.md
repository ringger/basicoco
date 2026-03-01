# TRS-80 Color Computer BASIC Emulator - Development Guidelines

## Command Execution: Two-Tier Dispatch

All BASIC statements flow through `process_statement()` in `core.py`:

```
process_statement(code)
  1. Multi-line IF handler  ← bare "IF cond THEN" (no action after THEN)
  2. _try_ast_execute()     ← AST-first for migrated commands
  3. CommandRegistry         ← fallback for non-migrated commands
  4. Syntax error            ← nothing matched
```

**Why multi-line IF is first:** The AST parser cannot parse bare `IF condition THEN` (no clause after THEN). It throws an "Empty statement" error. The multi-line IF handler catches this pattern before AST execution and pushes to `if_stack` directly.

### AST-Migrated Commands (`_ast_migrated_commands` set)

Executed by `ASTEvaluator.visit_*()` methods in `ast_parser.py`:

END, GOTO, LET, PRINT, GOSUB, RETURN, FOR, EXIT FOR, WHILE, DO, IF, INPUT

Also handles implicit assignment (`X = 5` without LET keyword).

### Registry Commands

Executed by `execute_*()` methods, registered via `CommandRegistry`:

NEXT, WEND, LOOP, ELSE, ENDIF, DIM, ON, STOP, CONT, DATA, READ, RESTORE, SOUND, PAUSE, NEW, DELETE, RENUM, HELP, SAFETY, and file/graphics commands.

### Where to Add New Commands

- **Control flow or core operations** → AST visitor in `ast_parser.py`
- **Utility/system commands** → Registry via `execute_*` method
- **BASIC functions** (CHR$, SIN, etc.) → `functions.py` only, never elsewhere

## Signal Types

All `visit_*` and `execute_*` methods return `List[Dict[str, Any]]`. The run loop in `run_program()` processes these signal types:

| Signal | Source | Meaning |
|--------|--------|---------|
| `{'type': 'text', 'text': ...}` | PRINT, LIST, etc. | Output text to user |
| `{'type': 'error', 'message': ...}` | Any | Error output |
| `{'type': 'input_request', 'prompt': ..., 'variable': ...}` | INPUT, KILL | Request user input |
| `{'type': 'jump', 'line': n}` | GOTO, IF THEN n | Jump to line n |
| `{'type': 'jump_return', 'line': n, 'sub_line': m}` | RETURN | Return from GOSUB |
| `{'type': 'jump_after_for'}` | FOR | Jump past matching NEXT |
| `{'type': 'skip_for_loop', 'var': ...}` | FOR (start > end) | Skip loop body entirely |
| `{'type': 'exit_for_loop'}` | EXIT FOR | Break out of current FOR |
| `{'type': 'skip_while_loop'}` | WHILE (false) | Skip to after WEND |
| `{'type': 'jump_after_while'}` | WEND | Loop back to WHILE |
| `{'type': 'skip_do_loop'}` | DO (WHILE false / UNTIL true) | Skip to after LOOP |
| `{'type': 'jump_after_do'}` | LOOP | Loop back to DO |
| `{'type': 'skip_if_block'}` | IF (false) | Skip to ELSE/ENDIF |

**END and STOP** don't use signals — they set `self.running = False` directly.

## Stack Ownership

AST visitors push; registry closing commands pop:

| Stack | Pushed by (AST) | Popped by (Registry) | Contents |
|-------|-----------------|---------------------|----------|
| `for_stack` | `visit_for_statement` | `execute_next` | var, start, end, step, line, sub_line |
| `call_stack` | `visit_gosub_statement` | via `visit_return_statement` (AST) | return line + sub_line |
| `while_stack` | `visit_while_statement` | `execute_wend` | condition_ast, line, sub_line |
| `do_stack` | `visit_do_statement` | `execute_loop` | condition_ast, condition_type, line, sub_line |
| `if_stack` | `visit_if_statement` / multi-line IF handler | `execute_else`, `execute_endif` | condition_met, in_else, line |

## Method Naming Convention

- **`process_*`**: Internal system methods — `process_command`, `process_line`, `process_statement`
- **`execute_*`**: Registry-dispatched BASIC commands — `execute_next`, `execute_wend`, etc.
- **`visit_*`**: AST-based execution — `visit_for_statement`, `visit_goto_statement`, etc.

## Error Handling

All modules use the Enhanced Error Context system:

```python
error = self.emulator.error_context.syntax_error(
    "Clear description of what went wrong",
    self.emulator.current_line,
    suggestions=[
        'Specific suggestion for fixing the error',
        'Example of correct syntax',
        'Additional helpful guidance'
    ]
)
return [{'type': 'error', 'message': error.format_detailed()}]
```

Error types: `syntax_error()`, `runtime_error()`, `type_error()`, `arithmetic_error()`

## Module Placement Guide

| What | Where | Notes |
|------|-------|-------|
| BASIC functions (CHR$, SIN, LEFT$...) | `functions.py` | Single source of truth; never duplicate elsewhere |
| Graphics commands (PSET, LINE, CIRCLE...) | `graphics.py` | Also handles PMODE, SCREEN, PCLS |
| DIM and array access | `variables.py` | `VariableManager` class |
| Expression evaluation | `expressions.py` | `evaluate_expression()`, `evaluate_condition()` — used by both AST visitors and execute_* methods |
| AST parsing + execution | `ast_parser.py` | Parser, node types, and `ASTEvaluator` all in one file |
| Single-line → multi-line conversion | `ast_converter.py` | Converts `IF A THEN B: C` → multi-line before execution |
| Print value formatting | `ast_parser.py` | `ASTEvaluator._format_print_value()` static method |

## Testing Patterns

```python
class TestMyFeature:
    def test_immediate_mode(self, basic, helpers):
        """Test command in immediate mode"""
        result = basic.process_command('PRINT "HELLO"')
        text_outputs = helpers.get_text_output(result)
        assert 'HELLO' in ' '.join(text_outputs)

    def test_program_mode(self, basic, helpers):
        """Test command in program context"""
        program = ['10 PRINT "HELLO"', '20 END']
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        assert 'HELLO' in ' '.join(text_outputs)

    def test_error_case(self, basic, helpers):
        """Test error handling"""
        helpers.assert_error_output(basic, 'GOTO', 'SYNTAX ERROR')
```

Fixtures (from `conftest.py`):
- `basic` — fresh `CoCoBasic` instance per test
- `helpers` — `TestHelpers` class with `get_text_output()`, `get_error_messages()`, `execute_program()`, `assert_error_output()`, etc.

**File command tests must use temp directories.** Both `test_file_commands.py` and `test_program_management_commands.py` have `autouse` fixtures that `chdir` to a temp directory. Never write tests that create `.bas` files in the real `programs/` directory.

## State Management

- `keyboard_buffer` is execution state — NOT cleared during RUN
- `clear_interpreter_state()` clears program execution state only, not input state
- Variables persist across immediate-mode commands; cleared by NEW and RUN

## Development Notes

- Always activate the virtual environment: `source venv/bin/activate`
- When running tests, let them run to completion instead of timing out
- Run all tests: `python -m pytest --ignore=tests/integration/test_websocket_completion_signals.py`
- Full suite including WebSocket: `python -m pytest` (619 passed, 32 skipped)
