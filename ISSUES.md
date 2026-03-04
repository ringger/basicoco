# BasiCoCo Issues

## Not Yet Implemented (from Extended Color BASIC)

Low priority — rarely needed or hard to emulate meaningfully:

- [ ] PEEK/POKE — memory access (would need a simulated memory map)
- [ ] FIELD — file field definition (random-access file I/O)
- [ ] GET/PUT (file) — file record I/O (random-access file I/O)
- [ ] VARPTR — variable pointer (rarely used outside machine language interfacing)
- [ ] EXEC — execute machine language (no-op or educational stub)
- [ ] USR — user-defined machine language function (no-op or educational stub)

## Known Behavioral Limitations

- **GOTO out of multi-line IF** leaves a stale `if_stack` entry (cleared on next RUN). This matches real CoCo behavior where GOTO from structured blocks is undefined.

## Refactoring Opportunities

Ordered by impact. Items 2 and 3 are independent of each other.

1. [ ] **Teach AST parser about registry command keywords** — the parser currently treats unknown command names (SOUND, DIM, NEXT, etc.) as variable references, silently returning a `VariableNode`. It should recognize registry command keywords and refuse to parse them, so callers don't need runtime guards against partial parses. Currently `_store_subline` in `core.py` checks `_ast_migrated_commands` before parsing; this knowledge belongs in the parser.
2. [x] **Migrate ON GOTO/GOSUB to AST** — ON expr GOTO/GOSUB has enough control-flow structure to benefit from AST parsing. Other registry commands (SOUND, DIM, READ, graphics) are simple evaluate-and-act patterns where `split_args()` + `evaluate_expression()` is the right level of abstraction. Small, self-contained.
3. [ ] **Pre-collect DATA at store-time** — DATA values are currently parsed once at the start of each RUN. Since their values are static, they could be collected into a structured map when program lines are stored, eliminating even that one-time parsing. Low impact (DATA-heavy programs are rare) but conceptually cleaner.