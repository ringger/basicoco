# Rubik's Cube Solver Plan

Beginner's layer-by-layer method implemented in CoCo BASIC.
Reference: [Ruwix Beginner Method](https://ruwix.com/the-rubiks-cube/how-to-solve-the-rubiks-cube-beginners-method/). See `docs/rubiks_reference_algorithms.md` for standard algorithms. Our solver uses the same method but solves bottom-first (Ruwix solves white/top-first), so first-layer algorithms use U instead of D.

## Engine (rubiks_engine.bas)

### Cube State
- `CL(IX,IY,IZ,F)` — color of face F on subcube at (IX,IY,IZ)
- Interior faces = -1, visible faces = color index
- IX,IY,IZ range 0-2; F ranges 0-5

### Face Indices and Solved Colors
| Face | F | Axis/Slice | Solved Color | Color # |
|------|---|-----------|-------------|---------|
| Front | 0 | IZ=0 | Red | 4 |
| Back | 1 | IZ=2 | Buff | 5 |
| Right | 2 | IX=2 | Blue | 3 |
| Left | 3 | IX=0 | Cyan | 6 |
| Top | 4 | IY=0 | Yellow | 2 |
| Bottom | 5 | IY=2 | Magenta | 7 |

### Available Moves
| TF | Move | Slice | Axis |
|----|------|-------|------|
| 1 | RIGHT (R) | IX=2 | X |
| 2 | TOP (U) | IY=0 | Y |
| 3 | FRONT (F) | IZ=0 | Z |
| 4 | ROT-X | all | X |
| 5 | ROT-Y | all | Y |
| 6 | ROT-Z | all | Z |
| 7 | LEFT (L) | IX=0 | X |
| 8 | DOWN (D) | IY=2 | Y |
| 9 | BACK (B) | IZ=2 | Z |

DR=1 for CW, DR=-1 for CCW. CW is defined looking at each face from outside.

### DoMoves Subroutine
Set `MS$` then `GOSUB DoMoves`. Uppercase = CW, lowercase = CCW.
Example: `MS$="RUruf"` executes R, U, R', U', F'.
For double moves (R2), repeat the character: `"RR"`.

## Solver Design

### Orientation
- Solve bottom-first: bottom face (F=5, IY=2, magenta/7) is solved first
- Last layer is top face (F=4, IY=0, yellow/2) — most visible during final steps
- Fixed orientation throughout (no whole-cube rotations during solve)
- All 6 face moves (R, U, F, L, D, B) used directly

### Center Colors (constants, never move)
```
CL(1,1,0,0) = 4  front center = red
CL(1,1,2,1) = 5  back center = buff
CL(2,1,1,2) = 3  right center = blue
CL(0,1,1,3) = 6  left center = cyan
CL(1,0,1,4) = 2  top center = yellow
CL(1,2,1,5) = 7  bottom center = magenta
```

### Piece Positions

#### Edge Pieces (12 edges, 2 visible stickers each)
| Edge | Coords | Sticker Faces |
|------|--------|--------------|
| Bottom-Front | (1,2,0) | F5, F0 |
| Bottom-Right | (2,2,1) | F5, F2 |
| Bottom-Back | (1,2,2) | F5, F1 |
| Bottom-Left | (0,2,1) | F5, F3 |
| Top-Front | (1,0,0) | F4, F0 |
| Top-Right | (2,0,1) | F4, F2 |
| Top-Back | (1,0,2) | F4, F1 |
| Top-Left | (0,0,1) | F4, F3 |
| Front-Right | (2,1,0) | F0, F2 |
| Front-Left | (0,1,0) | F0, F3 |
| Back-Right | (2,1,2) | F1, F2 |
| Back-Left | (0,1,2) | F1, F3 |

#### Corner Pieces (8 corners, 3 visible stickers each)
| Corner | Coords | Sticker Faces |
|--------|--------|--------------|
| Bottom-Front-Right (BFR) | (2,2,0) | F5, F0, F2 |
| Bottom-Front-Left (BFL) | (0,2,0) | F5, F0, F3 |
| Bottom-Back-Right (BBR) | (2,2,2) | F5, F1, F2 |
| Bottom-Back-Left (BBL) | (0,2,2) | F5, F1, F3 |
| Top-Front-Right (TFR) | (2,0,0) | F4, F0, F2 |
| Top-Front-Left (TFL) | (0,0,0) | F4, F0, F3 |
| Top-Back-Right (TBR) | (2,0,2) | F4, F1, F2 |
| Top-Back-Left (TBL) | (0,0,2) | F4, F1, F3 |

## Solving Steps

### Narrative Display

Each step PRINTs status messages so the observer can follow the solve on screen. Messages use a consistent pattern:
- **Step start**: `PRINT "STEP N: DESCRIPTION"` (e.g., `"STEP 1: BOTTOM CROSS"`)
- **Sub-actions**: `PRINT "  action..."` (e.g., `"  SOLVING FRONT EDGE..."`, `"  EXTRACTING FROM BFR"`)
- **Step complete**: `PRINT "  DONE!"` after invariant check passes

Messages are printed before the action they describe. Animation (`AN=1`) is turned on after solving to show the final state; solving runs with `AN=0` for speed.

### Program Structure
```basic
rubiks_solver.bas:
  MERGE "rubiks_engine"
  GOSUB InitCube
  Scramble (20 random moves)
  GOSUB SolveBottomCross    (Step 1)
  GOSUB SolveBottomCorners  (Step 2)
  GOSUB SolveMiddleEdges    (Step 3)
  GOSUB SolveTopCross       (Step 4)
  GOSUB SolveTopEdgeAlign   (Step 5)
  GOSUB SolveTopCornerPos   (Step 6)
  GOSUB SolveTopCornerOrient (Step 7)
```

### Step 1: Bottom Cross (DONE)

**Display**: `"STEP 1: BOTTOM CROSS"` at start. `"  FRONT EDGE"` / `"  RIGHT EDGE"` / `"  BACK EDGE"` / `"  LEFT EDGE"` before each edge.

**Goal**: 4 bottom edges placed with correct stickers on both faces.
- `CL(1,2,0,5)=7` AND `CL(1,2,0,0)=4` (bottom-front: magenta down, red on front)
- `CL(2,2,1,5)=7` AND `CL(2,2,1,2)=3` (bottom-right: magenta down, blue on right)
- `CL(1,2,2,5)=7` AND `CL(1,2,2,1)=5` (bottom-back: magenta down, buff on back)
- `CL(0,2,1,5)=7` AND `CL(0,2,1,3)=6` (bottom-left: magenta down, cyan on left)

**Strategy** (for each of the 4 edges):
a. Find the target piece by searching all 12 edge positions for the two target colors
b. If already in place, skip
c. If in bottom layer (wrong position or flipped), kick to top with a face turn
d. If in middle layer, kick to top with a face turn
e. Rotate U to align the edge above its target slot
f. Insert:
   - If bottom-color on top (EO=0): double face turn (e.g., `FF` for front slot)
   - If bottom-color on side (EO=1): 3-move insert (e.g., `uRF` for front slot)

Retry loop (up to 3 passes over all 4 edges) handles cases where inserting one edge disturbs another.

**Invariant**: 4 bottom edges correct: `CL(x,y,z,5)=7` and side sticker matches center, for all 4 bottom edge positions.

### Step 2: Bottom Corners

**Display**: `"STEP 2: BOTTOM CORNERS"` at start. `"  BFR CORNER"` / `"  BFL CORNER"` / `"  BBR CORNER"` / `"  BBL CORNER"` before each corner. `"  EXTRACTING"` / `"  ALIGNING"` / `"  INSERTING"` for sub-actions.

**Goal**: 4 bottom corners placed with correct stickers on all 3 faces.
- `CL(2,2,0,5)=7` AND `CL(2,2,0,0)=4` AND `CL(2,2,0,2)=3` (BFR: magenta, red, blue)
- `CL(0,2,0,5)=7` AND `CL(0,2,0,0)=4` AND `CL(0,2,0,3)=6` (BFL: magenta, red, cyan)
- `CL(2,2,2,5)=7` AND `CL(2,2,2,1)=5` AND `CL(2,2,2,2)=3` (BBR: magenta, buff, blue)
- `CL(0,2,2,5)=7` AND `CL(0,2,2,1)=5` AND `CL(0,2,2,3)=6` (BBL: magenta, buff, cyan)

Each bottom corner sits between two side faces (A and B). CO=0 means bottom color on Y-face (top), CO=1 on Z-face, CO=2 on X-face. Which CO triggers which insert depends on each face's axis:

| Target | Face A (axis) | Face B (axis) | Extraction | CO for A insert | CO for B insert |
|--------|--------------|--------------|-----------|----------------|----------------|
| BFR | R (X) | F (Z) | `ruR` (R' U' R) | CO=2 → `rUR` | CO=1 → `fuF` |
| BFL | F (Z) | L (X) | `fuF` (F' U' F) | CO=1 → `fUF` | CO=2 → `luL` |
| BBR | B (Z) | R (X) | `buB` (B' U' B) | CO=1 → `bUB` | CO=2 → `ruR` |
| BBL | L (X) | B (Z) | `luL` (L' U' L) | CO=2 → `lUL` | CO=1 → `buB` |

CO=0 (bottom color on top): use either insert — the retry loop will correct the orientation.

BFR algorithms verified against engine. Other slots follow the same pattern.

**Corner alignment**: Each bottom corner (CI) maps to the top corner directly above it:
- BFR (CI=0) → TFR (CP=4)
- BFL (CI=1) → TFL (CP=5)
- BBR (CI=2) → TBR (CP=6)
- BBL (CI=3) → TBL (CP=7)

U CW cycle for corners: TFR(4)→TFL(5)→TBL(7)→TBR(6)→TFR(4). Cycle positions: 4=0, 5=1, 7=2, 6=3.

**Strategy** (for each corner, retry loop up to 6 iterations):
a. Find the target corner (search all 8 positions for 3 target colors)
b. If solved (CP = target slot AND CO=0), done
c. If in bottom layer (CP 0-3) but not solved, extract to top using the **current slot's** extraction algorithm (dispatch on CP, not CI)
d. Rotate U to align corner above its target slot (use cycle positions to compute number of U turns)
e. Check CO and apply the **target slot's** insert algorithm:
   - CO matches face A's axis: apply A insert
   - CO matches face B's axis: apply B insert
   - CO=0 (bottom color on top): apply either insert — the retry loop will correct the orientation
f. Loop back to step (a)

**Invariant**: Step 1 still holds, plus 4 bottom corners correct: `CL(x,y,z,5)=7` and both side stickers match centers.

### Step 3: Middle Layer Edges

**Display**: `"STEP 3: MIDDLE EDGES"` at start. `"  FR EDGE"` / `"  FL EDGE"` / `"  BR EDGE"` / `"  BL EDGE"` before each edge. `"  EXTRACTING"` / `"  ALIGNING"` / `"  INSERTING"` for sub-actions.

**Goal**: 4 middle-layer edges placed correctly (FR, FL, BR, BL). Neither color is yellow or magenta — both are side colors.
- `CL(2,1,0,0)=4` AND `CL(2,1,0,2)=3` (FR: red on front, blue on right)
- `CL(0,1,0,0)=4` AND `CL(0,1,0,3)=6` (FL: red on front, cyan on left)
- `CL(2,1,2,1)=5` AND `CL(2,1,2,2)=3` (BR: buff on back, blue on right)
- `CL(0,1,2,1)=5` AND `CL(0,1,2,3)=6` (BL: buff on back, cyan on left)

**Target colors** (EI = edge index for iteration order):
| EI | Slot | TC1 | TC2 | Coords |
|----|------|-----|-----|--------|
| 0 | FR | 4 (red) | 3 (blue) | (2,1,0) |
| 1 | FL | 4 (red) | 6 (cyan) | (0,1,0) |
| 2 | BR | 5 (buff) | 3 (blue) | (2,1,2) |
| 3 | BL | 5 (buff) | 6 (cyan) | (0,1,2) |

**Finding edges**: Use FindEdge (same as Step 1) to search all 12 positions. After Steps 1-2, middle edges can only be in the top layer (EP 4-7) or middle layer (EP 8-11) — never bottom, since bottom edges contain magenta.

**Extraction from middle**: If the target edge is in a wrong middle slot (EP 8-11), apply the first insert algorithm for that slot to eject it to the top layer:
| Current EP | Current slot | Extraction algorithm |
|-----------|-------------|---------------------|
| 8 | FR | `URurufUF` |
| 9 | FL | `ulULUFuf` |
| 10 | BR | `UBuburUR` |
| 11 | BL | `ubUBULul` |

**Alignment**: After the edge is in the top layer (EP 4-7), one sticker is on the top face (F4) and one is on a side face. Rotate U until the **side sticker** matches its adjacent center. Then the top sticker's color determines which direction to insert.

**Insert algorithms**:
| Slot | Edge aligned with | Goes to | Algorithm | Standard notation |
|------|-------------------|---------|-----------|-------------------|
| FR | F | R | `URurufUF` | U R U' R' U' F' U F |
| FR | R | F | `ufUFURur` | U' F' U F U R U' R' |
| FL | F | L | `ulULUFuf` | U' L' U L U F U' F' |
| FL | L | F | `UFufulUL` | U F U' F' U' L' U L |
| BR | R | B | `UBuburUR` | U B U' B' U' R' U R |
| BR | B | R | `urURUBub` | U' R' U R U B U' B' |
| BL | L | B | `ubUBULul` | U' B' U B U L U' L' |
| BL | B | L | `ULulubuB` | U L U' L' U' B' U B |

"Edge aligned with" = the face whose center matches the side sticker after U alignment. "Goes to" = the face the top sticker's color matches, which is the insertion direction.

FR and FL are the standard Ruwix algorithms. All others follow the same two patterns with substituted face letters:
- `U [target] U' [target]' U' [source]' U [source]` (target is CW from source, viewed from top)
- `U' [target]' U [target] U [source] U' [source]'` (target is CCW from source)

**Strategy** (retry loop, up to 6 passes over all 4 edges):
a. Find the target edge (search all 12 positions for two target colors)
b. If already solved (correct position and orientation), skip
c. If in middle layer but wrong (EP 8-11), extract to top using the **current slot's** extraction algorithm
d. Re-find edge (now in top layer, EP 4-7)
e. Rotate U until the side sticker matches its adjacent center, then re-find edge
f. Look up the insert algorithm from the table: "Edge aligned with" = the face the side sticker now touches, "Goes to" = the face matching the top sticker's color
g. Apply insert algorithm
h. Check if solved; if not, retry loop handles it

**Invariant**: Steps 1-2 still hold, plus 4 middle edges correct: both stickers match adjacent centers.

### Step 4: Top Cross (OLL Edges)

**Display**: `"STEP 4: TOP CROSS"` at start. `"  DOT->L"` / `"  L->LINE"` / `"  LINE->CROSS"` before each algorithm application, describing the case being handled.

**Goal**: Yellow (2) on all 4 top-edge stickers.
- `CL(1,0,0,4)=2` (top-front)
- `CL(2,0,1,4)=2` (top-right)
- `CL(1,0,2,4)=2` (top-back)
- `CL(0,0,1,4)=2` (top-left)

**Algorithm**: `FRUruf` (F R U R' U' F')

**Strategy** (loop until cross):
a. Count how many of the 4 top edges show yellow (YC)
b. If YC=4, done
c. If YC=0 (dot): apply algorithm → creates L-shape, loop back
d. If YC=2, distinguish L-shape from line:
   - **L-shape** (two adjacent edges yellow): rotate U until the two yellow edges are at back and left (i.e., `CL(1,0,2,4)=2` AND `CL(0,0,1,4)=2`), apply algorithm → creates line, loop back
   - **Line** (two opposite edges yellow): rotate U until yellow edges are at left and right (i.e., `CL(2,0,1,4)=2` AND `CL(0,0,1,4)=2`), apply algorithm → creates cross
e. Loop back to step (a)

Adjacent vs opposite: if front+right, front+left, back+right, or back+left are yellow → L-shape. If front+back or left+right → line.

**Invariant**: Steps 1-3 still hold, plus 4 top edges show yellow on top: `CL(x,0,z,4)=2`.

### Step 5: Top Edge Alignment (PLL Edges)

**Display**: `"STEP 5: ALIGN TOP EDGES"` at start. `"  SWAPPING EDGES"` before each algorithm application.

**Goal**: Each top-edge side sticker matches its center color.
- `CL(1,0,0,0)=4` (front edge side = red)
- `CL(2,0,1,2)=3` (right edge side = blue)
- `CL(1,0,2,1)=5` (back edge side = buff)
- `CL(0,0,1,3)=6` (left edge side = cyan)

**Algorithm**: `RUrURUUrU` (R U R' U R U2 R' U) — swaps front and left edges.

**Strategy** (loop until all match):
a. Check which U rotation (0-3 CW turns) would make the most side stickers match their centers — check by comparing sticker colors around the cycle, without moving
b. Apply that many U turns
c. If all 4 match, done
d. Rotate U to position a matching edge at the back (the algorithm preserves the back edge)
e. Apply algorithm (swaps front and left)
f. Loop back to step (a)

If no rotation gives any match (rare but possible), apply algorithm once to create a match, then loop.

**Invariant**: Steps 1-4 still hold, plus 4 top edge side stickers match centers.

### Step 6: Top Corner Positioning (PLL Corners)

**Display**: `"STEP 6: POSITION TOP CORNERS"` at start. `"  CYCLING CORNERS"` before each algorithm application.

**Goal**: All 4 top corners in correct positions (colors may still be twisted).

A corner is "correctly positioned" if its 3 sticker colors (as a set) match the 3 adjacent centers, regardless of which face each color is on:
- TFR (2,0,0): `{CL(2,0,0,4), CL(2,0,0,0), CL(2,0,0,2)}` = `{2, 4, 3}` (yellow, red, blue)
- TFL (0,0,0): `{CL(0,0,0,4), CL(0,0,0,0), CL(0,0,0,3)}` = `{2, 4, 6}` (yellow, red, cyan)
- TBR (2,0,2): `{CL(2,0,2,4), CL(2,0,2,1), CL(2,0,2,2)}` = `{2, 5, 3}` (yellow, buff, blue)
- TBL (0,0,2): `{CL(0,0,2,4), CL(0,0,2,1), CL(0,0,2,3)}` = `{2, 5, 6}` (yellow, buff, cyan)

**Algorithm**: `URulUruL` (U R U' L' U R' U' L) — cycles 3 corners CCW (TFL→TBL→TBR), keeps TFR fixed.

**Strategy** (loop until all positioned):
a. Check which U rotation (0-3 CW turns) would place the most corners correctly — check by comparing color sets at each position, without moving
b. Apply that many U turns
c. If all 4 correct, done
d. Rotate U to place a correct corner at TFR (the algorithm keeps TFR fixed)
e. Apply algorithm (cycles the other 3 corners)
f. Loop back to step (a)

If no rotation gives any correct corner (rare), apply algorithm once to create one, then loop. At most 3 applications needed after finding a correct TFR.

**Invariant**: Steps 1-5 still hold, plus 4 top corners in correct positions (colors match adjacent centers, any orientation).

### Step 7: Top Corner Orientation

**Display**: `"STEP 7: ORIENT TOP CORNERS"` at start. `"  TWISTING CORNER N"` before each corner's R'D'RD sequence.

**Goal**: Twist top corners so yellow (2) faces up on all 4.
- `CL(2,0,0,4)=2` (TFR)
- `CL(0,0,0,4)=2` (TFL)
- `CL(2,0,2,4)=2` (TBR)
- `CL(0,0,2,4)=2` (TBL)

**Algorithm**: `rdRD` (R' D' R D) applied 2 or 4 times per corner.

**Strategy**:
a. For each of the 4 corners:
   - Rotate U (only) to bring an unsolved corner to TFR — unsolved means `CL(2,0,0,4)<>2`
   - Apply `rdRD` repeatedly (checking `CL(2,0,0,4)` after each application) until `CL(2,0,0,4)=2` — takes exactly 2 or 4 repetitions
   - Do NOT rotate the whole cube or apply any non-U move between corners
b. After all 4 corners are oriented, rotate U (0-3 turns) until the top edge side stickers match their centers — this final alignment completes the solve

U CW cycle for corners at this step: same as Step 2 — TFR(4)→TFL(5)→TBL(7)→TBR(6)→TFR(4). To bring TFL to TFR position, apply `u` (U'). To bring TBL, apply `UU`. To bring TBR, apply `U`.

**Critical**: Bottom layers appear scrambled during this step. This is normal — they restore after all 4 corners are processed. Only use U between corners. Always complete the full `rdRD` sequence (don't stop partway).

**Invariant**: Entire cube solved: all 54 visible stickers match solved state.

## Implementation Sequence

1. ~~Phase 1: Engine extension (L/D/B + DoMoves)~~ DONE
2. ~~Phase 2: Solver skeleton + Step 1 (bottom cross)~~ DONE — 16/16 scramble tests pass
3. Phase 3: Steps 2-3 (bottom corners + middle edges) — IN PROGRESS
   - FindCorner subroutine: DONE (searches 8 positions x 3 orientations)
   - BFR insertion algorithms verified for CO=1 and CO=2
   - SolveBottomCorners subroutine: not yet written
4. Phase 4: Steps 4-7 (top layer — more formulaic, fewer cases)

Verify each step's algorithms against our engine before writing the BASIC code.

## Validation

### Algorithm verification
Before writing BASIC code for each step, verify the algorithm strings work with our engine using a Python test (like `test_rubiks_moves.py`): apply the algorithm, check that it produces the expected result.

### Step-by-step solve verification
After implementing each step, run it on multiple scrambles and verify the step's invariant holds (see **Invariant** at end of each step above). Each step's invariant builds on the previous — later steps must not disturb earlier work.

### Test structure
Use `tests/unit/test_rubiks_moves.py` as a model. For each step, test with 10-20 random scrambles (marked `@pytest.mark.slow`). The test scrambles the cube, runs the solver through step N, then checks the invariant.
