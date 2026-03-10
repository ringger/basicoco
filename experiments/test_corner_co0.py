#!/usr/bin/env python3
"""Find insertion algorithm for CO=0 (bottom color on top) at TFR."""
import sys
sys.path.insert(0, '.')
from emulator.core import CoCoBasic

def init_and_apply(moves_str):
    basic = CoCoBasic()
    basic.process_command('NEW')
    basic.process_command('5 SAFETY OFF')
    basic.process_command('10 PMODE 4: SCREEN 1')
    basic.process_command('20 MERGE "lib_rubiks_engine"')
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

def bfr_solved(basic):
    return (basic.arrays['CL'][2][2][0][5] == 7 and
            basic.arrays['CL'][2][2][0][0] == 4 and
            basic.arrays['CL'][2][2][0][2] == 3)

setup = 'ruRfuFUruR'  # CO=0 at TFR

# CO=0 is the hardest case. Standard approach: use one trigger to get
# a different CO, then use the matching trigger to insert.
# CO=0 -> rUR -> changes CO (not insert) -> then fuF to insert
# Or: just apply the standard 7-move algorithm R U2 R' U' R U R'
tests = [
    ("R U2 R' U' R U R'", "RUUruRUr"),
    ("rUR then u then fuF", "rURufuF"),
    ("fuF then u then rUR", "fuFurUR"),
    ("rUR U fuF", "rURUfuF"),
    ("rUR U rUR", "rURUrUR"),
]

print(f"Setup: {setup} -> CO=0 at TFR")
for desc, insert in tests:
    basic = init_and_apply(setup + insert)
    solved = bfr_solved(basic)
    marker = " <<<< SOLVED!" if solved else ""
    print(f"  {desc:35s}{marker}")
