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
- [ ] **Stop round-tripping tab state on every tab switch** [#83]
  The server keeps a separate interpreter per tab, yet the client fetches each tab's program and variables (`get_state`) when leaving it and pushes them back (`set_state`) when returning. That is redundant, and because `get_state` answers asynchronously, a quick switch can push back a stale copy and overwrite newer work (e.g. lines typed just before switching). Tabs restored after a reload already skip the push (`stateFetched`).
  **Done when:** tab switches no longer send `set_state` (and `get_state` is dropped if nothing else needs it), with a browser test that types a line, switches away and back immediately, and still LISTs it.
- [ ] **Robustness test sweep** [#86]
  These areas work but haven't been tested with awkward inputs. Write the tests; any bug found becomes its own task.
  - File I/O: several files open at once; EOF exactly at the last record; a file of thousands of lines; closing a file mid-read.
  - ON ERROR / RESUME: handler inside a nested GOSUB using LOCAL; RESUME NEXT across sublines; an error raised inside the handler.
  - CHAIN ALL carrying arrays, open files and an active error handler.
  - GOTO out of deeply nested FOR/WHILE/IF blocks, repeated in a loop (stacks mustn't grow without bound).
  - Strings: very long strings; empty strings in +, MID$, INSTR; comparisons with trailing spaces.
  - Graphics: PAINT through narrow corridors; LINE/DRAW crossing the screen edge; switching PMODE mid-drawing.
  **Done when:** each bullet has at least one test (tests that expose bugs are marked xfail against a new task).
- [ ] **Enforce the fast/slow test boundary** [#91]
  `slow` means "over 1 second", but nothing checks it: `test_lunar_lander` (3.2 s) and `test_simple_lunar` (1.2 s) run in the default suite, and slow marking is spread over file markers, class markers and conftest path rules.
  **Done when:** a conftest check flags any unmarked test over the budget, the offenders are marked or sped up, and the rule is in tests/README.
- [ ] **LINE INPUT # into a numeric variable silently stores 0** [#94]
  `LINE INPUT #1, A` reads the line and sets A to 0 with no error. LINE INPUT only takes string variables.
  **Done when:** it gives TYPE MISMATCH (file and console LINE INPUT alike), with tests.

## Low priority — not implemented from Extended Color BASIC

Rarely needed, or hard to emulate meaningfully.

- [ ] **Unsupported machine-language words fail misleadingly: PEEK, POKE, VARPTR, EXEC, USR** [#87]
  Because unknown names with parentheses auto-dimension as arrays, `X=VARPTR(A)` and `X=USR(1)` silently return 0, `PEEK(100)` says BAD SUBSCRIPT, and `EXEC 100` says "Unrecognized command".
  **Done when:** each gives a clear "not supported in BasiCoCo" error with suggestions (they become reserved names, so they can't be used as arrays), with tests. Real PEEK/POKE (a simulated memory map) would be a separate task.
- [ ] **Random-access files: FIELD, GET/PUT (file)** [#88] — **Done when:** OPEN "R", FIELD, LSET/RSET, GET#/PUT# and LOC/LOF work with tests.
- [ ] **Error messages that leak Python or suggest the wrong syntax** [#95]
  `A("X")=5` says "invalid literal for int() with base 10: 'X'" (should be TYPE MISMATCH); a malformed LINE coordinate (`LINE (A,)-(1,1)`) says "LINE requires exactly two coordinates" and suggests `LINE(x,y)`; `IF 1 THEN "A"` reports "Unrecognized command: A", dropping the quotes.
  **Done when:** each gives a BASIC-style message with correct suggestions, with tests.
- [ ] **Prove or remove possibly unreachable branches** [#96]
  No test reaches these, and the #81 probes suggest nothing can: ast_evaluator.py `visit_if_statement` ELSE-with-a-number branch (`IF 0 THEN 30 ELSE 10+10` takes another path); control_flow.py's second NEXT WITHOUT FOR; ast_parser.py's `'` token and leftover-REM checks (the splitter removes comments first); ast_converter.py `_is_jump_target`'s quote branch.
  **Done when:** each has a test that reaches it, or is deleted with the full suite passing.
- [ ] **Optimal solver for short scrambles (bidirectional BFS)** [#62] (after #56)
  **Done when:** any ≤8-move scramble is solved optimally, checked against a Python BFS for seeded scrambles.
