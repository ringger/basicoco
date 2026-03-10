#!/usr/bin/env python3
"""
Diagnostic part 5: Check all 4 corners for the CO=0 infinite loop bug.

Finding so far:
  - BBR: CO=0 + Rur -> CO=2, extract -> CO=0 -> INFINITE LOOP
  - BFR: CO=0 + fuF -> CO=1, need to check if it loops too

Also: find the correct fix. The standard beginner approach uses a
double-trigger (insert, adjust U, insert again).
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
    for fname in ('lib_rubiks_engine.bas', 'lib_rubiks_solver.bas'):
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
        # ============================================================
        # TEST: BFR CO=0 cycling
        # ============================================================
        print("=" * 60)
        print("BFR CO=0 CYCLING TEST")
        print("=" * 60)
        # BFR: TC1=7, TC2=4, TC3=3, CI=0, extraction: ruR
        # TFR: CP=4
        # Setup FFu gives CO=0 at TFR (CP=4)
        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "lib_rubiks_engine"',
            '25 MERGE "lib_rubiks_solver"',
            '30 GOSUB InitCube',
            '35 AN=0',
            '40 TC1=7: TC2=4: TC3=3: CI=0',
            '50 MS$="FFu": GOSUB DoMoves',
            '55 GOSUB FindCorner: PRINT "START: CP=";CP;" CO=";CO',
            # Iter 1
            '60 GOSUB InsertBFR',
            '65 GOSUB FindCorner: PRINT "INSERT1: CP=";CP;" CO=";CO',
            '70 IF CP=0 AND CO=0 THEN PRINT "SOLVED": GOTO 300',
            '75 IF CP<=3 THEN GOSUB ExtractCorner',
            '80 GOSUB FindCorner: PRINT "EXTRACT1: CP=";CP;" CO=";CO',
            '85 GOSUB AlignCornerTop',
            '90 GOSUB FindCorner: PRINT "ALIGN1: CP=";CP;" CO=";CO',
            # Iter 2
            '100 GOSUB InsertBFR',
            '105 GOSUB FindCorner: PRINT "INSERT2: CP=";CP;" CO=";CO',
            '110 IF CP=0 AND CO=0 THEN PRINT "SOLVED": GOTO 300',
            '115 IF CP<=3 THEN GOSUB ExtractCorner',
            '120 GOSUB FindCorner: PRINT "EXTRACT2: CP=";CP;" CO=";CO',
            '125 GOSUB AlignCornerTop',
            '130 GOSUB FindCorner: PRINT "ALIGN2: CP=";CP;" CO=";CO',
            # Iter 3
            '140 GOSUB InsertBFR',
            '145 GOSUB FindCorner: PRINT "INSERT3: CP=";CP;" CO=";CO',
            '150 IF CP=0 AND CO=0 THEN PRINT "SOLVED": GOTO 300',
            '155 IF CP<=3 THEN GOSUB ExtractCorner',
            '160 GOSUB FindCorner: PRINT "EXTRACT3: CP=";CP;" CO=";CO',
            '165 GOSUB AlignCornerTop',
            '170 GOSUB FindCorner: PRINT "ALIGN3: CP=";CP;" CO=";CO',
            # Iter 4
            '180 GOSUB InsertBFR',
            '185 GOSUB FindCorner: PRINT "INSERT4: CP=";CP;" CO=";CO',
            '190 IF CP=0 AND CO=0 THEN PRINT "SOLVED": GOTO 300',
            '195 PRINT "NOT SOLVED AFTER 4"',
            '300 END',
        ]
        run_test(emulator, program)

        # ============================================================
        # TEST: BFL CO=0 cycling
        # ============================================================
        print()
        print("=" * 60)
        print("BFL CO=0 CYCLING TEST")
        print("=" * 60)
        # BFL: TC1=7, TC2=4, TC3=6, CI=1, extraction: FUf
        # TFL: CP=5
        # InsertBFL: CO=1 -> FUf, else -> LuL
        # Need CO=0 at TFL (CP=5)
        # First find setup
        for moves in ["FFU", "LLu", "LLU", "FFu", "llU", "llu"]:
            program = [
                '5 SAFETY OFF',
                '10 PMODE 4: SCREEN 1',
                '20 MERGE "lib_rubiks_engine"',
                '25 MERGE "lib_rubiks_solver"',
                '30 GOSUB InitCube',
                '35 AN=0',
                '40 TC1=7: TC2=4: TC3=6',
                f'50 MS$="{moves}": GOSUB DoMoves',
                '60 GOSUB FindCorner',
                f'70 PRINT "{moves}: CP=";CP;" CO=";CO',
                '100 END',
            ]
            run_test(emulator, program)

        # ============================================================
        # TEST: BBL CO=0 cycling
        # ============================================================
        print()
        print("=" * 60)
        print("BBL CO=0 CYCLING TEST")
        print("=" * 60)
        # BBL: TC1=7, TC2=5, TC3=6, CI=3, extraction: luL
        # TBL: CP=7
        # InsertBBL: CO=2 -> lUL, else -> buB
        # Need CO=0 at TBL (CP=7)
        for moves in ["BBu", "BBU", "LLU", "LLu", "llU", "llu", "bbu", "bbU"]:
            program = [
                '5 SAFETY OFF',
                '10 PMODE 4: SCREEN 1',
                '20 MERGE "lib_rubiks_engine"',
                '25 MERGE "lib_rubiks_solver"',
                '30 GOSUB InitCube',
                '35 AN=0',
                '40 TC1=7: TC2=5: TC3=6',
                f'50 MS$="{moves}": GOSUB DoMoves',
                '60 GOSUB FindCorner',
                f'70 PRINT "{moves}: CP=";CP;" CO=";CO',
                '100 END',
            ]
            run_test(emulator, program)

        # ============================================================
        # KEY INSIGHT: CO=0 needs a different approach
        # ============================================================
        print()
        print("=" * 60)
        print("SOLUTION ANALYSIS")
        print("=" * 60)
        print()
        print("The standard beginner's method for CO=0 (target color on top)")
        print("at the correct position above the target slot:")
        print()
        print("  1. Do the 'wrong' trigger to insert it twisted")
        print("  2. U or U' to misalign")
        print("  3. Extract with the 'right' trigger")
        print("  4. Re-align with U")
        print("  5. Insert with the correct trigger for the new CO")
        print()
        print("But the current code just does one trigger and expects")
        print("the extract+insert loop to converge. For CO=0, this creates")
        print("a fixed-point loop because:")
        print("  - Insert (Rur) gives CO=2 at BBR")
        print("  - Extract (BUb) gives CO=0 at TFR")
        print("  - Align brings it back to TBR with CO=0")
        print("  - Same state as before!")
        print()
        print("FIX OPTIONS:")
        print("  A. Use R U2 R' U' R U R' for CO=0 (double trigger)")
        print("  B. Use a different extraction for CO=0 case")
        print("  C. Check if simply using BUb for CO=0 would converge")

        # Test option C: What if CO=0 used BUb instead of Rur?
        print()
        print("TESTING: BUb for CO=0 cycling")
        # CO=0 + BUb -> CP=2 CO=1 (from Test 1 in part 3)
        # CO=1 at BBR -> extract BUb -> ?
        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "lib_rubiks_engine"',
            '25 MERGE "lib_rubiks_solver"',
            '30 GOSUB InitCube',
            '35 AN=0',
            '40 TC1=7: TC2=5: TC3=3: CI=2',
            '50 MS$="BBU": GOSUB DoMoves',
            '55 GOSUB FindCorner: PRINT "START: CP=";CP;" CO=";CO',
            # Use BUb instead of Rur for CO=0
            '60 MS$="BUb": GOSUB DoMoves',
            '65 GOSUB FindCorner: PRINT "AFTER BUb: CP=";CP;" CO=";CO',
            # CO=1 at BBR. Extract.
            '70 IF CP<=3 THEN GOSUB ExtractCorner',
            '75 GOSUB FindCorner: PRINT "EXTRACT: CP=";CP;" CO=";CO',
            '80 GOSUB AlignCornerTop',
            '85 GOSUB FindCorner: PRINT "ALIGN: CP=";CP;" CO=";CO',
            # Now InsertBBR: CO=1 -> BUb (correct!)
            '90 GOSUB InsertBBR',
            '95 GOSUB FindCorner: PRINT "INSERT: CP=";CP;" CO=";CO',
            '100 IF CP=2 AND CO=0 THEN PRINT "SOLVED!!"',
            '105 IF CP<>2 OR CO<>0 THEN PRINT "NOT SOLVED"',
            '200 END',
        ]
        run_test(emulator, program)

        print()
        print("TESTING: What if we swap the CO=0 algorithm?")
        print("  Current: CO=0 -> Rur (same as CO=2)")
        print("  Proposed: CO=0 -> BUb (same as CO=1)")
        print()
        print("If CO=0 + BUb -> CO=1, then extract -> ?, align -> ?,")
        print("then InsertBBR(CO=1) -> BUb -> CO=0. Would that work?")
        print("Let's check the full cycle.")

        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "lib_rubiks_engine"',
            '25 MERGE "lib_rubiks_solver"',
            '30 GOSUB InitCube',
            '35 AN=0',
            '40 TC1=7: TC2=5: TC3=3: CI=2',
            '50 MS$="BBU": GOSUB DoMoves',
            '55 GOSUB FindCorner: PRINT "START: CP=";CP;" CO=";CO',
            # Manually do BUb for CO=0
            '60 MS$="BUb": GOSUB DoMoves',
            '65 GOSUB FindCorner: PRINT "BUb1: CP=";CP;" CO=";CO',
            # Extract from BBR
            '70 IF CP<=3 THEN MS$="BUb": GOSUB DoMoves',
            '75 GOSUB FindCorner: PRINT "EXTR1: CP=";CP;" CO=";CO',
            '80 GOSUB AlignCornerTop',
            '85 GOSUB FindCorner: PRINT "ALGN1: CP=";CP;" CO=";CO',
            # CO should now be 1 -> InsertBBR uses BUb
            '90 MS$="BUb": GOSUB DoMoves',
            '95 GOSUB FindCorner: PRINT "BUb2: CP=";CP;" CO=";CO',
            '100 IF CP=2 AND CO=0 THEN PRINT "SOLVED!!"',
            '110 IF CP<=3 THEN MS$="BUb": GOSUB DoMoves',
            '115 GOSUB FindCorner: PRINT "EXTR2: CP=";CP;" CO=";CO',
            '120 GOSUB AlignCornerTop',
            '125 GOSUB FindCorner: PRINT "ALGN2: CP=";CP;" CO=";CO',
            '130 MS$="BUb": GOSUB DoMoves',
            '135 GOSUB FindCorner: PRINT "BUb3: CP=";CP;" CO=";CO',
            '140 IF CP=2 AND CO=0 THEN PRINT "SOLVED!!"',
            '145 PRINT "CYCLE STATE"',
            '200 END',
        ]
        run_test(emulator, program)

        # Test: what if CO=0 uses Rur followed by U then BUb?
        # i.e., R U' R' U B U B'
        print()
        print("TESTING: Double trigger RurUBUb for CO=0")
        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "lib_rubiks_engine"',
            '25 MERGE "lib_rubiks_solver"',
            '30 GOSUB InitCube',
            '35 AN=0',
            '40 TC1=7: TC2=5: TC3=3',
            '50 MS$="BBU": GOSUB DoMoves',
            '60 GOSUB FindCorner: PRINT "START: CP=";CP;" CO=";CO',
            '70 MS$="RurUBUb": GOSUB DoMoves',
            '80 GOSUB FindCorner: PRINT "RurUBUb: CP=";CP;" CO=";CO',
            '100 END',
        ]
        run_test(emulator, program)

        print()
        print("TESTING: Double trigger BUbuRur for CO=0")
        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "lib_rubiks_engine"',
            '25 MERGE "lib_rubiks_solver"',
            '30 GOSUB InitCube',
            '35 AN=0',
            '40 TC1=7: TC2=5: TC3=3',
            '50 MS$="BBU": GOSUB DoMoves',
            '60 GOSUB FindCorner: PRINT "START: CP=";CP;" CO=";CO',
            '70 MS$="BUbuRur": GOSUB DoMoves',
            '80 GOSUB FindCorner: PRINT "BUbuRur: CP=";CP;" CO=";CO',
            '100 END',
        ]
        run_test(emulator, program)

        print()
        print("TESTING: RuruRUR for CO=0 (extract+U+insert)")
        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "lib_rubiks_engine"',
            '25 MERGE "lib_rubiks_solver"',
            '30 GOSUB InitCube',
            '35 AN=0',
            '40 TC1=7: TC2=5: TC3=3',
            '50 MS$="BBU": GOSUB DoMoves',
            '60 GOSUB FindCorner: PRINT "START: CP=";CP;" CO=";CO',
            '70 MS$="RuruRUR": GOSUB DoMoves',
            '80 GOSUB FindCorner: PRINT "RuruRUR: CP=";CP;" CO=";CO',
            '100 END',
        ]
        run_test(emulator, program)

        print()
        print("TESTING: BUbUbuB for CO=0")
        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "lib_rubiks_engine"',
            '25 MERGE "lib_rubiks_solver"',
            '30 GOSUB InitCube',
            '35 AN=0',
            '40 TC1=7: TC2=5: TC3=3',
            '50 MS$="BBU": GOSUB DoMoves',
            '60 GOSUB FindCorner: PRINT "START: CP=";CP;" CO=";CO',
            '70 MS$="BUbUbuB": GOSUB DoMoves',
            '80 GOSUB FindCorner: PRINT "BUbUbuB: CP=";CP;" CO=";CO',
            '100 END',
        ]
        run_test(emulator, program)

    finally:
        cleanup()


if __name__ == '__main__':
    run_diagnostic()
