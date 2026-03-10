#!/usr/bin/env python3
"""
Diagnostic part 4: Find the correct CO=0 algorithm for BBR insertion.

The bug: CO=0 + Rur -> CO=2, extract -> CO=0, infinite loop.
Need: algorithm that takes CO=0 at TBR and produces CO=0 at BBR.

BBR is at (2,2,2). TBR is at (2,0,2).
BBR shares R face and B face.

Standard beginner approach for CO=0 (white/target on top):
  Use a "double trigger" - insert, rotate top, extract:
  R U' R' U  R U' R'  (for right-hand trigger, front-right)
  or
  B U B' U'  B U B'   (for back trigger, back-right)

For BBR specifically, the right-hand trigger uses R, and back trigger uses B.
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
        print("=" * 60)
        print("TESTING DOUBLE-TRIGGER ALGORITHMS FOR CO=0 AT TBR->BBR")
        print("=" * 60)
        print("Setup: BBU puts BBR corner at TBR with CO=0")
        print()

        # For BBR (back-right bottom), the two relevant faces are R and B.
        # Standard double-trigger patterns:
        #   Right trigger: R U' R' (inserts using R face)
        #   Back trigger:  B U B'  (inserts using B face)
        #
        # For CO=0 (white/target on top), beginner method says:
        #   Do trigger, U', trigger again. Or: trigger, U, trigger again.
        #   Specifically: R U' R' U' R U' R'  or  R U R' U R U' R'
        #   For B face: B U B' U' B U B'  or variations
        #
        # Let's try many combinations systematically:

        algos = [
            # R-based double triggers
            ("RurURur", "R U' R' U R U' R'"),
            ("RuruRur", "R U' R' U' R U' R'"),
            ("RURURur", "R U R U R U' R'"),    # probably wrong
            ("RURuRur", "R U R' U' R U' R'"),
            ("RuRURur", "R U' R U R U' R'"),   # probably wrong
            # B-based double triggers
            ("BUbuBUb", "B U B' U' B U B'"),
            ("BUbUBUb", "B U B' U B U B'"),
            ("BUbuBub", "B U B' U' B U' B'"),  # probably wrong
            # Mixed
            ("RuruBUb", "R U' R' U' B U B'"),
            ("BUbURur", "B U B' U R U' R'"),
            # Try the approach: insert + U adj + extract
            # Rur U Rur = R U' R' U R U' R'
            ("RurURur", "already listed"),
            # Rur u Rur = R U' R' U' R U' R'
            ("RuruRur", "already listed"),
            # BUb u BUb = B U B' U' B U B'
            ("BUbuBUb", "already listed"),
            # BUb U BUb = B U B' U B U B'
            ("BUbUBUb", "already listed"),
        ]

        # Remove duplicates
        seen = set()
        unique_algos = []
        for moves, desc in algos:
            if moves not in seen:
                seen.add(moves)
                unique_algos.append((moves, desc))

        for moves, desc in unique_algos:
            program = [
                '5 SAFETY OFF',
                '10 PMODE 4: SCREEN 1',
                '20 MERGE "lib_rubiks_engine"',
                '25 MERGE "lib_rubiks_solver"',
                '30 GOSUB InitCube',
                '35 AN=0',
                '40 TC1=7: TC2=5: TC3=3',
                '50 MS$="BBU": GOSUB DoMoves',
                '60 GOSUB FindCorner',
                f'80 MS$="{moves}": GOSUB DoMoves',
                '90 GOSUB FindCorner',
                f'100 PRINT "{moves}: CP=";CP;" CO=";CO',
                '110 END',
            ]
            run_test(emulator, program)

        print()
        print("=" * 60)
        print("CHECKING ALL CORNERS' CO=0 ALGORITHMS")
        print("=" * 60)
        print()
        print("For comparison, let's look at all 4 InsertX subroutines:")
        print()
        print("InsertBFR: CO=2 -> rUR (R' U R), CO=1 or CO=0 -> fuF (F' U' F)")
        print("InsertBFL: CO=1 -> FUf (F U F'), CO=2 or CO=0 -> LuL (L U' L' -- wait)")
        print()

        # Let me also check: does the BFR insertion have the same CO=0 problem?
        # BFR: TC1=7, TC2=4, TC3=3, CI=0
        # TFR: (2,0,0), CP=4
        # InsertBFR: CO=2 -> rUR, else -> fuF
        # What setup gives CO=0 at TFR?

        print("--- Finding CO=0 at TFR for BFR ---")
        for moves in ["FF", "FFU", "FFu", "RR", "RRU", "RRu", "rr", "rrU"]:
            program = [
                '5 SAFETY OFF',
                '10 PMODE 4: SCREEN 1',
                '20 MERGE "lib_rubiks_engine"',
                '25 MERGE "lib_rubiks_solver"',
                '30 GOSUB InitCube',
                '35 AN=0',
                '40 TC1=7: TC2=4: TC3=3',
                f'50 MS$="{moves}": GOSUB DoMoves',
                '60 GOSUB FindCorner',
                '70 PRINT "{moves}: CP=";CP;" CO=";CO',
                '100 END',
            ]
            # Can't do string interpolation in BASIC, fix:
            program[6] = f'70 PRINT "SETUP {moves}: CP=";CP;" CO=";CO'
            run_test(emulator, program)

        print()
        print("--- Testing InsertBFR with CO=0 ---")
        # Find a setup that gives CO=0 at CP=4 (TFR) for BFR corner
        for moves in ["FFU", "FFu", "RRU", "RRu"]:
            program = [
                '5 SAFETY OFF',
                '10 PMODE 4: SCREEN 1',
                '20 MERGE "lib_rubiks_engine"',
                '25 MERGE "lib_rubiks_solver"',
                '30 GOSUB InitCube',
                '35 AN=0',
                '40 TC1=7: TC2=4: TC3=3: CI=0',
                f'50 MS$="{moves}": GOSUB DoMoves',
                '60 GOSUB FindCorner',
                f'70 PRINT "BEFORE ({moves}): CP=";CP;" CO=";CO',
                '80 IF CP<>4 THEN PRINT "SKIP - NOT AT TFR": GOTO 200',
                '90 GOSUB InsertBFR',
                '100 GOSUB FindCorner',
                f'110 PRINT "AFTER INSERT: CP=";CP;" CO=";CO',
                '200 END',
            ]
            run_test(emulator, program)

    finally:
        cleanup()


if __name__ == '__main__':
    run_diagnostic()
