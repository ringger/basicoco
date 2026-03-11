"""
Trace what happens to bottom corners through the standard right-insert algorithm.
Applied to a solved cube, track all 4 bottom corners through each move.
"""

import os
import shutil
import pytest


@pytest.fixture(autouse=True)
def setup_engine(temp_programs_dir):
    programs_dir = os.path.join(os.path.dirname(__file__), '..', 'programs')
    for fname in ('lib_rubiks_engine.bas', 'lib_rubiks_solver.bas'):
        src = os.path.abspath(os.path.join(programs_dir, fname))
        shutil.copy(src, os.path.join(temp_programs_dir, fname))


def _run(basic, helpers, lines, max_frames=10000):
    program = [
        '5 SAFETY OFF',
        '10 PMODE 4: SCREEN 1',
        '20 MERGE "lib_rubiks_engine"',
        '25 MERGE "lib_rubiks_solver"',
        '30 GOSUB InitCube',
        '35 AN=0',
    ] + lines
    helpers.load_program(basic, program)
    results = helpers.run_to_completion(basic, max_frames=max_frames)
    errors = helpers.get_error_messages(results)
    assert errors == [], f"Errors: {errors}"
    return helpers.get_text_output(results)


class TestCornerTrace:

    def test_standard_right_insert_step_by_step(self, basic, helpers):
        """Apply urURUfuF one move at a time, print bottom corners after each."""
        moves = list("urURUfuF")
        lines = [
            '9000 PRINT "INIT:"',
            '9001 PRINT "BFR:";CL(2,2,0,5);CL(2,2,0,0);CL(2,2,0,2)',
            '9002 PRINT "BFL:";CL(0,2,0,5);CL(0,2,0,0);CL(0,2,0,3)',
            '9003 PRINT "BBR:";CL(2,2,2,5);CL(2,2,2,1);CL(2,2,2,2)',
            '9004 PRINT "BBL:";CL(0,2,2,5);CL(0,2,2,1);CL(0,2,2,3)',
        ]
        line_num = 9010
        for i, m in enumerate(moves):
            lines.append(f'{line_num} MS$="{m}": GOSUB DoMoves')
            line_num += 1
            lines.append(f'{line_num} PRINT "AFTER {m} (move {i+1}):"')
            line_num += 1
            lines.append(f'{line_num} PRINT "BFR:";CL(2,2,0,5);CL(2,2,0,0);CL(2,2,0,2)')
            line_num += 1
            lines.append(f'{line_num} PRINT "BFL:";CL(0,2,0,5);CL(0,2,0,0);CL(0,2,0,3)')
            line_num += 1
            lines.append(f'{line_num} PRINT "BBR:";CL(2,2,2,5);CL(2,2,2,1);CL(2,2,2,2)')
            line_num += 1
            lines.append(f'{line_num} PRINT "BBL:";CL(0,2,2,5);CL(0,2,2,1);CL(0,2,2,3)')
            line_num += 1
        lines.append(f'{line_num} END')
        out = _run(basic, helpers, lines)
        for t in out:
            if any(x in t for x in ['INIT', 'AFTER', 'BFR', 'BFL', 'BBR', 'BBL']):
                print(t)

    def test_what_standard_algorithm_means(self, basic, helpers):
        """The standard right-insert is U R U' R' U' F' U F.
        In our engine, U/R/L are reversed. So:
        Standard U = engine u, Standard R = engine r, etc.

        But wait - maybe R is NOT reversed. Let me test:
        On a solved cube, do engine R and check where the BFR corner went.
        Standard R CW should move BFR to TFR (top-front-right).
        """
        out = _run(basic, helpers, [
            '9000 PRINT "BEFORE R:"',
            '9001 PRINT "BFR:";CL(2,2,0,5);CL(2,2,0,0);CL(2,2,0,2)',
            '9002 PRINT "TFR:";CL(2,0,0,4);CL(2,0,0,0);CL(2,0,0,2)',
            '9010 MS$="R": GOSUB DoMoves',
            '9011 PRINT "AFTER R:"',
            '9012 PRINT "BFR:";CL(2,2,0,5);CL(2,2,0,0);CL(2,2,0,2)',
            '9013 PRINT "TFR:";CL(2,0,0,4);CL(2,0,0,0);CL(2,0,0,2)',
            '9014 PRINT "BBR:";CL(2,2,2,5);CL(2,2,2,1);CL(2,2,2,2)',
            '9015 PRINT "TBR:";CL(2,0,2,4);CL(2,0,2,1);CL(2,0,2,2)',
            '9020 END',
        ])
        for t in out:
            if 'BEFORE' in t or 'AFTER' in t or 'BFR' in t or 'TFR' in t or 'BBR' in t or 'TBR' in t:
                print(t)

    def test_R_direction(self, basic, helpers):
        """Determine: does engine R move BFR up-front or up-back?
        Standard R CW (from right): moves BFR to TFR
        Standard R CCW (from right): moves BFR to BBR
        """
        # Init: BFR has colors (5=bottom, 0=front, 2=right) = (7, 4, 3)
        out = _run(basic, helpers, [
            '9000 PRINT "BFR colors: bottom=";CL(2,2,0,5);" front=";CL(2,2,0,0);" right=";CL(2,2,0,2)',
            '9010 MS$="R": GOSUB DoMoves',
            '9020 PRINT "After R CW:"',
            '9021 PRINT "TFR top=";CL(2,0,0,4);" front=";CL(2,0,0,0);" right=";CL(2,0,0,2)',
            '9022 PRINT "BBR bottom=";CL(2,2,2,5);" back=";CL(2,2,2,1);" right=";CL(2,2,2,2)',
            '9023 PRINT "TBR top=";CL(2,0,2,4);" back=";CL(2,0,2,1);" right=";CL(2,0,2,2)',
            '9024 PRINT "BFR bottom=";CL(2,2,0,5);" front=";CL(2,2,0,0);" right=";CL(2,2,0,2)',
            '9030 END',
        ])
        for t in out:
            print(t)
