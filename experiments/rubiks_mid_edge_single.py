"""
Test: apply a single insertion algorithm to a solved cube.
Check what it disrupts. A valid middle layer algorithm should only
disrupt the target slot and the top layer — all other middle edges
and the entire bottom layer should be preserved.
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


# Check strings
FR_CHK = 'CL(2,1,0,0)=4 AND CL(2,1,0,2)=3'
FL_CHK = 'CL(0,1,0,0)=4 AND CL(0,1,0,3)=6'
BR_CHK = 'CL(2,1,2,1)=5 AND CL(2,1,2,2)=3'
BL_CHK = 'CL(0,1,2,1)=5 AND CL(0,1,2,3)=6'
CROSS_CHK = ('CL(1,2,0,5)=7 AND CL(1,2,0,0)=4 AND '
              'CL(2,2,1,5)=7 AND CL(2,2,1,2)=3 AND '
              'CL(1,2,2,5)=7 AND CL(1,2,2,1)=5 AND '
              'CL(0,2,1,5)=7 AND CL(0,2,1,3)=6')
CORNERS_CHK = ('CL(2,2,0,5)=7 AND CL(0,2,0,5)=7 AND '
               'CL(2,2,2,5)=7 AND CL(0,2,2,5)=7')


def _check_all(basic, helpers, alg):
    out = _run(basic, helpers, [
        f'9000 MS$="{alg}": GOSUB DoMoves',
        f'9010 IF {FR_CHK} THEN PRINT "FR OK" ELSE PRINT "FR BAD"',
        f'9020 IF {FL_CHK} THEN PRINT "FL OK" ELSE PRINT "FL BAD"',
        f'9030 IF {BR_CHK} THEN PRINT "BR OK" ELSE PRINT "BR BAD"',
        f'9040 IF {BL_CHK} THEN PRINT "BL OK" ELSE PRINT "BL BAD"',
        f'9050 IF {CROSS_CHK} THEN PRINT "CROSS OK" ELSE PRINT "CROSS BAD"',
        f'9060 IF {CORNERS_CHK} THEN PRINT "CORNERS OK" ELSE PRINT "CORNERS BAD"',
        '9070 END',
    ])
    return [t.strip() for t in out if 'OK' in t or 'BAD' in t]


class TestSingleAlgorithmEffect:
    """Apply each algorithm once to a solved cube."""

    def test_all_algorithms(self, basic, helpers):
        """Test every middle edge algorithm."""
        algs = [
            ("FR EP=4: URurufUF", "URurufUF"),
            ("FR EP=5: ufUFURur", "ufUFURur"),
            ("FL EP=4: ulULUFuf", "ulULUFuf"),
            ("FL EP=7: UFufulUL", "UFufulUL"),
            ("BR EP=5: URurubUB", "URurubUB"),
            ("BR EP=6: urURUBub", "urURUBub"),
            ("BL EP=7: ulULUBub", "ulULUBub"),
            ("BL EP=6: ubUBULul", "ubUBULul"),
            # Also test the reference standard right/left insert
            # Standard right (U R U' R' U' F' U F) → engine: uRUrUfuF
            ("STD right→engine: uRUrUfuF", "uRUrUfuF"),
            # Standard left (U' L' U L U F U' F') → engine: UlUluFUf
            ("STD left→engine:  UluLuFUf", "UluLuFUf"),
        ]
        for name, alg in algs:
            result = _check_all(basic, helpers, alg)
            disrupted = [r for r in result if 'BAD' in r]
            preserved = [r for r in result if 'OK' in r]
            print(f"  {name:40s}: preserved={preserved} disrupted={disrupted}")

    def test_reference_alg_effect(self, basic, helpers):
        """The reference algorithms converted to engine notation.
        Standard U = our u, Standard U' = our U.

        Right-insert: U R U' R' U' F' U F → u R U r U f u F = uRUrUfuF
        Left-insert:  U' L' U L U F U' F' → U l u L u F U f = UluLuFUf

        These should only disrupt FR (right-insert inserts into FR from EP=4)
        and FL (left-insert inserts into FL from EP=4).
        """
        # Right-insert from front
        out = _run(basic, helpers, [
            '9000 MS$="uRUrUfuF": GOSUB DoMoves',
            f'9010 IF {FR_CHK} THEN PRINT "FR OK" ELSE PRINT "FR BAD:";CL(2,1,0,0);CL(2,1,0,2)',
            f'9020 IF {FL_CHK} THEN PRINT "FL OK" ELSE PRINT "FL BAD:";CL(0,1,0,0);CL(0,1,0,3)',
            f'9030 IF {BR_CHK} THEN PRINT "BR OK" ELSE PRINT "BR BAD:";CL(2,1,2,1);CL(2,1,2,2)',
            f'9040 IF {BL_CHK} THEN PRINT "BL OK" ELSE PRINT "BL BAD:";CL(0,1,2,1);CL(0,1,2,3)',
            f'9050 IF {CROSS_CHK} THEN PRINT "CROSS OK" ELSE PRINT "CROSS BAD"',
            f'9060 IF {CORNERS_CHK} THEN PRINT "CORNERS OK" ELSE PRINT "CORNERS BAD"',
            '9070 END',
        ])
        print("\nStandard right-insert (uRUrUfuF):")
        for t in [x for x in out if 'OK' in x or 'BAD' in x]:
            print(f"  {t.strip()}")

    def test_our_FR_ep4_effect(self, basic, helpers):
        """Our current FR EP=4 algorithm: URurufUF
        Applied to solved cube — what exactly does it disrupt?"""
        out = _run(basic, helpers, [
            '9000 MS$="URurufUF": GOSUB DoMoves',
            # Check all edges and corners in detail
            '9010 PRINT "FR:";CL(2,1,0,0);CL(2,1,0,2)',
            '9020 PRINT "FL:";CL(0,1,0,0);CL(0,1,0,3)',
            '9030 PRINT "BR:";CL(2,1,2,1);CL(2,1,2,2)',
            '9040 PRINT "BL:";CL(0,1,2,1);CL(0,1,2,3)',
            '9050 PRINT "CROSS BOT F:";CL(1,2,0,5);CL(1,2,0,0)',
            '9055 PRINT "CROSS BOT R:";CL(2,2,1,5);CL(2,2,1,2)',
            '9058 PRINT "CROSS BOT B:";CL(1,2,2,5);CL(1,2,2,1)',
            '9059 PRINT "CROSS BOT L:";CL(0,2,1,5);CL(0,2,1,3)',
            '9060 END',
        ])
        for t in out:
            if any(x in t for x in ['FR:', 'FL:', 'BR:', 'BL:', 'CROSS']):
                print(f"  {t.strip()}")
