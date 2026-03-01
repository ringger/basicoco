# TRS-80 Color Computer BASIC Emulator - Development Guidelines

## Architecture Guidelines

### Current Architecture Foundation

The emulator has a clean, well-established architecture:

- Unified Error Handling: 145+ educational error messages across all modules
- Clean Method Naming: `process_*` for internal system vs `execute_*` for user commands
- Command Registry: Unified plugin-based command dispatch system
- Function Registry: Single source of truth for all BASIC functions
- Modular Design: Clear separation of concerns across specialized modules
- AST-Based Control Structures: Complete single-line control structure normalization with unified execution model
- Pytest Framework: Modern test infrastructure with fixtures and comprehensive coverage
- Robust GOTO Support: Non-brittle AST parsing handles both simple and complex control structures

### Architecture Patterns to Maintain

- Command registration via `register_commands()` in each module
- Enhanced error context with educational suggestions
- Clear internal/external API boundaries
- Function ownership by `functions.py` module only
- AST-based control structure processing for complex single-line statements
- Pytest fixtures for consistent test setup and execution
- Non-brittle AST parsing that handles control structures with or without colons consistently

### Method Naming Convention

**CRITICAL**: Maintain clear separation between internal system methods and user command methods:

- **`process_*` methods**: Internal system processing (process_command, process_line, process_statement)
- **`execute_*` methods**: User BASIC commands (execute_if, execute_goto, execute_print)

### Command Registry Architecture

All BASIC commands use the unified `CommandRegistry` system:

1. Add to appropriate module's `register_commands()` method
2. Use the established registration pattern with metadata
3. Do NOT add hardcoded if/elif chains in `process_statement()`
4. Do NOT bypass the command registry system

Registration pattern:
```python
def register_commands(self, registry):
    registry.register('COMMAND_NAME', self.execute_method,
                     category='appropriate_category',
                     description="Command description",
                     syntax="COMMAND syntax",
                     examples=["COMMAND example"])
```

**Function Registry**: All BASIC functions (CHR$, ASC, LEFT$, etc.) are handled by `/emulator/functions.py`. Never duplicate function implementations in other modules.

### Error Handling Standards

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

Requirements:
- Use enhanced error context with 2-3 helpful suggestions
- Provide specific examples of correct syntax
- Return `[{'type': 'error', 'message': formatted_message}]` format
- No generic error messages without educational value

### State Management Boundaries

- `keyboard_buffer` belongs to execution state, NOT cleared during program RUN
- Each state manager has clear ownership boundaries
- `clear_interpreter_state()` only clears program execution state, not input state

### AST vs Direct Execution Guidelines

**CRITICAL**: Clear separation between AST parsing and stateful execution:

**Use AST for:**
- Expression evaluation (mathematical/logical expressions without side effects)
- Single-line control structure expansion (transform `IF A THEN B:C:D` to multi-line)
- Program structure analysis (dead code detection, flow analysis)
- Stateless computation

**Do NOT use AST for:**
- Stateful command execution (GOTO, GOSUB, FOR)
- I/O operations (INPUT, PRINT with side effects)
- Stack management (for_stack, call_stack, if_stack)
- Program counter control

Rules:
1. AST for structure, `execute_*` for behavior
2. `execute_*` methods must return `[{'type': 'xxx', ...}]` format
3. Any AST integration must pass existing tests before merging

### Architecture Diagram
```
USER INPUT/PROGRAM
        |
        v
AST CONVERTER (ast_converter.py)
  Transform single-line -> multi-line control structs
        |
        v
COMMAND REGISTRY & EXECUTE_* METHODS
  Stateful execution with stack/counter management
        |
        v
EXPRESSION EVALUATOR (Uses AST)
  Stateless pure computation
```

## Development Notes

- Always activate the virtual environment before running Python: `source venv/bin/activate`
- When running tests, let them run to completion instead of timing out
- Backend server can be started with comprehensive logging using `./start_server_with_logging.sh`
- Use `./monitor_server_logs.sh` in a separate terminal to monitor server output in real-time

## Architecture Issue Priority

When encountering architectural inconsistencies, treat them as immediate blockers:
- Duplicate function implementations across modules
- Missing method dependencies or dead code references
- Bypassing established command registry patterns
- Inconsistent error handling patterns
- State management boundary violations
- Method naming convention violations (`process_*` vs `execute_*`)
