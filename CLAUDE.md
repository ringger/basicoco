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

## IF/THEN/ELSE Handling

Three paths handle IF statements:

1. **Single-line IF** (`IF cond THEN action`) — AST parser evaluates directly in `visit_if_statement()`. No stack involved.
2. **Multi-line IF** (bare `IF cond THEN`) — detected in `process_statement()`, pushes to `if_stack`. `skip_if_block` directive tells executor to skip via `_skip_if_or_else_block()`.
3. **AST-converted single-line** (e.g., `IF A=1 THEN B=2: C=3`) — AST converter expands to `IF cond THEN` / body / `ENDIF` sublines, which then follow the multi-line path.

Nesting: `_skip_if_or_else_block()` counts nested IFs by checking `stmt.startswith('IF ')` (not substring match, to avoid false positives from strings like `PRINT "IF THEN"`). GOTO out of an IF block leaves a stale if_stack entry — cleared on next RUN by `clear_all_stacks()`.

## ON ERROR GOTO / RESUME

`ON ERROR GOTO <line>` registers an error handler; `ON ERROR GOTO 0` disables it. When a runtime error occurs during program execution, `_handle_flow_control()` in `program_executor.py` intercepts the error (if a handler is registered and not already in an error handler), saves error state, and jumps to the handler line.

State fields on `CoCoBasic`: `on_error_goto_line`, `error_number` (ERR), `error_line` (ERL), `error_resume_position`, `in_error_handler`. All reset by `clear_interpreter_state()`.

`RESUME` / `RESUME NEXT` / `RESUME <line>` return `resume` / `resume_next` / `jump` directives handled by `_handle_flow_control()`. ERR and ERL are read-only pseudo-variables exposed in `visit_variable()`.

## INPUT Protocol

INPUT pauses execution by returning `{'type': 'input_request', ...}`. Variable targets are described by dicts: `{'name': 'V', 'array': True, 'indices': [1]}` or `{'name': 'X', 'array': False}`. After storing the value via `store_input_value(var_desc, value)`, call `continue_program_execution()` to resume.

## Statement Splitting

`BasicParser` in `parser.py` owns all statement-splitting and argument-splitting logic:

- `split_on_delimiter()` — split on colons (or custom delimiter), respecting quoted strings.
- `split_args()` — split on commas, respecting parentheses and quotes. The single shared comma-splitter for the entire codebase (replaces all former per-module `_split_args` variants).
- `split_on_delimiter_paren_aware()` — generalized version of `split_args()` for non-comma delimiters.
- `is_rem_line()` — guards against splitting REM comments.
- `has_control_keyword()` — detects IF/FOR/WHILE/DO at the start of a line.
- `CONTROL_KEYWORDS` — canonical tuple of control-flow keyword prefixes.

Never duplicate this logic — always call through to `BasicParser`.

### Immediate mode flow

`process_command()` detects multi-statement lines early (before the registry) and routes them to `process_line()`. `process_line()` then takes one of three paths:

1. **REM** → `process_statement()` directly (never split).
2. **Control structure + colons** (IF/FOR/WHILE/DO) → AST conversion → `_execute_converted_as_temporary_program()` → `run_program()`.
3. **Plain multi-statement** → sequential `process_statement()` loop, stopping on jump or error.

### Program storage flow

`expand_line_to_sublines()` in `core.py` splits stored lines once at entry time. REM lines and single-line IF/THEN are kept whole; everything else is split via `BasicParser.split_on_delimiter()`.

## Naming

- **`process_*`**: internal system (`process_command`, `process_statement`)
- **`execute_*`**: registry commands (`execute_next`, `execute_wend`)
- **`visit_*`**: AST execution (`visit_for_statement`, `visit_goto_statement`)

## Rules

- `functions.py` owns all BASIC functions — never duplicate elsewhere
- Graphics commands go in `graphics.py`, DIM/arrays in `variables.py`
- Graphics helpers: `_eval_int(expr)` for expression→int, `_syntax_error(msg, suggestions)` for error responses
- LINE coordinate pair syntax: `CommandRegistry.is_coordinate_pair_syntax()` and `parse_line_coordinates()` handle `(x1,y1)-(x2,y2)` with optional spaces around the dash
- System OK messages use `_system_ok()` (tagged with `'source': 'system'`)
- File-creating tests must use autouse temp directory fixtures — never write to real `programs/`
- All errors use `error_context.syntax_error()` / `runtime_error()` with 2-3 suggestions. `syntax_error()` auto-prefixes "SYNTAX ERROR:" — don't add it manually.
- Use `error_response(error)` and `text_response(text)` from `error_context` to build response lists — never hand-build `[{'type': 'error', ...}]` or `[{'type': 'text', ...}]`
- Use `basic_truthy(value)` from `ast_parser` for BASIC boolean conversion — never inline the `isinstance` check
- Use `check_reserved_name(name)` on `CoCoBasic` to guard against reserved function names in assignments and DIM
- Use `clear_all_stacks()`, `save_execution_state()`, `restore_execution_state()` for stack/state management
- `source venv/bin/activate` before running anything
- Tests: `python -m pytest --ignore=tests/integration/test_websocket_completion_signals.py`
