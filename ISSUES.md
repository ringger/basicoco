# BasiCoCo Issues

## Open

### Not Yet Implemented (from Extended Color BASIC)

- [ ] PEEK/POKE — memory access (would need a simulated memory map)
- [ ] VARPTR — variable pointer
- [ ] MEM — free memory
- [ ] TIMER — system timer
- [ ] FRE — free string space
- [ ] RANDOMIZE — seed random number generator
- [ ] OPEN/CLOSE — file I/O
- [ ] FIELD — file field definition
- [ ] GET/PUT (file) — file record I/O
- [ ] ON ERROR GOTO — error trapping
- [ ] HEX$ — hex string conversion
- [ ] OCT$ — octal string conversion
- [ ] PCLEAR — clear graphics pages
- [ ] PPOINT — read pixel color
- [ ] TRON/TROFF — trace on/off for debugging
- [ ] EXEC — execute machine language (could be a no-op or educational stub)
- [ ] USR — user-defined machine language function (same)
- [ ] SGN — sign function

### Refactoring Opportunities

- [ ] Split ast_parser.py (1925 lines) into three modules: `ast_nodes.py` (node classes + enums, ~240 lines), `ast_parser.py` (parser, ~1090 lines), `ast_evaluator.py` (visitor + evaluator, ~575 lines). Only 3 consumers import from it. Clean separation of concerns.

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
