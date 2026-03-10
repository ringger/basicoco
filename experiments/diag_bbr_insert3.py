#!/usr/bin/env python3
"""
Diagnostic part 3: CO=0 bug analysis.

KEY FINDING: When BBR corner is at TBR with CO=0 (magenta on top),
InsertBBR uses Rur, which gives CP=2 CO=2 (wrong twist).

Questions:
1. What does BUb do for CO=0 at TBR?
2. Does the extract+align+insert cycle converge or loop forever?
3. What is the correct algorithm for CO=0?
"""

import os
import sys
import shutil
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from emulator.core import CoCoBasic


def setup_emulator():
    test_dir = tempfile.mkdtemp(prefix='diag_bbr_')
    orig_cwd = os.getcwd()
    os.chdir(test_dir)
    programs_dir = os.path.join(test_dir, 'programs')
    os.makedirs(programs_dir, exist_ok=True)
    src_dir = os.path.join(os.path.dirname(__file__), 'programs')
    for fname in ('rubiks_engine.bas', 'rubiks_solver.bas'):
        shutil.copy(os.path.join(src_dir, fname), os.path.join(programs_dir, fname))
    emulator = CoCoBasic()
    emulator.process_command('NEW')
    def cleanup():
        os.chdir(orig_cwd)
        shutil.rmtree(test_dir)
    return emulator, cleanup


def load_and_run(emulator, program_lines, max_frames=50000):
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


def run_test(emulator, program_lines):
    results = load_and_run(emulator, program_lines)
    errors = get_errors(results)
    texts = get_text(results)
    if errors:
        print(f"  ERRORS: {errors}")
    for t in texts:
        if 'SAFETY' in t or 'MERGED' in t or 'HARD CAP' in t:
            continue
        print(f"  {t}")
    return texts


def run_diagnostic():
    emulator, cleanup = setup_emulator()

    try:
        print("=" * 60)
        print("TEST 1: CO=0 AT TBR - BOTH ALGORITHMS")
        print("=" * 60)
        print("Setup: BBU puts BBR corner at TBR with CO=0")
        print()

        # Rur on CO=0
        print("  --- Rur on CO=0 ---")
        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "rubiks_engine"',
            '25 MERGE "rubiks_solver"',
            '30 GOSUB InitCube',
            '35 AN=0',
            '40 TC1=7: TC2=5: TC3=3',
            '50 MS$="BBU": GOSUB DoMoves',
            '60 GOSUB FindCorner',
            '70 PRINT "BEFORE: CP=";CP;" CO=";CO',
            '75 PRINT "TBR: F4=";CL(2,0,2,4);" F1=";CL(2,0,2,1);" F2=";CL(2,0,2,2)',
            '80 MS$="Rur": GOSUB DoMoves',
            '90 GOSUB FindCorner',
            '100 PRINT "AFTER Rur: CP=";CP;" CO=";CO',
            '110 END',
        ]
        run_test(emulator, program)

        # BUb on CO=0
        print("  --- BUb on CO=0 ---")
        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "rubiks_engine"',
            '25 MERGE "rubiks_solver"',
            '30 GOSUB InitCube',
            '35 AN=0',
            '40 TC1=7: TC2=5: TC3=3',
            '50 MS$="BBU": GOSUB DoMoves',
            '60 GOSUB FindCorner',
            '70 PRINT "BEFORE: CP=";CP;" CO=";CO',
            '80 MS$="BUb": GOSUB DoMoves',
            '90 GOSUB FindCorner',
            '100 PRINT "AFTER BUb: CP=";CP;" CO=";CO',
            '110 END',
        ]
        run_test(emulator, program)

        print()
        print("=" * 60)
        print("COMPLETE TRUTH TABLE FOR BBR INSERT")
        print("=" * 60)
        print()
        print("At TBR (CP=6), applying algorithm -> result at BBR:")
        print()
        print("  CO=0 + Rur -> CP=2 CO=2 (WRONG)")
        print("  CO=0 + BUb -> (see above)")
        print("  CO=1 + BUb -> CP=2 CO=0 (CORRECT)")
        print("  CO=1 + Rur -> CP=2 CO=1 (WRONG)")
        print("  CO=2 + Rur -> CP=2 CO=0 (CORRECT)")
        print("  CO=2 + BUb -> CP=2 CO=2 (WRONG)")

        print()
        print("=" * 60)
        print("TEST 2: CO=0 CYCLING BEHAVIOR")
        print("=" * 60)
        print("If CO=0 + Rur -> CO=2 (at BBR), then extract+insert cycles:")

        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "rubiks_engine"',
            '25 MERGE "rubiks_solver"',
            '30 GOSUB InitCube',
            '35 AN=0',
            '40 TC1=7: TC2=5: TC3=3: CI=2',
            # Start with CO=0 at TBR
            '50 MS$="BBU": GOSUB DoMoves',
            '55 GOSUB FindCorner: PRINT "START: CP=";CP;" CO=";CO',
            # Iter 1: InsertBBR (CO=0 -> Rur)
            '60 GOSUB InsertBBR',
            '65 GOSUB FindCorner: PRINT "INSERT1: CP=";CP;" CO=";CO',
            # Extract
            '70 IF CP<=3 THEN GOSUB ExtractCorner',
            '75 GOSUB FindCorner: PRINT "EXTRACT1: CP=";CP;" CO=";CO',
            '80 GOSUB AlignCornerTop',
            '85 GOSUB FindCorner: PRINT "ALIGN1: CP=";CP;" CO=";CO',
            # Iter 2
            '90 GOSUB InsertBBR',
            '95 GOSUB FindCorner: PRINT "INSERT2: CP=";CP;" CO=";CO',
            '100 IF CP=2 AND CO=0 THEN PRINT "SOLVED ITER2": GOTO 200',
            # Extract
            '110 IF CP<=3 THEN GOSUB ExtractCorner',
            '115 GOSUB FindCorner: PRINT "EXTRACT2: CP=";CP;" CO=";CO',
            '120 GOSUB AlignCornerTop',
            '125 GOSUB FindCorner: PRINT "ALIGN2: CP=";CP;" CO=";CO',
            # Iter 3
            '130 GOSUB InsertBBR',
            '135 GOSUB FindCorner: PRINT "INSERT3: CP=";CP;" CO=";CO',
            '140 IF CP=2 AND CO=0 THEN PRINT "SOLVED ITER3": GOTO 200',
            # Extract
            '150 IF CP<=3 THEN GOSUB ExtractCorner',
            '155 GOSUB FindCorner: PRINT "EXTRACT3: CP=";CP;" CO=";CO',
            '160 GOSUB AlignCornerTop',
            '165 GOSUB FindCorner: PRINT "ALIGN3: CP=";CP;" CO=";CO',
            # Iter 4
            '170 GOSUB InsertBBR',
            '175 GOSUB FindCorner: PRINT "INSERT4: CP=";CP;" CO=";CO',
            '180 IF CP=2 AND CO=0 THEN PRINT "SOLVED ITER4": GOTO 200',
            '190 PRINT "NOT SOLVED AFTER 4"',
            '200 END',
        ]
        run_test(emulator, program)

        print()
        print("=" * 60)
        print("TEST 3: WHAT IS THE CORRECT ALGO FOR CO=0?")
        print("=" * 60)
        print("CO=0 means TC1 (magenta/7) is on Y-face (top, F4).")
        print("Neither side has it. Need to rotate it down to bottom (F5).")
        print()
        print("Standard beginner's method for CO=0 at top above target:")
        print("  Apply R U' R' (or B U B') to move it out, then realign,")
        print("  then insert with the correct CO.")
        print("  This takes 2-3 iterations to converge.")
        print()
        print("Let's verify: does Rur on CO=0 give CO that can be")
        print("fixed in the next iteration?")
        print()

        # The cycle should be: CO=0 -> Rur -> CO=2 -> extract -> align -> CO=? -> Rur -> CO=0?
        # Or does it cycle: CO=0 -> CO=2 -> CO=1 -> CO=0 (never reaching CO=0 at BBR with correct twist)?
        # Actually wait - Rur on CO=0 gives CO=2, but extraction changes the CO.
        # Let's trace it explicitly.

        print("Tracing: CO=0 -> InsertBBR(Rur) -> CO=2")
        print("  CO=2 at BBR -> ExtractBBR(BUb) -> where?")
        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "rubiks_engine"',
            '25 MERGE "rubiks_solver"',
            '30 GOSUB InitCube',
            '35 AN=0',
            '40 TC1=7: TC2=5: TC3=3: CI=2',
            # Create CO=2 at BBR by: setup BBU then Rur
            '50 MS$="BBU": GOSUB DoMoves',
            '55 MS$="Rur": GOSUB DoMoves',
            '60 GOSUB FindCorner: PRINT "CO=2 AT BBR: CP=";CP;" CO=";CO',
            # Extract with BUb
            '70 MS$="BUb": GOSUB DoMoves',
            '75 GOSUB FindCorner: PRINT "AFTER EXTRACT: CP=";CP;" CO=";CO',
            # Align
            '80 GOSUB AlignCornerTop',
            '85 GOSUB FindCorner: PRINT "AFTER ALIGN: CP=";CP;" CO=";CO',
            # Now InsertBBR dispatches based on CO
            '90 PRINT "DISPATCH: CO=";CO',
            '95 IF CO=1 THEN PRINT "WOULD USE BUb"',
            '96 IF CO=2 OR CO=0 THEN PRINT "WOULD USE Rur"',
            '100 GOSUB InsertBBR',
            '105 GOSUB FindCorner: PRINT "AFTER INSERT: CP=";CP;" CO=";CO',
            '110 END',
        ]
        run_test(emulator, program)

        print()
        print("=" * 60)
        print("TEST 4: TRY ALTERNATIVE ALGORITHMS FOR CO=0")
        print("=" * 60)

        # For CO=0 (magenta on top at TBR), the standard approach is
        # to do the insert twice: first insert moves corner to BBR with
        # wrong twist, extract brings it back with a different CO.
        # But maybe we need a different algorithm entirely for CO=0.
        #
        # Standard beginner's method: for CO=0 (color on top),
        # you need to do the "triple" version: (R U R') U' (R U R') U' (R U R')
        # which is 3x the trigger. This rotates the corner orientation.
        #
        # Actually the standard approach for CO=0 is:
        #   R U2 R' U' R U R'  (right trigger variant)
        #   or B' U2 B U B' U' B (left trigger variant for back-right)
        #
        # Let's test: RUURuRUR (= R U2 R' U' R U R')
        # And: buUBUbuB (= B' U2 B U B' U' B) -- wait, need to think about this
        # For BBR using R face: RUURuRuR = R U U R' U' R U' R'? Let me try variations.

        for algo_name, algo in [
            ("RUURuRuR", "RUURuRuR"),  # R U2 R' U' R U' R'
            ("RUURurUR", "RUURurUR"),  # R U2 R' U R U R' -- probably wrong
            ("ruURUruR", "ruURUruR"),  # R' U2 R U R' U R
            ("RuuruRUR", "RuuruRUR"),  # R U' U' R' U' R U R'
        ]:
            program = [
                '5 SAFETY OFF',
                '10 PMODE 4: SCREEN 1',
                '20 MERGE "rubiks_engine"',
                '25 MERGE "rubiks_solver"',
                '30 GOSUB InitCube',
                '35 AN=0',
                '40 TC1=7: TC2=5: TC3=3',
                '50 MS$="BBU": GOSUB DoMoves',
                '60 GOSUB FindCorner',
                '70 PRINT "BEFORE: CP=";CP;" CO=";CO',
                f'80 MS$="{algo}": GOSUB DoMoves',
                '90 GOSUB FindCorner',
                f'100 PRINT "AFTER {algo_name}: CP=";CP;" CO=";CO',
                '110 END',
            ]
            print(f"  --- {algo_name} on CO=0 ---")
            run_test(emulator, program)

        # Also try the standard approach: it SHOULD converge in 2-3 iterations
        # if the extract gives a different CO each time.
        print()
        print("The current approach (Rur for CO=0) gives CO=2,")
        print("which should be fixable in the next iteration.")
        print("Let's verify the full convergence in Test 2 output above.")

    finally:
        cleanup()


if __name__ == '__main__':
    run_diagnostic()
