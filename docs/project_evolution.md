# BasiCoCo: A Project Evolution

How a TRS-80 Color Computer BASIC interpreter became a lesson in the boundaries between algorithm implementation and state space search.

## Phase 1: The Interpreter (September 2025)

The project began as a straightforward emulator for TRS-80 Color Computer BASIC — a language where every variable is global, line numbers are addresses, and GOTO is a way of life. The first commit delivered a working interpreter with expression evaluation, control flow, and a WebSocket-based client that renders CoCo graphics in a browser.

Early commits moved fast: PAINT command, comprehensive test suite, modular architecture refactoring, a CLI client with real-time streaming. By the end of September 2025, the system had a dual-monitor interface, Qix-style demos with positional audio, and a growing battery of tests.

## Phase 2: The AST Migration (February–March 2026)

After a quiet period, the project underwent a major architectural transformation. The original interpreter used string-based dispatch — `process_statement()` would parse each statement from scratch every time it executed. This worked but was slow and brittle.

The migration to an AST-based architecture happened one command at a time across 10 commits:

```
b6927d3  Add AST execution infrastructure for incremental migration
c658d37  Migrate END command to AST-based execution
0e478b5  Migrate GOTO command to AST-based execution
0a09cc3  Migrate LET (assignment) command to AST-based execution
03baa27  Migrate PRINT command to AST-based execution
f5e27b5  Migrate GOSUB and RETURN commands to AST-based execution
eb0d37e  Migrate FOR and EXIT FOR commands to AST-based execution
a3a8e9b  Migrate WHILE and DO commands to AST-based execution
b573289  Migrate IF/THEN to AST-based execution
979f113  Migrate INPUT command to AST-based execution
528d502  Remove legacy execute_* methods after AST migration
```

Each commit migrated one command, kept all tests passing, and left the old path as fallback until the new one was proven. The final commit removed the legacy methods entirely.

This was followed by aggressive cleanup: dead code removal, vestigial test files, unused imports, stale comments. The codebase was renamed from its original name to "BasiCoCo" and given a proper educational mission statement.

## Phase 3: Feature Completeness (March 2026)

With the AST foundation solid, features came quickly:

- **File I/O**: OPEN, CLOSE, PRINT#, INPUT#, LINE INPUT, EOF — complete sequential file support
- **ON ERROR GOTO/RESUME**: Error handling with ERR, ERL pseudo-variables
- **Graphics**: LINE BOX/BF, DRAW with B/N/S/A/X modifiers, PPOINT
- **Functions**: SGN, HEX$, OCT$, TIMER, FRE, MEM, PCLEAR
- **Programs**: sorting demo, math quiz, string lab, math plotter, address book — each exercising different language features

Three parsing audits caught subtle bugs: PRINT# dropping the `#` symbol through the AST, ELSE matching inside quoted strings, IF/THEN arguments being silently truncated for registry commands.

The performance work was particularly satisfying. Pre-compiling statements at store time and caching parsed expressions eliminated redundant parsing in tight loops:

```
ec7ebfb  Pre-compile all program statements at store time,
         add expression cache and auto-yield
```

A BASIC program running a loop 1000 times no longer re-tokenized and re-parsed each statement on every iteration.

## Phase 4: The Rubik's Cube (March 2026)

The Rubik's cube started as a graphics demo — an isometric 3D rendering of a cube with face turns and animations. The first version (commit `3972b1a`) was self-contained. Then came the interactive version, the engine split, MERGE/CHAIN support for multi-file programs, and the DoMoves string-based move interface.

The cube representation uses a 3x3x3 array `CL(ix,iy,iz,f)` where each subcube has 6 face slots. Turns are implemented as layer permutations: `PermRight` cycles the X=2 layer, `PermFront` cycles Z=0, etc. The engine went through several iterations — the earliest version only supported R/F/U turns. Adding L/D/B required understanding which axes and directions mapped to which layer cycles.

Along the way, the interpreter needed new features to support the solver's needs:

- **LOCAL variables** (commit `8a2baed`): GOSUB subroutines in CoCo BASIC share all variables globally. A subroutine that uses `I` as a loop counter silently clobbers the caller's `I`. LOCAL saves and restores specified variables across GOSUB/RETURN boundaries, making subroutine composition possible.
- **Bitwise operators** (commit `626a8ba`): AND/OR/NOT were implemented as Python logical operators, returning `True`/`False` instead of integer results. `82 AND 223` returned `True` instead of `82`.
- **Case preservation** (commit `c0d7079`): `parse_line()` uppercased the entire line, destroying case in string literals. `MS$="Ll"` became `MS$="LL"`, breaking the move notation where lowercase means counter-clockwise.

Each of these bugs was discovered not by testing the interpreter in isolation, but by running the Rubik's solver and watching it produce wrong results.

## Phase 5: The Solver — and the State Space Trap

### The Plan

The solver follows the classic beginner's layer-by-layer method:

1. Bottom cross (4 edges)
2. Bottom corners (4 corners)
3. Middle layer edges (4 edges)
4. Top cross
5. Top edge alignment
6. Top corner positioning
7. Top corner orientation

The plan document (`docs/rubiks_solver_plan.md`) specifies each step's algorithms, dispatch logic, and verification checks. A reference algorithms document (`docs/rubiks_reference_algorithms.md`) maps the standard Ruwix tutorial to our bottom-first orientation.

### Step 1: Bottom Cross — The Smooth Start

The bottom cross solver was the first real test. It's "intuitive" in human terms — find the edge, figure out where it is, move it to the right place. In code, this became a cascade of position-and-orientation checks with move sequences for each case.

16 scramble tests, all passing. The solver worked because the cross is genuinely algorithmic: each edge can be solved independently without disturbing the others (mostly), and the case analysis is manageable.

### Step 2: Bottom Corners — The Trap Springs

Bottom corners is where the project encountered a phenomenon that would repeat at multiple levels: the seductive pull of state space search.

**The algorithm is simple in principle.** For each corner:
1. Find it (which of 8 positions, in which of 3 orientations)
2. If it's in the bottom layer in the wrong spot, extract it to the top
3. Rotate the top layer to position it above its target
4. Insert it with the right trigger sequence based on orientation

**The devil is in the dispatch tables.** The cube has 4 bottom corners, each adjacent to two faces. The trigger algorithms (`R' U R`, `F U' F'`, etc.) use those adjacent faces. The natural assumption is that all 4 corners are symmetric — the same pattern with different face letters substituted.

They are not.

**The handedness problem.** BFR and BBL are "CCW-first" corners: a face-prime turn (like `R'`) keeps the top corner in the top layer, cycling its orientation. BFL and BBR are "CW-first": a face-prime turn drops the corner directly to the bottom. This means the insertion algorithms for BFL and BBR cannot be naively derived from the BFR algorithms by substituting face letters.

This asymmetry was not obvious from the reference algorithms, which typically show only one corner and say "repeat for the others." The plan document initially presented a unified table. The code initially used symmetric algorithms. 10 of 16 tests failed.

### The Search Begins

What followed was a progression of increasingly sophisticated attempts to find the correct algorithms — each one a form of state space search:

**Level 1: Thinking tokens.** The first instinct was to work it out mentally. Trace the permutation: R' moves this sticker here, U moves it there, R puts it back... For a 3-move sequence on a cube with 54 stickers, this is feasible but error-prone. For understanding why an algorithm fails and what alternative would work, the branching factor explodes. Long pauses in the conversation — sometimes minutes — were spent doing mental permutation tracing that could have been resolved in milliseconds by running a test.

**Level 2: BASIC programs.** The next approach was to write BASIC programs that applied candidate algorithms and printed the resulting cube state. This worked but was slow (each test boots the interpreter, loads the engine, initializes the cube) and required parsing the output manually.

**Level 3: Python scripts using the emulator.** The `experiments/` directory tells this story:

```
test_corner_empirical.py   — Brute-force search over all 3-move sequences
                              to find BFR insertion algorithms
test_corner_empirical2.py  — Refined search for specific CO values
test_corner_empirical3.py  — Pure-Python mini cube sim (bypassing emulator)
                              to search faster
test_corner_co0.py         — Targeted search for CO=0 insertion
test_corner_verify.py      — Verification that standard algorithms actually
                              work with our engine
test_corner_insert.bas     — BASIC test harness for individual insertions
test_rubiks_corner_moves.py — 160-test exhaustive algorithm validator
                              (later moved from tests/ to experiments/)
```

The progression is revealing. Each script is more sophisticated than the last, but they're all doing the same thing: searching the space of possible move sequences to find ones that produce the desired result. This is exactly what the Rubik's cube community spent decades doing — and then published the results as algorithms.

**The irony.** The explicit project directive was to "implement existing algorithms, not discover new ones." But implementing an existing algorithm for a Rubik's cube requires interpreting it: the published algorithm says "R' D' R D" but doesn't specify which face maps to R when you're working on the back-left corner with the cube oriented bottom-down instead of white-up. That interpretation step — mapping abstract algorithm to concrete cube state — kept triggering search behavior.

### The Resolution

The fix came not from more searching but from understanding the underlying geometry:

1. **BFR and BBL** use face-prime triggers (`R' U R`, `L' U' L`) — the prime turn keeps the corner in the top layer.
2. **BFL and BBR** use face triggers (`F U' F'`, `B U B'`) — the non-prime turn keeps the corner in the top layer.
3. **CO fixed points**: Each trigger has one CO value it cannot change. If the corner's current orientation matches the trigger's fixed point, the solver loops forever. The dispatch must route around fixed points.
4. **BBR is special**: Both R-face triggers (`R U R'` and `R' U' R`) have CO fixed points, so BBR can only use B-face triggers.

Once these geometric facts were established (by a combination of analysis and targeted verification), the correct dispatch tables followed directly. All 32 tests passed in 3.2 seconds.

### The Meta-Lesson

The state space search trap manifested at three distinct levels:

| Level | Medium | What happened |
|-------|--------|---------------|
| Thinking tokens | Mental permutation tracing | Minutes spent on combinatorial work a computer could do in milliseconds |
| BASIC programs | Interpreter-mediated testing | Slow feedback loop, manual output parsing |
| Python scripts | Direct emulator manipulation | Faster but still searching for what could be looked up |

Each level was a reasonable response to the previous level's limitations, but all three shared the same fundamental error: treating algorithm implementation as algorithm discovery. The published algorithms exist. The challenge is mapping them to the specific representation — and that mapping is a finite, tractable problem once the geometry (handedness, fixed points) is understood.

The directive that eventually stuck: **"No state space search in thinking tokens. Never trace permutations, face remappings, or combinatorial computations mentally — write a test and execute it."**

## By the Numbers

- **126 commits** over 6 months (September 2025 — March 2026)
- **~1250 tests** (unit + integration, slow tests excluded by default)
- **24 BASIC programs** in the programs directory
- **7 experiment files** documenting the corner algorithm search
- **3 plan/reference documents** for the solver

## What's Next

The solver has two of seven steps complete. The bottom layer is solved — cross and corners. Remaining:

- Step 3: Middle layer edges (F2L)
- Steps 4–7: Top layer (cross, edge alignment, corner positioning, corner orientation)

Each step will bring its own algorithmic challenges, but the hard lesson has been learned. The algorithms are published. The job is to implement them faithfully, using targeted tests to verify the mapping from abstract notation to concrete cube state — not to rediscover them through search.

The experiments directory stands as an archive: a record of the path from "this should be straightforward" to "why is the cube inside out" to "oh, handedness is a thing" to working code. It's the kind of story that only happens when you build something real enough to surprise you.
