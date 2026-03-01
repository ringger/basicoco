# BasiCoCo

## Command Dispatch

`process_statement()` in `core.py` tries these in order:

1. **Multi-line IF** — bare `IF cond THEN` (no action). Must be first because the AST parser can't parse it.
2. **`_try_ast_execute()`** — AST-migrated commands: END, GOTO, LET, PRINT, GOSUB, RETURN, FOR, EXIT FOR, WHILE, DO, IF, INPUT. Also implicit assignment (`X = 5`).
3. **`CommandRegistry`** — everything else: NEXT, WEND, LOOP, ELSE, ENDIF, DIM, ON, STOP, CONT, DATA, READ, RESTORE, SOUND, PAUSE, etc.

New control flow → AST visitor in `ast_parser.py`. New utility command → registry via `execute_*`. New BASIC function → `functions.py` only.

## Execution Engine

All program execution goes through `_execute_statements_loop()` — the shared engine used by `run_program()`, `continue_program_execution()`, and `execute_cont()`. Flow-control is handled by `_handle_flow_control()` which dispatches jump/skip/pause directives. Helper methods: `_find_line_position()`, `_skip_to_keyword()`, `_skip_to_next()`, `_skip_if_or_else_block()`.

## Expression Evaluation

`evaluate_expression(expr)` on `CoCoBasic` parses and evaluates a BASIC expression string via the AST (`ASTParser.parse_expression()` + `ASTEvaluator.visit()`). `evaluate_condition(cond)` does the same, returning a boolean. `FunctionRegistry` (in `expressions.py`) maps BASIC function names to handlers in `functions.py`. Function handlers receive the `CoCoBasic` instance as their first argument.

## Stack Ownership

AST visitors push; registry closing commands pop:

| Stack | Pushed by | Popped by |
|-------|-----------|-----------|
| `for_stack` | `visit_for_statement` | `execute_next` |
| `call_stack` | `visit_gosub_statement` | `visit_return_statement` |
| `while_stack` | `visit_while_statement` | `execute_wend` |
| `do_stack` | `visit_do_statement` | `execute_loop` |
| `if_stack` | `visit_if_statement` / multi-line IF handler | `execute_else`, `execute_endif` |

## INPUT Protocol

INPUT pauses execution by returning `{'type': 'input_request', ...}`. Variable targets are described by dicts: `{'name': 'V', 'array': True, 'indices': [1]}` or `{'name': 'X', 'array': False}`. After storing the value via `store_input_value(var_desc, value)`, call `continue_program_execution()` to resume.

## Naming

- **`process_*`**: internal system (`process_command`, `process_statement`)
- **`execute_*`**: registry commands (`execute_next`, `execute_wend`)
- **`visit_*`**: AST execution (`visit_for_statement`, `visit_goto_statement`)

## Rules

- `functions.py` owns all BASIC functions — never duplicate elsewhere
- Graphics commands go in `graphics.py`, DIM/arrays in `variables.py`
- Graphics helpers: `_eval_int(expr)` for expression→int, `_syntax_error(msg, suggestions)` for error responses
- System OK messages use `_system_ok()` (tagged with `'source': 'system'`)
- File-creating tests must use autouse temp directory fixtures — never write to real `programs/`
- All errors use `error_context.syntax_error()` / `runtime_error()` with 2-3 suggestions
- `source venv/bin/activate` before running anything
- Tests: `python -m pytest --ignore=tests/integration/test_websocket_completion_signals.py`
