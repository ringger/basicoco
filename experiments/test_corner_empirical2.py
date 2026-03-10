#!/usr/bin/env python3
"""Find insertion algorithms for CO=1 and CO=0 at TFR (BFR target)."""
import sys
sys.path.insert(0, '.')
from emulator.core import CoCoBasic

def init_and_apply(moves_str):
    basic = CoCoBasic()
    basic.process_command('NEW')
    basic.process_command('5 SAFETY OFF')
    basic.process_command('10 PMODE 4: SCREEN 1')
    basic.process_command('20 MERGE "rubiks_engine"')
    basic.process_command('25 AN=0')
    basic.process_command('30 GOSUB InitCube')
    if moves_str:
        basic.process_command(f'40 MS$="{moves_str}": GOSUB DoMoves')
    basic.process_command('50 END')
    basic.process_command('RUN')
    while basic.waiting_for_pause_continuation:
        basic.waiting_for_pause_continuation = False
        basic.running = True
        basic.continue_program_execution()
    return basic

def get_cl(basic, ix, iy, iz, f):
    return basic.arrays['CL'][ix][iy][iz][f]

def bfr_solved(basic):
    return (get_cl(basic, 2,2,0,5) == 7 and
            get_cl(basic, 2,2,0,0) == 4 and
            get_cl(basic, 2,2,0,2) == 3)

def find_corner(basic, tc1, tc2, tc3):
    corners = [
        (2,2,0, 5,0,2), (0,2,0, 5,0,3), (2,2,2, 5,1,2), (0,2,2, 5,1,3),
        (2,0,0, 4,0,2), (0,0,0, 4,0,3), (2,0,2, 4,1,2), (0,0,2, 4,1,3),
    ]
    for cp, (ix,iy,iz,fa,fb,fc) in enumerate(corners):
        ca, cb, cc = get_cl(basic,ix,iy,iz,fa), get_cl(basic,ix,iy,iz,fb), get_cl(basic,ix,iy,iz,fc)
        if {ca,cb,cc} == {tc1,tc2,tc3}:
            if ca==tc1: co=0
            elif cb==tc1: co=1
            else: co=2
            return cp, co
    return -1,-1

TC1, TC2, TC3 = 7, 4, 3

# Generate all reasonable insertion sequences (3-5 moves using R/r/F/f/U/u)
moves_chars = 'RrUuFf'

# CO=1: extract with fUF (lands at TFR with CO=1), then try inserts
# CO=0: we haven't found this orientation at TFR yet
# Let's first find how to get CO=0 at TFR

print("=== FINDING CO=0 AT TFR ===")
# Try: extract to get CO=1 or CO=2, then re-extract to cycle orientation
# Method: do extraction twice with different sequences
tests = [
    'fuFUUruR',    # extract fuF (to TBR CO=1), UU align, then extract ruR again
    'ruRUfuF',     # extract ruR (to TFR CO=2), U, then fuF
    'ruRUUruR',    # double extraction
    'fUFruR',      # extract fUF (to TFR CO=1), then ruR
]

for t in tests:
    basic = init_and_apply(t)
    cp, co = find_corner(basic, TC1, TC2, TC3)
    print(f"  {t:20s}: CP={cp} CO={co}")

# Try all 2-extraction combos
print("\n=== SYSTEMATIC 2-EXTRACTION COMBOS ===")
extractions = ['ruR', 'fuF', 'rUR', 'fUF']
aligns = {'4': '', '5': 'u', '6': 'UU', '7': 'U'}

for ext1 in extractions:
    basic1 = init_and_apply(ext1)
    cp1, co1 = find_corner(basic1, TC1, TC2, TC3)
    if cp1 < 4: continue
    align1 = aligns[str(cp1)]
    for ext2 in extractions:
        full = ext1 + align1 + ext2
        basic = init_and_apply(full)
        cp, co = find_corner(basic, TC1, TC2, TC3)
        if cp == 4 and co == 0:
            print(f"  CO=0 at TFR: {full}")

print()
print("=== BRUTE FORCE 3-5 MOVE INSERTS FOR CO=1 AT TFR ===")
# Setup: fUF gives CO=1 at TFR
setup_co1 = 'fUF'  # CO=1 at TFR (CP=4)

# Try all 3-move combos
found_co1 = []
for a in moves_chars:
    for b in moves_chars:
        for c in moves_chars:
            ins = a+b+c
            basic = init_and_apply(setup_co1 + ins)
            if bfr_solved(basic):
                found_co1.append(ins)

if found_co1:
    print(f"CO=1 solved by 3-move: {found_co1}")
else:
    print("No 3-move solution for CO=1. Trying 4-move...")
    for a in moves_chars:
        for b in moves_chars:
            for c in moves_chars:
                for d in moves_chars:
                    ins = a+b+c+d
                    basic = init_and_apply(setup_co1 + ins)
                    if bfr_solved(basic):
                        found_co1.append(ins)
    if found_co1:
        print(f"CO=1 solved by 4-move: {found_co1[:10]}...")
    else:
        print("No 4-move solution for CO=1. Trying 5-move...")
        for a in moves_chars:
            for b in moves_chars:
                for c in moves_chars:
                    for d in moves_chars:
                        for e in moves_chars:
                            ins = a+b+c+d+e
                            basic = init_and_apply(setup_co1 + ins)
                            if bfr_solved(basic):
                                found_co1.append(ins)
                                if len(found_co1) >= 5:
                                    break
                        if len(found_co1) >= 5: break
                    if len(found_co1) >= 5: break
                if len(found_co1) >= 5: break
            if len(found_co1) >= 5: break
        if found_co1:
            print(f"CO=1 solved by 5-move: {found_co1}")

print()
print("=== CO=2 CONFIRMATION ===")
# Already found: rUR solves CO=2 at TFR
# Verify:
basic = init_and_apply('ruR' + 'rUR')
print(f"ruR then rUR: BFR_solved={bfr_solved(basic)}")

print("\nDONE")
