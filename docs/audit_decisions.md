# Audit follow-up: decisions log (Sept 2026)

Decisions made while fixing the findings of the September 2026 full-project
audit. Items marked **(user)** were chosen by Eric; items marked **(auto)**
were made autonomously overnight under the standing instruction "go ahead
with your recommendations and record them" — review these.

Task numbers (#N) refer to the audit task list.

## Semantics / dialect

| # | Decision | Who | Notes |
|---|----------|-----|-------|
| 40, 44 | Target **CoCo Color BASIC semantics** for shared features, keeping the modern extensions (MOD, WHILE, DO, LOCAL/PRIVATE, labels). | user | |
| 4 | **RND(0) returns a fresh fraction** in [0,1), as on CoCo (not MS BASIC-80's repeat-last). RND(x) for 0<x<1 behaves like RND(0). `last_rnd` removed. | user | Old `test_rnd_semantics.py` repeat-last tests rewritten. |
| 4 | **Per-interpreter RNG** (`CoCoBasic.rng`); RND(-n) and RANDOMIZE no longer reseed other sessions. | auto | Unambiguous bug fix. |
| 5 | **INT is floor** (INT(-3.5) = -4). | auto | True of every Microsoft-derived BASIC incl. Color BASIC. Two old tests asserted truncation; corrected. |
| 10 | **Undimensioned arrays auto-dimension to 10** on first use. | user | Old tests that used `UNDIM(999)=5` to force an error now expect BAD SUBSCRIPT. A consequence: an unknown name with parentheses, e.g. `FOO(5)`, is an array (as on CoCo), not an "undefined function" error. |
| 10 | `DIM A(0)` legal; total elements capped at **1,000,000** (`MAX_ARRAY_ELEMENTS`, variables.py) → OUT OF MEMORY error. | auto | Cap value is a judgment call (server memory safety). |
| 6 | Empty DATA items (`DATA 1,,3`) read as 0 / "". READ into a numeric variable from non-numeric DATA → TYPE MISMATCH error (real CoCo says ?SN ERROR in the DATA line; the clearer message was preferred). READ into a string variable converts numbers to their text. | auto | `split_args(keep_empty=True)` added to the shared splitter rather than a new one. |
| 9 | **VAL** follows MS BASIC prefix parsing: spaces ignored, &H/&O accepted, stops at the first non-numeric char, overflow → error. Implemented as `basic_number_prefix()` in functions.py. | auto | |
| 12 | STRING$ code outside 0–255, or an empty string argument → ILLEGAL FUNCTION CALL. | auto | |

## Filesystem sandbox

| # | Decision | Who | Notes |
|---|----------|-----|-------|
| 1, 3 | **Sandbox everywhere** (web server and local basicoco.py). Every filename resolves inside `./programs` (the writable root) via `FileManager.resolve_writable()` / `find_readable()`. Absolute paths, `~`, drive letters and `..` are refused; symlinks resolving outside are rejected. | user | |
| 1 | The project's bundled `programs/` is a **read-only fallback** for LOAD / MERGE / CHAIN / OPEN "I". KILL, SAVE and OPEN "O"/"A" only touch the writable root — so KILL can no longer delete a bundled program when the server runs from another directory. | auto | |
| 3 | **CD is a per-session virtual directory** inside programs/ (`FileManager.subdir`); `os.chdir` is never called. `CD "/"` and `CD "~"` go to the programs root; `CD ".."` stops at the root; `CD` alone prints `CURRENT DIRECTORY: PROGRAMS/...`. | user (auto: "~" and "/" both mean root) | Old CD tests that asserted a real chdir were rewritten. |
| 1 | **Paths are relative to programs/**: `SAVE "sub/pathtest"` writes `programs/sub/pathtest.bas` (a test that saved `"programs/pathtest"` was updated). | auto | |
| 2 | KILL records the target server-side (`FileManager.pending_kill`); the confirmation carries only Y/N and **any client-sent filename is ignored**. The input_request no longer leaks the absolute path. KILL confirmation now also works in the standalone basicoco.py CLI (it was never wired up). | auto | |
| 11 | LOAD / SAVE / MERGE / CHAIN / KILL / CD evaluate string-expression filenames (`SAVE F$`), like OPEN already did. | auto | |
| 7 | OPEN reports every OSError (e.g. a directory) as a BASIC FILE ERROR; INPUT#/LINE INPUT# report BAD SUBSCRIPT instead of silently dropping the value; EOF is true when only blank lines remain; the FILE MODE ERROR wording is no longer inverted. | auto | |
| 9 | Interactive INPUT of a number now parses like VAL (`12ABC` → 12, was 0). Real CoCo would print ?REDO and re-prompt; not implemented. | auto | Deduplicates the number heuristic. |

## Web server

| # | Decision | Who | Notes |
|---|----------|-----|-------|
| 26 | Server binds **127.0.0.1 by default**; LAN exposure is opt-in via `BASICOCO_HOST=0.0.0.0` (logs a no-authentication warning). Socket.IO accepts **same-origin only** (was `*`); extra origins via `BASICOCO_CORS_ORIGINS`. `DEBUG=true` with a non-loopback host refuses to start (Werkzeug debugger = remote code execution). | auto | **Behaviour change**: to reach the server from another machine you now must set BASICOCO_HOST. |
| 27 | Each interpreter has a `command_lock`; execute/input/continue/resume handlers run under it (`@_exclusive`), so a second command **waits** instead of racing. Ctrl+C never blocks: if a program is executing it sets `break_requested`, which the executor checks every statement and stops with `BREAK IN n` (CONT-able). | auto | |
| 27 | At most **16 interpreters (tabs) per connection**; the client now sends `close_tab` so closed tabs free their interpreter. | auto | Limit value is a judgment call. |
| 28 | Returning to a tab no longer auto-continues a program that is waiting for INPUT. | auto | Its live-server test was not re-run against the old code (it relies on the audit's probe of the bug). |
| 30 | A disconnected client's session is kept for **10 minutes** (`SESSION_GRACE_SECONDS`); on reconnect the client offers its old session id (Socket.IO `auth`) and gets its tabs/programs back ("RECONNECTED - PROGRAMS KEPT"). Only orphaned sessions can be resumed; unknown ids get a fresh session. A program executing at disconnect is asked to stop. | auto | Session ids are random UUIDs. |
| 29 | Client: INKEY$ keys go to the active tab; keys are forwarded during any immediate command (not just `RUN`); a forwarded key isn't also typed into the command line; Ctrl+C resets the text display's input flag. | auto | **JS changes are syntax-checked only — not exercised in a browser.** |
| 31 | Client: SOUND notes are queued back-to-back on the AudioContext timeline (a melody in a loop plays every note); Ctrl+C silences queued notes. | auto | Same caveat: not exercised in a browser. |
| 8 | PCLS c clears to color c (server and client). DRAW `M` draws (BM doesn't). The server tracks drawn pixels (LINE, boxes, CIRCLE, DRAW, PSET/PRESET; clipped to 256×192) so PPOINT answers correctly. | auto | PAINT fills and GPRINT text are not pixel-tracked. |
| 32 | Log level from `BASICOCO_LOG_LEVEL` (default INFO); `start_server_with_logging.sh` defaults to DEBUG. Debug pretty-printing of output is lazy (no cost when DEBUG is off). Removed the ineffective FLASK_ENV/FLASK_DEBUG exports. | auto | Each start writes a new log file, so no rotation added; the 60 MB of old logs in logs/ can be pruned by hand. |

## Interpreter behaviour

| # | Decision | Who | Notes |
|---|----------|-----|-------|
| 14 | All program-line edits go through one method, `CoCoBasic.store_program_line()` (typed lines, DELETE, LOAD/MERGE, RENUM, app.py tab restore). | auto | Removes 3 duplicated copies. |
| 16, 66 | The runaway-loop guard (50k / 10M statements) budgets **each uninterrupted slice** of execution: the counter resets whenever a program resumes after INPUT, PAUSE or a graphics auto-yield. | auto | Consequence: an animation loop that yields every frame never trips the guard; Ctrl+C (task #27) is the way to stop it. |
| 18, 43 | NEXT honours its variable list (`NEXT J,I`) and unwinds abandoned inner loops (MS BASIC). Re-executing FOR for an active variable discards that loop — **but only within the current GOSUB level**, so a subroutine's `LOCAL I` + `FOR I` leaves the caller's `FOR I` intact (keeps the LOCAL extension's documented behaviour). | auto | |
| 21 | RENUM refuses (error) when the new numbering would reorder lines, and also renumbers ELSE / RESTORE / RESUME targets. | auto | |
| 23 | Malformed LOOP/IF conditions are syntax errors (were silently false). `evaluate_condition()` now propagates errors. | auto | |
| 24 | RESUME accepts a label (labels win over same-named variables, as with GOTO). | auto | |

## Parser / single-line control structures

| # | Decision | Who | Notes |
|---|----------|-----|-------|
| 36, 37, 38, 42 | **Rewrote ast_converter.py as a text-level expander.** Statements are split on colons and kept verbatim (no AST→text round trip, so parentheses can't be lost). Only one-line IFs are expanded (`IF c THEN` / body / [`ELSE` / body] / `ENDIF`); FOR/WHILE/DO lines are plain colon splits, since the executor already runs loops across sublines of one line. | auto | Fixes statements-after-NEXT, nested one-line FORs, dropped parens, crunched THEN, REM colons, ELSE binding. |
| 42 | ELSE binds to the **nearest unmatched IF**; THEN may be crunched (`"X"THEN`, `0THEN`); `IF c GOTO n`, `THEN n`, `ELSE n` and `THEN <expression>` are implicit GOTOs. | auto | A branch is treated as a GOTO target when it doesn't start with a command word and has no top-level `=`/`,`/`;`. |
| 36 | **Deliberate deviation from CoCo kept:** inside a loop that opens and closes on the same line (`FOR I=1 TO 3: IF I=2 THEN PRINT "TWO": NEXT I`), an IF's body is only its own statement, so the NEXT isn't swallowed. Everywhere else an IF's body runs to the end of the line (CoCo). | auto — **review** | Existing tests and programs relied on this; real Color BASIC would put NEXT inside the IF. |
| — | A one-line IF whose branches are only GOTOs stays a single subline (no if_stack entry to leak on each taken jump, e.g. `IF A$="" THEN 10`). | auto | GOTO out of a multi-statement IF block still leaves a stale if_stack entry (pre-existing, documented). |
| 40 | Operator precedence now Color BASIC: OR < AND < **NOT** < relational (one level, left-to-right) < + − < **MOD** < * / < unary − < **^ (left-assoc)**. `=<`, `=>`, `><` accepted. | user (dialect) + auto | `NOT A=5` = NOT(A=5); `-2^2` = −4; `2^3^2` = 64; `10 MOD 3*2` = 4. |
| 40 | MOD rounds operands to integers and truncates toward zero (`-7 MOD 3` = −1). | auto | Microsoft BASIC semantics; CoCo itself has no MOD. |
| 39 | `^` computed in floating point (so `9^9^9` → OVERFLOW instantly instead of hanging the server); integer results stay integers when exact. Overflow in + − * / ^ → OVERFLOW error; negative base to fractional power → ILLEGAL FUNCTION CALL. All these are BASIC errors (trappable by ON ERROR) via one shared `BASIC_RUNTIME_ERRORS` tuple in error_context.py. | auto | |
| 44 | Numbers print CoCo-style: up to 9 significant digits, no leading 0 (`.5`), E notation outside .01 ≤ \|x\| < 1e9 (`1.26765061E+30` style, trailing zeros dropped, `1E-03`). Shared by PRINT, STR$, PRINT#: `format_basic_number()` in ast_nodes.py. | user (dialect) + auto | Exact CoCo rounding of the 9th digit may differ in edge cases. |
| 41 | **Strict parsing**: leftover tokens are a syntax error (`X=5 6`, `PRINT 1 2`); unknown characters are syntax errors (were silently dropped); `&HFF`/`&O17` literals; `?` = PRINT; `'` starts a comment; `1.2.3` and `1E` no longer leak Python messages. | auto | `#` is still tolerated by the tokenizer (file I/O is intercepted earlier). |

## Comments and crunched spacing (task #73, from the AST-usage survey #71)

| # | Decision | Who | Notes |
|---|----------|-----|-------|
| 73 | `'` is a comment (Extended Color BASIC shorthand for REM), both at the start of a line/statement and after a statement (`SOUND 100,5 ' beep`). **Exception:** after SAVE/LOAD/KILL/MERGE/CHAIN/CD a `'` quotes a filename (`SAVE 'GAME'`), which existing tests and users rely on. | auto | |
| 73 | **REM matches by prefix everywhere** (as the CoCo's keyword cruncher does): `REMARK` and `REMEMBER=5` are comments. The splitter, `is_rem_line` and the tokenizer now agree (previously they disagreed). | auto | One old test asserting `REMEMBER=5` splits as a variable was changed; another old test already asserted it's REM. |
| 73 | Comment sublines compile to a no-op instead of being re-dispatched as text on every execution. | auto | |
| 73 | Block IF recognised when written `IF(A=1)THEN` or followed only by a comment (`IF c THEN REM …`, `IF c THEN ' …`). | auto | |
| 73 | Accepted spacing variants: `DATA"A"`, `LINE  INPUT`, `LOOP WHILE(X<3)`. `LOOP` followed by anything other than WHILE/UNTIL/comment is a syntax error. | auto | |
| 78 | Crunched keywords generally (`SOUND100,5`, `FORI=1TO10`) are **not** supported — decided by the user: keep requiring spaces (see the #78 row below). | user | |

## Immediate mode, CHAIN, RENUM and other parsing fixes

| # | Decision | Who | Notes |
|---|----------|-----|-------|
| 19 | An immediate-mode line with control structures now runs **alongside** the stored program as a temporary line −1 (ending in END), not in place of it. It is removed when execution finishes and is never LISTed or SAVEd. So `IF X THEN GOTO 100` and INPUT inside an immediate loop now work. | auto | Replaces the save/restore-state approach, which discarded a pending INPUT. |
| 19 | `GOTO n` / `GOSUB n` typed at the prompt **run the stored program from line n** without clearing variables (CoCo behaviour). An immediate GOSUB's RETURN comes back to the prompt. An undefined target is UNDEFINED LINE. STOP typed at the prompt prints BREAK and does not arm CONT. | auto | Two old tests asserting a raw `jump` directive were updated. |
| 20 | CHAIN inside a running program returns a `chain` directive; the executor switches to the new program in the **same loop** (no nesting), so INPUT in a chained program resumes correctly and self-CHAIN loops don't hit Python's recursion limit. CHAIN typed at the prompt still starts a run. | auto | |
| 22 | Position lookups use binary search (bisect). A 20k-iteration loop in a 5,000-line program went from 0.96 s to 0.03 s. | auto | |
| 24 | Unknown command categories are created instead of dropped; RESUME moved to 'control', 'file' added — HELP lists every command. | auto | |
| 74 | RENUM rewrites only real jump targets, via a quote/comment-aware scan (never text inside strings or REMs); handles crunched `GOTO10`. | auto | |
| 75 | One graphics coordinate parser (`_parse_coord_range`) matches `(x1,y1)-(x2,y2)` by parenthesis depth; supports `LINE -(x,y)` from the last LINE end point; GET fixed; SCREEN/COLOR always split arguments properly; parenthesis matching ignores quoted text. | auto | `CommandRegistry.is_coordinate_pair_syntax`/`parse_line_coordinates` are now used only by their own tests (dead code, see #25). |
| 76 | File-number expressions may contain commas (`PRINT #F(1,2),X`); `LINE INPUT A$(3)` stores into the array element. | auto | PRINT# items are still parsed by file_io's own tokenizer, not the AST PRINT parser. |
| 77 | `10PRINT` accepted as a program line; `DATA &HFF,&O17` read as numbers; ERR classified from the error's first line with quoted text removed (user DATA can't change ERR). | auto | Not true typed error codes yet. |
| — | `continue_program_execution` clears `waiting_for_input` itself (resuming means the answer arrived). | auto | |
| 47 | `BlockNode` is live (multi-statement IF branches parse to it), so `visit_block` was **fixed**, not removed: it now stops at the first error, INPUT/PAUSE or flow-control directive (it checked a misspelled `exit_for`). `ELSE <line>` validates its target like `THEN <line>`. Removed as unused: `ProgramNode`, `NodeType.PROGRAM`, `visit_program`, `StatementSplitter.expand_line_to_sublines` (its 6 tests only re-tested `split_on_delimiter` cases that are already covered directly). | auto | |
| 25 | Removed code with no production callers: `core.clear_program`, `save_execution_state`/`restore_execution_state`, `StatementSplitter.has_control_keyword`/`CONTROL_KEYWORDS` (superseded by `ast_converter.starts_control_structure`), `CommandRegistry.parse_coordinates`/`is_coordinate_pair_syntax`/`parse_line_coordinates` (superseded by graphics' `_parse_coord_range`), the unused `pause_duration` field. Their tests were **ported** to the replacements where the cases were not already covered (control-structure detection; 2-D array coordinates in LINE), not just deleted. PAUSE no longer does its own resume-point bookkeeping (the executor's pause handler already does it). `run_program_from_line` is now a thin wrapper over `run_program(start_line=…)`, and every run resets the iteration counter. | auto | |
| 12 | Graphics argument validation: `COLOR` outside 0-8, `PMODE` mode outside 0-4 or start page outside 1-8 → ILLEGAL FUNCTION CALL (with suggestions). `SCREEN m,c`: any nonzero color set means set 1, as on the CoCo (not an error). A string where a graphics command needs a number (`PSET(A$,1)`) → TYPE MISMATCH via `eval_int`, instead of a leaked Python `int()` message. | auto | Off-screen PSET/LINE coordinates are still clipped silently (#8), not an FC error. CIRCLE's ratio/arc arguments are still ignored; that feature is folded into #62. |
| 12 | `INSTR(0,…)` → ILLEGAL FUNCTION CALL (was silently clamped to 1; one old test updated). No upper limit on the start position, because this project's strings aren't capped at 255. `LEN(number)` → TYPE MISMATCH (was the length of its text). | auto | CoCo semantics per the dialect decision. |
| 13 | **Error line attribution**: immediate-mode errors show no line (was "at line 0", sometimes twice), as on the CoCo; program errors name their line once (parser errors used to say "at line 1"; PRINT-expression errors had no line). New `ErrorContextManager.wrapped_error()` is the one way to wrap an inner error: it keeps the inner first line and the inner suggestions, so no doubled "Suggestions:" block. Runtime errors in immediate statements are no longer labelled "SYNTAX ERROR" (`X=Q(20)` → `BAD SUBSCRIPT`). | auto | |
| 13 | Every error site found with 0-1 suggestions now has at least 2, including EOF's errors (which used to be plain ValueErrors), file errors and graphics errors. Removed as unused: `ErrorContextManager.push_context/pop_context/execution_stack/warning/get_stack_trace`, the global `error_context` instance and the legacy dict helpers (`create_legacy_error`, `syntax_error()`, ... at module level), and `VariableManager.set_variable/_calculate_linear_index/_get_default_value`. The "unused import in functions.py" finding was stale: every import is used. | auto | |
| 45 | **Type checking** (CoCo ?TM): strings may only be concatenated (`+`) or compared (`= <> < > <= >=`) with other strings; any other operator on a string, and any string/number mix, is TYPE MISMATCH (ERR 13, trappable by ON ERROR). `"A"*2` used to give "AA" (Python semantics). Assignment checks the `$` suffix: `A = "X"`, `A$ = 5`, `N(1) = "S"` are TYPE MISMATCH (they used to be stored silently). `FOR A$=…`, string FOR bounds (even numeric-looking ones like `"1"`, which used to be converted), and `LINE INPUT` into a numeric variable are TYPE MISMATCH too. | auto | Python-level string comparison (by code point) matches CoCo's ASCII ordering. |
| 35 | **CLI**: Ctrl+C used to *disconnect* the CLI from the server, because engine.io installs its own SIGINT handler; the client is now created with `handle_sigint=False`. Ctrl+C now sends BREAK during *any* command (not only RUN, so it works for `GOTO 100` or an immediate loop), and the CLI stays connected. The 30 s RUN timeout (which returned to the prompt while the program was still printing) and the unbounded wait for other commands are replaced by one wait that ends on completion or on a dropped connection. CLS clears the terminal (the CLI listened for a `clear` message the server never sends). New e2e tests cover Ctrl+C and CLS. | auto | |
| 35 | **Web client** (syntax-checked with `node --check`; not exercised in a browser): removed handlers for messages the server never sends (`draw`, `clear_graphics`, `set_pmode`) and the `executeDraw` stub; Copy copies the real text buffer (it used to copy a placeholder); the graphics info shows the real background color name (every non-black was "Green"); removed the SVG button, which only showed "coming soon", and the help lines advertising SVG export and "Share programs via URL". | auto | **Left for review**: `saveSession`/`loadSession` and the auto-save preference are half-built (`loadSession` is never called, and saved ImageData serializes to `{}`). Finish them or remove them? The server-side reconnect grace (#30) already keeps programs across a reload within 10 minutes. |
| 53 | Tests strengthened: the pycuber gate (`tools/validate_moves.py`, 11 tests) is collected via `tests/unit/test_validate_moves.py`, so `-m slow` / `-m ""` run it; vacuous assertions (`len(result) >= 0`, bare `isinstance(result, list)`, `if result is not None:`) replaced with real ones; the TIMER tests use a frozen clock instead of a ±10-tick tolerance; new tests for GET/PUT, GPRINT and CLEAR. Two bugs they found: `CLEAR n` printed "OK" in the middle of a running program (now silent while running), and `PUT` accepted any action word (now PSET/PRESET/AND/OR/NOT, else SYNTAX ERROR). | auto | The web client only draws PUT's PSET action; the others do nothing (added to #34). |
| 34 | GPRINT text is uppercased on the server (the 4×6 font, like the CoCo's, has no lowercase, so lowercase drew as "?"), and numbers use BASIC formatting (`GPRINT(0,0),4/2` drew "2.0"). The other #34 items are client-only rendering fixes that need a browser to verify, so they were left for a supervised session. | auto | |
| 34 | **Client rendering fixed** (user asked, 2026-09-21): CIRCLE is drawn with the server's midpoint algorithm in whole BASIC pixels (the antialiased arc left blended edges PAINT could leak through); PUT implements PRESET/AND/OR/NOT; a new tab gets proper default colors and tabs save/restore their colors, GET blocks and text history; the command being typed is kept in the scrollback buffer, wraps at 80 columns and leaves no stale cursor block; the GPRINT font gains `# $ % & ; < = > @ [ \ ] ^ _`. | user | The browser extension wasn't connected, so this was verified with `tests/client/dual_monitor_harness.js`: the real client code running in Node on a fake canvas with real pixels, cross-checked against the server's circle pixels (17 checks; the pre-fix client fails 16). Not yet looked at in a real browser. |
| 69 | `rubiks_interactive.bas` offers all nine turns (7=LEFT, 8=BOTTOM, 9=BACK added; the engine already had them), with a new test that drives the menu through INPUT and checks the exact turns. **Left as they are**: the unused S slice / X,Y,Z in the engine (they fold into #56's table-driven ApplyMove); `rubiks_cube_rotate.bas` and `rubiks_test_moves.bas` duplicating engine code, because they're deliberately self-contained demos that don't MERGE the library. | auto | |
| 78 | **Decided (user, 2026-09-21): keep requiring spaces around keywords.** Crunched keywords (`FORI=1TO3`, `GOTO10`, `SOUND100,5`, `IFX=1THENPRINT"Y"`) are SYNTAX ERRORs today (crunched *line numbers* like `10PRINT` and `"X"THEN` do work, #77/#38). Real Color BASIC accepts them because its tokenizer matches keywords anywhere, and the price is that no variable name may contain a keyword (`TOTAL` holds TO, `FORM` holds FOR, `SCORE` holds OR). Adopting that would break names the bundled programs use. **Recommendation: keep requiring spaces around keywords**, and maybe add a clearer hint ("put a space after GOTO") when an unknown word starts with a keyword. | user | Recommendation accepted. |
| 79 | **PMODE 0-4 follow the CoCo** (user asked, 2026-09-21): every mode uses 0-255 × 0-191 coordinates; lower modes only have coarser pixels (PMODE 0/1: 2×2 coordinates per pixel, 2/3: 2×1). The client used to scale coordinates per mode, so in PMODE 1-3 most of the screen was drawn off-canvas. **PMODE 0 is a graphics mode**: it used to be treated as "text mode", so drawing after `PMODE 0` gave ILLEGAL FUNCTION CALL. "No PMODE yet" is now `None` (server) / `null` (client). PPOINT snaps to the mode's pixel, as on the CoCo (in PMODE 1, `PSET(1,1)` lights (0,0) too). GPRINT draws each font pixel as one mode pixel, so text stays legible in coarse modes. | user | Checked by server tests, the Node harness (16 new checks) and headless-Chrome tests in PMODE 0/1/3/4. |
| 25 | `min_args` / `max_args` on `CommandRegistry.register` are **left in place** but not enforced: no command passes them, and enforcing them would mean auditing every handler's argument count. | auto | |
| 25 | **Dropped (user, 2026-09-21)**: `min_args` / `max_args` removed from `CommandRegistry.register`. Each handler already validates its own arguments with command-specific errors, and a generic comma count fits BASIC syntax badly (`LINE(0,0)-(9,9),PSET,BF`). | user | |

## Rubik's cube programs

| # | Decision | Who | Notes |
|---|----------|-----|-------|
| 63 | Step 6 no longer applies a net U rotation; RotateCorrectToTFR's setup turn is undone after the algorithm (UD$). | auto | Audit's verified patch; 1,519/1,519 scrambles solve. |
| 64 | Step 1 flipped-edge insertions: TI=1 `bR`, TI=3 `fLF`. | auto | Found by brute-force search against pycuber. |
| 65 | Scramble uses face turns only (R U F L D B). | auto | |
| 51 | AlignMidEdge scratch variable renamed SC → SK (SC is the render scale). | auto | |
| 67 | R and L animation rotation signs swapped. ROT-X keeps its formula (it turns like L). | auto | The ISSUES.md z-sort diagnosis was wrong; to be updated with the docs task. |

## Tests / tooling

| # | Decision | Who | Notes |
|---|----------|-----|-------|
| 48 | `testpaths = tests` (was `tests/unit`). | auto | |
| 49 | 8 old e2e/cli files removed (`git rm`); replaced by `tests/integration/e2e/test_cli_sessions.py` + a `live_server` fixture that starts app.py in a temp dir on a free port. | user approved removal | |
| 50, 33 | `pycuber`, `pytest-timeout` added to requirements.txt. | auto | |
| 33 | `Werkzeug==3.1.6` and `simple-websocket==1.1.0` pinned at the versions installed and tested (Werkzeug was unpinned; Flask 2.3 accepts anything ≥ 2.3.7). The Flask 2.3 / Flask-SocketIO 5.3 stack was **not** upgraded: that needs package installs, so it waits for approval. | auto | |
| 33 | **Upgraded (user, 2026-09-21)** to Flask 3.1.3, Flask-SocketIO 5.6.1, python-socketio 5.17.0, python-engineio 4.14.0, Werkzeug 3.1.8. No code changes were needed; the full suite (1948 tests, including live-server, websocket and CLI e2e) passes. | user | Previous environment saved as a `pip freeze` in the session scratchpad. |
| — | `tests/unit/test_utilities.py` removed; stray `programs/CHARTDATA.DAT` removed (backed up to the session scratchpad). | user | |
