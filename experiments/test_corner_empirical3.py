#!/usr/bin/env python3
"""Pure-Python mini cube sim to find corner insertion algorithms.
Only tracks corners (not edges) for speed."""
import copy

# CL[ix][iy][iz][face] - only visible faces get colors, interior = -1
# Face indices: 0=Front(Z=0), 1=Back(Z=2), 2=Right(X=2), 3=Left(X=0), 4=Top(Y=0), 5=Bottom(Y=2)
# Solved colors: F0=4, F1=5, F2=3, F3=6, F4=2, F5=7

def init_cube():
    cl = [[[[-1]*6 for _ in range(3)] for _ in range(3)] for _ in range(3)]
    for ix in range(3):
        for iy in range(3):
            cl[ix][iy][0][0] = 4  # Front = red
            cl[ix][iy][2][1] = 5  # Back = buff
        for iz in range(3):
            cl[ix][0][iz][4] = 2  # Top = yellow
            cl[ix][2][iz][5] = 7  # Bottom = magenta
    for iy in range(3):
        for iz in range(3):
            cl[2][iy][iz][2] = 3  # Right = blue
            cl[0][iy][iz][3] = 6  # Left = cyan
    return cl

def apply_turn(cl, tf, dr):
    """Apply a face turn. tf: 1=R,2=U,3=F,7=L,8=D,9=B. dr: 1=CW, -1=CCW."""
    # CW looking from outside the face
    # Each turn permutes a 3x3 slice of subcubes and remaps their face colors

    # Define which slice and axis
    if tf == 1:   # RIGHT: IX=2, permute in YZ plane
        do_turn_slice(cl, 'x', 2, dr)
    elif tf == 2: # UP: IY=0, permute in XZ plane
        do_turn_slice(cl, 'y', 0, dr)
    elif tf == 3: # FRONT: IZ=0, permute in XY plane
        do_turn_slice(cl, 'z', 0, dr)
    elif tf == 7: # LEFT: IX=0, permute in YZ plane
        do_turn_slice(cl, 'x', 0, dr)
    elif tf == 8: # DOWN: IY=2, permute in XZ plane
        do_turn_slice(cl, 'y', 2, dr)
    elif tf == 9: # BACK: IZ=2, permute in XY plane
        do_turn_slice(cl, 'z', 2, dr)

def do_turn_slice(cl, axis, slice_val, dr):
    """Perform a face turn on the given slice."""
    # Make a copy of the slice
    if axis == 'x':
        # IX=slice_val, permute YZ plane
        # CW from +X (right): (Y,Z) -> (2-Z, Y)
        # CCW: (Y,Z) -> (Z, 2-Y)
        ix = slice_val
        tc = [[[-1]*6 for _ in range(3)] for _ in range(3)]
        for iy in range(3):
            for iz in range(3):
                if dr == 1:  # CW from outside
                    # For IX=2 (right face), CW from +X
                    # For IX=0 (left face), CW from -X (opposite direction in YZ)
                    if ix == 2:
                        ny, nz = 2-iz, iy
                        fmap = {4:0, 0:5, 5:1, 1:4, 2:2, 3:3}
                    else:  # ix == 0, CW from -X is opposite
                        ny, nz = iz, 2-iy
                        fmap = {4:1, 1:5, 5:0, 0:4, 2:2, 3:3}
                else:  # CCW
                    if ix == 2:
                        ny, nz = iz, 2-iy
                        fmap = {0:4, 5:0, 1:5, 4:1, 2:2, 3:3}
                    else:
                        ny, nz = 2-iz, iy
                        fmap = {1:4, 5:1, 0:5, 4:0, 2:2, 3:3}
                for f in range(6):
                    tc[ny][nz][fmap[f]] = cl[ix][iy][iz][f]
        for iy in range(3):
            for iz in range(3):
                cl[ix][iy][iz] = tc[iy][iz][:]

    elif axis == 'y':
        iy = slice_val
        tc = [[[-1]*6 for _ in range(3)] for _ in range(3)]
        for ix in range(3):
            for iz in range(3):
                if dr == 1:
                    if iy == 0:  # Top face, CW from -Y (top)
                        nx, nz = 2-iz, ix
                        fmap = {0:2, 2:1, 1:3, 3:0, 4:4, 5:5}
                    else:  # iy == 2, Bottom face, CW from +Y
                        nx, nz = iz, 2-ix
                        fmap = {0:3, 3:1, 1:2, 2:0, 4:4, 5:5}
                else:
                    if iy == 0:
                        nx, nz = iz, 2-ix
                        fmap = {2:0, 1:2, 3:1, 0:3, 4:4, 5:5}
                    else:
                        nx, nz = 2-iz, ix
                        fmap = {3:0, 1:3, 2:1, 0:2, 4:4, 5:5}
                for f in range(6):
                    tc[nx][nz][fmap[f]] = cl[ix][iy][iz][f]
        for ix in range(3):
            for iz in range(3):
                cl[ix][iy][iz] = tc[ix][iz][:]

    elif axis == 'z':
        iz = slice_val
        tc = [[[-1]*6 for _ in range(3)] for _ in range(3)]
        for ix in range(3):
            for iy in range(3):
                if dr == 1:
                    if iz == 0:  # Front face, CW from -Z (front)
                        nx, ny = 2-iy, ix
                        fmap = {2:4, 4:3, 3:5, 5:2, 0:0, 1:1}
                    else:  # iz == 2, Back face, CW from +Z
                        nx, ny = iy, 2-ix
                        fmap = {2:5, 5:3, 3:4, 4:2, 0:0, 1:1}
                else:
                    if iz == 0:
                        nx, ny = iy, 2-ix
                        fmap = {4:2, 3:4, 5:3, 2:5, 0:0, 1:1}
                    else:
                        nx, ny = 2-iy, ix
                        fmap = {5:2, 3:5, 4:3, 2:4, 0:0, 1:1}
                for f in range(6):
                    tc[nx][ny][fmap[f]] = cl[ix][iy][iz][f]
        for ix in range(3):
            for iy in range(3):
                cl[ix][iy][iz] = tc[ix][iy][:]

MOVE_MAP = {
    'R': (1, 1), 'r': (1, -1),
    'U': (2, 1), 'u': (2, -1),
    'F': (3, 1), 'f': (3, -1),
    'L': (7, 1), 'l': (7, -1),
    'D': (8, 1), 'd': (8, -1),
    'B': (9, 1), 'b': (9, -1),
}

def do_moves(cl, moves_str):
    for ch in moves_str:
        tf, dr = MOVE_MAP[ch]
        apply_turn(cl, tf, dr)

def find_corner(cl, tc1, tc2, tc3):
    corners = [
        (2,2,0, 5,0,2), (0,2,0, 5,0,3), (2,2,2, 5,1,2), (0,2,2, 5,1,3),
        (2,0,0, 4,0,2), (0,0,0, 4,0,3), (2,0,2, 4,1,2), (0,0,2, 4,1,3),
    ]
    for cp, (ix,iy,iz,fa,fb,fc) in enumerate(corners):
        ca, cb, cc = cl[ix][iy][iz][fa], cl[ix][iy][iz][fb], cl[ix][iy][iz][fc]
        if {ca,cb,cc} == {tc1,tc2,tc3}:
            if ca==tc1: co=0
            elif cb==tc1: co=1
            else: co=2
            return cp, co
    return -1,-1

def bfr_solved(cl):
    return cl[2][2][0][5]==7 and cl[2][2][0][0]==4 and cl[2][2][0][2]==3

TC1, TC2, TC3 = 7, 4, 3

# First, verify against emulator results
print("=== VERIFICATION ===")
for moves in ['ruR', 'fuF', 'fUF', 'rUR']:
    cl = init_cube()
    do_moves(cl, moves)
    cp, co = find_corner(cl, TC1, TC2, TC3)
    print(f"  {moves}: CP={cp} CO={co} solved={bfr_solved(cl)}")

print()

# Verify confirmed solution: ruR then rUR = identity
cl = init_cube()
do_moves(cl, 'ruRrUR')
print(f"  ruR+rUR: solved={bfr_solved(cl)}")

# Also verify sexy move 6x = identity
cl = init_cube()
do_moves(cl, 'RUru' * 6)
print(f"  (RUru)x6: solved={bfr_solved(cl)}")

print()
print("=== FINDING ALL 3 ORIENTATIONS AT TFR ===")

# Extractions that move BFR corner to top:
# ruR -> CP=4 TFR, CO=2
# fUF -> CP=4 TFR, CO=1
# Need CO=0 at TFR

# Try double extractions
for ext1 in ['ruR', 'fUF']:
    cl = init_cube()
    do_moves(cl, ext1)
    cp1, co1 = find_corner(cl, TC1, TC2, TC3)
    if cp1 >= 4:
        aligns = {4:'', 5:'u', 6:'UU', 7:'U'}
        align = aligns[cp1]
        for ext2 in ['ruR', 'rUR', 'fuF', 'fUF', 'FUf', 'Fuf']:
            cl2 = copy.deepcopy(cl)
            do_moves(cl2, align + ext2)
            cp2, co2 = find_corner(cl2, TC1, TC2, TC3)
            if cp2 == 4 and co2 == 0:
                print(f"  CO=0 at TFR: {ext1}+{align}+{ext2}")
            # Also check if we can align to TFR
            if cp2 >= 4 and co2 == 0:
                align2 = aligns.get(cp2, '')
                if align2 is not None:
                    print(f"  CO=0 at CP={cp2}: {ext1}+{align}+{ext2} (align with '{align2}')")

# More targeted: extract with ruR (CO=2 at TFR), then apply rUR (reinsert=identity)
# ... that just gives solved. Need a different approach.
# Try: put corner at TFR with wrong insert, cycle orientation
for setup in ['ruRURuruR', 'fUFUruR', 'ruRufUF', 'fUFUfUF']:
    cl = init_cube()
    do_moves(cl, setup)
    cp, co = find_corner(cl, TC1, TC2, TC3)
    if cp >= 4:
        print(f"  {setup}: CP={cp} CO={co}")

print()
print("=== BRUTE FORCE INSERTIONS FOR EACH CO ===")

setups = {}
# CO=2 at TFR: use ruR
setups[2] = 'ruR'
# CO=1 at TFR: use fUF
setups[1] = 'fUF'

# For CO=0, try to find a setup
for n_u in range(4):
    for ext in ['ruR', 'fUF']:
        for ext2 in ['ruR', 'fUF', 'rUR', 'fuF', 'FUf', 'Fuf']:
            moves = ext + 'U'*n_u + ext2
            cl = init_cube()
            do_moves(cl, moves)
            cp, co = find_corner(cl, TC1, TC2, TC3)
            if cp == 4 and co == 0:
                setups[0] = moves
                break
        if 0 in setups: break
    if 0 in setups: break

if 0 not in setups:
    # Try 3 extractions
    for ext1 in ['ruR', 'fUF']:
        for n1 in range(4):
            for ext2 in ['ruR', 'fUF']:
                for n2 in range(4):
                    for ext3 in ['ruR', 'fUF']:
                        moves = ext1 + 'U'*n1 + ext2 + 'U'*n2 + ext3
                        cl = init_cube()
                        do_moves(cl, moves)
                        cp, co = find_corner(cl, TC1, TC2, TC3)
                        if cp == 4 and co == 0:
                            setups[0] = moves
                            break
                    if 0 in setups: break
                if 0 in setups: break
            if 0 in setups: break
        if 0 in setups: break

for co_val in sorted(setups):
    print(f"  CO={co_val} setup: '{setups[co_val]}'")

print()
moves_chars = 'RrUuFf'

for co_val in sorted(setups):
    setup = setups[co_val]
    print(f"--- CO={co_val} (setup: {setup}) ---")

    # Try 3-move inserts
    found = []
    for a in moves_chars:
        for b in moves_chars:
            for c in moves_chars:
                ins = a+b+c
                cl = init_cube()
                do_moves(cl, setup + ins)
                if bfr_solved(cl):
                    found.append(ins)
    if found:
        print(f"  3-move solutions: {found}")
    else:
        print(f"  No 3-move solution.")
        # Try 4-move
        found4 = []
        for a in moves_chars:
            for b in moves_chars:
                for c in moves_chars:
                    for d in moves_chars:
                        ins = a+b+c+d
                        cl = init_cube()
                        do_moves(cl, setup + ins)
                        if bfr_solved(cl):
                            found4.append(ins)
        if found4:
            print(f"  4-move solutions: {found4[:20]}")
        else:
            print(f"  No 4-move solution.")
            # Try 5-move
            found5 = []
            for a in moves_chars:
                for b in moves_chars:
                    for c in moves_chars:
                        for d in moves_chars:
                            for e in moves_chars:
                                ins = a+b+c+d+e
                                cl = init_cube()
                                do_moves(cl, setup + ins)
                                if bfr_solved(cl):
                                    found5.append(ins)
                                    if len(found5) >= 10: break
                            if len(found5) >= 10: break
                        if len(found5) >= 10: break
                    if len(found5) >= 10: break
                if len(found5) >= 10: break
            if found5:
                print(f"  5-move solutions: {found5}")
            else:
                print(f"  No 5-move solution. Trying 7...")
                # Skip to 7 (R U2 R' U' R U R' = 7 moves)
                found7 = []
                # Only try known patterns
                patterns = [
                    'RUUruRUr', 'RUUruRur', 'RuuruRUr',
                    'fuuFUfuF', 'fuuFUfUF', 'fUUFufuF',
                    'RUURuRUr', 'rUUrURur',
                ]
                for p in patterns:
                    cl = init_cube()
                    do_moves(cl, setup + p)
                    if bfr_solved(cl):
                        found7.append(p)
                if found7:
                    print(f"  7-move solutions: {found7}")

print()
print("=== DONE ===")
