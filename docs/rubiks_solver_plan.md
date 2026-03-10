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
| 8 | FR | `f` | `r` (if TI≥1), `fUF` (if TI≥2) |
| 9 | FL | `F` | `L` (if TI≥1) |
| 10 | BR | `B` | `R` (if TI≥1), `BUb` (if TI≥3) |
| 11 | BL | `b` | `l` (if TI≥3) |

**Alignment**: After the edge is in the top layer (EP 4-7), rotate U to position it above its target slot. Top-edge cycle under U CW: EP 4 (front) → EP 7 (left) → EP 6 (back) → EP 5 (right) → EP 4. Compute 0-3 U turns needed.

**Insertion** (dispatch on target slot EI and edge orientation EO):
| EI | Slot | EO=0 (bottom-color on top) | EO=1 (bottom-color on side) |
|----|------|---------------------------|----------------------------|
| 0 | Front | `FF` | `uRF` |
| 1 | Right | `RR` | `uBR` |
| 2 | Back | `BB` | `uLB` |
| 3 | Left | `LL` | `uFL` |

EO=0 inserts with a double face turn. EO=1 uses a 3-move sequence: U' then two CW turns (the adjacent face in the CW direction, then the target face).

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

**Display**: `"STEP 2: BOTTOM CORNERS"` at start. `"  BFR CORNER"` / `"  BFL CORNER"` / `"  BBR CORNER"` / `"  BBL CORNER"` before each corner. `"  EXTRACTING"` / `"  ALIGNING"` / `"  INSERTING"` for sub-actions.

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
| 0 | BFR | `ruR` (R' U' R) |
| 1 | BFL | `FUf` (F U F') |
| 2 | BBR | `BUb` (B U B') |
| 3 | BBL | `luL` (L' U' L) |

**Alignment**: Each bottom corner (CI) maps to the top corner directly above it:
- BFR (CI=0) → TFR (CP=4)
- BFL (CI=1) → TFL (CP=5)
- BBR (CI=2) → TBR (CP=6)
- BBL (CI=3) → TBL (CP=7)

U CW cycle for corners: TFR(4)→TFL(5)→TBL(7)→TBR(6)→TFR(4). Cycle positions: 4=0, 5=1, 7=2, 6=3.

**Insertion** (dispatch on target CI and CO):

Handedness: BFR and BBL are "CCW-first" — triggers use the pattern `face' U' face`. BFL and BBR are "CW-first" — triggers use the pattern `face U face'`. Each trigger has one CO fixed point; the two triggers for a slot complement each other. Exception: BBR has no working R-face trigger, so only the B trigger is used.

| Target | Handedness | CO=0 default | CO=1 (Z-face) | CO=2 (X-face) |
|--------|-----------|-------------|---------------|---------------|
| BFR | CCW-first | `fuF` | `fuF` (F' U' F) | `rUR` (R' U R) |
| BFL | CW-first | `FUf` | `FUf` (F U F') | `Lul` (L U' L') |
| BBR | CW-first | `BUb` | `BUb` (B U B') | `BUb` (B U B') |
| BBL | CCW-first | `buB` | `buB` (B' U' B) | `lUL` (L' U L) |

CO=0 (bottom color on top) converges in 2 insert+retry cycles using the default listed above.

**Strategy** (for each corner, retry loop up to 6 iterations):
a. Find the target corner (search all 8 positions for 3 target colors)
b. If solved (CP = target slot AND CO=0), done
c. If in bottom layer (CP 0-3) but not solved, extract to top using the **current slot's** extraction algorithm (dispatch on CP, not CI)
d. Rotate U to align corner above its target slot (use cycle positions to compute number of U turns)
e. Look up the target slot's row in the algorithm table. Apply the insert for the current CO value (CO=1 or CO=2 column). For CO=0, use the CO=0 default.
f. Loop back to step (a)

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
| 10 | BR | `UBuburUR` |
| 11 | BL | `ubUBULul` |

**Alignment**: After the edge is in the top layer (EP 4-7), one sticker is on the top face (F4) and one is on a side face (F0/F1/F2/F3). Rotate U until the side sticker's color matches the center color on that same face. The top-edge side stickers cycle under U CW as: top-front(F0) → top-left(F3) → top-back(F1) → top-right(F2) → top-front(F0). Compute the number of U turns needed (0-3) using cycle positions, same method as Steps 1-2 alignment. After alignment, the top sticker's color determines which direction to insert.

**Insertion**:
| Slot | Side sticker matches | Insert toward | Algorithm | Standard notation |
|------|-------------------|---------|-----------|-------------------|
| FR | F | R | `URurufUF` | U R U' R' U' F' U F |
| FR | R | F | `ufUFURur` | U' F' U F U R U' R' |
| FL | F | L | `ulULUFuf` | U' L' U L U F U' F' |
| FL | L | F | `UFufulUL` | U F U' F' U' L' U L |
| BR | R | B | `UBuburUR` | U B U' B' U' R' U R |
| BR | B | R | `urURUBub` | U' R' U R U B U' B' |
| BL | L | B | `ubUBULul` | U' B' U B U L U' L' |
| BL | B | L | `ULulubuB` | U L U' L' U' B' U B |

"Side sticker matches" = the face whose center matches the side sticker after U alignment. "Insert toward" = the face whose center matches the top sticker's color, determining the insertion direction.

FR and FL are the standard Ruwix algorithms. All others follow the same two patterns with substituted face letters:
- `U [target] U' [target]' U' [source]' U [source]` (target is CW from source, viewed from top)
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

**Invariant**: Steps 1-3 still hold, plus 4 top edges show yellow on top: `CL(x,0,z,4)=2`.

### Step 5: Top Edge Alignment (PLL Edges)

**Display**: `"STEP 5: ALIGN TOP EDGES"` at start. `"  SWAPPING EDGES"` before each algorithm application.

**Goal**: Each top-edge side sticker matches its center color.
- `CL(1,0,0,0)=4` (front edge side = red)
- `CL(2,0,1,2)=3` (right edge side = blue)
- `CL(1,0,2,1)=5` (back edge side = buff)
- `CL(0,0,1,3)=6` (left edge side = cyan)

**Algorithm**: `RUrURUUrU` (R U R' U R U2 R' U) — swaps the front and left edges (right and back preserved). Verified against engine. Note: also disrupts corner positions/orientations, so must be applied after Step 4 (OLL edges) but corners are handled in Steps 6-7.

**Edge side sticker cycle under U CW**: front(F0) → left(F3) → back(F1) → right(F2) → front(F0). Cycle positions: front=0, left=1, back=2, right=3.

**Strategy** (loop, at most 4 algorithm applications):
a. For each r=0..3, shift the 4 side sticker colors by r positions in the cycle and count how many match their target center colors (front=4, right=3, back=5, left=6). Pick the r with the highest count.
b. Apply r U turns (0=none, 1=`U`, 2=`UU`, 3=`u`)
c. If all 4 match, done
d. If no rotation gives any match (rare but possible), apply algorithm once to create a match, then loop back to (a)
e. Rotate U to position a matching edge at the back or right (the algorithm preserves both; back is conventional)
f. Apply algorithm (swaps front and left edges; right and back preserved)
g. Loop back to step (a). Error out if not solved after 5 iterations.

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

**Corner position cycle under U CW**: TFR→TFL→TBL→TBR→TFR. Cycle positions: TFR=0, TFL=1, TBL=2, TBR=3.

**Strategy** (loop, at most 4 algorithm applications):
a. For each r=0..3, shift the 4 corner color sets by r positions in the cycle and count how many match their target color sets (TFR={2,4,3}, TFL={2,4,6}, TBR={2,5,3}, TBL={2,5,6}). Pick the r with the highest count.
b. Apply r U turns (0=none, 1=`U`, 2=`UU`, 3=`u`)
c. If all 4 correct, done
d. If no rotation gives any correct corner (rare), apply algorithm once to create one, then loop back to (a)
e. Rotate U to place a correct corner at TFR (the algorithm keeps TFR fixed)
f. Apply algorithm (cycles the other 3 corners)
g. Loop back to step (a). Error out if not solved after 5 iterations.

**Invariant**: Steps 1-5 still hold, plus 4 top corners in correct positions (colors match adjacent centers, any orientation).

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
| TFL | `u` (U') |
| TBR | `U` |
| TBL | `UU` |

**Strategy** (process up to 4 corners, then final alignment):
a. If all 4 top corners show `CL(x,0,z,4)=2`, go to (e)
b. If TFR is already oriented (`CL(2,0,0,4)=2`), find the first unsolved corner (check TFL, TBR, TBL in order) and rotate U per the table above to bring it to TFR
c. Apply `rdRD` repeatedly (checking `CL(2,0,0,4)` after each pair of applications) until `CL(2,0,0,4)=2` — takes exactly 2 or 4 repetitions. Error out if not solved after 6 repetitions.
d. Loop back to (a). Only U moves are allowed between corners — no other face moves, no whole-cube rotations.
e. Final alignment: rotate U (0-3 turns) until the top edge side stickers match their centers (same cycle-position method as Step 5). This completes the solve.

**Critical**: Bottom layers appear scrambled during this step. This is normal — they restore after all 4 corners are processed. Only use U between corners. Always complete the full `rdRD` sequence (don't stop partway).

**Invariant**: Entire cube solved: all 54 visible stickers match solved state.

## Implementation Progress

- ~~Engine extension (L/D/B + DoMoves)~~ DONE
- ~~Step 1 (bottom cross)~~ DONE — 16/16 scramble tests pass
- ~~Step 2 (bottom corners)~~ DONE — 16/16 scramble tests pass. FindCorner, extraction, alignment, insertion all implemented. Handedness issue resolved (CW-first vs CCW-first triggers).
- Step 3 (middle edges): not yet written
- Steps 4-7 (top layer): not yet written

Verify each step's algorithms against our engine before writing the BASIC code.

## Validation

### Algorithm verification
Before writing BASIC code for each step, verify the algorithm strings work with our engine using a Python test (like `test_rubiks_moves.py`): apply the algorithm, check that it produces the expected result.

### Step-by-step solve verification
After implementing each step, run it on multiple scrambles and verify the step's invariant holds (see **Invariant** at end of each step above). Each step's invariant builds on the previous — later steps must not disturb earlier work.

### Test structure
Use `tests/unit/test_rubiks_moves.py` as a model. For each step, test with 10-20 random scrambles (marked `@pytest.mark.slow`). The test scrambles the cube, runs the solver through step N, then checks the invariant.
