# BasiCoCo Issues

## Not Yet Implemented (from Extended Color BASIC)

Prioritized by how often real CoCo BASIC programs need them.

**High — affects common programs:**
- [x] PRINT comma zones — commas advance to next 16-column zone. `print_column` tracks position across inline PRINT statements.
- [x] RND argument semantics — `RND(0)` repeats last value, `RND(-n)` reseeds. `last_rnd` state on emulator.

**Medium — useful but less common:**
- [x] OPEN/CLOSE/PRINT#/INPUT# — sequential file I/O (OPEN "I"/"O"/"A", CLOSE, PRINT#, INPUT#, LINE INPUT, EOF)
- [ ] PPOINT — read pixel color as a function; collision detection in games
- [ ] DRAW B/N/S — pen-up move, no-draw return, and scale are parsed but silently no-op'd
- [ ] PCLEAR — allocate graphics pages

**Low — rarely needed or hard to emulate meaningfully:**
- [ ] PEEK/POKE — memory access (would need a simulated memory map)
- [ ] MEM — free memory (could return a fixed large value)
- [ ] FRE — free string space (could return a fixed large value)
- [ ] FIELD — file field definition (random-access file I/O)
- [ ] GET/PUT (file) — file record I/O (random-access file I/O)
- [ ] VARPTR — variable pointer (rarely used outside machine language interfacing)
- [ ] EXEC — execute machine language (no-op or educational stub)
- [ ] USR — user-defined machine language function (no-op or educational stub)

## Known Behavioral Limitations

- **DRAW A/X not supported** — angle rotation (A) and substring execution (X) are silently consumed by the parser but not implemented.
- **PAINT trailing-comma edge case** — `PAINT(x,y),` (trailing comma, no color value) defaults to color 1 rather than raising an error. The no-comma case (`PAINT(x,y)`) correctly raises a syntax error.
- **GOTO out of multi-line IF** leaves a stale `if_stack` entry (cleared on next RUN). This matches real CoCo behavior where GOTO from structured blocks is undefined.

## Refactoring Opportunities

Ordered by dependency and impact. AST migration depends on the split.

1. [ ] Split ast_parser.py (~1940 lines) into three modules: `ast_nodes.py` (node classes + enums, ~240 lines), `ast_parser.py` (parser, ~1090 lines), `ast_evaluator.py` (visitor + evaluator, ~575 lines). Only 3 consumers import from it. Clean separation of concerns. Do this before further AST migration to keep files manageable.
2. [ ] Migrate remaining registry commands to AST — SOUND, DIM, READ, ON GOTO/GOSUB, and graphics commands currently use string-based argument splitting with `BasicParser.split_args()` before passing to `evaluate_expression()`. Full AST migration would add node types, parser rules, and evaluator visitors for each, eliminating structural string parsing entirely. Currently AST-migrated: FOR, IF, PRINT, LET, GOTO, GOSUB, RETURN, INPUT, END, EXIT FOR, WHILE, DO.
