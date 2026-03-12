# BasiCoCo Issues

## Not Yet Implemented (from Extended Color BASIC)

Low priority — rarely needed or hard to emulate meaningfully:

- [ ] PEEK/POKE — memory access (would need a simulated memory map)
- [ ] FIELD — file field definition (random-access file I/O)
- [ ] GET/PUT (file) — file record I/O (random-access file I/O)
- [ ] VARPTR — variable pointer (rarely used outside machine language interfacing)
- [ ] EXEC — execute machine language (no-op or educational stub)
- [ ] USR — user-defined machine language function (no-op or educational stub)

## Testing

- [ ] **`interactive_session()` test harness helper** — create helper in conftest.py for pexpect-based program audit tests to reduce boilerplate in `test_program_audit.py`.

## Robustness Exploration

Areas that work but haven't been stress-tested with adversarial or exotic inputs:

- [ ] **File I/O edge cases** — partial reads, large files, error recovery mid-stream, multiple files open simultaneously, EOF boundary conditions
- [ ] **ON ERROR GOTO / RESUME edge cases** — error handler inside nested GOSUB with LOCAL, RESUME NEXT across subline boundaries, re-raising errors from within handlers
- [ ] **Graphics edge cases** — PAINT on complex shapes with narrow corridors, LINE/DRAW at screen boundaries, rapid PMODE switching
- [ ] **Exotic control flow combinations** — ON ERROR inside nested GOSUB with LOCAL variables, CHAIN with ALL preserving complex state (arrays, open files, error handlers), GOTO/GOSUB from inside deeply nested IF/FOR/WHILE blocks
- [ ] **String expression edge cases** — very long strings, empty strings in concatenation/MID$/INSTR, string comparisons with trailing spaces

## Rubik's Cube Solver

- [ ] **Step 3 algorithms differ from standard F2L** — Our middle-edge insertion algorithms work but are not the standard Ruwix F2L algorithms (e.g., FR EP=4 is `U' R U R' U F' U' F` instead of standard `U R U' R' U' F' U F`). Consider adopting the standard algorithms so the code is easier to audit against external references. Would require updating AlignMidEdge alignment logic and all 8 insertion + extraction algorithms.

## Known Behavioral Limitations

- **GOTO out of multi-line IF** leaves a stale `if_stack` entry (cleared on next RUN). This matches real CoCo behavior where GOTO from structured blocks is undefined. Note: RETURN out of IF blocks inside GOSUB is handled correctly — GOSUB saves if_stack/for_stack depth and RETURN restores it.

## Refactoring Opportunities

- [ ] **Error wrapper base class for command modules** *(low priority)* — `error_context.syntax_error()` → `error_response()` two-step pattern across 5 modules (51 sites). Graphics.py already has local helpers. A base class would save ~1 line per call but requires changing 5+ class hierarchies. Consider if more modules accumulate error helpers.
