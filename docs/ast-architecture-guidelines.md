# AST Architecture Guidelines for TRS-80 Emulator

## Executive Summary

The TRS-80 BASIC emulator uses an AST-first execution architecture. All migrated BASIC commands (END, GOTO, LET, PRINT, GOSUB, RETURN, FOR, EXIT FOR, WHILE, DO, IF, INPUT) are parsed into AST nodes by `ASTParser` and executed by `ASTEvaluator` visitor methods that directly manage emulator state. Non-migrated commands (NEXT, WEND, LOOP, ELSE, ENDIF, DIM, ON, etc.) remain in the `CommandRegistry` as `execute_*` methods.

## Architecture Overview

```
USER INPUT / PROGRAM LINE
        |
        v
AST CONVERTER (ast_converter.py)
  Expand single-line control structures to multi-line
  e.g., "IF X=1 THEN A=5: B=10" → ["IF X=1 THEN", "A=5", "B=10", "ENDIF"]
        |
        v
process_statement()
        |
        ├─ Multi-line IF handler (bare "IF cond THEN")
        |    Push to if_stack, return skip_if_block or []
        |
        ├─ File I/O intercepts (PRINT#, INPUT#, LINE INPUT#)
        |    Intercepted before AST (parser doesn't understand #)
        |
        ├─ _try_ast_execute() — AST-first execution
        |    Parse → ASTEvaluator.visit_*() → return List[Dict]
        |    Handles: END, GOTO, LET, PRINT, GOSUB, RETURN,
        |             FOR, EXIT FOR, WHILE, DO, IF, INPUT
        |    Also handles implicit assignment (X = 5)
        |
        ├─ CommandRegistry.execute() — registry fallback
        |    Handles: NEXT, WEND, LOOP, ELSE, ENDIF, DIM, ON,
        |             STOP, CONT, DATA, READ, SOUND, etc.
        |
        └─ Syntax error (nothing matched)
```

## Core Principles

### 1. AST Visitors ARE the Primary Execution Path

Migrated commands execute through `ASTEvaluator.visit_*()` methods that directly manage emulator state (stacks, variables, program counter signals). This is **Approach 1** (Stateful AST Visitors).

```python
class ASTEvaluator:
    def visit_for_statement(self, node: ForStatementNode):
        # Directly manages emulator state
        self.emulator.variables[var_name] = start_val
        self.emulator.for_stack.append({
            'var': var_name, 'end': end_val, 'step': step_val,
            'line': self.emulator.current_line,
            'sub_line': self.emulator.current_sub_line
        })
        return []  # List[Dict] format
```

### 2. Signal-Based Control Flow

Visitors return `List[Dict[str, Any]]` with type fields that `run_program()` interprets:
- `jump` — GOTO target line
- `jump_return` — RETURN from GOSUB
- `skip_for_loop` — FOR loop should be skipped (start > end)
- `exit_for_loop` — EXIT FOR signal
- `skip_while_loop` — WHILE condition false
- `skip_do_loop` — DO condition false (top-tested)
- `skip_if_block` — IF condition false (multi-line)
- `input_request` — INPUT waiting for user
- `text` — output text
- `error` — error message

### 3. Closing Commands Stay in Registry

Structural closing commands (NEXT, WEND, LOOP, ELSE, ENDIF) remain as `execute_*` methods in the registry. They reference stack state pushed by AST visitors:
- `execute_next` reads `for_stack` (pushed by `visit_for_statement`)
- `execute_wend` reads `while_stack` (pushed by `visit_while_statement`)
- `execute_loop` reads `do_stack` (pushed by `visit_do_loop_statement`)
- `execute_else`/`execute_endif` read `if_stack` (pushed by multi-line IF handler)

### 4. AST Condition Storage

WHILE and DO store AST condition nodes for re-evaluation:
```python
# visit_while_statement stores:
self.emulator.while_stack.append({
    'condition_ast': node.condition,  # AST node for re-evaluation
    'line': ..., 'sub_line': ...
})

# execute_wend re-evaluates:
result = self._ast_evaluator.visit(while_info['condition_ast'])
```

## Migrated Commands

| Command | AST Visitor | Notes |
|---------|------------|-------|
| END | `visit_end_statement` | Sets `running=False` |
| GOTO | `visit_goto_statement` | Returns `jump` signal |
| LET | `visit_assignment` | Handles arrays, reserved name check |
| PRINT | `visit_print_statement` | Uses `_format_print_value()` |
| GOSUB | `visit_gosub_statement` | Pushes `call_stack`, returns `jump` |
| RETURN | `visit_return_statement` | Pops `call_stack`, returns `jump_return` |
| FOR | `visit_for_statement` | Manages `for_stack` directly |
| EXIT FOR | `visit_exit_for_statement` | Returns `exit_for_loop` signal |
| WHILE | `visit_while_statement` | Pushes `while_stack` with `condition_ast` |
| DO | `visit_do_loop_statement` | Pushes `do_stack` with `condition_ast` |
| IF | `visit_if_statement` | Single-line; multi-line handled in `process_statement` |
| INPUT | `visit_input_statement` | Sets `waiting_for_input`, returns `input_request` |

## Non-Migrated Commands (Registry)

NEXT, WEND, LOOP, ELSE, ENDIF, STOP, CONT, DIM, ON, DATA, READ, RESTORE, SOUND, PAUSE, CLS, NEW, LIST, RUN, CLEAR, DELETE, RENUM, LOAD, SAVE, HELP, REM, and graphics commands.

## Key Implementation Details

### Implicit Assignment Detection

`_try_ast_execute()` detects implicit assignments (`X = 5` without `LET`) by checking:
1. `=` present in code
2. No comparison operators in LHS (`<`, `>`, `!`)
3. First word is not a registered command
4. First token starts with a letter (variable name)

### Multi-line IF Handling

Bare `IF condition THEN` (without action) is handled in `process_statement()` before AST execution. The AST parser cannot parse bare THEN (empty statement), so this is caught early and pushes to `if_stack` directly.

### Error Propagation

When AST parsing fails for a migrated command, `_try_ast_execute()` returns the parse error with a "SYNTAX ERROR" prefix instead of falling through to the generic "Unrecognized command" error.

## Testing Guidelines

- Unit tests: `python -m pytest tests/unit/ --tb=short -q` (~1s)
- Full suite: `python -m pytest --ignore=tests/integration/test_websocket_completion_signals.py --tb=short -q` (~11s)
- All changes must pass the full suite before committing
- 1054 tests covering all migrated and non-migrated commands

## Historical Context

This architecture evolved from an initial hybrid approach (Approach 3) where AST was used only for expression evaluation and single-line control structure expansion, while all commands used `execute_*` methods via the registry. Through a 12-phase migration, all core control flow and I/O commands were moved to AST-first execution. The legacy `execute_*` methods for migrated commands have been removed.
