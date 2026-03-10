# Rubik's Cube Beginner Method — Reference Algorithms

Source: [Ruwix Beginner Method](https://ruwix.com/the-rubiks-cube/how-to-solve-the-rubiks-cube-beginners-method/)

Standard Ruwix tutorial solves **white on top first**, then flips to solve yellow last layer.
Our solver solves **bottom (magenta) first** with top (yellow) as last layer — same concept, different orientation.

## Step 1: First Layer Edges (White Cross)

Source: [Step 1](https://ruwix.com/the-rubiks-cube/how-to-solve-the-rubiks-cube-beginners-method/step-1-first-layer-edges/)

Intuitive — no fixed algorithm. Find edges, move to correct position.

## Step 2: First Layer Corners

Source: [Step 2](https://ruwix.com/the-rubiks-cube/how-to-solve-the-rubiks-cube-beginners-method/step-2-first-layer-corners/)

**Universal algorithm**: `R' D' R D` repeated until corner is oriented correctly.

Working position: corner piece at front-right-down (below its target slot at front-right-up).

Repetitions by orientation (where the white/bottom sticker faces):
- **Facing right**: 1x (= 4 moves)
- **Facing down**: 3x (= 12 moves)
- **Facing front**: 5x (= 20 moves)

Note: The Ruwix method works from the BOTTOM (corner below target). Our solver works from the TOP (corner above target). This changes which algorithms apply — our `Right' U Right` and `Front' U' Front` triggers work from above, which is equivalent but uses U instead of D.

## Step 3: Second Layer Edges (F2L)

Source: [Step 3](https://ruwix.com/the-rubiks-cube/how-to-solve-the-rubiks-cube-beginners-method/step3-second-layer-f2l/)

**Right-insert** (edge goes to right): `U R U' R' U' F' U F`
**Left-insert** (edge goes to left): `U' L' U L U F U' F'`

These are for the front-right and front-left slots respectively. Other slots use the same pattern with substituted face letters.

## Step 4: Yellow Cross (OLL Edges)

Source: [Step 4](https://ruwix.com/the-rubiks-cube/how-to-solve-the-rubiks-cube-beginners-method/step-4-yellow-cross/)

**Algorithm**: `F R U R' U' F'`

Cases:
- **Dot** (0 edges): apply 3x (or use `F R U R' U' F'` once to get L, then proceed)
- **L-shape** (2 edges, adjacent): orient L to back-left, apply 1x → line
  - Alternative shortcut for L-shape: `F U R U' R' F'` goes direct to cross
- **Line** (2 edges, opposite): orient horizontally, apply 1x → cross
- **Cross** (4 edges): done

## Step 5: Yellow Edge Alignment (PLL Edges)

Source: [Step 5](https://ruwix.com/the-rubiks-cube/how-to-solve-the-rubiks-cube-beginners-method/step-5-swap-yellow-edges/)

**Algorithm**: `R U R' U R U2 R' U`

Swaps the front-top and left-top edges.

Strategy:
1. Rotate U to find two adjacent edges that need swapping
2. Position them at front and left
3. Apply algorithm
4. If opposite edges need swapping, apply twice (with y2 whole-cube rotation between)

## Step 6: Yellow Corner Positioning (PLL Corners)

Source: [Step 6](https://ruwix.com/the-rubiks-cube/how-to-solve-the-rubiks-cube-beginners-method/step-6-position-yellow-corners/)

**Algorithm**: `U R U' L' U R' U' L`

Cycles 3 corners counterclockwise, keeping front-right-top fixed.

Strategy:
1. Rotate U until at least one corner is correctly positioned (colors match adjacent centers)
2. Hold that corner at front-right-top
3. Apply algorithm until all positioned
4. If no corner correct initially, apply once to create one

## Step 7: Yellow Corner Orientation

Source: [Step 7](https://ruwix.com/the-rubiks-cube/how-to-solve-the-rubiks-cube-beginners-method/orient-yellow-corners-how-to-solve-last-layer-corner/)

**Algorithm**: `R' D' R D` applied 2x or 4x per corner

Strategy:
1. Hold unsolved corner at front-right-top
2. Apply `R' D' R D` until yellow faces up (2 or 4 repetitions)
3. Turn ONLY U (not whole cube) to bring next unsolved corner to front-right-top
4. Repeat for all corners
5. Final U turns to align top layer

Critical: Bottom layers appear scrambled during this step — normal, they restore after all corners done. Never rotate whole cube, only U between corners. Always complete the full `R' D' R D` sequence (don't skip the final D).
