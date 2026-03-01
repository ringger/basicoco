# BasiCoCo Issues

## Open

### Not Yet Implemented (from Extended Color BASIC)

Prioritized by how often real BASIC programs need them.

**High — commonly used in programs:**
- [ ] SGN — sign function (trivial, many math programs use it)
- [ ] RANDOMIZE — seed random number generator (any game with RND needs this)
- [ ] ON ERROR GOTO — error trapping (robust programs depend on this)
- [ ] HEX$ — hex string conversion (frequently used for display/debugging)
- [ ] TIMER — system timer (games, benchmarks, delays)

**Medium — useful but less common:**
- [ ] TRON/TROFF — trace on/off for debugging (helpful for learners)
- [ ] OPEN/CLOSE — file I/O (sequential file access)
- [ ] PCLEAR — clear graphics pages (graphics programs may need it)
- [ ] PPOINT — read pixel color (collision detection in games)
- [ ] OCT$ — octal string conversion

**Low — rarely needed or hard to emulate meaningfully:**
- [ ] PEEK/POKE — memory access (would need a simulated memory map)
- [ ] MEM — free memory (could return a fixed large value)
- [ ] FRE — free string space (could return a fixed large value)
- [ ] FIELD — file field definition (random-access file I/O)
- [ ] GET/PUT (file) — file record I/O (random-access file I/O)
- [ ] VARPTR — variable pointer (rarely used outside machine language interfacing)
- [ ] EXEC — execute machine language (no-op or educational stub)
- [ ] USR — user-defined machine language function (no-op or educational stub)

### Refactoring Opportunities

Ordered by dependency and impact. AST migration depends on the split.

1. [ ] Split ast_parser.py (1925 lines) into three modules: `ast_nodes.py` (node classes + enums, ~240 lines), `ast_parser.py` (parser, ~1090 lines), `ast_evaluator.py` (visitor + evaluator, ~575 lines). Only 3 consumers import from it. Clean separation of concerns. Do this before further AST migration to keep files manageable.
2. [ ] Migrate remaining registry commands to AST — SOUND, DIM, READ, ON GOTO/GOSUB, and graphics commands (PMODE, SCREEN, COLOR, CIRCLE, PAINT, GET, PUT) currently use string-based argument splitting with `_split_args()` before passing to `evaluate_expression()`. Full AST migration would add node types, parser rules, and evaluator visitors for each, eliminating structural string parsing entirely. Currently FOR, IF, PRINT, LET, GOTO, GOSUB, RETURN, INPUT, END are AST-migrated.

## Completed

### DRY Refactoring (March 2026)

- [x] Extract quote-stripping helper in core.py
- [x] Extract coordinate parsing helper in graphics.py
- [x] Extract arg validation helper in functions.py
- [x] Extract graphics mode check helper in graphics.py
- [x] Extract file error handling helper in core.py
- [x] Extract filename validation helper in core.py
- [x] Consolidate path search logic in core.py
- [x] Consolidate test helpers in conftest.py — already well-consolidated
- [x] Refactor operator dispatch in ast_parser.py — kept as-is, special logic per operator
- [x] Consolidate array bounds checking — only 2 locations with different patterns

### Architecture (March 2026)

- [x] Retire ExpressionEvaluator; move AST parser/evaluator onto CoCoBasic
- [x] Extract shared execution engine (_execute_statements_loop, _handle_flow_control)
- [x] Consolidate OK message generation via _system_ok()
- [x] Add _eval_int() and _syntax_error() helpers in graphics.py
- [x] Add standalone CLI REPL (basicoco.py)
- [x] Remove dev_tests/ directory
