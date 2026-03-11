"""
Test actual insertion: extract a middle edge, align it, apply algorithm,
check it ends up at the correct EP with EO=0.
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


FULL_BOTTOM = (
    'CL(1,2,0,5)=7 AND CL(1,2,0,0)=4 AND '
    'CL(2,2,1,5)=7 AND CL(2,2,1,2)=3 AND '
    'CL(1,2,2,5)=7 AND CL(1,2,2,1)=5 AND '
    'CL(0,2,1,5)=7 AND CL(0,2,1,3)=6 AND '
    'CL(2,2,0,5)=7 AND CL(2,2,0,0)=4 AND CL(2,2,0,2)=3 AND '
    'CL(0,2,0,5)=7 AND CL(0,2,0,0)=4 AND CL(0,2,0,3)=6 AND '
    'CL(2,2,2,5)=7 AND CL(2,2,2,1)=5 AND CL(2,2,2,2)=3 AND '
    'CL(0,2,2,5)=7 AND CL(0,2,2,1)=5 AND CL(0,2,2,3)=6'
)


class TestActualInsertion:
    """For each algorithm: extract the target edge from a solved cube,
    position it at the correct top EP, apply the algorithm, verify EP/EO."""

    def _test_insertion(self, basic, helpers, slot_name, tc1, tc2, target_ep,
                        extract_alg, position_ep, insert_alg):
        """Extract edge, position it, insert it, check result."""
        out = _run(basic, helpers, [
            # Extract the edge from the solved cube
            f'9000 MS$="{extract_alg}": GOSUB DoMoves',
            # Find the edge
            f'9010 TC1={tc1}: TC2={tc2}: GOSUB FindEdge',
            '9015 PRINT "AFTER EXTRACT: EP=";EP;" EO=";EO',
            # Align to desired position
            f'9020 GOSUB AlignMidEdge',
            f'9025 TC1={tc1}: TC2={tc2}: GOSUB FindEdge',
            '9030 PRINT "AFTER ALIGN: EP=";EP;" EO=";EO',
            # Apply the insertion algorithm
            f'9040 MS$="{insert_alg}": GOSUB DoMoves',
            # Check result
            f'9050 TC1={tc1}: TC2={tc2}: GOSUB FindEdge',
            '9055 PRINT "AFTER INSERT: EP=";EP;" EO=";EO',
            f'9060 IF EP={target_ep} AND EO=0 THEN PRINT "INSERT OK" ELSE PRINT "INSERT BAD"',
            f'9070 IF {FULL_BOTTOM} THEN PRINT "BOTTOM OK" ELSE PRINT "BOTTOM BAD"',
            '9080 END',
        ])
        results = {t.strip() for t in out if 'OK' in t or 'BAD' in t or 'EP=' in t}
        insert_ok = any('INSERT OK' in t for t in out)
        bottom_ok = any('BOTTOM OK' in t for t in out)
        ep_lines = [t.strip() for t in out if 'EP=' in t]
        return insert_ok, bottom_ok, ep_lines

    def test_all_8_algorithms(self, basic, helpers):
        """Test all 8 insertion algorithms."""
        # For each slot: use the first algorithm as extraction,
        # then test both insertion algorithms.
        tests = [
            # (name, tc1, tc2, target_ep, extract_alg, insert_alg)
            ("FR EP=4", 4, 3, 8, "UruRufUF", "UruRufUF"),
            ("FR EP=5", 4, 3, 8, "ufUFUruR", "ufUFUruR"),
            ("FL EP=4", 4, 6, 9, "uLUlUFuf", "uLUlUFuf"),
            ("FL EP=7", 4, 6, 9, "UFufuLUl", "UFufuLUl"),
            ("BR EP=6", 5, 3, 10, "uRUrUBub", "uRUrUBub"),
            ("BR EP=5", 5, 3, 10, "UBubuRUr", "UBubuRUr"),
            ("BL EP=7", 5, 6, 11, "UluLubUB", "UluLubUB"),
            ("BL EP=6", 5, 6, 11, "ubUBUluL", "ubUBUluL"),
        ]
        for name, tc1, tc2, target_ep, extract, insert in tests:
            ok, bottom_ok, ep_lines = self._test_insertion(
                basic, helpers, name, tc1, tc2, target_ep, extract, 0, insert
            )
            status = 'PASS' if ok and bottom_ok else 'FAIL'
            print(f"  {name:12s}: {status} | {' | '.join(ep_lines)}")

    def test_bl_all_candidates(self, basic, helpers):
        """Try many BL algorithm candidates and check actual insertion."""
        # BL: TC1=5, TC2=6, target EP=11
        # Extract using one algorithm, then try others to insert
        candidates = [
            ("ubUBUluL", "current BL EP=6"),
            ("UluLubUB", "current BL EP=7"),
            ("ubUBULul", "old BL EP=6"),
            ("ulULUBub", "old BL EP=7"),
            # Try all remaining 8-char combos with U,L,B
            ("uBUbUluL", "alt1"),
            ("UbubULuL", "alt2"),
            ("uBUbulUL", "alt3"),
            ("UbuBUluL", "alt4"),
        ]
        # Extract BL edge using a known-working extraction
        for alg, label in candidates:
            out = _run(basic, helpers, [
                # Extract BL edge to top
                '9000 MS$="UluLubUB": GOSUB DoMoves',
                '9005 TC1=5: TC2=6: GOSUB FindEdge',
                '9006 PRINT "EXTRACTED: EP=";EP;" EO=";EO',
                # Now we need to position at EP=6 for back-face case
                # or EP=7 for left-face case
                # Use AlignMidEdge to determine natural position
                '9010 EI=3: GOSUB AlignMidEdge',
                '9015 TC1=5: TC2=6: GOSUB FindEdge',
                '9016 PRINT "ALIGNED: EP=";EP;" EO=";EO',
                # Try candidate
                f'9020 MS$="{alg}": GOSUB DoMoves',
                '9025 TC1=5: TC2=6: GOSUB FindEdge',
                '9026 PRINT "RESULT: EP=";EP;" EO=";EO',
                '9030 IF EP=11 AND EO=0 THEN PRINT "OK" ELSE PRINT "BAD"',
                f'9040 IF {FULL_BOTTOM} THEN PRINT "BOTTOM OK" ELSE PRINT "BOTTOM BAD"',
                '9050 END',
            ])
            ep_lines = [t.strip() for t in out if 'EP=' in t]
            ok = any('OK' == t.strip() for t in out)
            bottom = any('BOTTOM OK' in t for t in out)
            print(f"  {label:20s} ({alg:8s}): {'PASS' if ok and bottom else 'FAIL':4s} | {' | '.join(ep_lines)}")
