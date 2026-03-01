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
- **`execute_*` methods**: Non-migrated BASIC commands in registry (execute_next, execute_wend, execute_loop, etc.)
- **`visit_*` methods**: AST-based execution for migrated commands (visit_for_statement, visit_goto_statement, etc.)

### Command Execution Architecture

BASIC commands use a two-tier dispatch system:

1. **AST-first execution** via `_try_ast_execute()` → `ASTEvaluator.visit_*()` methods
   - Handles: END, GOTO, LET, PRINT, GOSUB, RETURN, FOR, EXIT FOR, WHILE, DO, IF, INPUT
   - Also handles implicit assignment (`X = 5` without LET)
   - Controlled by `_ast_migrated_commands` set

2. **Command Registry fallback** via `CommandRegistry.execute()`
   - Handles: NEXT, WEND, LOOP, ELSE, ENDIF, DIM, ON, STOP, CONT, DATA, READ, etc.
   - Registration pattern:
     ```python
     def register_commands(self, registry):
         registry.register('COMMAND_NAME', self.execute_method,
                          category='appropriate_category',
                          description="Command description",
                          syntax="COMMAND syntax",
                          examples=["COMMAND example"])
     ```

For new commands: add an AST visitor in `ast_parser.py` if the command involves control flow or core operations; use the registry for utility/system commands.

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

### AST Execution Architecture

The emulator uses AST-first execution for migrated commands. Stateful AST visitors in `ASTEvaluator` directly manage emulator state (stacks, variables) and return signal-based `List[Dict]` results.

**AST visitors handle:**
- Control flow: GOTO, GOSUB, RETURN, FOR, EXIT FOR, WHILE, DO, IF, END
- I/O: INPUT, PRINT
- Assignment: LET (explicit and implicit)

**Registry handles (non-migrated):**
- Closing commands: NEXT, WEND, LOOP, ELSE, ENDIF
- Utility: DIM, ON, STOP, CONT, DATA, READ, SOUND, etc.

Rules:
1. Both `visit_*` and `execute_*` methods return `[{'type': 'xxx', ...}]` format
2. AST visitors manage state directly (for_stack, call_stack, while_stack, etc.)
3. Closing commands in registry reference stack state pushed by AST visitors
4. Any changes must pass existing tests before merging

### Architecture Diagram
```
USER INPUT/PROGRAM
        |
        v
AST CONVERTER (ast_converter.py)
  Expand single-line → multi-line control structures
        |
        v
process_statement()
  ├─ Multi-line IF handler (bare "IF cond THEN")
  ├─ _try_ast_execute() → ASTEvaluator.visit_*()
  │     Migrated commands: stateful AST execution
  ├─ CommandRegistry.execute()
  │     Non-migrated commands: execute_* methods
  └─ Syntax error
        |
        v
EXPRESSION EVALUATOR (Uses AST internally)
  Called by both visitors and execute_* methods
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
