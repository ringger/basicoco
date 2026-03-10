"""
Exploratory tests to find correct corner insertion algorithms.
Runs as BASIC programs since direct-mode GOSUB to labels doesn't work.
User lines use 9000+ to avoid conflicts with engine auto-numbered lines.
"""

import os
import shutil
import pytest


@pytest.fixture(autouse=True)
def setup_engine(temp_programs_dir):
    programs_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'programs')
    src = os.path.abspath(os.path.join(programs_dir, 'lib_rubiks_engine.bas'))
    shutil.copy(src, os.path.join(temp_programs_dir, 'lib_rubiks_engine.bas'))


def _run(basic, helpers, lines, max_frames=10000):
    """Run a BASIC program and return text output.
    Uses the same line number structure as the working solver tests."""
    program = [
        '5 SAFETY OFF',
        '10 PMODE 4: SCREEN 1',
        '20 MERGE "lib_rubiks_engine"',
        '30 GOSUB InitCube',
        '35 AN=0',
    ] + lines
    helpers.load_program(basic, program)
    results = helpers.run_to_completion(basic, max_frames=max_frames)
    errors = helpers.get_error_messages(results)
    assert errors == [], f"Errors: {errors}"
    return helpers.get_text_output(results)


class TestCornerAlgorithms:

    def test_R_displaces_BFR(self, basic, helpers):
        """Verify R via DoMoves changes BFR corner.
        Match the exact solver test structure that works."""
        # This matches _build_solver_test exactly, with print added
        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "lib_rubiks_engine"',
            '30 GOSUB InitCube',
            '35 AN=0',
            '36 PRINT "BEFORE:";CL(2,2,0,5);CL(2,2,0,0);CL(2,2,0,2)',
            '40 MS$="R": GOSUB DoMoves',
            '50 PRINT "AFTER:";CL(2,2,0,5);CL(2,2,0,0);CL(2,2,0,2)',
            '60 END',
        ]
        helpers.load_program(basic, program)
        results = helpers.run_to_completion(basic, max_frames=10000)
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        out = helpers.get_text_output(results)
        for t in out:
            print(t)
        after_line = [t for t in out if 'AFTER' in t]
        assert after_line, "Should have AFTER output"
        assert '7  4  3' not in after_line[0], f"R should change BFR: {after_line[0]}"

    def test_bfr_insert_candidates(self, basic, helpers):
        """Try candidate algorithms for BFR slot after R scramble."""
        candidates = ["RUru", "rDRd", "RDrd", "fuFU", "fDFd"]
        for alg in candidates:
            out = _run(basic, helpers, [
                '9000 MS$="R": GOSUB DoMoves',
                f'9010 FOR I=1 TO 6',
                f'9020   MS$="{alg}": GOSUB DoMoves',
                f'9030   IF CL(2,2,0,5)=7 AND CL(2,2,0,0)=4 AND CL(2,2,0,2)=3 THEN PRINT "SOLVED:";I: GOTO 9050',
                f'9040 NEXT I',
                f'9045 PRINT "FAILED"',
                '9050 END',
            ])
            result = ' '.join(out)
            print(f"  {alg}: {result.strip()}")

    def test_bfr_harder_scrambles(self, basic, helpers):
        """BFR insertion after harder scrambles."""
        candidates = ["RUru", "rDRd", "RDrd", "fuFU"]
        scrambles = ["RF", "RUF", "RUFB", "RUFU", "RUFBLDru"]
        for scramble in scrambles:
            print(f"\nScramble: {scramble}")
            for alg in candidates:
                out = _run(basic, helpers, [
                    f'9000 MS$="{scramble}": GOSUB DoMoves',
                    '9005 IF CL(2,2,0,5)=7 AND CL(2,2,0,0)=4 AND CL(2,2,0,2)=3 THEN PRINT "SKIP": END',
                    f'9010 FOR I=1 TO 6',
                    f'9020   MS$="{alg}": GOSUB DoMoves',
                    f'9030   IF CL(2,2,0,5)=7 AND CL(2,2,0,0)=4 AND CL(2,2,0,2)=3 THEN PRINT "SOLVED:";I: GOTO 9050',
                    f'9040 NEXT I',
                    f'9045 PRINT "FAILED"',
                    '9050 END',
                ], max_frames=20000)
                result = ' '.join(out).strip()
                print(f"  {alg}: {result}")

    def test_all_slot_candidates(self, basic, helpers):
        """For each of 4 bottom slots, find working insert algorithm."""
        slots = [
            ("BFR", "2,2,0,5", 7, "2,2,0,0", 4, "2,2,0,2", 3,
             ["RUru", "rDRd", "RDrd", "fuFU"]),
            ("BBR", "2,2,2,5", 7, "2,2,2,1", 5, "2,2,2,2", 3,
             ["BUbu", "bDBd", "BDbd", "ruRU"]),
            ("BBL", "0,2,2,5", 7, "0,2,2,1", 5, "0,2,2,3", 6,
             ["LUlu", "lDLd", "LDld", "buBU"]),
            ("BFL", "0,2,0,5", 7, "0,2,0,0", 4, "0,2,0,3", 6,
             ["FUfu", "fDFd", "FDfd", "luLU"]),
        ]
        scrambles = ["R", "F", "U", "B", "L", "D", "RF", "RUF", "RUFB", "RUFBLDru"]

        for name, s1, c1, s2, c2, s3, c3, algs in slots:
            print(f"\n=== {name} ===")
            for scramble in scrambles:
                for alg in algs:
                    check = f'CL({s1})={c1} AND CL({s2})={c2} AND CL({s3})={c3}'
                    out = _run(basic, helpers, [
                        f'9000 MS$="{scramble}": GOSUB DoMoves',
                        f'9005 IF {check} THEN PRINT "SKIP": END',
                        f'9010 FOR I=1 TO 6',
                        f'9020   MS$="{alg}": GOSUB DoMoves',
                        f'9030   IF {check} THEN PRINT "OK:";I: GOTO 9050',
                        f'9040 NEXT I',
                        f'9045 PRINT "FAIL"',
                        '9050 END',
                    ], max_frames=20000)
                    result = ' '.join(out).strip()
                    if 'FAIL' in result:
                        print(f"  scr={scramble} {alg}: {result}")

    def test_cross_preservation(self, basic, helpers):
        """Verify candidate algorithms preserve the bottom cross."""
        candidates = ["RUru", "rDRd", "fuFU", "BUbu", "LUlu", "FUfu"]
        cross_check = ('CL(1,2,0,5)=7 AND CL(1,2,0,0)=4 AND '
                       'CL(2,2,1,5)=7 AND CL(2,2,1,2)=3 AND '
                       'CL(1,2,2,5)=7 AND CL(1,2,2,1)=5 AND '
                       'CL(0,2,1,5)=7 AND CL(0,2,1,3)=6')
        for alg in candidates:
            out = _run(basic, helpers, [
                f'9000 MS$="{alg}": GOSUB DoMoves',
                f'9010 IF {cross_check} THEN PRINT "CROSS OK" ELSE PRINT "CROSS BROKEN"',
                '9020 END',
            ])
            result = ' '.join(out).strip()
            print(f"  {alg}: {result}")
