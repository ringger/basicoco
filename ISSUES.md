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

- [ ] **Step 4 wide-f algorithm** — `F R U R' U' F'` (narrow F) disrupts F2L by swapping a middle-layer edge into the top. The correct OLL edge algorithm is `f R U R' U' f'` (wide f), decomposed as `Z B' R U R' U' B z` since the engine doesn't support wide moves natively. Solver passes all 16 scramble tests with narrow F, but 2 algorithm-level tests fail. See plan file for details.

## Known Behavioral Limitations

- **GOTO out of multi-line IF** leaves a stale `if_stack` entry (cleared on next RUN). This matches real CoCo behavior where GOTO from structured blocks is undefined. Note: RETURN out of IF blocks inside GOSUB is handled correctly — GOSUB saves if_stack/for_stack depth and RETURN restores it.

## Refactoring Opportunities

- [ ] **Error wrapper base class for command modules** *(low priority)* — `error_context.syntax_error()` → `error_response()` two-step pattern across 5 modules (51 sites). Graphics.py already has local helpers. A base class would save ~1 line per call but requires changing 5+ class hierarchies. Consider if more modules accumulate error helpers.
