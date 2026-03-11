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

## Rubik's Cube Solver

## Known Behavioral Limitations

- **GOTO out of multi-line IF** leaves a stale `if_stack` entry (cleared on next RUN). This matches real CoCo behavior where GOTO from structured blocks is undefined. Note: RETURN out of IF blocks inside GOSUB is handled correctly — GOSUB saves if_stack/for_stack depth and RETURN restores it.

## Refactoring Opportunities

- [ ] **Error wrapper base class for command modules** *(low priority)* — `error_context.syntax_error()` → `error_response()` two-step pattern across 5 modules (51 sites). Graphics.py already has local helpers. A base class would save ~1 line per call but requires changing 5+ class hierarchies. Consider if more modules accumulate error helpers.
