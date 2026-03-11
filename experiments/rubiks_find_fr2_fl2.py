"""
Find the correct second algorithms for FR (from right) and FL (from left).
Standard FR from right: U' F' U F U R U' R' = pattern ufUFURur
Standard FL from left: U F U' F' U' L' U L = pattern UFufulUL
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

FR_CHK = 'CL(2,1,0,0)=4 AND CL(2,1,0,2)=3'
FL_CHK = 'CL(0,1,0,0)=4 AND CL(0,1,0,3)=6'


def _make_alg(pattern, face1, swap1, face2, swap2, face3, swap3):
    result = []
    for c in pattern:
        face = c.upper()
        is_upper = c.isupper()
        if face == face1 and swap1:
            is_upper = not is_upper
        elif face == face2 and swap2:
            is_upper = not is_upper
        elif face == face3 and swap3:
            is_upper = not is_upper
        result.append(face if is_upper else face.lower())
    return ''.join(result)


class TestSecondAlgorithms:

    def test_fr_from_right(self, basic, helpers):
        """Standard FR from right: U' F' U F U R U' R' = ufUFURur"""
        print("\n=== FR from right: U' F' U F U R U' R' ===")
        for swap_u in [False, True]:
            for swap_r in [False, True]:
                for swap_f in [False, True]:
                    alg = _make_alg("ufUFURur", 'U', swap_u, 'R', swap_r, 'F', swap_f)
                    label = f"swapU={swap_u} swapR={swap_r} swapF={swap_f}"
                    out = _run(basic, helpers, [
                        f'9000 MS$="{alg}": GOSUB DoMoves',
                        f'9010 IF {FULL_BOTTOM} THEN PRINT "BOTTOM OK" ELSE PRINT "BOTTOM BAD"',
                        f'9020 IF {FR_CHK} THEN PRINT "FR SAME" ELSE PRINT "FR CHANGED"',
                        '9030 END',
                    ])
                    bottom = 'OK' if any('BOTTOM OK' in t for t in out) else 'BAD'
                    fr = 'same' if any('FR SAME' in t for t in out) else 'changed'
                    marker = ' *** CORRECT ***' if bottom == 'OK' and fr == 'changed' else ''
                    print(f"  {label:40s} {alg:8s}: bottom={bottom}, FR={fr}{marker}")

    def test_fl_from_left(self, basic, helpers):
        """Standard FL from left: U F U' F' U' L' U L = UFufulUL"""
        print("\n=== FL from left: U F U' F' U' L' U L ===")
        for swap_u in [False, True]:
            for swap_l in [False, True]:
                for swap_f in [False, True]:
                    alg = _make_alg("UFufulUL", 'U', swap_u, 'L', swap_l, 'F', swap_f)
                    label = f"swapU={swap_u} swapL={swap_l} swapF={swap_f}"
                    out = _run(basic, helpers, [
                        f'9000 MS$="{alg}": GOSUB DoMoves',
                        f'9010 IF {FULL_BOTTOM} THEN PRINT "BOTTOM OK" ELSE PRINT "BOTTOM BAD"',
                        f'9020 IF {FL_CHK} THEN PRINT "FL SAME" ELSE PRINT "FL CHANGED"',
                        '9030 END',
                    ])
                    bottom = 'OK' if any('BOTTOM OK' in t for t in out) else 'BAD'
                    fl = 'same' if any('FL SAME' in t for t in out) else 'changed'
                    marker = ' *** CORRECT ***' if bottom == 'OK' and fl == 'changed' else ''
                    print(f"  {label:40s} {alg:8s}: bottom={bottom}, FL={fl}{marker}")
