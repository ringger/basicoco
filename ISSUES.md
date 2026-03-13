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

## Known Bugs

- [ ] **REM lines with colons are split by statement splitter** — `expand_line_to_sublines()` splits on colons inside REM comments, causing text after the colon to be executed as code. Example: `REM U CW CYCLE: TFR(0)` splits into `REM U CW CYCLE` + `TFR(0)` which triggers a syntax error. Workaround: avoid colons in REM comments. Fix would be to check for REM before splitting on colons in `expand_line_to_sublines()`.

## Known Behavioral Limitations

- **GOTO out of multi-line IF** leaves a stale `if_stack` entry (cleared on next RUN). This matches real CoCo behavior where GOTO from structured blocks is undefined. Note: RETURN out of IF blocks inside GOSUB is handled correctly — GOSUB saves if_stack/for_stack depth and RETURN restores it.

## Refactoring Opportunities

*(No pending refactoring opportunities at this time.)*
