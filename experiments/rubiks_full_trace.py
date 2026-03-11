"""
Full corner trace through the standard right-insert algorithm.
Track ALL 8 corners through each move.
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


class TestFullTrace:

    def test_setup_4move_and_teardown_4move(self, basic, helpers):
        """Test that urUR (standard U R U' R') restores bottom right corners."""
        out = _run(basic, helpers, [
            '9000 PRINT "AFTER urUR (std U R U\' R\'):"',
            '9001 MS$="urUR": GOSUB DoMoves',
            '9002 PRINT "BFR:";CL(2,2,0,5);CL(2,2,0,0);CL(2,2,0,2)',
            '9003 PRINT "BBR:";CL(2,2,2,5);CL(2,2,2,1);CL(2,2,2,2)',
            '9004 PRINT "BFL:";CL(0,2,0,5);CL(0,2,0,0);CL(0,2,0,3)',
            '9005 PRINT "BBL:";CL(0,2,2,5);CL(0,2,2,1);CL(0,2,2,3)',
            '9010 PRINT ""',
            '9011 PRINT "AFTER UfuF (std U\' F\' U F):"',
            '9012 MS$="UfuF": GOSUB DoMoves',
            '9013 PRINT "BFR:";CL(2,2,0,5);CL(2,2,0,0);CL(2,2,0,2)',
            '9014 PRINT "BBR:";CL(2,2,2,5);CL(2,2,2,1);CL(2,2,2,2)',
            '9015 PRINT "BFL:";CL(0,2,0,5);CL(0,2,0,0);CL(0,2,0,3)',
            '9016 PRINT "BBL:";CL(0,2,2,5);CL(0,2,2,1);CL(0,2,2,3)',
            '9020 END',
        ])
        for t in out:
            print(t)

    def test_standard_alg_direct(self, basic, helpers):
        """Just apply the standard F2L right algorithm in engine notation
        and check if bottom layer is preserved."""
        # Standard: U R U' R' U' F' U F = engine: urURUfuF
        out = _run(basic, helpers, [
            '9000 MS$="urURUfuF": GOSUB DoMoves',
            '9001 PRINT "BFR:";CL(2,2,0,5);CL(2,2,0,0);CL(2,2,0,2)',
            '9002 PRINT "BFL:";CL(0,2,0,5);CL(0,2,0,0);CL(0,2,0,3)',
            '9003 PRINT "BBR:";CL(2,2,2,5);CL(2,2,2,1);CL(2,2,2,2)',
            '9004 PRINT "BBL:";CL(0,2,2,5);CL(0,2,2,1);CL(0,2,2,3)',
            '9005 PRINT "CROSS F:";CL(1,2,0,5);CL(1,2,0,0)',
            '9006 PRINT "CROSS R:";CL(2,2,1,5);CL(2,2,1,2)',
            '9007 PRINT "CROSS B:";CL(1,2,2,5);CL(1,2,2,1)',
            '9008 PRINT "CROSS L:";CL(0,2,1,5);CL(0,2,1,3)',
            '9020 END',
        ])
        print("\n=== Standard right-insert (urURUfuF) ===")
        for t in out:
            print(t)

    def test_try_reversed_conversion(self, basic, helpers):
        """What if the conversion is the OPPOSITE?
        Maybe standard U = engine U (not u)?
        Standard: U R U' R' U' F' U F
        If U=U, R=R: URurufUF (our current FR EP=4 algorithm!)
        """
        out = _run(basic, helpers, [
            '9000 MS$="URurufUF": GOSUB DoMoves',
            '9001 PRINT "BFR:";CL(2,2,0,5);CL(2,2,0,0);CL(2,2,0,2)',
            '9002 PRINT "BFL:";CL(0,2,0,5);CL(0,2,0,0);CL(0,2,0,3)',
            '9003 PRINT "BBR:";CL(2,2,2,5);CL(2,2,2,1);CL(2,2,2,2)',
            '9004 PRINT "BBL:";CL(0,2,2,5);CL(0,2,2,1);CL(0,2,2,3)',
            '9005 PRINT "CROSS F:";CL(1,2,0,5);CL(1,2,0,0)',
            '9006 PRINT "CROSS R:";CL(2,2,1,5);CL(2,2,1,2)',
            '9007 PRINT "CROSS B:";CL(1,2,2,5);CL(1,2,2,1)',
            '9008 PRINT "CROSS L:";CL(0,2,1,5);CL(0,2,1,3)',
            '9020 END',
        ])
        print("\n=== Current FR EP=4 (URurufUF) ===")
        for t in out:
            print(t)

    def test_mixed_conversion(self, basic, helpers):
        """Since F matches standard but U and R don't,
        what if we only swap U (not R)?
        Standard: U R U' R' U' F' U F
        swap U only: u R U r U f u F = uRUrUfuF (different from both above)

        Or swap R only: U r U' R U' F' U F = UrURUfuF? Not valid either.

        Let me try all 4 combos of swapping/not-swapping U and R.
        """
        combos = [
            ("U=U, R=R", "URurufUF"),  # our current
            ("U=u, R=r", "urURUfuF"),  # full swap
            ("U=u, R=R", "uRUrUfuF"),  # swap U only
            ("U=U, R=r", "UrURufUF"),  # swap R only
        ]
        for label, alg in combos:
            out = _run(basic, helpers, [
                f'9000 MS$="{alg}": GOSUB DoMoves',
                '9001 PRINT "BFR:";CL(2,2,0,5);CL(2,2,0,0);CL(2,2,0,2)',
                '9002 PRINT "BFL:";CL(0,2,0,5);CL(0,2,0,0);CL(0,2,0,3)',
                '9003 PRINT "BBR:";CL(2,2,2,5);CL(2,2,2,1);CL(2,2,2,2)',
                '9004 PRINT "BBL:";CL(0,2,2,5);CL(0,2,2,1);CL(0,2,2,3)',
                '9005 PRINT "CROSS F:";CL(1,2,0,5);CL(1,2,0,0)',
                '9006 PRINT "CROSS R:";CL(2,2,1,5);CL(2,2,1,2)',
                '9007 PRINT "CROSS B:";CL(1,2,2,5);CL(1,2,2,1)',
                '9008 PRINT "CROSS L:";CL(0,2,1,5);CL(0,2,1,3)',
                '9020 END',
            ])
            corners_ok = all(
                any(f'{c}: 7' in t for t in out)
                for c in ['BFR', 'BFL', 'BBR', 'BBL']
            )
            cross_ok = all(
                any(f'CROSS {c}: 7' in t for t in out)
                for c in ['F', 'R', 'B', 'L']
            )
            print(f"  {label:20s} ({alg:8s}): corners={'OK' if corners_ok else 'BAD'}, cross={'OK' if cross_ok else 'BAD'}")
            if not corners_ok or not cross_ok:
                for t in out:
                    if 'BFR' in t or 'CROSS' in t:
                        print(f"    {t}")
