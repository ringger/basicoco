# BasiCoCo Issues

## Not Yet Implemented (from Extended Color BASIC)

Prioritized by how often real CoCo BASIC programs need them.

**High — commonly used in programs:**
- [x] LINE BOX/BF — `LINE (x1,y1)-(x2,y2), color, B` (box) and `BF` (filled box)
- [ ] HEX$ — hex string conversion (display, debugging, base converter programs)
- [ ] ON ERROR GOTO — error trapping (robust programs depend on this)
- [ ] TIMER — system timer function (games, benchmarks, delays)

**Medium — useful but less common:**
- [ ] TRON/TROFF — trace on/off for debugging (helpful for learners)
- [ ] OPEN/CLOSE/PRINT#/INPUT# — sequential file I/O
- [ ] PCLEAR — allocate graphics pages
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

## Known Behavioral Limitations

- GOTO out of a multi-line IF block leaves a stale `if_stack` entry (cleared on next RUN). This matches real CoCo behavior where GOTO from structured blocks is undefined.
- PAINT requires `PAINT(x,y),color` syntax — color is mandatory, unlike some BASIC variants where it defaults.
- DRAW supports basic turtle commands (U/D/L/R/E/F/G/H/M/B/N/S/C) but not angle rotation (A command) or substrings (X command).
- Numbers print with CoCo-style spacing (leading space for positive, trailing space) but comma-zone alignment (16-column zones) is not implemented.

## Refactoring Opportunities

Ordered by dependency and impact. AST migration depends on the split.

1. [ ] Split ast_parser.py (1933 lines) into three modules: `ast_nodes.py` (node classes + enums, ~240 lines), `ast_parser.py` (parser, ~1090 lines), `ast_evaluator.py` (visitor + evaluator, ~575 lines). Only 3 consumers import from it. Clean separation of concerns. Do this before further AST migration to keep files manageable.
2. [ ] Migrate remaining registry commands to AST — SOUND, DIM, READ, ON GOTO/GOSUB, and graphics commands currently use string-based argument splitting with `_split_args()` before passing to `evaluate_expression()`. Full AST migration would add node types, parser rules, and evaluator visitors for each, eliminating structural string parsing entirely. Currently AST-migrated: FOR, IF, PRINT, LET, GOTO, GOSUB, RETURN, INPUT, END, EXIT FOR, WHILE, DO.
