"""
Test properly converted standard algorithms.

Engine face directions vs standard:
- F, B, D: match standard CW
- U, R, L: REVERSED (engine CW = standard CCW)

Conversion rule: swap case for U, R, L; keep case for F, B, D.

Standard right-insert (FR, edge on front): U R U' R' U' F' U F → engine: urURUfuF
Standard left-insert (FL, edge on front):  U' L' U L U F U' F' → engine: ULuluFUf

For other slots, apply face substitution THEN convert.
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


def _test_alg(basic, helpers, alg, label):
    """Apply algorithm to solved cube, report what's preserved."""
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
    preserved = [t.strip() for t in out if 'OK' in t]
    disrupted = [t.strip() for t in out if 'BAD' in t]
    print(f"  {label:45s} ({alg:8s}): preserved={preserved} disrupted={disrupted}")
    return preserved, disrupted


class TestCorrectAlgorithms:
    """Test properly converted standard algorithms."""

    def test_fr_algorithms(self, basic, helpers):
        """FR slot algorithms.
        Standard right-insert: U R U' R' U' F' U F → engine: urURUfuF
        For EP=5 case: U' F' U F U R U' R' → engine: Uf uF ur UR → UfuFuRUr... wait
        Let me just systematically derive:
        Standard FR case 2 (edge on right, insert to front): U' F' U F U R U' R'
        Engine: Swap U,R: UfuFuRUr... hmm

        Actually, the second FR algorithm is the mirror. From right face perspective:
        Standard: U' R' U R U F U' F' → swap case of U,R: URuruFUf
        """
        print("\n=== FR algorithms ===")
        # Standard right-insert converted: urURUfuF
        _test_alg(basic, helpers, "urURUfuF", "STD right-insert→engine")
        # Standard left-insert for FR from right: reverse
        _test_alg(basic, helpers, "UfuFuRUr", "STD FR-from-right→engine")
        # Our current working FR algorithms
        _test_alg(basic, helpers, "URurufUF", "Current FR EP=4")
        _test_alg(basic, helpers, "ufUFURur", "Current FR EP=5")

    def test_fl_algorithms(self, basic, helpers):
        """FL slot algorithms.
        Standard left-insert: U' L' U L U F U' F' → engine: ULuluFUf
        Standard FL case 2: U F U' F' U' L' U L → engine: uFUfULul
        """
        print("\n=== FL algorithms ===")
        _test_alg(basic, helpers, "ULuluFUf", "STD left-insert→engine")
        _test_alg(basic, helpers, "uFUfULul", "STD FL-from-left→engine")
        _test_alg(basic, helpers, "ulULUFuf", "Current FL EP=4")
        _test_alg(basic, helpers, "UFufulUL", "Current FL EP=7")

    def test_br_algorithms(self, basic, helpers):
        """BR slot algorithms.
        Derive from FR by face substitution F→B (CW around vertical):
        Standard BR right (edge on back): U R U' R' U' B' U B → engine: urURUBuB
        Wait, but B keeps its case (engine B = standard B).
        Standard: U R U' R' U' B' U B
        Engine: u r U R U b u B = urURUbuB

        Standard BR case 2 (edge on right): U' B' U B U R U' R'
        Engine: U b u B u r U R... hmm wait
        Standard: U' B' U B U R U' R' → engine: UbuBuRUr... swap U,R not B:
        U' → U, B' → b, U → u, B → B, U → u, R → r... wait

        Let me be very careful.
        Standard: U' B' U B U R U' R'
        Convert each:
        U' → U (swap U case)
        B' → b (B keeps case)
        U → u (swap U case)
        B → B (B keeps case)
        U → u (swap U case)
        R → r (swap R case)
        U' → U (swap U case)
        R' → R (swap R case)
        Result: UbuBurUR
        """
        print("\n=== BR algorithms ===")
        # Standard BR right (from back): U R U' R' U' B' U B → engine
        # U→u, R→r, U'→U, R'→R, U'→U, B'→b, U→u, B→B
        _test_alg(basic, helpers, "urURUbuB", "STD BR-from-back→engine")
        # Standard BR case 2 (from right): U' B' U B U R U' R'
        # U'→U, B'→b, U→u, B→B, U→u, R→r, U'→U, R'→R
        _test_alg(basic, helpers, "UbuBurUR", "STD BR-from-right→engine")
        # Current algorithms
        _test_alg(basic, helpers, "URurubUB", "Current BR EP=5")
        _test_alg(basic, helpers, "urURUBub", "Current BR EP=6")

    def test_bl_algorithms(self, basic, helpers):
        """BL slot algorithms.
        Derive from FL by face substitution F→B:
        Standard BL left (from back): U' L' U L U B U' B'
        Convert: U'→U, L'→L, U→u, L→l, U→u, B→B, U'→U, B'→b
        Result: ULulUBub... wait that's wrong, let me redo:
        U'→U, L'→L, U→u, L→l, U→u, B→B, U'→U, B'→b = ULuluBUb

        Standard BL case 2 (from left): U B U' B' U' L' U L
        Convert: U→u, B→B, U'→U, B'→b, U'→U, L'→L, U→u, L→l
        Result: uBUbULul
        """
        print("\n=== BL algorithms ===")
        _test_alg(basic, helpers, "ULuluBUb", "STD BL-from-back→engine")
        _test_alg(basic, helpers, "uBUbULul", "STD BL-from-left→engine")
        # Current algorithms
        _test_alg(basic, helpers, "ulULUBub", "Current BL EP=7")
        _test_alg(basic, helpers, "ubUBULul", "Current BL EP=6")
