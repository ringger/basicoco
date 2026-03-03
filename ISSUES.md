# BasiCoCo Issues

## Not Yet Implemented (from Extended Color BASIC)

Prioritized by how often real CoCo BASIC programs need them.

**Medium — useful but less common:**
- [ ] PCLEAR — allocate graphics pages
- [ ] MEM — free memory (could return a fixed large value)
- [ ] FRE — free string space (could return a fixed large value)

**Low — rarely needed or hard to emulate meaningfully:**
- [ ] PEEK/POKE — memory access (would need a simulated memory map)
- [ ] FIELD — file field definition (random-access file I/O)
- [ ] GET/PUT (file) — file record I/O (random-access file I/O)
- [ ] VARPTR — variable pointer (rarely used outside machine language interfacing)
- [ ] EXEC — execute machine language (no-op or educational stub)
- [ ] USR — user-defined machine language function (no-op or educational stub)

## Known Behavioral Limitations

- **DRAW A/X not supported** — angle rotation (A) and substring execution (X) are silently skipped by the draw parser but not implemented.
- **PAINT trailing-comma edge case** — `PAINT(x,y),` (trailing comma, no color value) defaults to color 1 rather than raising an error. The no-comma case (`PAINT(x,y)`) correctly raises a syntax error.
- **GOTO out of multi-line IF** leaves a stale `if_stack` entry (cleared on next RUN). This matches real CoCo behavior where GOTO from structured blocks is undefined.

## Refactoring Opportunities

Ordered by dependency and impact.

1. [ ] **Migrate remaining registry commands to AST** — SOUND, DIM, READ, ON GOTO/GOSUB, and graphics commands currently use string-based argument splitting with `BasicParser.split_args()` before passing to `evaluate_expression()`. Full AST migration would add node types, parser rules, and evaluator visitors for each, eliminating structural string parsing entirely. Currently AST-migrated: FOR, IF, PRINT, LET, GOTO, GOSUB, RETURN, INPUT, END, EXIT FOR, WHILE, DO.
2. [ ] **Eliminate AST converter round-trip** — the AST converter parses single-line control structures (e.g., `IF A=1 THEN B=2: C=3`) into AST nodes, then serializes them back to text strings for storage, and the AST parser re-parses those strings at execution time. Storing AST nodes directly in `expanded_program` would avoid the double parse, but requires rearchitecting the execution engine to work with AST nodes instead of text sublines.
3. [ ] **Pre-collect DATA at store-time** — DATA statements are currently re-parsed every RUN. Since their values are static, they could be collected into a structured map when program lines are stored, eliminating runtime parsing. Low impact (DATA-heavy programs are rare) but conceptually cleaner.