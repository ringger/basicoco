# BasiCoCo Tasks

The project backlog. Every entry is a task that can be finished, with a
**Done when** line. Standing rules and known behaviour live in
[CLAUDE.md](CLAUDE.md); past decisions and their rationale in
[docs/audit_decisions.md](docs/audit_decisions.md). Numbers like `[#82]`
match the session task list, where every entry here is mirrored.

## High priority

- [ ] **Check the Rubik's static-render bleed-through in a real browser** [#82]
  Reported: in the static "CUBE SOLVED!" view, stickers from back subcubes bleed through at the boundaries between the three visible faces. The Sept 2026 audit could not reproduce it outside a browser: the per-subcube depth sort matched a true per-pixel z-buffer for every move type at 15/45/75°, and a replica of the client's LINE/PAINT rasterization was within 16 px of an ideal fill. Headless-Chrome tests (`tests/integration/browser/`) can now look at the real canvas.
  **Done when:** a browser test renders the solved cube and asserts no back-face sticker color shows inside the front faces. If it passes, close the report; if it reproduces, fix it with that test.
- [ ] **Generate the move tables from pycuber** [#55]
  A `tools/` script that derives each move's facelet 4-cycles (R L U D F B M E S X Y Z) from pycuber and emits BASIC DATA for the existing `CL(2,2,2,5)` layout. Extend `tools/validate_moves.py` rather than duplicating it.
  **Done when:** the script emits all 12 moves, and a test applying each move from the tables matches pycuber on every sticker.
- [ ] **One table-driven ApplyMove instead of 10 Perm\* routines** [#56] (after #55)
  The Perm\* routines are ~230 of the engine's 423 lines; CCW is 3×CW. One ~15-line routine walking the DATA cycles (reversed for CCW) is ~25× faster and removes the class of code behind past cycle-direction bugs. Keep `CL` so DrawCube and the solver are untouched.
  **Done when:** the Perm\* routines are gone and the move, sticker-stability, validate_moves and 100-scramble solver tests pass unchanged.

## Medium priority

- [ ] **Cycle-notation tool for algorithms** [#57] (after #55)
  Prints a move string's net effect ("swaps 2 top edges, corners fixed").
  **Done when:** the tool exists in `tools/` with a test, and every algorithm claim in `docs/rubiks_solver_plan.md` has been checked with it.
- [ ] **Flat-net view of the cube (ShowNet)** [#58] (easier after #56)
  54 boxes from a DATA layout, no depth sort, no PAINT.
  **Done when:** a ShowNet subroutine exists, a program shows it beside the 3D cube, and a test checks the net's colors after moves against pycuber.
- [ ] **Move-cancellation pass on solver output** [#59]
  Merge same-face turns (UUU→u), cancel inverses (bB→∅), commute opposite faces. Audit data: mean 152 quarter turns after #63/#64; a merge pass cuts ~13%.
  **Done when:** the simplified sequence is what gets animated, the 100-scramble test still solves every cube, and before/after mean move counts are recorded.
- [ ] **Table-driven solver lookups** [#60] (after #56)
  Replace the ~150 lines of hand-unrolled FE0–FE11 / FC0–FC7 / KickMid\* lookups with loops over DATA tables.
  **Done when:** they're gone and the solver tests pass unchanged.
- [ ] **Ring (circle-graph) view with synchronized animation** [#61] (after #55, #58)
  9 loops of 12 stickers, one per layer; precompute node positions in Python. Teaching value.
  **Done when:** a program animates the ring view in sync with moves, and a test checks node colors against pycuber.
- [ ] **CIRCLE ratio and arc arguments** [#84]
  `CIRCLE(x,y),r,c,ratio,start,end` — the ratio, start and end arguments are parsed but ignored (`CIRCLE(100,100),20,1,.5` still draws a full round circle).
  **Done when:** server pixel tracking and the client draw ellipses and arcs the same way (shared algorithm, as for circles), with server tests, a harness check and a browser check.
- [ ] **PPOINT sees PAINT fills and GPRINT text** [#85]
  The server tracks LINE/CIRCLE/DRAW/PSET pixels but not PAINT or GPRINT, so `PPOINT` inside a painted area or on GPRINT text returns 0.
  **Done when:** the server records PAINT fills (same flood-fill rules as the client) and GPRINT glyph pixels, and tests check PPOINT inside a painted box and on a GPRINT stroke.
- [ ] **PRINT# writes numbers without PRINT's spaces** [#103]
  `PRINT #1,5;6;-3` writes `56-3`, so INPUT # reads back one wrong number; PRINT writes ` 5  6 -3 `. PRINT# has its own item tokenizer instead of PRINT's formatting. Also decide commas: PRINT# writes `A,B` for `PRINT #1,"A","B"` (INPUT # then reads two fields), where Color BASIC pads to the next print zone.
  **Done when:** PRINT# formats items exactly like PRINT (xfail in `test_robustness.py` passes), the comma choice is recorded in docs/audit_decisions.md, and the bundled programs that write files still read them back.
- [ ] **Re-entering a WHILE or DO leaks a stack frame** [#100]
  `FOR K=1 TO 2000: WHILE 1: IF 1 THEN GOTO 40 ... 40 NEXT K` leaves 2000 frames on `while_stack` (DO: `do_stack`). FOR already replaces its frame when the same loop starts again (#43); WHILE and DO push a new one each time.
  **Done when:** starting a WHILE or DO whose frame (same line and subline) is already on its stack replaces it (dropping frames above it), and the two xfails in `test_robustness.py` pass.
- [ ] **DRAW: a `;` drops the command before it; the pen starts off-centre** [#101]
  `DRAW "BM100,100;R20"` never moves to (100,100) (`BM100,100R20` does), silently; and the pen starts at (64,48), a leftover of the old per-mode coordinates, not the screen centre (128,96).
  **Done when:** `;` separates DRAW commands everywhere, a malformed DRAW command is an error instead of being skipped, the pen starts (and resets on NEW/PCLS as today) at (128,96), with tests; the xfail in `test_robustness.py` passes.
- [ ] **Decide ERR's numbering** [#102]
  `_ERROR_CODES` (program_executor.py) mixes schemes: SYNTAX 1, OUT OF DATA 4, ILLEGAL FUNCTION CALL 5, OVERFLOW 6, UNDEFINED LINE 7, BAD SUBSCRIPT 9, TYPE MISMATCH 13, STRING TOO LONG 14, division by zero 99. Color BASIC has no ERR; Microsoft BASIC numbers them SN 2, OD 4, FC 5, OV 6, UL 8, BS 9, /0 11, TM 13, LS 15.
  **Done when:** one scheme is chosen (Microsoft's is the natural fit for an ERR extension) and recorded in docs/audit_decisions.md, the table and tests follow it, and the xfail in `test_robustness.py` passes.

## Low priority — not implemented from Extended Color BASIC

Rarely needed, or hard to emulate meaningfully.

- [ ] **Unsupported machine-language words fail misleadingly: PEEK, POKE, VARPTR, EXEC, USR** [#87]
  Because unknown names with parentheses auto-dimension as arrays, `X=VARPTR(A)` and `X=USR(1)` silently return 0, `PEEK(100)` says BAD SUBSCRIPT, and `EXEC 100` says "Unrecognized command".
  **Done when:** each gives a clear "not supported in BasiCoCo" error with suggestions (they become reserved names, so they can't be used as arrays), with tests. Real PEEK/POKE (a simulated memory map) would be a separate task.
- [ ] **Random-access files: FIELD, GET/PUT (file)** [#88] — **Done when:** OPEN "R", FIELD, LSET/RSET, GET#/PUT# and LOC/LOF work with tests.
- [ ] **PRINT items without a separator** [#99]
  Color BASIC accepts `PRINT "A""B"` and `PRINT "X="X` (adjacent items print as if separated by `;`); BasiCoCo says `Unexpected "B"`.
  **Done when:** adjacent PRINT items print like `;`-separated ones (PRINT and PRINT#), with tests, and the rule is in docs/audit_decisions.md.
- [ ] **Optimal solver for short scrambles (bidirectional BFS)** [#62] (after #56)
  **Done when:** any ≤8-move scramble is solved optimally, checked against a Python BFS for seeded scrambles.
