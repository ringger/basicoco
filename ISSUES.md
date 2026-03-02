# BasiCoCo Issues

## Not Yet Implemented (from Extended Color BASIC)

Prioritized by how often real CoCo BASIC programs need them.

**Medium — useful but less common:**
- [ ] OPEN/CLOSE/PRINT#/INPUT# — sequential file I/O
- [ ] PCLEAR — allocate graphics pages
- [ ] PPOINT — read pixel color as a function; collision detection in games

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

- **DRAW B/N/S parsed but silently no-op'd** — B (pen-up/blind move), N (no-draw then return to origin), and S (scale) are parsed by `BasicParser` but `_execute_draw_command` has no handler for them. All three silently do nothing — B doesn't move without drawing, N doesn't return to origin, S doesn't apply scale.
- **DRAW A/X not supported** — angle rotation (A) and substring execution (X) are silently consumed by the parser but not implemented.
- **RND ignores its argument** — `RND(0)` should repeat the last value, `RND(-n)` should reseed. Currently all arguments are ignored and `random.random()` is always called.
- **PAINT trailing-comma edge case** — `PAINT(x,y),` (trailing comma, no color value) silently defaults to color 1 instead of raising an error. The no-comma case (`PAINT(x,y)`) correctly raises a syntax error.
- **PRINT comma zones not implemented** — commas emit a tab character rather than advancing to the next 16-column zone as real CoCo BASIC does.
- **GOTO out of multi-line IF** leaves a stale `if_stack` entry (cleared on next RUN). This matches real CoCo behavior where GOTO from structured blocks is undefined.

## Refactoring Opportunities

Ordered by dependency and impact. AST migration depends on the split.

1. [ ] Split ast_parser.py (~1940 lines) into three modules: `ast_nodes.py` (node classes + enums, ~240 lines), `ast_parser.py` (parser, ~1090 lines), `ast_evaluator.py` (visitor + evaluator, ~575 lines). Only 3 consumers import from it. Clean separation of concerns. Do this before further AST migration to keep files manageable.
2. [ ] Migrate remaining registry commands to AST — SOUND, DIM, READ, ON GOTO/GOSUB, and graphics commands currently use string-based argument splitting with `BasicParser.split_args()` before passing to `evaluate_expression()`. Full AST migration would add node types, parser rules, and evaluator visitors for each, eliminating structural string parsing entirely. Currently AST-migrated: FOR, IF, PRINT, LET, GOTO, GOSUB, RETURN, INPUT, END, EXIT FOR, WHILE, DO.
