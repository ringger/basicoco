# Rubik's Cube Solver Plan

Beginner's layer-by-layer method implemented in CoCo BASIC.
Reference: [Ruwix Beginner Method](https://ruwix.com/the-rubiks-cube/how-to-solve-the-rubiks-cube-beginners-method/). See `docs/rubiks_reference_algorithms.md` for standard algorithms. Our solver uses the same method but solves bottom-first (Ruwix solves white/top-first), so first-layer algorithms use U instead of D.

## Engine (lib_rubiks_engine.bas)

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

DR=1 for CW, DR=-1 for CCW. CW is defined looking at each face from outside. All faces match standard Rubik's notation: engine `R` = standard R (CW), engine `r` = standard R' (CCW), etc.

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

#### Terminology

- **EP** (edge position): Index 0-11 identifying an edge slot (see table below)
- **CP** (corner position): Index 0-7 identifying a corner slot (see table below)
- **EI** (edge index): Iteration index for target edges within a step (e.g., 0-3 for the 4 middle edges in Step 3)
- **CI** (corner index): Iteration index for target corners within a step (e.g., 0-3 for the 4 bottom corners in Step 2)
- **EO** (edge orientation): 0 = bottom/top color on the Y-face (top or bottom sticker), 1 = bottom/top color on the side face (Z or X sticker)
- **CO** (corner orientation): 0 = bottom/top color on the Y-face, 1 = on the Z-face, 2 = on the X-face

#### Edge Pieces (12 edges, 2 visible stickers each)
| EP | Edge | Coords | Sticker Faces |
|----|------|--------|--------------|
| 0 | Bottom-Front | (1,2,0) | F5, F0 |
| 1 | Bottom-Right | (2,2,1) | F5, F2 |
| 2 | Bottom-Back | (1,2,2) | F5, F1 |
| 3 | Bottom-Left | (0,2,1) | F5, F3 |
| 4 | Top-Front | (1,0,0) | F4, F0 |
| 5 | Top-Right | (2,0,1) | F4, F2 |
| 6 | Top-Back | (1,0,2) | F4, F1 |
| 7 | Top-Left | (0,0,1) | F4, F3 |
| 8 | Front-Right | (2,1,0) | F0, F2 |
| 9 | Front-Left | (0,1,0) | F0, F3 |
| 10 | Back-Right | (2,1,2) | F1, F2 |
| 11 | Back-Left | (0,1,2) | F1, F3 |

#### Corner Pieces (8 corners, 3 visible stickers each)
| CP | Corner | Coords | Sticker Faces |
|----|--------|--------|--------------|
| 0 | Bottom-Front-Right (BFR) | (2,2,0) | F5, F0, F2 |
| 1 | Bottom-Front-Left (BFL) | (0,2,0) | F5, F0, F3 |
| 2 | Bottom-Back-Right (BBR) | (2,2,2) | F5, F1, F2 |
| 3 | Bottom-Back-Left (BBL) | (0,2,2) | F5, F1, F3 |
| 4 | Top-Front-Right (TFR) | (2,0,0) | F4, F0, F2 |
| 5 | Top-Front-Left (TFL) | (0,0,0) | F4, F0, F3 |
| 6 | Top-Back-Right (TBR) | (2,0,2) | F4, F1, F2 |
| 7 | Top-Back-Left (TBL) | (0,0,2) | F4, F1, F3 |

## Solving Steps

### Narrative Display

Each step PRINTs status messages so the observer can follow the solve on screen. Messages use a consistent pattern:
- **Step start**: `PRINT "STEP N: DESCRIPTION"` (e.g., `"STEP 1: BOTTOM CROSS"`)
- **Sub-actions**: `PRINT "  action..."` (e.g., `"  SOLVING FRONT EDGE..."`, `"  EXTRACTING FROM BFR"`)
- **Step complete**: `PRINT "  DONE!"` after invariant check passes

Messages are printed before the action they describe. Animation (`AN=1`) is turned on after solving to show the final state; solving runs with `AN=0` for speed.

### Program Structure
```basic
lib_rubiks_solver.bas:
  MERGE "lib_rubiks_engine"
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

### Step 1: Bottom Cross

**Display**: `"STEP 1: BOTTOM CROSS"` at start. `"  FRONT EDGE"` / `"  RIGHT EDGE"` / `"  BACK EDGE"` / `"  LEFT EDGE"` before each edge.

**Goal**: 4 bottom edges placed with correct stickers on both faces.
- `CL(1,2,0,5)=7` AND `CL(1,2,0,0)=4` (bottom-front: magenta down, red on front)
- `CL(2,2,1,5)=7` AND `CL(2,2,1,2)=3` (bottom-right: magenta down, blue on right)
- `CL(1,2,2,5)=7` AND `CL(1,2,2,1)=5` (bottom-back: magenta down, buff on back)
- `CL(0,2,1,5)=7` AND `CL(0,2,1,3)=6` (bottom-left: magenta down, cyan on left)

**Target edges** (EI = iteration order, solved in this order):
| EI | Slot | Target EP | Target colors | Coords |
|----|------|-----------|---------------|--------|
| 0 | Front | 0 | 7 (magenta), 4 (red) | (1,2,0) |
| 1 | Right | 1 | 7 (magenta), 3 (blue) | (2,2,1) |
| 2 | Back | 2 | 7 (magenta), 5 (buff) | (1,2,2) |
| 3 | Left | 3 | 7 (magenta), 6 (cyan) | (0,2,1) |

**Finding**: Use FindEdge to search all 12 edge positions (EP 0-11) for the two target colors.

**Extraction from bottom**: If the target edge is in the bottom layer (EP 0-3) but wrong position or flipped, a double face turn kicks it to the top:
| Current EP | Slot | Algorithm |
|-----------|------|-----------|
| 0 | Front | `FF` |
| 1 | Right | `RR` |
| 2 | Back | `BB` |
| 3 | Left | `LL` |

**Extraction from middle**: If the target edge is in the middle layer (EP 8-11), a single face turn kicks it to the top. The choice of turn avoids disturbing already-solved bottom edges (TI = number of edges solved so far, 0-3):
| Current EP | Slot | Default | If would disturb solved edge |
|-----------|------|---------|------------------------------|
| 8 | FR | `f` | `R` (if TI≥1), `fUF` (if TI≥2) |
| 9 | FL | `F` | `l` (if TI≥1) |
| 10 | BR | `B` | `r` (if TI≥1), `BUb` (if TI≥3) |
| 11 | BL | `b` | `L` (if TI≥3) |

**Alignment**: After the edge is in the top layer (EP 4-7), rotate U to position it above its target slot. Top-edge cycle under U CW: EP 4 (front) → EP 7 (left) → EP 6 (back) → EP 5 (right) → EP 4. Cycle positions: 4=0, 7=1, 6=2, 5=3. Compute 0-3 U turns needed.

**Insertion** (dispatch on target slot EI and edge orientation EO):
| EI | Slot | EO=0 (bottom-color on top) | EO=1 (bottom-color on side) |
|----|------|---------------------------|----------------------------|
| 0 | Front | `FF` | `rF` |
| 1 | Right | `RR` | `Br` |
| 2 | Back | `BB` | `lB` |
| 3 | Left | `LL` | `Fl` |

EO=0 inserts with a double face turn. EO=1 uses a 2-move sequence: the adjacent face CCW, then the target face CW.

**Strategy** (retry loop, up to 3 passes over all 4 edges):
a. Find the target edge (search all 12 positions for the two target colors)
b. If already solved (correct EP and both stickers match), skip
c. If in bottom layer (EP 0-3) but not solved, extract to top using the current slot's bottom extraction algorithm
d. If in middle layer (EP 8-11), extract to top using the current slot's middle extraction algorithm (context-sensitive to avoid disturbing solved edges)
e. Rotate U to align the edge above its target slot
f. Look up the target slot's insertion algorithm for the current EO value. Apply it.
g. Check if solved; if not, retry loop handles it

**Invariant**: 4 bottom edges correct: `CL(x,y,z,5)=7` and side sticker matches center, for all 4 bottom edge positions.

### Step 2: Bottom Corners

**Display**: `"STEP 2: BOTTOM CORNERS"` at start. `"  BFR CORNER"` / `"  BFL CORNER"` / `"  BBR CORNER"` / `"  BBL CORNER"` before each corner. `"    EXTRACTING"` / `"    ALIGNING"` / `"    INSERTING"` for sub-actions (4-space indent).

**Goal**: 4 bottom corners placed with correct stickers on all 3 faces.
- `CL(2,2,0,5)=7` AND `CL(2,2,0,0)=4` AND `CL(2,2,0,2)=3` (BFR: magenta, red, blue)
- `CL(0,2,0,5)=7` AND `CL(0,2,0,0)=4` AND `CL(0,2,0,3)=6` (BFL: magenta, red, cyan)
- `CL(2,2,2,5)=7` AND `CL(2,2,2,1)=5` AND `CL(2,2,2,2)=3` (BBR: magenta, buff, blue)
- `CL(0,2,2,5)=7` AND `CL(0,2,2,1)=5` AND `CL(0,2,2,3)=6` (BBL: magenta, buff, cyan)

Each bottom corner sits between two side faces (A and B). CO=0 means bottom color on Y-face (top), CO=1 on Z-face, CO=2 on X-face.

**Target corners** (CI = iteration order):
| CI | Slot | Target CP | Target colors | Coords |
|----|------|-----------|---------------|--------|
| 0 | BFR | 0 | 7 (magenta), 4 (red), 3 (blue) | (2,2,0) |
| 1 | BFL | 1 | 7 (magenta), 4 (red), 6 (cyan) | (0,2,0) |
| 2 | BBR | 2 | 7 (magenta), 5 (buff), 3 (blue) | (2,2,2) |
| 3 | BBL | 3 | 7 (magenta), 5 (buff), 6 (cyan) | (0,2,2) |

**Finding**: Use FindCorner to search all 8 corner positions (CP 0-7) for the 3 target colors.

**Extraction** (dispatch on current position CP, not target CI — a corner can be in any bottom slot):

| Current CP | Slot | Algorithm |
|-----------|------|-----------|
| 0 | BFR | `Rur` (R U' R') |
| 1 | BFL | `FUf` (F U F') |
| 2 | BBR | `BUb` (B U B') |
| 3 | BBL | `Lul` (L U' L') |

**Alignment**: Each bottom corner (CI) maps to the top corner directly above it:
- BFR (CI=0) → TFR (CP=4)
- BFL (CI=1) → TFL (CP=5)
- BBR (CI=2) → TBR (CP=6)
- BBL (CI=3) → TBL (CP=7)

U CW cycle for corners: TFR(4)→TFL(5)→TBL(7)→TBR(6)→TFR(4). Cycle positions: 4=0, 5=1, 7=2, 6=3.

**Insertion** (dispatch on target CI and CO):

Each slot has two adjacent faces with one trigger each. CO=1 and CO=2 each have a single-application trigger. CO=0 (bottom color on top) requires two applications — the first trigger changes the CO, then a retry with the complementary trigger solves it.

| Target | CO=0 default | CO=1 (Z-face) | CO=2 (X-face) |
|--------|-------------|---------------|---------------|
| BFR | `fuF` | `fuF` (F' U' F) | `RUr` (R U R') |
| BFL | `FUf` | `FUf` (F U F') | `luL` (L' U' L) |
| BBR | `BUb` | `BUb` (B U B') | `ruR` (R' U' R) |
| BBL | `buB` | `buB` (B' U' B) | `LUl` (L U L') |

CO=0 (bottom color on top) converges in 2 insert+retry cycles using the default listed above.

**Strategy** (up to 6 passes over all 4 corners; for each corner, retry loop up to 6 iterations):
a. Find the target corner (search all 8 positions for 3 target colors)
b. If solved (CP = target slot AND CO=0), done
c. If in bottom layer (CP 0-3) but not solved, extract to top using the **current slot's** extraction algorithm (dispatch on CP, not CI)
d. Rotate U to align corner above its target slot (use cycle positions to compute number of U turns)
e. Look up the target slot's row in the algorithm table. Apply the insert for the current CO value (CO=1 or CO=2 column). For CO=0, use the CO=0 default.
f. Loop back to step (a)
After each pass over all 4 corners, check if all are solved; if so, return early.

**Invariant**: Step 1 still holds, plus 4 bottom corners correct: `CL(x,y,z,5)=7` and both side stickers match centers.

### Step 3: Middle Layer Edges

**Display**: `"STEP 3: MIDDLE EDGES"` at start. `"  FR EDGE"` / `"  FL EDGE"` / `"  BR EDGE"` / `"  BL EDGE"` before each edge. `"  EXTRACTING"` / `"  ALIGNING"` / `"  INSERTING"` for sub-actions.

**Goal**: 4 middle-layer edges placed correctly (FR, FL, BR, BL). Neither color is yellow or magenta — both are side colors.
- `CL(2,1,0,0)=4` AND `CL(2,1,0,2)=3` (FR: red on front, blue on right)
- `CL(0,1,0,0)=4` AND `CL(0,1,0,3)=6` (FL: red on front, cyan on left)
- `CL(2,1,2,1)=5` AND `CL(2,1,2,2)=3` (BR: buff on back, blue on right)
- `CL(0,1,2,1)=5` AND `CL(0,1,2,3)=6` (BL: buff on back, cyan on left)

**Target edges** (EI = iteration order):
| EI | Slot | Target EP | Target colors | Coords |
|----|------|-----------|---------------|--------|
| 0 | FR | 8 | 4 (red), 3 (blue) | (2,1,0) |
| 1 | FL | 9 | 4 (red), 6 (cyan) | (0,1,0) |
| 2 | BR | 10 | 5 (buff), 3 (blue) | (2,1,2) |
| 3 | BL | 11 | 5 (buff), 6 (cyan) | (0,1,2) |

**Finding**: Use FindEdge (same as Step 1) to search all 12 positions. After Steps 1-2, middle edges can only be in the top layer (EP 4-7) or middle layer (EP 8-11) — never bottom, since bottom edges contain magenta.

**Extraction**: If the target edge is in a wrong middle slot (EP 8-11), apply the first insert algorithm for that slot to eject it to the top layer:
| Current EP | Current slot | Extraction algorithm |
|-----------|-------------|---------------------|
| 8 | FR | `URurufUF` |
| 9 | FL | `ulULUFuf` |
| 10 | BR | `urURUBub` |
| 11 | BL | `ULulubUB` |

**Alignment**: After the edge is in the top layer (EP 4-7), one sticker is on the top face (F4) and one is on a side face (F0/F1/F2/F3). Rotate U until the side sticker's color matches the center color on that same face. The top-edge side stickers cycle under U CW as: top-front(F0) → top-left(F3) → top-back(F1) → top-right(F2) → top-front(F0). Compute the number of U turns needed (0-3) using cycle positions, same method as Steps 1-2 alignment. After alignment, the top sticker's color determines which direction to insert.

**Insertion**:
| Slot | Side sticker matches | Insert toward | Algorithm | Standard notation |
|------|-------------------|---------|-----------|-------------------|
| FR | F | R | `URurufUF` | U R U' R' U' F' U F |
| FR | R | F | `ufUFURur` | U' F' U F U R U' R' |
| FL | F | L | `ulULUFuf` | U' L' U L U F U' F' |
| FL | L | F | `UFufulUL` | U F U' F' U' L' U L |
| BR | B | R | `urURUBub` | U' R' U R U B U' B' |
| BR | R | B | `UBuburUR` | U B U' B' U' R' U R |
| BL | B | L | `ULulubUB` | U L U' L' U' B' U B |
| BL | L | B | `ubUBULul` | U' B' U B U L U' L' |

"Side sticker matches" = the face whose center matches the side sticker after U alignment. "Insert toward" = the face whose center matches the top sticker's color, determining the insertion direction.

These are the standard Ruwix F2L algorithms (`U R U' R' U' F' U F` / `U' L' U L U F U' F'`) with face letters substituted for each slot. All 8 follow two symmetric patterns:
- `U [target] U' [target]' U' [source]' U [source]` (target is CW from source in physical layout F→R→B→L)
- `U' [target]' U [target] U [source] U' [source]'` (target is CCW from source)

**Strategy** (retry loop, up to 6 passes over all 4 edges):
a. Find the target edge (search all 12 positions for two target colors)
b. If already solved (correct position and orientation), skip
c. If in middle layer but wrong (EP 8-11), extract to top using the **current slot's** extraction algorithm
d. Re-find edge (now in top layer, EP 4-7)
e. Rotate U until the side sticker matches its adjacent center, then re-find edge
f. Look up the insert algorithm from the table: "Side sticker matches" = the face the side sticker now touches, "Insert toward" = the face matching the top sticker's color
g. Apply insert algorithm
h. Check if solved; if not, retry loop handles it

**Invariant**: Steps 1-2 still hold, plus 4 middle edges correct: both stickers match adjacent centers.

### Steps 4-7: Top Layer (Last Layer)

**Minimal invariants**: Each step preserves all prior work. Steps 4-7 do NOT need to be treated as a unit — each algorithm individually preserves F2L. Exception: Step 7's `R' D' R D` temporarily scrambles bottom layers *during* execution, but restores them after all 4 corners are processed.

### Step 4: Top Cross (OLL Edges)

**Display**: `"STEP 4: TOP CROSS"` at start. `"  DOT->L"` / `"  L->LINE"` / `"  LINE->CROSS"` before each algorithm application, describing the case being handled.

**Goal**: Yellow (2) on all 4 top-edge stickers.
- `CL(1,0,0,4)=2` (top-front)
- `CL(2,0,1,4)=2` (top-right)
- `CL(1,0,2,4)=2` (top-back)
- `CL(0,0,1,4)=2` (top-left)

**Algorithm**: `FRUruf` (F R U R' U' F')

**Strategy** (loop, at most 3 algorithm applications):
a. Count how many of the 4 top edges show yellow (YC)
b. If YC=4, done
c. If YC=0 (dot): apply algorithm (no pre-rotation needed) → creates L-shape, loop back
d. If YC=2, distinguish L-shape from line:
   - **L-shape** (two adjacent edges yellow): rotate U until the two yellow edges are at back and left (i.e., `CL(1,0,2,4)=2` AND `CL(0,0,1,4)=2`), apply algorithm → creates line, loop back
   - **Line** (two opposite edges yellow): rotate U until yellow edges are at left and right (i.e., `CL(2,0,1,4)=2` AND `CL(0,0,1,4)=2`), apply algorithm → creates cross
e. If YC=1 or YC=3, error out (impossible on a valid cube — indicates a bug or bad state)
f. Loop back to step (a). Error out if not solved after 4 iterations.

Adjacent vs opposite: if front+right, front+left, back+right, or back+left are yellow → L-shape. If front+back or left+right → line.

**Invariant**: F2L preserved (Steps 1-3 still hold), plus 4 top edges show yellow on top: `CL(x,0,z,4)=2`.

### Step 5: Top Edge Alignment (PLL Edges)

**Display**: `"STEP 5: ALIGN TOP EDGES"` at start. `"  SWAPPING EDGES"` before each algorithm application.

**Goal**: Each top-edge side sticker matches its center color.
- `CL(1,0,0,0)=4` (front edge side = red)
- `CL(2,0,1,2)=3` (right edge side = blue)
- `CL(1,0,2,1)=5` (back edge side = buff)
- `CL(0,0,1,3)=6` (left edge side = cyan)

**Algorithm**: `RUrURUUrU` (R U R' U R U2 R' U) — swaps the front and left top edges (right and back preserved). Uses only R and U moves, preserves F2L. Also disrupts top corner positions/orientations, but corners are handled in Steps 6-7.

**Edge side sticker cycle under U CW**: front(F0) → left(F3) → back(F1) → right(F2) → front(F0). Cycle positions: front=0, left=1, back=2, right=3.

**Strategy** (loop, at most 4 algorithm applications):
a. For each r=0..3, shift the 4 side sticker colors by r positions in the cycle and count how many match their target center colors (front=4, right=3, back=5, left=6). Pick the r with the highest count.
b. Apply r U turns (0=none, 1=`U`, 2=`UU`, 3=`u`)
c. If all 4 match, done
d. If no rotation gives any match (rare but possible), apply algorithm once to create a match, then loop back to (a)
e. Rotate U to position a matching edge at the back or right (the algorithm preserves both; back is conventional)
f. Apply algorithm (swaps front and left edges; right and back preserved)
g. Loop back to step (a). Error out if not solved after 5 iterations.

**Invariant**: F2L preserved, plus top cross intact and 4 top edge side stickers match centers.

### Step 6: Top Corner Positioning (PLL Corners)

**Display**: `"STEP 6: POSITION TOP CORNERS"` at start. `"  CYCLING CORNERS"` before each algorithm application.

**Goal**: All 4 top corners in correct positions (colors may still be twisted).

A corner is "correctly positioned" if its 3 sticker colors (as a set) match the 3 adjacent centers, regardless of which face each color is on:
- TFR (2,0,0): `{CL(2,0,0,4), CL(2,0,0,0), CL(2,0,0,2)}` = `{2, 4, 3}` (yellow, red, blue)
- TFL (0,0,0): `{CL(0,0,0,4), CL(0,0,0,0), CL(0,0,0,3)}` = `{2, 4, 6}` (yellow, red, cyan)
- TBR (2,0,2): `{CL(2,0,2,4), CL(2,0,2,1), CL(2,0,2,2)}` = `{2, 5, 3}` (yellow, buff, blue)
- TBL (0,0,2): `{CL(0,0,2,4), CL(0,0,2,1), CL(0,0,2,3)}` = `{2, 5, 6}` (yellow, buff, cyan)

**Algorithm**: `URulUruL` (U R U' L' U R' U' L) — cycles 3 corners CCW (TFL→TBL→TBR), keeps TFR fixed. Preserves F2L.

**Corner position cycle under U CW**: TFR→TBR→TBL→TFL→TFR. Cycle positions: TFR=0, TFL=3, TBR=1, TBL=2.

**Strategy** (loop, at most 4 algorithm applications):
a. For each r=0..3, shift the 4 corner color sets by r positions in the cycle and count how many match their target color sets (TFR={2,4,3}, TFL={2,4,6}, TBR={2,5,3}, TBL={2,5,6}). Pick the r with the highest count.
b. Apply r U turns (0=none, 1=`U`, 2=`UU`, 3=`u`)
c. If all 4 correct, done
d. If no rotation gives any correct corner (rare), apply algorithm once to create one, then loop back to (a)
e. Rotate U to place a correct corner at TFR (the algorithm keeps TFR fixed)
f. Apply algorithm (cycles the other 3 corners)
g. Loop back to step (a). Error out if not solved after 5 iterations.

**Invariant**: F2L preserved, top edges aligned, plus 4 top corners in correct positions (colors match adjacent centers, any orientation).

### Step 7: Top Corner Orientation

**Display**: `"STEP 7: ORIENT TOP CORNERS"` at start. `"  TWISTING CORNER N"` before each corner's R'D'RD sequence.

**Goal**: Twist top corners so yellow (2) faces up on all 4.
- `CL(2,0,0,4)=2` (TFR)
- `CL(0,0,0,4)=2` (TFL)
- `CL(2,0,2,4)=2` (TBR)
- `CL(0,0,2,4)=2` (TBL)

**Algorithm**: `rdRD` (R' D' R D) applied 2 or 4 times per corner.

**U rotation to bring corner to TFR**:
| Corner | U moves |
|--------|---------|
| TFR | (already there) |
| TFL | `U` (U) |
| TBR | `u` (U') |
| TBL | `UU` |

**Strategy** (process up to 4 corners, then final alignment):
a. If all 4 top corners show `CL(x,0,z,4)=2`, go to (e)
b. If TFR is already oriented (`CL(2,0,0,4)=2`), find the first unsolved corner (check TFL, TBR, TBL in order) and rotate U per the table above to bring it to TFR
c. Apply `rdRD` repeatedly (checking `CL(2,0,0,4)` after each pair of applications) until `CL(2,0,0,4)=2` — takes exactly 2 or 4 repetitions. Error out if not solved after 6 repetitions.
d. Loop back to (a). Only U moves are allowed between corners — no other face moves, no whole-cube rotations.
e. Final alignment: rotate U (0-3 turns) until the top edge side stickers match their centers (same cycle-position method as Step 5). This completes the solve.

**Critical**: Bottom layers appear scrambled during this step. This is normal — they restore after all 4 corners are processed. Only use U between corners. Always complete the full `RdrD` sequence (don't stop partway).

**Invariant**: Entire cube solved: all 54 visible stickers match solved state.

## Implementation Progress

- ~~Engine extension (L/D/B + DoMoves)~~ DONE
- ~~Step 1 (bottom cross)~~ DONE — 16/16 scramble tests pass
- ~~Step 2 (bottom corners)~~ DONE — 16/16 scramble tests pass. FindCorner, extraction, alignment, insertion all implemented. Handedness issue resolved (CW-first vs CCW-first triggers).
- ~~Step 3 (middle edges)~~ DONE — 16/16 scramble tests pass. FindEdge, extraction, alignment, insertion all implemented. All 8 insertion algorithms verified empirically.
- ~~Step 4 (top cross)~~ DONE — 16/16 scramble tests pass. `FRUruf` (F R U R' U' F') preserves F2L — verified against pycuber and in engine tests.
- Steps 5-7 (top layer): not yet written

Verify each step's algorithms against our engine before writing the BASIC code.

## Validation

### Engine move validation (CRITICAL)

Every basic face move (R, U, F, L, D, B) in the BASIC engine must be validated against a trusted reference implementation (pycuber) before any solver work proceeds. This is the foundation — if the moves are wrong, every algorithm built on them will silently produce incorrect results, and debugging at the algorithm level will be misleading.

The validation tool (`tools/validate_moves.py`) applies each move in both our engine and pycuber, then compares every sticker on all 6 faces. All 6 moves must match exactly. Any mismatch indicates a bug in the engine's permutation or sticker remap logic.

**History**: The original PermTop (U move) had a reversed coordinate transform, making U rotate counterclockwise instead of clockwise. Steps 1-3 were developed and passed 48/48 tests against this backwards U — the solver algorithms compensated for the bug without anyone realizing the engine was wrong. The bug was only discovered when Step 4's `F R U R' U' F'` (which combines F and U) failed to preserve F2L. Validating against pycuber immediately identified the single broken move.

**Lesson**: Always validate the engine against a trusted implementation first. Never assume the engine is correct just because solver tests pass — the solver may have been tuned to work around an engine bug.

### Algorithm verification
Before writing BASIC code for each step, verify the algorithm strings work with our engine using a Python test (like `test_rubiks_moves.py`): apply the algorithm, check that it produces the expected result against pycuber.

### Step-by-step solve verification
After implementing each step, run it on multiple scrambles and verify the step's invariant holds (see **Invariant** at end of each step above).

**All steps**: Each step's invariant builds on the previous — later steps must not disturb earlier work. Verify F2L preservation after every step (Steps 4-7 included). Exception: during Step 7 execution, bottom layers are temporarily scrambled but must restore by completion.

### Test structure
Use `tests/unit/test_rubiks_moves.py` as a model. For each step, test with 10-20 random scrambles (marked `@pytest.mark.slow`). The test scrambles the cube, runs the solver through step N, then checks the full cumulative invariant (F2L + step's own goal).
