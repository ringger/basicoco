#!/usr/bin/env python3
"""
Diagnostic part 2: Focus on the extract-align-insert cycle for BBR.

Key finding from part 1: BUb extraction sends BBR(CP=2) to TFR(CP=4), NOT TBR(CP=6).
The solver then calls AlignCornerTop to rotate U, then InsertBBR.

Let's trace exactly what happens with the full solver cycle, and also
test CO=0 at TBR since we haven't found a setup for that yet.
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


def run_test(emulator, program_lines, label=""):
    results = load_and_run(emulator, program_lines)
    errors = get_errors(results)
    texts = get_text(results)
    if errors:
        print(f"  ERRORS: {errors}")
    for t in texts:
        # Skip boilerplate
        if 'SAFETY' in t or 'MERGED' in t or 'HARD CAP' in t:
            continue
        print(f"  {t}")
    return texts


def run_diagnostic():
    emulator, cleanup = setup_emulator()

    try:
        print("=" * 60)
        print("TEST A: FULL SOLVER CYCLE FOR BBR (extract+align+insert)")
        print("=" * 60)

        # Simulate exactly what SolveBotCorner does for CI=2
        # Start with solved cube, extract BBR, align, insert, repeat
        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "rubiks_engine"',
            '25 MERGE "rubiks_solver"',
            '30 GOSUB InitCube',
            '35 AN=0',
            '40 TC1=7: TC2=5: TC3=3: CI=2',
            # Initial
            '50 GOSUB FindCorner',
            '55 PRINT "START: CP=";CP;" CO=";CO',
            # --- Iteration 1: extract ---
            '60 PRINT "--- ITER 1 ---"',
            '65 IF CP<=3 THEN GOSUB ExtractCorner: PRINT "EXTRACTED"',
            '70 GOSUB FindCorner: PRINT "AFTER EXTRACT: CP=";CP;" CO=";CO',
            '75 GOSUB AlignCornerTop',
            '80 GOSUB FindCorner: PRINT "AFTER ALIGN: CP=";CP;" CO=";CO',
            '85 GOSUB InsertBBR',
            '90 GOSUB FindCorner: PRINT "AFTER INSERT: CP=";CP;" CO=";CO',
            '95 IF CP=2 AND CO=0 THEN PRINT "SOLVED!": GOTO 500',
            # --- Iteration 2 ---
            '100 PRINT "--- ITER 2 ---"',
            '105 IF CP<=3 THEN GOSUB ExtractCorner: PRINT "EXTRACTED"',
            '110 GOSUB FindCorner: PRINT "AFTER EXTRACT: CP=";CP;" CO=";CO',
            '115 GOSUB AlignCornerTop',
            '120 GOSUB FindCorner: PRINT "AFTER ALIGN: CP=";CP;" CO=";CO',
            '125 GOSUB InsertBBR',
            '130 GOSUB FindCorner: PRINT "AFTER INSERT: CP=";CP;" CO=";CO',
            '135 IF CP=2 AND CO=0 THEN PRINT "SOLVED!": GOTO 500',
            # --- Iteration 3 ---
            '140 PRINT "--- ITER 3 ---"',
            '145 IF CP<=3 THEN GOSUB ExtractCorner: PRINT "EXTRACTED"',
            '150 GOSUB FindCorner: PRINT "AFTER EXTRACT: CP=";CP;" CO=";CO',
            '155 GOSUB AlignCornerTop',
            '160 GOSUB FindCorner: PRINT "AFTER ALIGN: CP=";CP;" CO=";CO',
            '165 GOSUB InsertBBR',
            '170 GOSUB FindCorner: PRINT "AFTER INSERT: CP=";CP;" CO=";CO',
            '175 IF CP=2 AND CO=0 THEN PRINT "SOLVED!": GOTO 500',
            # --- Iteration 4 ---
            '180 PRINT "--- ITER 4 ---"',
            '185 IF CP<=3 THEN GOSUB ExtractCorner: PRINT "EXTRACTED"',
            '190 GOSUB FindCorner: PRINT "AFTER EXTRACT: CP=";CP;" CO=";CO',
            '195 GOSUB AlignCornerTop',
            '200 GOSUB FindCorner: PRINT "AFTER ALIGN: CP=";CP;" CO=";CO',
            '205 GOSUB InsertBBR',
            '210 GOSUB FindCorner: PRINT "AFTER INSERT: CP=";CP;" CO=";CO',
            '215 IF CP=2 AND CO=0 THEN PRINT "SOLVED!": GOTO 500',
            '220 PRINT "NOT SOLVED AFTER 4 ITERS"',
            '500 END',
        ]
        run_test(emulator, program)

        print()
        print("=" * 60)
        print("TEST B: FIND CO=0 SETUP AT TBR, THEN TEST INSERT")
        print("=" * 60)

        # CO=0 means TC1 (magenta/7) on Y-face (F4 for top).
        # TBR is (2,0,2): F4=top, F1=back, F2=right
        # CO=0 at TBR: magenta on top (F4=7)
        # Need a sequence that puts 7 on F4 of (2,0,2)
        # Try: extract with different methods

        # ruR extracts BFR. What about extracting BBR differently?
        # Let's try: R' U R (ruR) starting from solved - this extracts BFR not BBR.
        # We want BBR at TBR with CO=0.
        # BBR(2,2,2): F5=7, F1=5, F2=3
        # TBR(2,0,2): F4=top, F1=back, F2=right
        # CO=0 at TBR means F4=7, so top sticker = magenta
        # R sends BBR to TBR: F5->F1 (7->F1), F1->F4 (5->F4), F2->F2 (3->F2)
        #   So at TBR: F4=5, F1=7, F2=3 -> CO=1 (7 on Z/F1) - matches our finding
        # B sends BBR to TBR: F5->F2 (7->F2), F1->F1 (5->F1), F2->F4 (3->F4)
        #   So at TBR: F4=3, F1=5, F2=7 -> CO=2 (7 on X/F2) - matches our finding
        # For CO=0 we need F4=7. Let's try RR or BB.
        # RR: (2,2,2) IY=2,IZ=2 -> R once: NY=0,NZ=2 (TBR). R twice: from (2,0,2) IY=0,IZ=2 -> NY=0,NZ=0 -> (2,0,0)=TFR.
        # So RR sends BBR to TFR, not TBR.
        # What about r (R CCW)? r = R^3. (2,2,2)->R^3.
        # R: (2,2,2)->(2,0,2), R: (2,0,2)->(2,0,0), R: (2,0,0)->(2,2,0). So r sends BBR to BFR.
        # What about UR? or uR?
        # Let me just search programmatically.

        search = ["RuR", "RUR", "rUR", "ruR", "BuB", "BUB", "bUB", "buB",
                  "URu", "URU", "uRu", "uRU", "UBu", "UBU", "uBu", "uBU",
                  "RRU", "BBU", "RRu", "BBu",
                  "RRUU", "BBUU",
                  "URR", "UBB", "uRR", "uBB"]

        co0_setup = None
        for moves in search:
            program = [
                '5 SAFETY OFF',
                '10 PMODE 4: SCREEN 1',
                '20 MERGE "rubiks_engine"',
                '25 MERGE "rubiks_solver"',
                '30 GOSUB InitCube',
                '35 AN=0',
                '40 TC1=7: TC2=5: TC3=3',
                f'50 MS$="{moves}": GOSUB DoMoves',
                '60 GOSUB FindCorner',
                '70 PRINT CP;" ";CO',
                '100 END',
            ]
            results = load_and_run(emulator, program)
            texts = get_text(results)
            for t in texts:
                if 'SAFETY' in t or 'MERGED' in t or 'HARD CAP' in t:
                    continue
                parts = t.strip().split()
                if len(parts) == 2:
                    cp, co = int(parts[0]), int(parts[1])
                    if cp == 6 and co == 0:
                        co0_setup = moves
                        print(f"  Found CO=0 at TBR: setup='{moves}'")
                        break
            if co0_setup:
                break

        if not co0_setup:
            print("  Could not find CO=0 setup at TBR!")
        else:
            # Test InsertBBR with CO=0
            program = [
                '5 SAFETY OFF',
                '10 PMODE 4: SCREEN 1',
                '20 MERGE "rubiks_engine"',
                '25 MERGE "rubiks_solver"',
                '30 GOSUB InitCube',
                '35 AN=0',
                '40 TC1=7: TC2=5: TC3=3: CI=2',
                f'50 MS$="{co0_setup}": GOSUB DoMoves',
                '60 GOSUB FindCorner',
                '70 PRINT "BEFORE: CP=";CP;" CO=";CO',
                '80 GOSUB InsertBBR',
                '90 GOSUB FindCorner',
                '100 PRINT "AFTER: CP=";CP;" CO=";CO',
                '110 PRINT "BBR: F5=";CL(2,2,2,5);" F1=";CL(2,2,2,1);" F2=";CL(2,2,2,2)',
                '120 END',
            ]
            run_test(emulator, program)

        print()
        print("=" * 60)
        print("TEST C: VERIFY INSERT ALGORITHMS IN ISOLATION")
        print("=" * 60)

        # Test what Rur (R U' R') does to corner at TBR with each CO
        # Test what BUb (B U B') does to corner at TBR with each CO
        # Using R setup (CO=1) and B setup (CO=2)

        print("  --- Rur on CO=1 (setup R) ---")
        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "rubiks_engine"',
            '25 MERGE "rubiks_solver"',
            '30 GOSUB InitCube',
            '35 AN=0',
            '40 TC1=7: TC2=5: TC3=3',
            '50 MS$="R": GOSUB DoMoves',
            '60 GOSUB FindCorner',
            '70 PRINT "BEFORE: CP=";CP;" CO=";CO',
            '80 MS$="Rur": GOSUB DoMoves',
            '90 GOSUB FindCorner',
            '100 PRINT "AFTER Rur: CP=";CP;" CO=";CO',
            '110 END',
        ]
        run_test(emulator, program)

        print("  --- BUb on CO=1 (setup R) ---")
        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "rubiks_engine"',
            '25 MERGE "rubiks_solver"',
            '30 GOSUB InitCube',
            '35 AN=0',
            '40 TC1=7: TC2=5: TC3=3',
            '50 MS$="R": GOSUB DoMoves',
            '60 GOSUB FindCorner',
            '70 PRINT "BEFORE: CP=";CP;" CO=";CO',
            '80 MS$="BUb": GOSUB DoMoves',
            '90 GOSUB FindCorner',
            '100 PRINT "AFTER BUb: CP=";CP;" CO=";CO',
            '110 END',
        ]
        run_test(emulator, program)

        print("  --- Rur on CO=2 (setup B) ---")
        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "rubiks_engine"',
            '25 MERGE "rubiks_solver"',
            '30 GOSUB InitCube',
            '35 AN=0',
            '40 TC1=7: TC2=5: TC3=3',
            '50 MS$="B": GOSUB DoMoves',
            '60 GOSUB FindCorner',
            '70 PRINT "BEFORE: CP=";CP;" CO=";CO',
            '80 MS$="Rur": GOSUB DoMoves',
            '90 GOSUB FindCorner',
            '100 PRINT "AFTER Rur: CP=";CP;" CO=";CO',
            '110 END',
        ]
        run_test(emulator, program)

        print("  --- BUb on CO=2 (setup B) ---")
        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "rubiks_engine"',
            '25 MERGE "rubiks_solver"',
            '30 GOSUB InitCube',
            '35 AN=0',
            '40 TC1=7: TC2=5: TC3=3',
            '50 MS$="B": GOSUB DoMoves',
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
        print("TEST D: WHAT DOES InsertCorner DO? (it dispatches)")
        print("=" * 60)
        print("InsertBBR code:")
        print("  CO=1 -> BUb")
        print("  CO=2 or CO=0 -> Rur")
        print()
        print("From Test 5 results:")
        print("  Rur on CO=1: CP=2 CO=1 (WRONG - twisted!)")
        print("  BUb on CO=1: CP=2 CO=0 (correct)")
        print("  Rur on CO=2: CP=2 CO=0 (correct)")
        print("  BUb on CO=2: CP=2 CO=2 (WRONG - twisted!)")
        print()
        print("InsertBBR dispatches: CO=1->BUb (correct), CO=2->Rur (correct)")
        print("So InsertBBR gives correct results for CO=1 and CO=2.")
        print()
        print("The REAL question: what happens with CO=0?")
        print("InsertBBR for CO=0 uses Rur. Does that work?")

        print()
        print("=" * 60)
        print("TEST E: TRACE THE ACTUAL SOLVER ON 'R' SCRAMBLE")
        print("=" * 60)

        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "rubiks_engine"',
            '25 MERGE "rubiks_solver"',
            '30 GOSUB InitCube',
            '35 AN=0',
            # Scramble with just R - this moves BBR corner
            '40 MS$="R": GOSUB DoMoves',
            '45 TC1=7: TC2=5: TC3=3: CI=2',
            # Where is BBR corner now?
            '50 GOSUB FindCorner',
            '55 PRINT "AFTER R SCRAMBLE: CP=";CP;" CO=";CO',
            # Now do what SolveBotCorner does
            # CP=6 (top), so no extraction needed
            # AlignCornerTop: target is CI+4=6, corner already at CP=6
            '60 GOSUB AlignCornerTop',
            '65 GOSUB FindCorner',
            '70 PRINT "AFTER ALIGN: CP=";CP;" CO=";CO',
            # InsertCorner dispatches to InsertBBR
            '75 GOSUB InsertCorner',
            '80 GOSUB FindCorner',
            '85 PRINT "AFTER INSERT: CP=";CP;" CO=";CO',
            '90 IF CP=2 AND CO=0 THEN PRINT "SOLVED!"',
            '95 IF CP<>2 OR CO<>0 THEN PRINT "NOT SOLVED"',
            '100 END',
        ]
        run_test(emulator, program)

        print()
        print("=" * 60)
        print("TEST F: TRACE THE ACTUAL SOLVER ON 'B' SCRAMBLE")
        print("=" * 60)

        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "rubiks_engine"',
            '25 MERGE "rubiks_solver"',
            '30 GOSUB InitCube',
            '35 AN=0',
            '40 MS$="B": GOSUB DoMoves',
            '45 TC1=7: TC2=5: TC3=3: CI=2',
            '50 GOSUB FindCorner',
            '55 PRINT "AFTER B SCRAMBLE: CP=";CP;" CO=";CO',
            '60 GOSUB AlignCornerTop',
            '65 GOSUB FindCorner',
            '70 PRINT "AFTER ALIGN: CP=";CP;" CO=";CO',
            '75 GOSUB InsertCorner',
            '80 GOSUB FindCorner',
            '85 PRINT "AFTER INSERT: CP=";CP;" CO=";CO',
            '90 IF CP=2 AND CO=0 THEN PRINT "SOLVED!"',
            '95 IF CP<>2 OR CO<>0 THEN PRINT "NOT SOLVED"',
            '100 END',
        ]
        run_test(emulator, program)

        print()
        print("=" * 60)
        print("TEST G: WHAT HAPPENS WHEN BBR IS ALREADY IN PLACE")
        print("       WITH WRONG CO (TWISTED IN PLACE)?")
        print("=" * 60)

        # Simulate: do RUR'U' 3 times to twist BBR corner in place
        # Actually, the standard twist is: R U R' U' repeated - but that
        # doesn't twist a single corner. Let me try R U r u repeated.
        # Actually, let's just do: extract + insert with wrong algo to create twist
        # Start solved, extract BBR with BUb -> goes to TFR(CP=4)
        # Then manually apply Rur to put it back twisted

        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "rubiks_engine"',
            '25 MERGE "rubiks_solver"',
            '30 GOSUB InitCube',
            '35 AN=0',
            '40 TC1=7: TC2=5: TC3=3: CI=2',
            # Put BBR at TBR with a specific CO by doing R
            '50 MS$="R": GOSUB DoMoves',
            '55 GOSUB FindCorner: PRINT "AFTER R: CP=";CP;" CO=";CO',
            # Now manually apply Rur (wrong algo for CO=1)
            '60 MS$="Rur": GOSUB DoMoves',
            '65 GOSUB FindCorner: PRINT "AFTER Rur: CP=";CP;" CO=";CO',
            # It's at CP=2 CO=1 (twisted in place)
            # Now what does the solver do? It detects CP=2, CO!=0
            # It extracts: CP=2 -> ExtractCorner uses BUb
            '70 PRINT "--- SOLVER WOULD EXTRACT ---"',
            '75 MS$="BUb": GOSUB DoMoves',
            '80 GOSUB FindCorner: PRINT "AFTER EXTRACT: CP=";CP;" CO=";CO',
            '85 GOSUB AlignCornerTop',
            '90 GOSUB FindCorner: PRINT "AFTER ALIGN: CP=";CP;" CO=";CO',
            '95 GOSUB InsertBBR',
            '100 GOSUB FindCorner: PRINT "AFTER INSERT: CP=";CP;" CO=";CO',
            '105 IF CP=2 AND CO=0 THEN PRINT "SOLVED!"',
            '110 IF CP<>2 OR CO<>0 THEN PRINT "NOT SOLVED - WOULD LOOP"',
            '200 END',
        ]
        run_test(emulator, program)

        print()
        print("=" * 60)
        print("SUMMARY OF INSERT ALGORITHM TRUTH TABLE")
        print("=" * 60)
        print("At TBR (CP=6):")
        print("  CO=1 + BUb -> CP=2 CO=0 (CORRECT)")
        print("  CO=1 + Rur -> CP=2 CO=1 (WRONG)")
        print("  CO=2 + Rur -> CP=2 CO=0 (CORRECT)")
        print("  CO=2 + BUb -> CP=2 CO=2 (WRONG)")
        print()
        print("InsertBBR dispatches:")
        print("  CO=1 -> BUb (CORRECT)")
        print("  CO=2 -> Rur (CORRECT)")
        print("  CO=0 -> Rur (NEED TO VERIFY)")
        print()
        print("The issue might be in the EXTRACT+ALIGN cycle,")
        print("not in the INSERT algorithm itself.")

    finally:
        cleanup()


if __name__ == '__main__':
    run_diagnostic()
