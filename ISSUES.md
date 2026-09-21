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

- [ ] **Rubik's cube static render artifacts (unverified)** — reported: at boundaries between the three visible faces, stickers from back subcubes bleed through in the static "CUBE SOLVED!" view.
  - **Sept 2026 audit**: the per-subcube painter's-algorithm depth sort was compared against a true per-pixel z-buffer for every move type at 15/45/75° and matched (0 wrong interior pixels), and a Python replica of the client's LINE/PAINT rasterization differed from an ideal polygon fill by at most 16 px per frame. The bleed-through could **not** be reproduced outside the browser. Next step: check in the real browser; if it persists, suspect the client's canvas rasterization (antialiased strokes vs. the BASIC-pixel PAINT fill) rather than the depth sort.
- [x] **Stickers change colors mid-turn** — FIXED Sept 2026 (task #67): not a depth-sort problem. R and L animated in the wrong direction and then snapped when the permutation applied. The animation rotation signs for R/L were swapped; a test now checks every move's last animation frame against the static redraw.
- [x] **Rubik's cube shrinks momentarily during solver** — FIXED Sept 2026 (task #51): `AlignMidEdge` used `PRIVATE SC` as scratch, clobbering the engine's render scale `SC` while DoMoves animated. Renamed to `SK`; a test checks every animated frame's size.

## Known Behavioral Limitations

- **GOTO out of multi-line IF** leaves a stale `if_stack` entry (cleared on next RUN). This matches real CoCo behavior where GOTO from structured blocks is undefined. Note: RETURN out of IF blocks inside GOSUB is handled correctly — GOSUB saves if_stack/for_stack depth and RETURN restores it.

## Language Extension Ideas

*(No pending language extension ideas at this time.)*

## Refactoring Opportunities

*(No pending refactoring opportunities at this time.)*
