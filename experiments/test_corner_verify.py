#!/usr/bin/env python3
"""Verify standard corner insertion algorithms work with our engine.
Uses the emulator directly (not pure-Python sim) for ground truth."""
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

TC1, TC2, TC3 = 7, 4, 3  # magenta, red, blue (BFR corner)

print("=== VERIFY STANDARD CORNER ALGORITHMS FOR BFR ===")
print("BFR slot: Right=R, Front=F")
print("Corner above slot = TFR (CP=4)")
print()

# Step 1: Verify extractions — which moves extract BFR to TFR?
print("--- Extractions from BFR ---")
for label, moves in [
    ("R U R' (RUr)", "RUr"),
    ("R U' R' (Rur)", "Rur"),
    ("R' U R (rUR)", "rUR"),
    ("R' U' R (ruR)", "ruR"),
    ("F U F' (FUf)", "FUf"),
    ("F U' F' (Fuf)", "Fuf"),
    ("F' U F (fUF)", "fUF"),
    ("F' U' F (fuF)", "fuF"),
]:
    basic = init_and_apply(moves)
    cp, co = find_corner(basic, TC1, TC2, TC3)
    marker = " <-- EXTRACTS TO TOP" if cp >= 4 else ""
    print(f"  {label:20s}: CP={cp} CO={co}{marker}")

print()

# Step 2: For each CO at TFR, verify standard insertion algorithms
# Standard beginner algorithms for bottom-right slot:
#   CO=0 (bottom on top):    R U U R' U' R U R'  (= RUUruRUr)
#   CO=1 (bottom on front):  F' U' F             (= fuF)  -- "left trigger"
#   CO=2 (bottom on right):  R U R'              (= RUr)  -- "right trigger"
#
# But we also have the "repeated" approach:
#   CO=2: repeat (R U R' U') until solved = sexy move
#   CO=1: repeat (F' U' F U) until solved

# First, set up each CO at TFR:
print("--- Setup: getting each CO at TFR ---")
# From extraction tests above:
# ruR -> CP=4, CO=2 (confirmed from earlier)
# fUF -> CP=4, CO=1 (confirmed from earlier)
# For CO=0, need to find a setup

# CO=0 means bottom color on Y-face (top face at TFR)
# Standard: do two wrong insertions to cycle through orientations
# R U R' puts CO=2 corner into BFR... wait, we showed that doesn't work for BFR directly.
# Let me just test: extract, try 1 sexy move, extract again, check CO
for setup_label, setup_moves in [
    ("ruR (direct)", "ruR"),
    ("fUF (direct)", "fUF"),
    ("ruR + RUru + ruR (re-extract after 1 sexy)", "ruRRUruruR"),
    ("fUF + fuFU + fUF (re-extract after 1 left-sexy)", "fUFfuFUfUF"),
    ("ruR + fuFU + ruR", "ruRfuFUruR"),
]:
    basic = init_and_apply(setup_moves)
    cp, co = find_corner(basic, TC1, TC2, TC3)
    if cp >= 4:
        aligns = {4:'', 5:'u', 6:'UU', 7:'U'}
        align = aligns[cp]
        if align:
            basic2 = init_and_apply(setup_moves + align)
            cp2, co2 = find_corner(basic2, TC1, TC2, TC3)
            print(f"  {setup_label:50s}: CP={cp} CO={co} -> aligned CP={cp2} CO={co2}")
        else:
            print(f"  {setup_label:50s}: CP={cp} CO={co} (already at TFR)")
    else:
        print(f"  {setup_label:50s}: CP={cp} CO={co} (bottom layer)")

print()
print("--- Verify insertion algorithms ---")

# Test insertions for each CO
tests = [
    # (description, setup_to_get_CO_at_TFR, insertion, expected_CO)
    # CO=2 tests
    ("CO=2: R U R' (RUr)", "ruR", "RUr", 2),
    ("CO=2: R' U R (rUR) [undo]", "ruR", "rUR", 2),
    ("CO=2: sexy x1 (RUru)", "ruR", "RUru", 2),
    ("CO=2: sexy x3 (RUru x3)", "ruR", "RUruRUruRUru", 2),
    ("CO=2: sexy x5", "ruR", "RUru"*5, 2),

    # CO=1 tests
    ("CO=1: F' U' F (fuF)", "fUF", "fuF", 1),
    ("CO=1: F U' F' (Fuf)", "fUF", "Fuf", 1),
    ("CO=1: F' U F [undo] (fUF)", "fUF", "fUF", 1),
    ("CO=1: left-sexy x1 (fuFU)", "fUF", "fuFU", 1),
    ("CO=1: left-sexy x3", "fUF", "fuFU"*3, 1),
    ("CO=1: left-sexy x5", "fUF", "fuFU"*5, 1),
    ("CO=1: R U R' (RUr)", "fUF", "RUr", 1),
    ("CO=1: R U2 R' U' R U R'", "fUF", "RUUruRUr", 1),
]

for desc, setup, insert, expected_co in tests:
    basic = init_and_apply(setup + insert)
    cp, co = find_corner(basic, TC1, TC2, TC3)
    solved = bfr_solved(basic)
    marker = " <<<< SOLVED!" if solved else ""
    print(f"  {desc:45s}: CP={cp} CO={co}{marker}")

print()
print("DONE")
