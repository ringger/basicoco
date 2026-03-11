"""
Test standard F2L algorithms in the new engine (which matches standard notation).

Standard algorithms from reference doc:
- Right-insert (FR): U R U' R' U' F' U F
- Left-insert (FL):  U' L' U L U F U' F'

Other slots derived by rotation:
- BR right (side on R, EP=5): U B U' B' U' R' U R
- BR left  (side on B, EP=6): U' R' U R U B U' B'
- BL right (side on L, EP=7): U' B' U B U L U' L'  (mirror of BR)
- BL left  (side on B, EP=6): U L U' L' U' B' U B  (mirror of BR)
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


BOTTOM_CHECK = (
    'CL(1,2,0,5)=7 AND CL(1,2,0,0)=4 AND '
    'CL(2,2,1,5)=7 AND CL(2,2,1,2)=3 AND '
    'CL(1,2,2,5)=7 AND CL(1,2,2,1)=5 AND '
    'CL(0,2,1,5)=7 AND CL(0,2,1,3)=6 AND '
    'CL(2,2,0,5)=7 AND CL(2,2,0,0)=4 AND CL(2,2,0,2)=3 AND '
    'CL(0,2,0,5)=7 AND CL(0,2,0,0)=4 AND CL(0,2,0,3)=6 AND '
    'CL(2,2,2,5)=7 AND CL(2,2,2,1)=5 AND CL(2,2,2,2)=3 AND '
    'CL(0,2,2,5)=7 AND CL(0,2,2,1)=5 AND CL(0,2,2,3)=6'
)


class TestStandardAlgs:
    """Test standard F2L algorithms directly in the new engine."""

    @pytest.mark.slow
    def test_all_standard_algs(self, basic, helpers):
        """Extract each edge, align, apply standard algorithm, verify."""
        # Standard algorithms in new engine notation (engine = standard):
        # FR EP=4: U R U' R' U' F' U F = URurufUF
        # FR EP=5: U' F' U F U R U' R' = ufUFURur
        # FL EP=4: U' L' U L U F U' F' = ulULUFuf
        # FL EP=7: U F U' F' U' L' U L = UFufuluL
        # BR EP=5: U B U' B' U' R' U R = UBuburUR
        # BR EP=6: U' R' U R U B U' B' = urURUBub
        # BL EP=7: U' B' U B U L U' L' = ubUBULul
        # BL EP=6: U L U' L' U' B' U B = ULulubuB

        # For extraction, we can use the same algorithm (it's self-inverse for insertion/extraction)
        # Actually, extraction = applying one of the slot's algorithms to a solved edge

        tests = [
            # (name, tc1, tc2, ei, target_ep, extract_alg, insert_ep, insert_alg)
            ("FR-4", 4, 3, 0, 8, "URurufUF", 4, "URurufUF"),
            ("FR-5", 4, 3, 0, 8, "ufUFURur", 5, "ufUFURur"),
            ("FL-4", 4, 6, 1, 9, "ulULUFuf", 4, "ulULUFuf"),
            ("FL-7", 4, 6, 1, 9, "UFufuluL", 7, "UFufuluL"),
            ("BR-5", 5, 3, 2, 10, "UBuburUR", 5, "UBuburUR"),
            ("BR-6", 5, 3, 2, 10, "urURUBub", 6, "urURUBub"),
            ("BL-7", 5, 6, 3, 11, "ubUBULul", 7, "ubUBULul"),
            ("BL-6", 5, 6, 3, 11, "ULulubuB", 6, "ULulubuB"),
        ]

        for name, tc1, tc2, ei, target_ep, extract, insert_ep, insert in tests:
            out = _run(basic, helpers, [
                # Extract edge from solved cube
                f'40 MS$="{extract}": GOSUB DoMoves',
                f'50 TC1={tc1}: TC2={tc2}: GOSUB FindEdge',
                '55 PRINT "EXT: EP=";EP;" EO=";EO',
                # Align
                f'60 EI={ei}: GOSUB AlignMidEdge',
                f'65 TC1={tc1}: TC2={tc2}: GOSUB FindEdge',
                '70 PRINT "ALN: EP=";EP;" EO=";EO',
                # Insert
                f'75 MS$="{insert}": GOSUB DoMoves',
                f'80 TC1={tc1}: TC2={tc2}: GOSUB FindEdge',
                '85 PRINT "INS: EP=";EP;" EO=";EO',
                f'90 IF EP={target_ep} AND EO=0 THEN PRINT "OK" ELSE PRINT "FAIL"',
                f'95 IF {BOTTOM_CHECK} THEN PRINT "BOT OK" ELSE PRINT "BOT FAIL"',
                '100 END',
            ])
            ep_lines = [t.strip() for t in out if 'EP=' in t or t.strip() in ('OK','FAIL','BOT OK','BOT FAIL')]
            ok = any(t.strip() == 'OK' for t in out)
            bot = any('BOT OK' in t for t in out)
            print(f"  {name:6s}: {'PASS' if ok and bot else 'FAIL':4s} | {' | '.join(ep_lines)}")
