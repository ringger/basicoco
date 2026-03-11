"""
Test standard F2L insertion algorithms in the new engine.
Strategy: use a D turn to displace the edge, let the solver cross+corners
fix the bottom, then we have a mid-edge in the top layer that we can
align and insert manually.

Simpler approach: just scramble with a single move and check if the full
solver step 3 works with the standard algorithms.

Actually simplest: just check whether each algorithm applied twice is identity
(since F2L algorithms are involutions — they extract and re-insert).
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


class TestInsertionAlgs:
    """Test various candidate algorithms to find which ones correctly insert."""

    @pytest.mark.slow
    def test_fr_candidates(self, basic, helpers):
        """Test FR insertion candidates.
        Setup: do a D turn on solved cube, then solve cross+corners.
        This leaves FR edge displaced to top. Then align and insert."""

        # Standard F2L algorithms and their "swapped" versions
        candidates = [
            # Standard notation in new engine:
            ("std-right URurufUF", "URurufUF"),
            ("std-left  ufUFURur", "ufUFURur"),
            # My swapped versions:
            ("swap-right uRUrUfuF", "uRUrUfuF"),
            ("swap-left  UfuFuRUr", "UfuFuRUr"),
            # Old engine algorithms (unmodified):
            ("old-right  UruRufUF", "UruRufUF"),
            ("old-left   ufUFUruR", "ufUFUruR"),
        ]

        for label, alg in candidates:
            out = _run(basic, helpers, [
                # Scramble with D to displace middle edges
                '40 MS$="D": GOSUB DoMoves',
                # Solve cross and corners (these work)
                '50 GOSUB SolveBottomCross',
                '55 GOSUB SolveBottomCorners',
                # Find FR edge
                '60 TC1=4: TC2=3: GOSUB FindEdge',
                '65 PRINT "BEFORE: EP=";EP;" EO=";EO',
                # Align for FR slot
                '70 EI=0: GOSUB AlignMidEdge',
                '75 TC1=4: TC2=3: GOSUB FindEdge',
                '80 PRINT "ALIGNED: EP=";EP;" EO=";EO',
                # Try candidate algorithm
                f'85 MS$="{alg}": GOSUB DoMoves',
                '90 TC1=4: TC2=3: GOSUB FindEdge',
                '95 PRINT "AFTER: EP=";EP;" EO=";EO',
                '100 IF EP=8 AND EO=0 THEN PRINT "INSERT OK" ELSE PRINT "INSERT FAIL"',
                '110 END',
            ])
            ep_lines = [t.strip() for t in out if 'EP=' in t or 'OK' in t or 'FAIL' in t]
            ok = any('INSERT OK' in t for t in out)
            print(f"  {label}: {'PASS' if ok else 'FAIL':4s} | {' | '.join(ep_lines)}")

    @pytest.mark.slow
    def test_br_candidates(self, basic, helpers):
        """Test BR insertion candidates after D scramble."""
        candidates = [
            ("std-right UBuburUR", "UBuburUR"),
            ("std-left  urURUBub", "urURUBub"),
            ("swap-right uBUbUruR", "uBUbUruR"),
            ("swap-left  UruRuBUb", "UruRuBUb"),
            ("old-right  UBubuRUr", "UBubuRUr"),
            ("old-left   uRUrUBub", "uRUrUBub"),
        ]

        for label, alg in candidates:
            out = _run(basic, helpers, [
                '40 MS$="D": GOSUB DoMoves',
                '50 GOSUB SolveBottomCross',
                '55 GOSUB SolveBottomCorners',
                '60 TC1=5: TC2=3: GOSUB FindEdge',
                '65 PRINT "BEFORE: EP=";EP;" EO=";EO',
                '70 EI=2: GOSUB AlignMidEdge',
                '75 TC1=5: TC2=3: GOSUB FindEdge',
                '80 PRINT "ALIGNED: EP=";EP;" EO=";EO',
                f'85 MS$="{alg}": GOSUB DoMoves',
                '90 TC1=5: TC2=3: GOSUB FindEdge',
                '95 PRINT "AFTER: EP=";EP;" EO=";EO',
                '100 IF EP=10 AND EO=0 THEN PRINT "INSERT OK" ELSE PRINT "INSERT FAIL"',
                '110 END',
            ])
            ep_lines = [t.strip() for t in out if 'EP=' in t or 'OK' in t or 'FAIL' in t]
            ok = any('INSERT OK' in t for t in out)
            print(f"  {label}: {'PASS' if ok else 'FAIL':4s} | {' | '.join(ep_lines)}")
