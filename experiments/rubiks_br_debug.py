"""
Debug BR insertion after Permute fix.
Extract BR edge, align, insert, check result.
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


class TestBRInsertion:
    """Test both BR insertion algorithms directly."""

    @pytest.mark.slow
    def test_br_alg1_ep5(self, basic, helpers):
        """BR alg1: side on right (EP=5), insert toward back."""
        # Extract BR edge from solved cube, align, insert
        out = _run(basic, helpers, [
            # Extract BR edge (EP=10) to top
            '40 MS$="uBUbUruR": GOSUB DoMoves',
            '50 TC1=5: TC2=3: GOSUB FindEdge',
            '55 PRINT "EXTRACTED: EP=";EP;" EO=";EO',
            # Align
            '60 EI=2: GOSUB AlignMidEdge',
            '65 TC1=5: TC2=3: GOSUB FindEdge',
            '70 PRINT "ALIGNED: EP=";EP;" EO=";EO',
            # Insert using alg1 (EP=5 case)
            '75 IF EP=5 THEN MS$="uBUbUruR": GOSUB DoMoves',
            '76 IF EP=6 THEN MS$="UruRuBUb": GOSUB DoMoves',
            '80 TC1=5: TC2=3: GOSUB FindEdge',
            '85 PRINT "INSERTED: EP=";EP;" EO=";EO',
            '90 IF EP=10 AND EO=0 THEN PRINT "INSERT OK" ELSE PRINT "INSERT FAIL"',
            '100 END',
        ])
        for t in out:
            if 'EP=' in t or 'OK' in t or 'FAIL' in t:
                print(f"  {t.strip()}")

    @pytest.mark.slow
    def test_br_alg2_ep6(self, basic, helpers):
        """BR alg2: side on back (EP=6), insert toward right."""
        # Extract BR edge using the other algorithm to get different EO
        out = _run(basic, helpers, [
            '40 MS$="UruRuBUb": GOSUB DoMoves',
            '50 TC1=5: TC2=3: GOSUB FindEdge',
            '55 PRINT "EXTRACTED: EP=";EP;" EO=";EO',
            '60 EI=2: GOSUB AlignMidEdge',
            '65 TC1=5: TC2=3: GOSUB FindEdge',
            '70 PRINT "ALIGNED: EP=";EP;" EO=";EO',
            '75 IF EP=5 THEN MS$="uBUbUruR": GOSUB DoMoves',
            '76 IF EP=6 THEN MS$="UruRuBUb": GOSUB DoMoves',
            '80 TC1=5: TC2=3: GOSUB FindEdge',
            '85 PRINT "INSERTED: EP=";EP;" EO=";EO',
            '90 IF EP=10 AND EO=0 THEN PRINT "INSERT OK" ELSE PRINT "INSERT FAIL"',
            '100 END',
        ])
        for t in out:
            if 'EP=' in t or 'OK' in t or 'FAIL' in t:
                print(f"  {t.strip()}")

    @pytest.mark.slow
    def test_all_mid_algs(self, basic, helpers):
        """Test all 8 mid-edge algorithms by extract+align+insert round-trip."""
        # For each slot, test both algorithms
        tests = [
            # (name, tc1, tc2, ei, target_ep, extract_alg)
            ("FR-ep4", 4, 3, 0, 8, "uRUrUfuF"),
            ("FR-ep5", 4, 3, 0, 8, "UfuFuRUr"),
            ("FL-ep4", 4, 6, 1, 9, "UluLuFUf"),
            ("FL-ep7", 4, 6, 1, 9, "uFUfUluL"),
            ("BR-ep5", 5, 3, 2, 10, "uBUbUruR"),
            ("BR-ep6", 5, 3, 2, 10, "UruRuBUb"),
            ("BL-ep7", 5, 6, 3, 11, "UbuBuLUl"),
            ("BL-ep6", 5, 6, 3, 11, "uLUlUbuB"),
        ]
        for name, tc1, tc2, ei, target_ep, extract in tests:
            out = _run(basic, helpers, [
                f'40 MS$="{extract}": GOSUB DoMoves',
                f'50 TC1={tc1}: TC2={tc2}: GOSUB FindEdge',
                '55 PRINT "EXT: EP=";EP;" EO=";EO',
                f'60 EI={ei}: GOSUB AlignMidEdge',
                f'65 TC1={tc1}: TC2={tc2}: GOSUB FindEdge',
                '70 PRINT "ALN: EP=";EP;" EO=";EO',
                f'75 GOSUB InsertMidEdge',
                f'80 TC1={tc1}: TC2={tc2}: GOSUB FindEdge',
                '85 PRINT "INS: EP=";EP;" EO=";EO',
                f'90 IF EP={target_ep} AND EO=0 THEN PRINT "OK" ELSE PRINT "FAIL"',
                '100 END',
            ])
            ep_lines = [t.strip() for t in out if 'EP=' in t or 'OK' in t.strip() or 'FAIL' in t.strip()]
            ok = any(t.strip() == 'OK' for t in out)
            print(f"  {name:10s}: {'PASS' if ok else 'FAIL':4s} | {' | '.join(ep_lines)}")
