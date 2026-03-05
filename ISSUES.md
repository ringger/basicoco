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

1. [x] **Teach AST parser about registry command keywords** — parser now has a `registry_commands` set and raises `RegistryCommandError` instead of silently returning a `VariableNode`. Callers no longer need runtime guards; `_ast_migrated_commands` removed.
2. [x] **Migrate ON GOTO/GOSUB to AST** — ON expr GOTO/GOSUB has enough control-flow structure to benefit from AST parsing. Other registry commands (SOUND, DIM, READ, graphics) are simple evaluate-and-act patterns where `split_args()` + `evaluate_expression()` is the right level of abstraction. Small, self-contained.
3. [x] **Pre-collect DATA at store-time** — `data_values` dict now collects parsed DATA values when program lines are stored. `run_program()` builds `data_statements` from pre-collected values instead of re-parsing. Also fixes a latent bug where DATA in multi-statement lines (e.g., `10 PRINT "HI": DATA 100`) was silently lost.