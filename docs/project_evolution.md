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

### Step 3: Middle Edges — Smooth Sailing

With the handedness lesson learned, Step 3 (middle layer edges) went smoothly. 8 insertion algorithms, all verified empirically against the engine. 16/16 tests passing. The F2L was complete.

## Phase 6: The Flawed Engine

### Step 4: The Algorithm That Couldn't Work

Step 4 (top cross) uses a single well-known algorithm: `F R U R' U' F'`. It's one of the most widely published algorithms in Rubik's cube pedagogy. Apply it to a dot, get an L-shape. Apply it to an L-shape, get a line. Apply it to a line, get a cross. Simple.

6 of 16 tests failed. The algorithm appeared to disrupt the F2L — the first two layers, which should be untouched by any OLL algorithm.

### The Misdirection

What followed was a multi-session investigation that went in circles. The algorithm was correct (verified by pycuber, a trusted Python Rubik's library). The algorithm's group-theoretic order was correct (`(F R U R' U' F')^6 = identity`). Individual moves seemed to work. Yet the composition produced wrong results.

Multiple hypotheses were explored and discarded:
- Was `F R U R' U' F'` the wrong algorithm? No — pycuber confirmed it preserves F2L.
- Was the wide-f variant (`f R U R' U' f'`) needed instead? No — the regular algorithm is correct.
- Was the sticker remap wrong for the F move? No — F matched pycuber perfectly.
- Was the U move going the wrong direction? This question was asked and then lost in a sea of manual permutation tracing.

A hand-written Python cubie simulator was built to investigate. It had the same bug as the engine — because the same geometric misunderstanding informed both implementations. A plan was drafted to decompose `f R U R' U' f'` into basic moves using whole-cube rotations, working around the alleged F2L disruption. The conversation consumed enormous context tracing permutations mentally — exactly the behavior the project's own directive warned against.

### The Breakthrough: Trust But Verify

The breakthrough came from a simple principle: **validate the engine's basic moves against a trusted implementation before debugging anything built on top of them.**

A test script applied each of the 6 basic face moves (R, U, F, L, D, B) through the actual BASIC engine and compared every sticker on all 6 faces against pycuber. The results were immediate and unambiguous:

| Move | Result |
|------|--------|
| R | MATCH |
| U | **MISMATCH** |
| F | MATCH |
| L | MATCH |
| D | MATCH |
| B | MATCH |

One move was wrong. Just one. The U move rotated the top layer counterclockwise instead of clockwise — a mirror image of the correct behavior.

### The Fix

The bug was in `PermTop`, the engine subroutine that permutes the top layer. The coordinate transform that maps each subcube's old position to its new position had two terms swapped. Where PermRight (which was correct) used the pattern `new_first = old_second, new_second = 2 - old_first`, PermTop used the reversed pattern: `new_first = 2 - old_second, new_second = old_first`. The corresponding sticker face remap was also reversed, consistent with the backwards coordinate transform.

A two-line fix. Every sticker on every face now matched pycuber for all 6 basic moves, and `F R U R' U' F'` correctly preserved F2L.

### Why Steps 1–3 Passed With a Broken Engine

This is the most instructive part. Steps 1–3 passed 48/48 tests with the backwards U move. How?

The solver algorithms for Steps 1–3 were developed empirically — each step was tuned and verified against the engine's actual behavior. When the solver needed to "rotate U to align a piece above its target slot," it computed the number of U turns based on where pieces actually ended up, not where they should end up in standard notation. The algorithms compensated for the broken U without anyone realizing the engine was wrong.

This is the danger of testing a system only against itself. The solver and the engine agreed with each other — they just both disagreed with the rest of the world. It took an algorithm that combines multiple move types (F and U together in `F R U R' U' F'`) to expose the inconsistency, because the individual moves' errors didn't cancel out the way they did in U-only sequences.

### The Deeper Lesson

The Phase 5 lesson was "don't search — implement published algorithms." The Phase 6 lesson goes deeper: **validate your foundations against a trusted external reference before building on them.**

In retrospect, pycuber should have been the starting point. Before writing a single solver algorithm, each of the engine's six basic moves should have been validated against a trusted library. That one comparison — run `U` through the engine, run `U` through pycuber, diff the stickers — would have caught the bug in seconds. Instead, three phases of solver work were built on a flawed foundation, and the error was only discovered when a published algorithm failed to produce published results.

The cost wasn't just debugging time. Every solver algorithm for Steps 1–3 had to be re-derived after the fix, because the originals had silently compensated for the backwards U. The direction test written alongside the fix initially had its expected values backwards too — the same geometric confusion that produced the original bug persisted in the mental model even after the code was corrected. Only the pycuber comparison was immune to this, because it didn't depend on anyone's mental model of which direction "clockwise" goes.

Symmetries matter. A Rubik's cube has 48 symmetries, and a move that rotates the wrong direction looks locally consistent — it still cycles 4 pieces, still returns to identity after 4 applications, still composes cleanly with itself. The error only becomes visible when you compose it with moves on other axes, breaking the symmetry group's internal consistency.

Passing tests are not proof of correctness. They are proof of internal consistency — which is a much weaker property. Start with external ground truth.

### The Thinking Token Trap

Both the Phase 5 and Phase 6 failures share a deeper root cause: a natural impulse to *reason about* the puzzle rather than *execute code against* it.

The project's explicit strategy was to implement a known, published solution — the beginner's method, with algorithms taken directly from Ruwix. No discovery required. But at every stage, the conversation drifted toward puzzle-solving behavior: mentally tracing where stickers move, exploring candidate move sequences, reasoning about which direction "clockwise" goes when viewed from above. The Rubik's cube is especially seductive because each sub-problem feels tractable — "just trace where this one sticker goes" — but the combinatorial explosion makes thinking tokens the worst possible tool for the job.

This is a true AI assistant failure mode, not a one-off mistake. Given a problem that *could* be reasoned about, the assistant defaults to reasoning about it — even when the plan is to look up the answer and transcribe it. The emulator can answer any concrete question about cube state in milliseconds. The published algorithms exist. The correct workflow is: look up, transcribe, test, fix. Not: think, trace, hypothesize, explore.

The directive that captures all three lessons: **Don't reason about the puzzle. Look up the answer. Validate against ground truth. Run the test.**

## By the Numbers

- **130+ commits** over 6 months (September 2025 — March 2026)
- **~1250 tests** (unit + integration, slow tests excluded by default)
- **24 BASIC programs** in the programs directory
- **7 experiment files** documenting the corner algorithm search
- **3 plan/reference documents** for the solver

## What's Next

After the engine fix, Steps 1–3 were re-verified against pycuber, their algorithms re-derived, and all 48 tests pass again. Step 4 (top cross) also passes 16/16 scramble tests.

### Step 5: Top Edge Alignment — The Fastest Step

Step 5 was the cleanest implementation yet. The algorithm `R U R' U R U2 R' U` swaps the front and left top edge side stickers while preserving back and right. Validated against pycuber in one shot, no surprises.

The only subtlety was the pre-rotation strategy. A greedy approach — rotate U for the best alignment, then apply the algorithm — oscillates for certain permutations (e.g., back↔left swapped). The fix: simulate all 4 possible pre-rotations combined with the algorithm, pick the one that yields the best post-algorithm alignment. This guarantees monotonic progress toward the solution.

The implementation exposed an interpreter bug: `GOSUB Sub: IF cond THEN A=1: B=2` splits incorrectly when the line starts with a non-control keyword. The statement splitter sees GOSUB (not IF) at the start, splits on all colons, and `B=2` executes unconditionally regardless of the condition. The workaround — separate lines — was trivial, but the bug is worth noting as a reminder that the interpreter's statement splitting has a blind spot for mid-line control structures. Filed in ISSUES.md.

16/16 scramble tests passing. Five of seven steps complete.

### Step 6: Top Corner Positioning — Sum Matching

Step 6 positions the 4 top corners so each corner's 3 sticker colors (as a set) match its 3 adjacent center colors, regardless of orientation. The algorithm `U R U' L' U R' U' L` cycles three corners (TFL→TBL→TBR) while keeping TFR fixed.

The interesting optimization: rather than checking color sets element-by-element, the solver uses color-sum matching. Each corner's 3 sticker colors add to a unique sum (TFR=9, TFL=12, TBL=13, TBR=10), so a single addition replaces a set comparison. The solver simulates all 4 possible U pre-rotations, picks the one with the most correctly positioned corners, then rotates a correct corner to TFR (the fixed point) before applying the algorithm.

One more plan bug surfaced: the U CW corner cycle direction was specified incorrectly. The same cycle that was established in Step 2 and validated against pycuber applied here — but the plan had it backwards. Fixed and re-validated.

16/16 scramble tests passing. Six of seven steps complete.

### Step 7: Top Corner Orientation — The Finish Line

The final step twists each top corner so yellow faces up, using `R' D' R D` repeated 2 or 4 times per corner. The algorithm temporarily scrambles the bottom layers — this is expected and intentional. After all corners are processed, the bottom restores, and a final U alignment completes the solve.

The implementation is compact: a main loop checks if all 4 top corners show yellow, brings the first misoriented corner to TFR via U rotation, applies `R' D' R D` until TFR shows yellow, and repeats. A final subroutine rotates U until the top edge side stickers match their centers.

The plan's U rotation table had TFL and TBR swapped — another instance of the recurring cycle-direction confusion. U CW moves the piece at TBR to TFR (one turn), but bringing TFL to TFR requires U' (three CW turns, or equivalently one CCW). The fix was two characters: swap `U` and `u` in the rotation dispatch. The bug manifested as an infinite loop: the solver kept bringing already-oriented corners to TFR and twisting them out of alignment, then trying again.

16/16 scramble tests passing. A final end-to-end test class (`TestFullSolve`) verifies all 54 stickers against the solved state — not just cumulative invariant checks, but a complete sticker-by-sticker comparison. 16/16 passing. The solver is complete.

## The Completed Solver

Seven steps, 128 solver tests (16 per step plus 16 end-to-end), every scramble from single moves to 20-move sequences solved and verified. The solver runs entirely in CoCo BASIC — a language with no local scope, no structured data types, and 249-character line limits — implementing a well-known algorithm that most tutorials explain in 20 minutes but that required careful attention to coordinate systems, cycle directions, and corner handedness to get right.

The pycuber validation gate held throughout: every algorithm (`F R U R' U' F'`, `R U R' U R U2 R' U`, `U R U' L' U R' U' L`, `R' D' R D`) was validated against pycuber before the BASIC code was written. The engine's 6 basic moves were validated first, and each step's algorithm was verified independently. No solver bugs survived that were rooted in engine errors — the Phase 6 lesson stuck.

The recurring theme across all seven steps was cycle direction confusion. The U move's piece cycle (TFR→TFL→TBL→TBR) is a simple fact, but it's easy to reverse when reasoning about "which U rotation brings corner X to position Y." Steps 2, 6, and 7 all had plan errors related to this. The fix was always the same: stop reasoning, run the code, observe which piece actually ends up where.

## By the Numbers

- **140+ commits** over 6 months (September 2025 — March 2026)
- **~1,200 tests** (unit + integration, slow tests excluded by default)
- **128 solver tests** across 8 test classes (7 steps + end-to-end)
- **24 BASIC programs** in the programs directory
- **4 documentation files** (plan, reference algorithms, project evolution, bitwise operators)
- **1 validation tool** (`tools/validate_moves.py`) — the pycuber gate
