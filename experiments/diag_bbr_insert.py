#!/usr/bin/env python3
"""
Diagnostic: BBR corner insertion analysis.

Tests what happens when InsertBBR is applied to a corner at TBR (CP=6)
with each possible CO value (0, 1, 2). Also tests extract+insert cycles.

BBR corner target colors: TC1=7 (magenta/bottom), TC2=5 (buff/back), TC3=3 (blue/right)
BBR position: (2,2,2), CP=2
TBR position: (2,0,2), CP=6

Faces: F0=front(red/4), F1=back(buff/5), F2=right(blue/3),
       F3=left(cyan/6), F4=top(green/2), F5=bottom(magenta/7)

InsertBBR algorithms:
  CO=1 (Z-face/back): BUb = B U B'
  CO=2 (X-face/right) or CO=0: Rur = R U' R'

Extraction from BBR (CP=2): BUb = B U B'
"""

import os
import sys
import shutil
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from emulator.core import CoCoBasic


def setup_emulator():
    """Create emulator, set up temp dir with engine+solver, return (emulator, cleanup_fn)."""
    test_dir = tempfile.mkdtemp(prefix='diag_bbr_')
    orig_cwd = os.getcwd()
    os.chdir(test_dir)
    programs_dir = os.path.join(test_dir, 'programs')
    os.makedirs(programs_dir, exist_ok=True)

    src_dir = os.path.join(os.path.dirname(__file__), 'programs')
    for fname in ('lib_rubiks_engine.bas', 'lib_rubiks_solver.bas'):
        shutil.copy(os.path.join(src_dir, fname), os.path.join(programs_dir, fname))

    emulator = CoCoBasic()
    emulator.process_command('NEW')

    def cleanup():
        os.chdir(orig_cwd)
        shutil.rmtree(test_dir)

    return emulator, cleanup


def load_and_run(emulator, program_lines, max_frames=50000):
    """Load a BASIC program and run it to completion."""
    emulator.process_command('NEW')
    for line in program_lines:
        emulator.process_command(line)

    all_output = emulator.process_command('RUN')
    frames = 1
    while emulator.waiting_for_pause_continuation and frames < max_frames:
        emulator.waiting_for_pause_continuation = False
        emulator.running = True
        result = emulator.continue_program_execution()
        all_output.extend(result)
        frames += 1
        if any(r.get('type') == 'error' for r in result):
            break
    return all_output


def get_text(results):
    return [item['text'] for item in results if item.get('type') == 'text']


def get_errors(results):
    return [item['message'] for item in results if item.get('type') == 'error']


def run_diagnostic():
    emulator, cleanup = setup_emulator()

    try:
        # ================================================================
        # TEST 1: What does a single R move do to BBR corner?
        # R CW cycles: BFR->TFR->TBR->BBR (wait, need to check)
        # Actually R CW: looking from right, CW rotation
        # Cycle: BFR(2,2,0) -> BBR(2,2,2) -> TBR(2,0,2) -> TFR(2,0,0) -> BFR
        # So R sends BBR -> TBR? No. Let me trace it properly.
        # PermRight: NY=2-IZ, NZ=IY
        # (2,2,2) IY=2,IZ=2 -> NY=0, NZ=2 -> (2,0,2) = TBR  YES!
        # So R sends BBR(2,2,2) to TBR(2,0,2)
        # ================================================================

        print("=" * 60)
        print("DIAGNOSTIC: BBR CORNER INSERTION")
        print("=" * 60)

        # Test 1A: R move - what CO does BBR get at TBR?
        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "lib_rubiks_engine"',
            '25 MERGE "lib_rubiks_solver"',
            '30 GOSUB InitCube',
            '35 AN=0',
            '40 MS$="R": GOSUB DoMoves',
            '50 TC1=7: TC2=5: TC3=3',
            '60 GOSUB FindCorner',
            '70 PRINT "AFTER R: CP=";CP;" CO=";CO',
            # Also dump the actual sticker colors at TBR (2,0,2)
            '80 PRINT "TBR F4=";CL(2,0,2,4);" F1=";CL(2,0,2,1);" F2=";CL(2,0,2,2)',
            # And BBR (2,2,2)
            '90 PRINT "BBR F5=";CL(2,2,2,5);" F1=";CL(2,2,2,1);" F2=";CL(2,2,2,2)',
            '100 END',
        ]
        results = load_and_run(emulator, program)
        errors = get_errors(results)
        if errors:
            print(f"ERRORS: {errors}")
        for t in get_text(results):
            print(f"  {t}")

        # Test 1B: B move (CCW) - what CO does BBR get at TBR?
        # PermBack: NX=IY, NY=2-IX
        # (2,2,2) IX=2, IY=2 -> NX=2, NY=0 -> (2,0,2)  YES, B CW also sends BBR to TBR
        # But B CCW (b) would send differently. Let's check B CW.
        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "lib_rubiks_engine"',
            '25 MERGE "lib_rubiks_solver"',
            '30 GOSUB InitCube',
            '35 AN=0',
            '40 MS$="B": GOSUB DoMoves',
            '50 TC1=7: TC2=5: TC3=3',
            '60 GOSUB FindCorner',
            '70 PRINT "AFTER B: CP=";CP;" CO=";CO',
            '80 PRINT "TBR F4=";CL(2,0,2,4);" F1=";CL(2,0,2,1);" F2=";CL(2,0,2,2)',
            '100 END',
        ]
        results = load_and_run(emulator, program)
        errors = get_errors(results)
        if errors:
            print(f"ERRORS: {errors}")
        for t in get_text(results):
            print(f"  {t}")

        # Test 2: For each CO at TBR, run InsertBBR and check result
        # We need to engineer specific CO values at TBR.
        # Let's try multiple setups and see what FindCorner reports.

        print()
        print("=" * 60)
        print("TEST 2: ENGINEERED CO VALUES AT TBR")
        print("=" * 60)

        # Try several move sequences to get BBR corner to TBR with different COs
        setups = [
            ("R", "R sends BBR->TBR"),
            ("B", "B sends BBR->TBR"),
            ("Ru", "R then u"),
            ("RU", "R then U"),
            ("Bu", "B then u"),
            ("BU", "B then U"),
            ("RUU", "R then UU"),
            ("BUU", "B then UU"),
        ]

        for moves, desc in setups:
            program = [
                '5 SAFETY OFF',
                '10 PMODE 4: SCREEN 1',
                '20 MERGE "lib_rubiks_engine"',
                '25 MERGE "lib_rubiks_solver"',
                '30 GOSUB InitCube',
                '35 AN=0',
                f'40 MS$="{moves}": GOSUB DoMoves',
                '50 TC1=7: TC2=5: TC3=3',
                '60 GOSUB FindCorner',
                f'70 PRINT "SETUP {moves}: CP=";CP;" CO=";CO',
                '100 END',
            ]
            results = load_and_run(emulator, program)
            errors = get_errors(results)
            if errors:
                print(f"  ERRORS for {moves}: {errors}")
            for t in get_text(results):
                print(f"  {t}")

        print()
        print("=" * 60)
        print("TEST 3: INSERT FROM TBR WITH EACH CO")
        print("=" * 60)

        # For each CO (0, 1, 2), set up corner at TBR, run InsertBBR, check result
        # From Test 2 we'll know which setups give which CO.
        # For now, let's try the full insert cycle for each setup that lands at TBR (CP=6).

        # Use R (which should give some CO at CP=6), then insert
        setups_for_insert = [
            ("R", "R->TBR"),
            ("B", "B->TBR"),
        ]

        for moves, desc in setups_for_insert:
            program = [
                '5 SAFETY OFF',
                '10 PMODE 4: SCREEN 1',
                '20 MERGE "lib_rubiks_engine"',
                '25 MERGE "lib_rubiks_solver"',
                '30 GOSUB InitCube',
                '35 AN=0',
                f'40 MS$="{moves}": GOSUB DoMoves',
                '50 TC1=7: TC2=5: TC3=3: CI=2',
                '60 GOSUB FindCorner',
                f'70 PRINT "BEFORE INSERT ({moves}): CP=";CP;" CO=";CO',
                '80 GOSUB InsertBBR',
                '90 GOSUB FindCorner',
                f'100 PRINT "AFTER INSERT ({moves}): CP=";CP;" CO=";CO',
                # Dump BBR stickers
                '110 PRINT "BBR: F5=";CL(2,2,2,5);" F1=";CL(2,2,2,1);" F2=";CL(2,2,2,2)',
                '120 END',
            ]
            results = load_and_run(emulator, program)
            errors = get_errors(results)
            if errors:
                print(f"  ERRORS for {moves}: {errors}")
            for t in get_text(results):
                print(f"  {t}")

        print()
        print("=" * 60)
        print("TEST 4: FULL EXTRACT+INSERT CYCLES FROM BBR")
        print("=" * 60)

        # Start with solved cube. Extract BBR (BUb), then try to insert it back.
        # Track CO through multiple extract+insert cycles.
        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "lib_rubiks_engine"',
            '25 MERGE "lib_rubiks_solver"',
            '30 GOSUB InitCube',
            '35 AN=0',
            '40 TC1=7: TC2=5: TC3=3: CI=2',
            # Initial state
            '50 GOSUB FindCorner',
            '60 PRINT "INITIAL: CP=";CP;" CO=";CO',
            # Extract (BUb)
            '70 MS$="BUb": GOSUB DoMoves',
            '80 GOSUB FindCorner',
            '90 PRINT "AFTER EXTRACT BUb: CP=";CP;" CO=";CO',
            # Now align if needed (should already be at TBR=CP6)
            # Insert
            '100 GOSUB InsertBBR',
            '110 GOSUB FindCorner',
            '120 PRINT "AFTER INSERT 1: CP=";CP;" CO=";CO',
            # If not solved, extract again and try
            '130 IF CP=2 AND CO=0 THEN PRINT "SOLVED!": GOTO 300',
            '140 IF CP<>2 THEN PRINT "NOT AT BBR!": GOTO 300',
            # Extract again
            '150 MS$="BUb": GOSUB DoMoves',
            '160 GOSUB FindCorner',
            '170 PRINT "AFTER EXTRACT 2: CP=";CP;" CO=";CO',
            '180 GOSUB InsertBBR',
            '190 GOSUB FindCorner',
            '200 PRINT "AFTER INSERT 2: CP=";CP;" CO=";CO',
            '210 IF CP=2 AND CO=0 THEN PRINT "SOLVED!": GOTO 300',
            '220 IF CP<>2 THEN PRINT "NOT AT BBR!": GOTO 300',
            # Extract again
            '230 MS$="BUb": GOSUB DoMoves',
            '240 GOSUB FindCorner',
            '250 PRINT "AFTER EXTRACT 3: CP=";CP;" CO=";CO',
            '260 GOSUB InsertBBR',
            '270 GOSUB FindCorner',
            '280 PRINT "AFTER INSERT 3: CP=";CP;" CO=";CO',
            '290 IF CP=2 AND CO=0 THEN PRINT "SOLVED!": GOTO 300',
            '295 PRINT "STILL NOT SOLVED AFTER 3 CYCLES"',
            '300 END',
        ]
        results = load_and_run(emulator, program)
        errors = get_errors(results)
        if errors:
            print(f"  ERRORS: {errors}")
        for t in get_text(results):
            print(f"  {t}")

        print()
        print("=" * 60)
        print("TEST 5: TRACE EACH INSERT ALGORITHM INDIVIDUALLY")
        print("=" * 60)

        # Test Rur (R U' R') on a corner at TBR
        # Test BUb (B U B') on a corner at TBR
        # For each, check where corner ends up

        for algo_name, algo_moves in [("Rur", "Rur"), ("BUb", "BUb")]:
            for setup_moves in ["R", "B"]:
                program = [
                    '5 SAFETY OFF',
                    '10 PMODE 4: SCREEN 1',
                    '20 MERGE "lib_rubiks_engine"',
                    '25 MERGE "lib_rubiks_solver"',
                    '30 GOSUB InitCube',
                    '35 AN=0',
                    '40 TC1=7: TC2=5: TC3=3',
                    f'50 MS$="{setup_moves}": GOSUB DoMoves',
                    '60 GOSUB FindCorner',
                    f'70 PRINT "SETUP {setup_moves} -> CP=";CP;" CO=";CO',
                    f'80 MS$="{algo_moves}": GOSUB DoMoves',
                    '90 GOSUB FindCorner',
                    f'100 PRINT "AFTER {algo_name}: CP=";CP;" CO=";CO',
                    '110 PRINT "BBR: F5=";CL(2,2,2,5);" F1=";CL(2,2,2,1);" F2=";CL(2,2,2,2)',
                    '120 END',
                ]
                results = load_and_run(emulator, program)
                errors = get_errors(results)
                if errors:
                    print(f"  ERRORS ({setup_moves}+{algo_name}): {errors}")
                for t in get_text(results):
                    print(f"  {t}")

        print()
        print("=" * 60)
        print("TEST 6: ALL 3 COs AT TBR -> InsertBBR")
        print("=" * 60)
        print("Finding setups that give CO=0, CO=1, CO=2 at CP=6...")

        # We need to find move sequences that put BBR corner at TBR with each CO.
        # Let's try many combinations.
        search_setups = [
            "R", "B", "RU", "Ru", "BU", "Bu", "RUU", "BUU", "Ruu",
            "ruR", "BUb", "rUR", "bUB",
            "URu", "UBu", "uRU", "uBU",
        ]

        co_found = {}  # co -> (moves, cp)
        for moves in search_setups:
            program = [
                '5 SAFETY OFF',
                '10 PMODE 4: SCREEN 1',
                '20 MERGE "lib_rubiks_engine"',
                '25 MERGE "lib_rubiks_solver"',
                '30 GOSUB InitCube',
                '35 AN=0',
                '40 TC1=7: TC2=5: TC3=3',
                f'50 MS$="{moves}": GOSUB DoMoves',
                '60 GOSUB FindCorner',
                '70 PRINT CP',
                '80 PRINT CO',
                '100 END',
            ]
            results = load_and_run(emulator, program)
            texts = get_text(results)
            if len(texts) >= 2:
                cp = int(texts[0].strip())
                co = int(texts[1].strip())
                if cp == 6 and co not in co_found:
                    co_found[co] = moves
                    print(f"  CO={co} at TBR: setup='{moves}'")

        print(f"  Found COs: {sorted(co_found.keys())}")

        # Now for each CO, do InsertBBR and check
        for co_val in sorted(co_found.keys()):
            setup = co_found[co_val]
            program = [
                '5 SAFETY OFF',
                '10 PMODE 4: SCREEN 1',
                '20 MERGE "lib_rubiks_engine"',
                '25 MERGE "lib_rubiks_solver"',
                '30 GOSUB InitCube',
                '35 AN=0',
                '40 TC1=7: TC2=5: TC3=3: CI=2',
                f'50 MS$="{setup}": GOSUB DoMoves',
                '60 GOSUB FindCorner',
                f'70 PRINT "CO={co_val} BEFORE: CP=";CP;" CO=";CO',
                '80 GOSUB InsertBBR',
                '90 GOSUB FindCorner',
                f'100 PRINT "CO={co_val} AFTER: CP=";CP;" CO=";CO',
                '110 PRINT "BBR stickers: F5=";CL(2,2,2,5);" F1=";CL(2,2,2,1);" F2=";CL(2,2,2,2)',
                '120 PRINT "TBR stickers: F4=";CL(2,0,2,4);" F1=";CL(2,0,2,1);" F2=";CL(2,0,2,2)',
                '130 END',
            ]
            results = load_and_run(emulator, program)
            errors = get_errors(results)
            if errors:
                print(f"  ERRORS (CO={co_val}): {errors}")
            for t in get_text(results):
                print(f"  {t}")

        print()
        print("=" * 60)
        print("TEST 7: EXTRACT-ALIGN-INSERT LOOP (LIKE SOLVER)")
        print("=" * 60)

        # Simulate what the solver does: extract, find, align, find, insert, check
        # Use a scramble that puts BBR corner somewhere problematic
        for scramble in ["R", "B", "RU", "BU", "RF", "RUF"]:
            program = [
                '5 SAFETY OFF',
                '10 PMODE 4: SCREEN 1',
                '20 MERGE "lib_rubiks_engine"',
                '25 MERGE "lib_rubiks_solver"',
                '30 GOSUB InitCube',
                '35 AN=0',
                '40 TC1=7: TC2=5: TC3=3: CI=2',
                f'45 MS$="{scramble}": GOSUB DoMoves',
                '50 GOSUB FindCorner',
                f'55 PRINT "SCRAMBLE {scramble}: CP=";CP;" CO=";CO',
                # Iteration 1
                '60 IF CP=CI AND CO=0 THEN PRINT "ALREADY SOLVED": GOTO 200',
                '70 IF CP<=3 THEN MS$="BUb": GOSUB DoMoves: PRINT "EXTRACTED"',
                '80 GOSUB FindCorner: PRINT "FIND1: CP=";CP;" CO=";CO',
                '90 GOSUB AlignCornerTop',
                '95 GOSUB FindCorner: PRINT "ALIGNED: CP=";CP;" CO=";CO',
                '100 GOSUB InsertBBR',
                '110 GOSUB FindCorner: PRINT "INSERTED: CP=";CP;" CO=";CO',
                '120 IF CP=CI AND CO=0 THEN PRINT "SOLVED ITER 1": GOTO 200',
                # Iteration 2
                '125 IF CP<=3 THEN MS$="BUb": GOSUB DoMoves: PRINT "EXTRACTED2"',
                '130 GOSUB FindCorner: PRINT "FIND2: CP=";CP;" CO=";CO',
                '135 GOSUB AlignCornerTop',
                '137 GOSUB FindCorner: PRINT "ALIGNED2: CP=";CP;" CO=";CO',
                '140 GOSUB InsertBBR',
                '145 GOSUB FindCorner: PRINT "INSERTED2: CP=";CP;" CO=";CO',
                '150 IF CP=CI AND CO=0 THEN PRINT "SOLVED ITER 2": GOTO 200',
                # Iteration 3
                '155 IF CP<=3 THEN MS$="BUb": GOSUB DoMoves: PRINT "EXTRACTED3"',
                '160 GOSUB FindCorner: PRINT "FIND3: CP=";CP;" CO=";CO',
                '165 GOSUB AlignCornerTop',
                '167 GOSUB FindCorner: PRINT "ALIGNED3: CP=";CP;" CO=";CO',
                '170 GOSUB InsertBBR',
                '175 GOSUB FindCorner: PRINT "INSERTED3: CP=";CP;" CO=";CO',
                '180 IF CP=CI AND CO=0 THEN PRINT "SOLVED ITER 3": GOTO 200',
                '190 PRINT "NOT SOLVED AFTER 3 ITERS"',
                '200 PRINT "---"',
                '210 END',
            ]
            results = load_and_run(emulator, program)
            errors = get_errors(results)
            if errors:
                print(f"  ERRORS ({scramble}): {errors}")
            for t in get_text(results):
                print(f"  {t}")
            print()

    finally:
        cleanup()


if __name__ == '__main__':
    run_diagnostic()
