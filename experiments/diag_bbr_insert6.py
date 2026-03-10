#!/usr/bin/env python3
"""
Diagnostic part 6: Verify BFL and BBL CO=0 behavior + confirm the fix.

CONFIRMED BUG: For BBR, CO=0 + Rur -> CO=2, extract -> CO=0 -> INFINITE LOOP
CONFIRMED FIX: For BBR, CO=0 should use BUb (not Rur). This gives CO=1,
               which extract+align+InsertBBR(CO=1->BUb) -> CO=0. SOLVED.

BFR: CO=0 + fuF -> CO=1, extract -> CO=1, InsertBFR(CO=1->fuF) -> CO=0. CONVERGES.
     (But takes 2 iterations, not 1. Already works by luck.)

Now check BFL and BBL for the same pattern.
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
        # ============================================================
        # BFL CO=0 CYCLING
        # ============================================================
        print("=" * 60)
        print("BFL CO=0 CYCLING TEST")
        print("=" * 60)
        # BFL: TC1=7, TC2=4, TC3=6, CI=1
        # TFL: CP=5
        # InsertBFL: CO=1 -> FUf, else (CO=0,CO=2) -> LuL
        # Extraction from BFL (CP=1): FUf
        # Setup: LLu gives CO=0 at TFL (CP=5)
        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "rubiks_engine"',
            '25 MERGE "rubiks_solver"',
            '30 GOSUB InitCube',
            '35 AN=0',
            '40 TC1=7: TC2=4: TC3=6: CI=1',
            '50 MS$="LLu": GOSUB DoMoves',
            '55 GOSUB FindCorner: PRINT "START: CP=";CP;" CO=";CO',
            # Iter 1: InsertBFL (CO=0 -> LuL)
            '60 GOSUB InsertBFL',
            '65 GOSUB FindCorner: PRINT "INSERT1: CP=";CP;" CO=";CO',
            '70 IF CP=1 AND CO=0 THEN PRINT "SOLVED": GOTO 300',
            '75 IF CP<=3 THEN GOSUB ExtractCorner',
            '80 GOSUB FindCorner: PRINT "EXTRACT1: CP=";CP;" CO=";CO',
            '85 GOSUB AlignCornerTop',
            '90 GOSUB FindCorner: PRINT "ALIGN1: CP=";CP;" CO=";CO',
            # Iter 2
            '100 GOSUB InsertBFL',
            '105 GOSUB FindCorner: PRINT "INSERT2: CP=";CP;" CO=";CO',
            '110 IF CP=1 AND CO=0 THEN PRINT "SOLVED": GOTO 300',
            '115 IF CP<=3 THEN GOSUB ExtractCorner',
            '120 GOSUB FindCorner: PRINT "EXTRACT2: CP=";CP;" CO=";CO',
            '125 GOSUB AlignCornerTop',
            '130 GOSUB FindCorner: PRINT "ALIGN2: CP=";CP;" CO=";CO',
            # Iter 3
            '140 GOSUB InsertBFL',
            '145 GOSUB FindCorner: PRINT "INSERT3: CP=";CP;" CO=";CO',
            '150 IF CP=1 AND CO=0 THEN PRINT "SOLVED": GOTO 300',
            '155 IF CP<=3 THEN GOSUB ExtractCorner',
            '160 GOSUB FindCorner: PRINT "EXTRACT3: CP=";CP;" CO=";CO',
            '165 GOSUB AlignCornerTop',
            '170 GOSUB FindCorner: PRINT "ALIGN3: CP=";CP;" CO=";CO',
            # Iter 4
            '180 GOSUB InsertBFL',
            '185 GOSUB FindCorner: PRINT "INSERT4: CP=";CP;" CO=";CO',
            '190 IF CP=1 AND CO=0 THEN PRINT "SOLVED": GOTO 300',
            '195 PRINT "NOT SOLVED AFTER 4"',
            '300 END',
        ]
        run_test(emulator, program)

        # ============================================================
        # BBL CO=0 CYCLING
        # ============================================================
        print()
        print("=" * 60)
        print("BBL CO=0 CYCLING TEST")
        print("=" * 60)
        # BBL: TC1=7, TC2=5, TC3=6, CI=3
        # TBL: CP=7
        # InsertBBL: CO=2 -> lUL, else (CO=0,CO=1) -> buB
        # Extraction from BBL (CP=3): luL
        # Setup: BBu gives CO=0 at TBL (CP=7)
        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "rubiks_engine"',
            '25 MERGE "rubiks_solver"',
            '30 GOSUB InitCube',
            '35 AN=0',
            '40 TC1=7: TC2=5: TC3=6: CI=3',
            '50 MS$="BBu": GOSUB DoMoves',
            '55 GOSUB FindCorner: PRINT "START: CP=";CP;" CO=";CO',
            # Iter 1: InsertBBL (CO=0 -> buB)
            '60 GOSUB InsertBBL',
            '65 GOSUB FindCorner: PRINT "INSERT1: CP=";CP;" CO=";CO',
            '70 IF CP=3 AND CO=0 THEN PRINT "SOLVED": GOTO 300',
            '75 IF CP<=3 THEN GOSUB ExtractCorner',
            '80 GOSUB FindCorner: PRINT "EXTRACT1: CP=";CP;" CO=";CO',
            '85 GOSUB AlignCornerTop',
            '90 GOSUB FindCorner: PRINT "ALIGN1: CP=";CP;" CO=";CO',
            # Iter 2
            '100 GOSUB InsertBBL',
            '105 GOSUB FindCorner: PRINT "INSERT2: CP=";CP;" CO=";CO',
            '110 IF CP=3 AND CO=0 THEN PRINT "SOLVED": GOTO 300',
            '115 IF CP<=3 THEN GOSUB ExtractCorner',
            '120 GOSUB FindCorner: PRINT "EXTRACT2: CP=";CP;" CO=";CO',
            '125 GOSUB AlignCornerTop',
            '130 GOSUB FindCorner: PRINT "ALIGN2: CP=";CP;" CO=";CO',
            # Iter 3
            '140 GOSUB InsertBBL',
            '145 GOSUB FindCorner: PRINT "INSERT3: CP=";CP;" CO=";CO',
            '150 IF CP=3 AND CO=0 THEN PRINT "SOLVED": GOTO 300',
            '155 IF CP<=3 THEN GOSUB ExtractCorner',
            '160 GOSUB FindCorner: PRINT "EXTRACT3: CP=";CP;" CO=";CO',
            '165 GOSUB AlignCornerTop',
            '170 GOSUB FindCorner: PRINT "ALIGN3: CP=";CP;" CO=";CO',
            '180 GOSUB InsertBBL',
            '185 GOSUB FindCorner: PRINT "INSERT4: CP=";CP;" CO=";CO',
            '190 IF CP=3 AND CO=0 THEN PRINT "SOLVED": GOTO 300',
            '195 PRINT "NOT SOLVED AFTER 4"',
            '300 END',
        ]
        run_test(emulator, program)

        # ============================================================
        # FINAL SUMMARY
        # ============================================================
        print()
        print("=" * 60)
        print("FINAL SUMMARY")
        print("=" * 60)
        print()
        print("Insert algorithm truth table (at TXX above target):")
        print()
        print("BBR (CI=2): InsertBBR")
        print("  CO=0 + Rur(current) -> CO=2 -> extract -> CO=0 -> LOOPS!")
        print("  CO=0 + BUb(proposed) -> CO=1 -> extract -> CO=2 -> Rur -> CO=0 SOLVED")
        print("  CO=1 + BUb -> CO=0 SOLVED (correct)")
        print("  CO=2 + Rur -> CO=0 SOLVED (correct)")
        print()
        print("BFR (CI=0): InsertBFR")
        print("  CO=0 + fuF -> CO=1 -> extract -> CO=1 -> fuF -> CO=0 SOLVED (2 iters)")
        print("  CO=1 + fuF -> CO=0 SOLVED (correct)")
        print("  CO=2 + rUR -> CO=0 SOLVED (correct)")
        print()
        print("FIX FOR BBR:")
        print("  Change InsertBBR CO=0 case from Rur to BUb")
        print("  Current code:")
        print('    IF CO=1 THEN MS$="BUb": GOSUB DoMoves: RETURN')
        print('    MS$="Rur": GOSUB DoMoves  (handles CO=2 AND CO=0)')
        print("  Fixed code:")
        print('    IF CO=2 THEN MS$="Rur": GOSUB DoMoves: RETURN')
        print('    MS$="BUb": GOSUB DoMoves  (handles CO=1 AND CO=0)')

    finally:
        cleanup()


if __name__ == '__main__':
    run_diagnostic()
