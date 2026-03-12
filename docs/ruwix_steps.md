# Ruwix Beginner Method — Raw Reference

Fetched from ruwix.com on 2026-03-12. These are the standard algorithms as published.

## Step 1: First Layer Edges (White Cross)
Source: https://ruwix.com/the-rubiks-cube/how-to-solve-the-rubiks-cube-beginners-method/step-1-first-layer-edges/

Intuitive — no fixed algorithm. Find white edges, move to correct position. One useful sequence for flipping: F U' R U. Bring each white edge to the yellow face, rotate yellow to align with side center, then rotate that face to bring white to white center.

## Step 2: First Layer Corners
Source: https://ruwix.com/the-rubiks-cube/how-to-solve-the-rubiks-cube-beginners-method/step-2-first-layer-corners/

**Algorithm**: `R' D' R D` (applied from below the target slot)

Position corner directly below its target, then repeat:
- White faces right: 1x (4 moves)
- White faces down: 3x (12 moves)
- White faces forward: 5x (20 moves)

Inverse variant: `D R' D' R` (also works, 4 moves).

If corner is in correct layer but wrong position, extract to bottom first.

Advanced shortcut: `R2 D' R2 D R2` for certain configurations.

## Step 3: Second Layer Edges (F2L)
Source: https://ruwix.com/the-rubiks-cube/how-to-solve-the-rubiks-cube-beginners-method/step3-second-layer-f2l/

Hold cube with white face down. Position edge in top layer aligned with its side center.

**Right-insert** (edge at front, goes right): `U R U' R' U' F' U F`
**Left-insert** (edge at front, goes left): `U' L' U L U F U' F'`

For other slots: substitute face letters by rotating perspective.

If edge is in second layer but wrong, use the right algorithm to extract it to top, then reinsert.

## Step 4: Yellow Cross (OLL Edges)
Source: https://ruwix.com/the-rubiks-cube/how-to-solve-the-rubiks-cube-beginners-method/step-4-yellow-cross/

**Algorithm**: `F R U R' U' F'`

Cases:
- **Dot** (0 edges): apply 3x
- **L-shape** (2 adjacent): orient as shown (back-left), apply 2x (or use shortcut `F U R U' R' F'` for direct cross)
- **Line** (2 opposite): orient horizontally, apply 1x
- **Cross** (4 edges): done

Orientation matters: L must be at back-left, line must be horizontal.

## Step 5: Yellow Edge Alignment (PLL Edges)
Source: https://ruwix.com/the-rubiks-cube/how-to-solve-the-rubiks-cube-beginners-method/step-5-swap-yellow-edges/

**Algorithm**: `R U R' U R U2 R'`

Swaps the front-top and left-top edges.

Strategy:
1. Rotate U to find two adjacent edges that need swapping
2. Position them at front and left
3. Apply algorithm
4. For opposite edges: `U (R U R' U R U2 R') y2 (R U R' U R U2 R')`

Note: The Ruwix page shows `R U R' U R U2 R'` (7 moves). Some sources add a trailing `U` to make `R U R' U R U2 R' U` (8 moves) which also adjusts the top layer after the swap.

## Step 6: Yellow Corner Positioning (PLL Corners)
Source: https://ruwix.com/the-rubiks-cube/how-to-solve-the-rubiks-cube-beginners-method/step-6-position-yellow-corners/

**Algorithm**: `U R U' L' U R' U' L`

Cycles 3 corners counterclockwise, front-right-top stays fixed.

Strategy:
1. Rotate U until at least one corner is correctly positioned (color set matches adjacent centers)
2. Hold that corner at front-right-top
3. Apply algorithm (repeat if needed)
4. If no correct corner, apply once to create one

Parity: only 0, 1, or 4 correct corners are possible.

## Step 7: Yellow Corner Orientation
Source: https://ruwix.com/the-rubiks-cube/how-to-solve-the-rubiks-cube-beginners-method/orient-yellow-corners-how-to-solve-last-layer-corner/

**Algorithm**: `R' D' R D` applied 2x or 4x per corner

Strategy:
1. Hold unsolved corner at front-right-top
2. Apply `R' D' R D` until yellow faces up (2 or 4 repetitions)
3. Turn ONLY U to bring next unsolved corner to front-right-top
4. Repeat for all corners
5. Final U turns to align

Critical: bottom appears scrambled during this step — normal, restores after all corners. Never rotate whole cube, only U between corners. Never skip the final D.
