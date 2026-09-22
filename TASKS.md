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

## Decisions waiting for the user

Each was decided provisionally (`auto` in docs/audit_decisions.md) and works as described there.
**Done when** (each): the user confirms or picks the alternative; if it changes, code, tests and the decision row follow.

- [ ] **ERR numbering: Microsoft's (current, /0 = 11) or CoCo 3 ERNO's (/0 = 10)?** [#109] Also whether errors with no code (LOOP WITHOUT DO, ELSE/ENDIF WITHOUT IF) should stay ERR 0.
- [ ] **PRINT# comma: a literal `,` (current) or Color BASIC's print-zone padding?** [#110] address_book.bas relies on the literal comma; Color BASIC's own behaviour is unverified.
- [ ] **Enforce the 255-character string limit (?LS ERROR)?** [#111] Currently unlimited.
- [ ] **PAINT with no border colour: fill the start colour's region (current) or default the border to the paint colour?** [#112] Check the Extended Color BASIC manual; server `_record_paint` and client `paint()` change together.
- [ ] **Line numbers up to 65535 (current) or the CoCo's 63999?** [#113]
- [ ] **CIRCLE arcs: 64-segment polygon (current) vs the CoCo's own rasterisation and ratio rule?** [#114]
- [ ] **Non-numeric INPUT answer: read as 0 (current, VAL's rule) or re-ask with ?REDO as Color BASIC does?** [#125]

## Loose ends

- [ ] **DRAW variable substitution (`M=X;,=Y;`, `U=N;`)** [#117] Now an error ("unknown command '='"); Extended Color BASIC supports it.
  **Done when:** implemented with tests, or documented as unsupported in HELP DRAW and docs/audit_decisions.md.
- [ ] **Coverage pass over what changed since the last one** [#119]
  **Done when:** `tools/diff_coverage.py` against 33f5f6e shows every uncovered changed line tested or listed with a reason in tests/README.
- [ ] **A reusable BASIC probe tool** [#122] The session repeatedly hand-wrote scratch scripts to run snippets and print outputs, errors, stack depths and pixels.
  **Done when:** `tools/basic_probe.py` does that from arguments or stdin (checking conftest helpers first), with a test.
- [ ] **Restructure Claude's project memory into an index** [#121] `MEMORY.md` (in Claude's per-project memory directory, outside the repo) holds long sections (key bugs, Rubik's solver history, architecture) where it should be a one-line-per-memory index.
  **Done when:** durable facts live one per memory file, anything CLAUDE.md or the repo already records is dropped, and MEMORY.md is only the index.
- [ ] **Post-audit chapter in docs/project_evolution.md** [#90]
  **Done when:** the chapter covers the audit's follow-up work (coverage pass, browser tests, parity between server and canvas, decisions) in the document's collaboration-story voice.

## Low priority — not implemented from Extended Color BASIC

Rarely needed, or hard to emulate meaningfully.

- [ ] **Random-access files: FIELD, GET/PUT (file)** [#88] — **Done when:** OPEN "R", FIELD, LSET/RSET, GET#/PUT# and LOC/LOF work with tests.
- [ ] **Optimal solver for short scrambles (bidirectional BFS)** [#62] (after #56)
  **Done when:** any ≤8-move scramble is solved optimally, checked against a Python BFS for seeded scrambles.
