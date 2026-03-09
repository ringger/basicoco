# Rubik's Cube Solver Plan

Beginner's layer-by-layer method implemented in CoCo BASIC.

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
| Bottom-Front-Right | (2,2,0) | F5, F0, F2 |
| Bottom-Front-Left | (0,2,0) | F5, F0, F3 |
| Bottom-Back-Right | (2,2,2) | F5, F1, F2 |
| Bottom-Back-Left | (0,2,2) | F5, F1, F3 |
| Top-Front-Right | (2,0,0) | F4, F0, F2 |
| Top-Front-Left | (0,0,0) | F4, F0, F3 |
| Top-Back-Right | (2,0,2) | F4, F1, F2 |
| Top-Back-Left | (0,0,2) | F4, F1, F3 |

## Solving Steps

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

### Step 1: Bottom Cross

**Goal**: 4 bottom edges placed with correct stickers on both faces.
- `CL(1,2,0,5)=7` AND `CL(1,2,0,0)=4` (bottom-front: magenta down, red on front)
- `CL(2,2,1,5)=7` AND `CL(2,2,1,2)=3` (bottom-right: magenta down, blue on right)
- `CL(1,2,2,5)=7` AND `CL(1,2,2,1)=5` (bottom-back: magenta down, buff on back)
- `CL(0,2,1,5)=7` AND `CL(0,2,1,3)=6` (bottom-left: magenta down, cyan on left)

**Strategy** (for each of the 4 edges):
1. Find the target piece by searching all 12 edge positions for the two target colors
2. If already in place, skip
3. If in bottom layer (wrong position or flipped), kick to top with one face turn
4. If in middle layer, kick to top with one face turn
5. Rotate U to align the edge above its target slot
6. Insert:
   - If bottom-color faces the side: double face turn (e.g., `FF` for front slot)
   - If bottom-color faces up: use a 3-move insert (e.g., `URf` or similar)

**Most complex step** due to many source positions (12 possible locations x 2 orientations).

### Step 2: Bottom Corners

**Goal**: 4 bottom corners placed with correct stickers on all 3 faces.

**Strategy** (for each corner):
1. Find the target corner piece (search 8 corner positions for 3 target colors)
2. If already correct, skip
3. If in bottom layer but wrong, extract to top: e.g., `RUr` for bottom-front-right
4. Rotate U until target corner is above its slot
5. Insert based on which face has the bottom color:
   - Bottom color on right face: `RUrRUr` (repeated sexy move)
   - Bottom color on front face: `fUF` variant
   - Bottom color on top face: `RUUruRur`

**Working positions** (each corner uses different face pairs):
| Target | "Right" | "Front" | Position above slot |
|--------|---------|---------|-------------------|
| BFR (2,2,0) | R | F | (2,0,0) |
| BFL (0,2,0) | F | L | (0,0,0) |
| BBL (0,2,2) | L | B | (0,0,2) |
| BBR (2,2,2) | B | R | (2,0,2) |

### Step 3: Middle Layer Edges

**Goal**: 4 middle-layer edges placed correctly (FR, FL, BR, BL).

**Strategy**:
1. Find each target edge in the top layer or in a wrong middle-layer position
2. If in middle layer but wrong, extract by applying an insert algorithm (kicks it to top)
3. Rotate U to align the edge above the target slot
4. Apply right-insert or left-insert depending on which way the edge needs to go

**Algorithms** (standard middle-layer insertion):
| Slot | Right-insert (from above) | Left-insert (from above) |
|------|--------------------------|--------------------------|
| FR | `URurufUF` | `ufUFURur` |
| FL | `ulULUFuf` | `UFufuLUl` |
| BR | `UBuburUR` | `urURUBub` |
| BL | `ubUBULul` | `ULulubUB` |

Note: These algorithm strings need verification during implementation. The FR pair is the standard reference; others are adapted by substituting face letters.

### Step 4: Top Cross (OLL Edges)

**Goal**: Yellow (2) on all 4 top-edge stickers: `CL(x,0,z,4)=2` for the 4 edge positions.

**Algorithm**: `FRUruf` (standard OLL edge flip)

**Cases** (count how many top edges show yellow):
- **0 (dot)**: Apply algorithm once → get L-shape
- **2 (L-shape)**: Orient so the two yellow edges point back and left, apply → get line
- **2 (line)**: Orient horizontally (left-right), apply → get cross
- **4 (cross)**: Done

Apply 1-3 times with U rotations between to set up orientation.

### Step 5: Top Edge Alignment (PLL Edges)

**Goal**: Each top-edge side sticker matches its center color.
- `CL(1,0,0,0)=4`, `CL(2,0,1,2)=3`, `CL(1,0,2,1)=5`, `CL(0,0,1,3)=6`

**Algorithm**: `RURuRUUr` (cycles 3 edges, keeps one fixed)

**Strategy**:
1. Rotate U until at least one edge matches its center
2. If all 4 match, done
3. Position the matching edge at the back, apply algorithm
4. Repeat until all match

If no edges match after initial U rotations, apply algorithm once, then at least one will match.

### Step 6: Top Corner Positioning (PLL Corners)

**Goal**: All 4 top corners in correct positions (sticker colors may still be twisted).

A corner is "correctly positioned" if its 3 colors match the 3 adjacent centers, regardless of which face each color is on.

**Algorithm**: `URulUrUL` (cycles 3 corners, keeps top-front-right fixed)

**Strategy**:
1. Rotate U until at least one corner is in the correct position
2. Hold correct corner at top-front-right
3. Apply algorithm until all corners are correctly positioned

If no corner is correct, apply once — at least one will become correct.

### Step 7: Top Corner Orientation

**Goal**: Twist top corners so yellow (2) faces up on all 4.

**Algorithm**: `rdRD` (R' D' R D) applied 2 or 4 times per corner

**Strategy**:
1. With an unsolved corner at top-front-right (2,0,0):
   - Apply `rdRD` repeatedly until `CL(2,0,0,4)=2` (yellow faces up)
   - This takes 2 or 4 applications (never odd)
2. Rotate U to bring next unsolved corner to (2,0,0)
3. Repeat for all 4 corners
4. Final U rotations to align the top layer

**Critical**: During this step, bottom layers appear scrambled — this is normal. They restore after all 4 corners are processed. Only use U to cycle between corners.

## Implementation Sequence

1. ~~Phase 1: Engine extension (L/D/B + DoMoves)~~ DONE
2. Phase 2: Solver skeleton + Step 1 (bottom cross)
3. Phase 3: Steps 2-3 (bottom corners + middle edges)
4. Phase 4: Steps 4-7 (top layer — more formulaic, fewer cases)

## Testing

- Each step can be tested independently: scramble, run solver through step N, verify the invariant
- Identity tests for move correctness: `LLLL`, `Ll`, `RrUuFfLlDdBb` → all return to solved
- Full solve test: scramble with known seed, run solver, verify all 54 stickers correct
