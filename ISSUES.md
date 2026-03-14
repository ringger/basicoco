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

- [ ] **Rubik's cube z-sorting artifacts** — DrawCube in `lib_rubiks_engine.bas` uses a painter's algorithm with per-subcube depth sorting. This produces visible artifacts:
  - **Static render**: at boundaries between the three visible faces (front, right, top), stickers from back subcubes bleed through — e.g., yellow on the front face, blue on the top face in the "CUBE SOLVED!" view.
  - **Animation**: during face rotation, rotating subcubes' corners get occluded by static faces, and stickers appear to change colors mid-turn.
  - **Root cause**: per-subcube average depth doesn't correctly resolve overlap ordering between faces from adjacent subcubes that extend in different directions. The cross-product cull alone isn't sufficient. Fixed iteration order (back→front) was tried but made animation worse.
  - **Possible approaches**: (1) Only paint the three camera-visible face orientations (front/right/top) for non-rotating subcubes, with special handling during rotation when back/left/bottom faces can rotate into view. (2) Render static and rotating layers separately with different strategies. (3) Rethink depth metric — e.g., per-face depth for the rotating layer only. The internal 4D CL array is verified correct by sticker-stability tests against pycuber.

## Known Behavioral Limitations

- **GOTO out of multi-line IF** leaves a stale `if_stack` entry (cleared on next RUN). This matches real CoCo behavior where GOTO from structured blocks is undefined. Note: RETURN out of IF blocks inside GOSUB is handled correctly — GOSUB saves if_stack/for_stack depth and RETURN restores it.

## Language Extension Ideas

*(No pending language extension ideas at this time.)*

## Refactoring Opportunities

*(No pending refactoring opportunities at this time.)*
