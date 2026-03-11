"""
Test whether middle edge insertion algorithms preserve other middle edges.
Start from solved cube, extract one edge, reinsert, check all 4 slots.
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


def _run(basic, helpers, lines, max_frames=20000):
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


# Check strings for each middle slot
FR_CHECK = 'CL(2,1,0,0)=4 AND CL(2,1,0,2)=3'
FL_CHECK = 'CL(0,1,0,0)=4 AND CL(0,1,0,3)=6'
BR_CHECK = 'CL(2,1,2,1)=5 AND CL(2,1,2,2)=3'
BL_CHECK = 'CL(0,1,2,1)=5 AND CL(0,1,2,3)=6'
CROSS_CHECK = ('CL(1,2,0,5)=7 AND CL(1,2,0,0)=4 AND '
               'CL(2,2,1,5)=7 AND CL(2,2,1,2)=3 AND '
               'CL(1,2,2,5)=7 AND CL(1,2,2,1)=5 AND '
               'CL(0,2,1,5)=7 AND CL(0,2,1,3)=6')


class TestAlgorithmPreservation:
    """Test that each insertion algorithm preserves the bottom + other middle edges."""

    def _test_alg(self, basic, helpers, extract_moves, alg_moves, alg_name):
        """Extract an edge with extract_moves, reinsert with alg_moves, check everything."""
        out = _run(basic, helpers, [
            # Extract edge to top
            f'9000 MS$="{extract_moves}": GOSUB DoMoves',
            # Apply insertion algorithm
            f'9010 MS$="{alg_moves}": GOSUB DoMoves',
            # Check all 4 middle edges
            f'9020 IF {FR_CHECK} THEN PRINT "FR OK" ELSE PRINT "FR BAD"',
            f'9030 IF {FL_CHECK} THEN PRINT "FL OK" ELSE PRINT "FL BAD"',
            f'9040 IF {BR_CHECK} THEN PRINT "BR OK" ELSE PRINT "BR BAD"',
            f'9050 IF {BL_CHECK} THEN PRINT "BL OK" ELSE PRINT "BL BAD"',
            f'9060 IF {CROSS_CHECK} THEN PRINT "CROSS OK" ELSE PRINT "CROSS BAD"',
            '9070 END',
        ])
        result = {t.strip() for t in out if 'OK' in t or 'BAD' in t}
        return result

    def test_FR_ep4_preservation(self, basic, helpers):
        """FR insert from EP=4: extract FR to top with URurufUF reverse, then reinsert."""
        # Extract FR to front-top: the reverse of insertion
        # Actually just use the extraction algorithm
        result = self._test_alg(basic, helpers, "URurufUF", "URurufUF", "FR EP=4")
        print(result)

    def test_all_current_algorithms(self, basic, helpers):
        """Test each insertion algorithm from a solved cube.
        Extract the target edge, align to correct position, reinsert."""
        # For each slot: extract to top, align, insert, check
        tests = [
            # (name, extract_seq, align, insert_alg, target_slot)
            # FR EP=4: extract FR, edge goes to top, align to EP=4, insert
            ("FR EP=4", "URurufUF", "", "URurufUF"),
            ("FR EP=5", "ufUFURur", "", "ufUFURur"),
            # FL EP=4: extract FL
            ("FL EP=4", "ulULUFuf", "", "ulULUFuf"),
            ("FL EP=7", "UFufulUL", "", "UFufulUL"),
            # BR EP=5: extract BR
            ("BR EP=5", "URurubUB", "", "URurubUB"),
            ("BR EP=6", "urURUBub", "", "urURUBub"),
            # BL EP=7: extract BL
            ("BL EP=7", "ulULUBub", "", "ulULUBub"),
            ("BL EP=6", "ubUBULul", "", "ubUBULul"),
        ]

        for name, extract, align, insert in tests:
            out = _run(basic, helpers, [
                f'9000 MS$="{extract}": GOSUB DoMoves',
                f'9005 MS$="{align}": GOSUB DoMoves' if align else '9005 REM no align',
                f'9010 MS$="{insert}": GOSUB DoMoves',
                f'9020 IF {FR_CHECK} THEN PRINT "FR OK" ELSE PRINT "FR BAD:";CL(2,1,0,0);CL(2,1,0,2)',
                f'9030 IF {FL_CHECK} THEN PRINT "FL OK" ELSE PRINT "FL BAD:";CL(0,1,0,0);CL(0,1,0,3)',
                f'9040 IF {BR_CHECK} THEN PRINT "BR OK" ELSE PRINT "BR BAD:";CL(2,1,2,1);CL(2,1,2,2)',
                f'9050 IF {BL_CHECK} THEN PRINT "BL OK" ELSE PRINT "BL BAD:";CL(0,1,2,1);CL(0,1,2,3)',
                f'9060 IF {CROSS_CHECK} THEN PRINT "CROSS OK" ELSE PRINT "CROSS BAD"',
                '9070 END',
            ])
            results = [t.strip() for t in out if 'OK' in t or 'BAD' in t]
            ok = all('OK' in r for r in results)
            print(f"  {name:10s}: {'PASS' if ok else 'FAIL'} — {results}")

    def test_cross_algorithm_pairs(self, basic, helpers):
        """For each slot, verify extract+insert is identity (restores all)."""
        pairs = [
            ("FR", "URurufUF", "ufUFURur"),
            ("FL", "ulULUFuf", "UFufulUL"),
            ("BR", "URurubUB", "urURUBub"),
            ("BL", "ulULUBub", "ubUBULul"),
        ]
        for name, alg1, alg2 in pairs:
            out = _run(basic, helpers, [
                f'9000 MS$="{alg1}": GOSUB DoMoves',
                f'9010 MS$="{alg2}": GOSUB DoMoves',
                f'9020 IF {FR_CHECK} THEN PRINT "FR OK" ELSE PRINT "FR BAD:";CL(2,1,0,0);CL(2,1,0,2)',
                f'9030 IF {FL_CHECK} THEN PRINT "FL OK" ELSE PRINT "FL BAD:";CL(0,1,0,0);CL(0,1,0,3)',
                f'9040 IF {BR_CHECK} THEN PRINT "BR OK" ELSE PRINT "BR BAD:";CL(2,1,2,1);CL(2,1,2,2)',
                f'9050 IF {BL_CHECK} THEN PRINT "BL OK" ELSE PRINT "BL BAD:";CL(0,1,2,1);CL(0,1,2,3)',
                f'9060 IF {CROSS_CHECK} THEN PRINT "CROSS OK" ELSE PRINT "CROSS BAD"',
                '9070 END',
            ])
            results = [t.strip() for t in out if 'OK' in t or 'BAD' in t]
            ok = all('OK' in r for r in results)
            print(f"  {name}: extract+insert = {'IDENTITY' if ok else 'NOT IDENTITY'} — {results}")
