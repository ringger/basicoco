# BasiCoCo

The main interpreter module is `emulator/core.py` (`CoCoBasic` class). All emulator source lives under `emulator/`. The conftest with test fixtures (`basic`, `helpers`, `temp_programs_dir`) is at `conftest.py` (project root).

## Command Dispatch

`process_statement()` in `core.py` tries these in order:

1. **Multi-line IF** — bare `IF cond THEN` (no action). Must be first because the AST parser can't parse it.
2. **File I/O intercepts** — PRINT#, INPUT#, LINE INPUT# (and console LINE INPUT). Intercepted before AST because the AST parser doesn't understand `#` syntax.
3. **`_try_ast_execute()`** — anything not in the `CommandRegistry`. The parser knows registry command keywords via `registry_commands` set and raises `RegistryCommandError` for them. Handles: END, GOTO, LET, PRINT, GOSUB, RETURN, FOR, EXIT FOR, WHILE, DO, IF, INPUT, ON (GOTO/GOSUB and ERROR GOTO), and implicit assignment (`X = 5`).
4. **`CommandRegistry`** — everything else: NEXT, WEND, LOOP, ELSE, ENDIF, LOCAL, DIM, STOP, CONT, DATA, READ, RESTORE, SOUND, PAUSE, etc.

New control flow → AST visitor in `ast_evaluator.py`. New utility command → registry via `execute_*`. New BASIC function → `functions.py` only.

## Execution Engine

All program execution goes through `_execute_statements_loop()` — the shared engine used by `run_program()`, `run_program_from_line()`, `continue_program_execution()`, and `execute_cont()`. Flow-control is handled by `_handle_flow_control()` which dispatches jump/skip/pause directives (plus `program_modified` from MERGE and `chain` from CHAIN, which switch programs inside the same loop — never a nested run). Helper methods: `_find_line_position()` / `_find_position_index()` (binary search on the sorted position list), `_skip_to_keyword()`, `_skip_to_next()` (both nesting-aware), `_skip_if_or_else_block()`, `_rebuild_data_statements()`.

- Any Python exception raised while running a statement (all kinds: AST, `CompiledCommand`, `CompiledMultiLineIf`) is turned into a BASIC runtime error so ON ERROR can trap it. The list of such exceptions is `BASIC_RUNTIME_ERRORS` in `error_context.py` — use it, don't hand-write tuples.
- The runaway guard (`max_iterations` / `max_absolute_iterations`) budgets each uninterrupted slice: `iteration_count` resets whenever execution resumes after INPUT, PAUSE or a graphics auto-yield.
- `break_requested` (set by the web server's Ctrl+C handler from another thread) is checked every statement; the loop stops with `BREAK IN n`, CONT-able.

## Expression Evaluation

`evaluate_expression(expr)` on `CoCoBasic` parses and evaluates a BASIC expression string via the AST (`ASTParser.parse_expression()` + `ASTEvaluator.visit()`). `evaluate_condition(cond)` does the same, returning a boolean. Both cache parsed AST nodes in `_expr_cache` (keyed by expression string) so repeated evaluations in loops skip the tokenizer and parser. `FunctionRegistry` (in `function_registry.py`) maps BASIC function names to handlers in `functions.py`. Function handlers receive the `CoCoBasic` instance as their first argument.

## Stack Ownership

AST visitors push; registry closing commands pop:

| Stack | Pushed by | Popped by |
|-------|-----------|-----------|
| `for_stack` | `visit_for_statement` | `execute_next` (control_flow.py) |
| `call_stack` | `visit_gosub_statement` (4-tuple: line, sub_line, if_depth, for_depth) | `visit_return_statement` (also restores if_stack/for_stack depth) |
| `local_stack` | `visit_gosub_statement` (empty frame) | `visit_return_statement` (restores variables); LOCAL/PRIVATE append entries |
| `while_stack` | `visit_while_statement` | `execute_wend` (control_flow.py) |
| `do_stack` | `visit_do_statement` | `execute_loop` (control_flow.py) |
| `if_stack` | `visit_if_statement` / multi-line IF handler | `execute_else`, `execute_endif` (control_flow.py) |

## IF/THEN/ELSE Handling

Three paths handle IF statements:

1. **Single-line IF whose branches are only GOTOs** (`IF A$="" THEN 10`, `IF X THEN 100 ELSE 200`) — kept as one subline, evaluated directly by `visit_if_statement()`. No stack involved (so a polling loop can't leak if_stack entries).
2. **Multi-line IF** (bare `IF cond THEN`, also `IF(cond)THEN` and `IF cond THEN REM ...`) — compiled to `CompiledMultiLineIf`, pushes to `if_stack`. `skip_if_block` directive tells executor to skip via `_skip_if_or_else_block()`.
3. **Expanded single-line** (e.g., `IF A=1 THEN B=2: C=3 ELSE D=4`) — `ast_converter.expand_statements()` expands it at the TEXT level to `IF cond THEN` / body / `ELSE` / body / `ENDIF` sublines (statements kept verbatim, never regenerated from an AST), which then follow the multi-line path.

`ast_converter.py` rules (Color BASIC): an IF's body runs to the end of the line; ELSE binds to the nearest unmatched IF; THEN may be crunched (`"X"THEN`, `0THEN`); `IF c GOTO n`, `THEN n`, `ELSE n` and `THEN <expr>` are implicit GOTOs. **Deliberate exception:** inside a loop that opens and closes on the same line (`FOR ...: IF c THEN x: NEXT`), an IF's body is only its own statement, so the NEXT isn't swallowed. FOR/WHILE/DO lines are simply split on colons — the executor runs loops across sublines of one line.

Nesting: `_skip_if_or_else_block()` counts nested IFs by checking `stmt.startswith('IF ')` (not substring match, to avoid false positives from strings like `PRINT "IF THEN"`). GOTO out of an IF block leaves a stale if_stack entry — cleared on next RUN by `clear_all_stacks()`.

## ON ERROR GOTO / RESUME

`ON ERROR GOTO <line>` registers an error handler; `ON ERROR GOTO 0` disables it. When a runtime error occurs during program execution, `_handle_flow_control()` in `program_executor.py` intercepts the error (if a handler is registered and not already in an error handler), saves error state, and jumps to the handler line.

State fields on `CoCoBasic`: `on_error_goto_line`, `error_number` (ERR), `error_line` (ERL), `error_resume_position`, `in_error_handler`. All reset by `clear_interpreter_state()`.

`RESUME` / `RESUME NEXT` / `RESUME <line>` return `resume` / `resume_next` / `jump` directives handled by `_handle_flow_control()`. ERR and ERL are read-only pseudo-variables exposed in `visit_variable()`.

## LOCAL and PRIVATE Variables

`LOCAL var1, var2, ...` inside a GOSUB subroutine saves the listed variables' current values. On RETURN, saved values are restored. This prevents subroutine variable collisions — the main pain point when all variables are global.

`PRIVATE var1, var2, ...` works like LOCAL but additionally initializes each variable to 0 (numeric) or "" (string). This creates clean scratch space — variables start fresh and don't leak after RETURN.

- GOSUB pushes an empty frame onto `local_stack`; LOCAL/PRIVATE append (name, saved_value) entries to the current frame
- PRIVATE also sets each variable to its default value (0 or "") after saving
- RETURN pops the frame and restores variables in reverse order; variables that didn't exist before LOCAL/PRIVATE are removed
- LOCAL/PRIVATE outside GOSUB is a runtime error
- `local_stack` is cleared alongside `call_stack` in `clear_all_stacks()`
- `execute_local` and `execute_private` live in `control_flow.py` (registry commands)

## INPUT Protocol

INPUT pauses execution by returning `{'type': 'input_request', ...}`. Variable targets are described by dicts: `{'name': 'V', 'array': True, 'indices': [1]}` or `{'name': 'X', 'array': False}`. After storing the value via `store_input_value(var_desc, value)`, call `continue_program_execution()` to resume.

## Statement Splitting

`StatementSplitter` in `text_utils.py` owns all statement-splitting and argument-splitting logic:

- `split_on_delimiter()` — split on colons (or custom delimiter), respecting quoted strings and comments: a segment starting with REM, or a `'` outside quotes, consumes the rest of the line (a `'` after a statement becomes its own part). After SAVE/LOAD/KILL/MERGE/CHAIN/CD a `'` quotes a filename instead.
- `split_args(text, keep_empty=False)` — split on commas, respecting parentheses and quotes. The single shared comma-splitter for the entire codebase. `keep_empty=True` keeps empty items (DATA 1,,3).
- `split_on_delimiter_paren_aware()` — generalized version of `split_args()` for non-comma delimiters.
- `is_rem_line()` — REM by **prefix** (CoCo crunching: `REMARK`, `REMEMBER=5` are comments) or `'`. The tokenizer and the converter's keyword scan follow the same rule.

Never duplicate this logic — always call through to `StatementSplitter`. For keyword search in BASIC text (THEN/ELSE/GOTO outside quotes and comments) use `ast_converter.find_keyword()`.

### Immediate mode flow

`process_command()` intercepts LINE INPUT before the registry (since `LINE` would otherwise match the graphics command), then detects multi-statement lines early and routes them to `process_line()`. `process_line()` then takes one of three paths:

1. **Comment** → no-op.
2. **Contains a control structure** (IF/FOR/WHILE/DO anywhere) → `expand_statements()` → `_execute_converted_as_temporary_program()`, which adds the statements to the program as line **−1** (sorts first) followed by END and runs it with `run_program_from_line(-1)`. The real program stays loaded, so jumps into it work and a pending INPUT can be resumed. `finish_immediate_line()` removes line −1 once nothing is pending; LIST/SAVE skip negative lines.
3. **Plain multi-statement** → sequential `process_statement()` loop, stopping on jump or error.

A `GOTO`/`GOSUB` jump typed at the prompt is followed by `_follow_immediate_jump()`: it runs the stored program from that line without clearing variables (an immediate GOSUB's RETURN comes back to the prompt).

### Program storage flow

All program-line edits (typed lines, DELETE, LOAD/MERGE, RENUM, app.py's tab restore) go through `store_program_line(line_num, code)`, which first removes the line's old sublines, DATA values and labels via `_remove_expanded_lines()`. `expand_line_to_sublines()` then compiles the line once: comment lines become a no-op; labels register; everything else goes through `expand_statements()` (colon split + one-line IF expansion). Each subline is then pre-compiled by `_store_subline()`:

1. **Comment** (REM / `'`) → shared no-op `CompiledCommand` (`self._COMMENT`)
2. **DATA** (also crunched `DATA"A"`) → values pre-collected into `data_values` inline, then compiled as `CompiledCommand` (handler is a no-op at runtime)
3. **Multi-line IF** (`IF cond THEN`) → condition pre-parsed to AST, stored as `CompiledMultiLineIf(condition_ast)` — executor evaluates condition and pushes to `if_stack`
4. **File I/O** (PRINT#, INPUT#, LINE INPUT — detected by `_FILE_IO_RE` / `_LINE_INPUT_RE`) → stays as string (AST drops `#`)
5. **AST-parseable** (PRINT, FOR, GOTO, assignments, etc.) → stored as AST node. The parser rejects leftover tokens, so `X=5 6` is a syntax error, not `X=5`.
6. **Registry command** (NEXT, WEND, LOOP, ELSE, ENDIF, DIM, SOUND, etc.) → stored as `CompiledCommand(handler, args, keyword)` — skips tokenization and registry lookup at runtime

At runtime, `_execute_statements_loop()` dispatches four ways: `CompiledMultiLineIf` → condition eval + if_stack, `CompiledCommand` → direct handler call, AST node → `ast_evaluator.visit()`, string → `process_statement()` (file I/O, and an IF whose condition failed to parse, which then reports the syntax error). Skip methods (`_skip_to_next`, `_skip_to_keyword`, `_skip_if_or_else_block`) check `CompiledCommand.keyword`, `CompiledMultiLineIf`, AST loop-node types, and strings.

On RUN, `data_statements` is built from `data_values` in sorted order by `_rebuild_data_statements()` — no re-parsing needed. Parsing logic lives in `DataCommands.parse_data_values()` (static method).

## Dialect

CoCo Color BASIC semantics for shared features, keeping the modern extensions (MOD, WHILE/WEND, DO/LOOP, LOCAL/PRIVATE, labels). Decisions and rationale: `docs/audit_decisions.md`. Key points:

- Precedence (loosest → tightest): OR < AND < NOT < relational (one level, left-to-right) < + − < MOD < * / < unary − < ^ (left-associative). `NOT A=5` is `NOT (A=5)`; `-2^2` = −4; `2^3^2` = 64.
- `^` is computed in floating point; overflow → OVERFLOW error; negative base to a fractional power → ILLEGAL FUNCTION CALL.
- Numbers print CoCo-style via `format_basic_number()` (ast_nodes.py): up to 9 significant digits, `.5` not `0.5`, E notation outside .01 ≤ |x| < 1e9. PRINT, STR$ and PRINT# share it.
- INT is floor; RND(0) is a fresh fraction; each interpreter has its own RNG (`CoCoBasic.rng`); VAL/numeric INPUT use `basic_number_prefix()` (functions.py).
- Undimensioned arrays auto-dimension to 10; DIM A(0) is legal; arrays are capped at `MAX_ARRAY_ELEMENTS`.

## Filesystem sandbox

Every file a BASIC program names resolves through `FileManager.resolve_writable()` / `find_readable()` (program_files.py): confined to `./programs` plus a per-session virtual CD directory (`FileManager.subdir`). Absolute paths, `~`, drive letters, `..` and symlink escapes raise `SandboxError`. The project's bundled `programs/` is a read-only fallback for LOAD/MERGE/CHAIN/OPEN "I". **Never call `os.chdir`** and never build a path from a BASIC filename any other way. KILL keeps its target server-side (`pending_kill`); a client-sent filename is ignored.

## Naming

- **`process_*`**: internal system (`process_command`, `process_statement`)
- **`execute_*`**: registry commands (`execute_next`, `execute_wend`)
- **`visit_*`**: AST execution (`visit_for_statement`, `visit_goto_statement`)

## Rules

- `functions.py` owns all BASIC functions — never duplicate elsewhere
- Graphics commands go in `graphics.py`, DIM/arrays in `variables.py`, control-flow closing commands in `control_flow.py`, DATA/READ/RESTORE in `data_commands.py`
- `GPRINT(x,y),"text"[,color]` draws text on the graphics screen using a 4x6 pixel font. Implemented as registry command in `graphics.py` (server emits `{'type': 'gtext', ...}`), rendered client-side by `drawText()` using `GPRINT_FONT` bitmap data in `dual_monitor.js`
- Graphics helpers: `self.emulator.eval_int(expr)` for expression→int, `_syntax_error(msg, suggestions)` for error responses
- Coordinate syntax: `_parse_coord_pair()` / `_parse_coord_range()` in `graphics.py` handle `(x,y)` and `(x1,y1)-(x2,y2)` (or `-(x2,y2)` from the last LINE end) by parenthesis depth, so array refs and function calls inside coordinates work. All graphics commands use them — don't add regex coordinate parsing
- System OK messages use `_system_ok()` (tagged with `'source': 'system'`)
- File-creating tests must use autouse temp directory fixtures — never write to real `programs/`
- All errors use `error_context.syntax_error()` / `runtime_error()` with 2-3 suggestions. `syntax_error()` auto-prefixes "SYNTAX ERROR:" — don't add it manually.
- Use `error_response(error)` and `text_response(text)` from `error_context` to build response lists — never hand-build `[{'type': 'error', ...}]` or `[{'type': 'text', ...}]`
- To report a caught exception inside another error ("Error in PSET: ..."), use `error_context.wrapped_error(prefix, exc, line, suggestions)` — never `f"...: {e}"`. It keeps only the inner first line and the inner suggestions, so there's no doubled location or Suggestions block. Pass the current line: immediate mode (line 0/-1) prints no location
- Use `basic_truthy(value)` from `ast_nodes` for BASIC boolean conversion — never inline the `isinstance` check
- Use `check_reserved_name(name)` on `CoCoBasic` to guard against reserved function names in assignments and DIM
- Use `clear_all_stacks()` / `clear_interpreter_state()` for stack/state management
- `source venv/bin/activate` before running anything
- Tests: `python -m pytest` (slow tests excluded by default via `-m "not slow"` in pytest.ini)
- Run slow tests explicitly: `python -m pytest -m slow`
- Run all tests: `python -m pytest -m ""`
- Server logs: `./monitor_server_logs.sh` tails `logs/server_latest.log` (created by `./start_server_with_logging.sh`)
