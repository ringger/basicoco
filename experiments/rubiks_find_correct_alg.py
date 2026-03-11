"""
Empirically find middle edge insertion algorithms that preserve the full bottom layer.

Our engine has F,B,D matching standard CW but U,R,L reversed.
The standard right-insert is U R U' R' U' F' U F.

We need to find the correct mapping. Instead of theorizing,
try all 8 possible case-swap combos for the 3 faces (U, R, F)
and check which one preserves the entire first layer.
"""

import os
import shutil
import itertools
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


# Full first-layer check (cross + all 4 corners with all 3 stickers)
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

# Middle edge checks
FR_CHK = 'CL(2,1,0,0)=4 AND CL(2,1,0,2)=3'
FL_CHK = 'CL(0,1,0,0)=4 AND CL(0,1,0,3)=6'
BR_CHK = 'CL(2,1,2,1)=5 AND CL(2,1,2,2)=3'
BL_CHK = 'CL(0,1,2,1)=5 AND CL(0,1,2,3)=6'


def _make_alg(pattern, swap_u, swap_r, swap_f):
    """Generate algorithm string from a pattern like 'URurufUF',
    optionally swapping case for specific faces."""
    result = []
    for c in pattern:
        face = c.upper()
        is_upper = c.isupper()
        if face == 'U' and swap_u:
            is_upper = not is_upper
        elif face == 'R' and swap_r:
            is_upper = not is_upper
        elif face == 'F' and swap_f:
            is_upper = not is_upper
        result.append(face if is_upper else face.lower())
    return ''.join(result)


class TestFindCorrectFRAlgorithm:
    """Try all 8 swap combos for the standard right-insert pattern."""

    def test_all_swaps_for_right_insert(self, basic, helpers):
        """Standard right-insert: U R U' R' U' F' U F
        As a pattern: URurufUF
        Try all 8 combinations of swapping U, R, F case."""
        print("\n=== Standard right-insert: U R U' R' U' F' U F ===")
        print("Pattern: URurufUF with optional case-swaps")
        for swap_u in [False, True]:
            for swap_r in [False, True]:
                for swap_f in [False, True]:
                    alg = _make_alg("URurufUF", swap_u, swap_r, swap_f)
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

    def test_all_swaps_for_left_insert(self, basic, helpers):
        """Standard left-insert: U' L' U L U F U' F'
        As a pattern: ulULUFuf
        Try all 8 combinations of swapping U, L, F case."""
        print("\n=== Standard left-insert: U' L' U L U F U' F' ===")
        print("Pattern: ulULUFuf with optional case-swaps")
        for swap_u in [False, True]:
            for swap_l in [False, True]:
                for swap_f in [False, True]:
                    alg = _make_alg_3("ulULUFuf", 'U', swap_u, 'L', swap_l, 'F', swap_f)
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


def _make_alg_3(pattern, face1, swap1, face2, swap2, face3, swap3):
    """Same as _make_alg but for 3 named faces."""
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


class TestFindCorrectBRBLAlgorithm:
    """Find correct BR and BL algorithms."""

    def test_br_from_back(self, basic, helpers):
        """Standard BR from back: U R U' R' U' B' U B (face sub F→B from right-insert)
        Pattern: URuruBUb with swaps for U, R, B."""
        print("\n=== BR from back: U R U' R' U' B' U B ===")
        for swap_u in [False, True]:
            for swap_r in [False, True]:
                for swap_b in [False, True]:
                    alg = _make_alg_3("URuruBUb", 'U', swap_u, 'R', swap_r, 'B', swap_b)
                    label = f"swapU={swap_u} swapR={swap_r} swapB={swap_b}"
                    out = _run(basic, helpers, [
                        f'9000 MS$="{alg}": GOSUB DoMoves',
                        f'9010 IF {FULL_BOTTOM} THEN PRINT "BOTTOM OK" ELSE PRINT "BOTTOM BAD"',
                        f'9020 IF {BR_CHK} THEN PRINT "BR SAME" ELSE PRINT "BR CHANGED"',
                        '9030 END',
                    ])
                    bottom = 'OK' if any('BOTTOM OK' in t for t in out) else 'BAD'
                    br = 'same' if any('BR SAME' in t for t in out) else 'changed'
                    marker = ' *** CORRECT ***' if bottom == 'OK' and br == 'changed' else ''
                    print(f"  {label:40s} {alg:8s}: bottom={bottom}, BR={br}{marker}")

    def test_br_from_right(self, basic, helpers):
        """Standard BR from right: U' B' U B U R U' R' (face sub F→B from left-insert... or equiv)
        Pattern: ubUBURur with swaps for U, R, B."""
        print("\n=== BR from right: U' B' U B U R U' R' ===")
        for swap_u in [False, True]:
            for swap_r in [False, True]:
                for swap_b in [False, True]:
                    alg = _make_alg_3("ubUBURur", 'U', swap_u, 'R', swap_r, 'B', swap_b)
                    label = f"swapU={swap_u} swapR={swap_r} swapB={swap_b}"
                    out = _run(basic, helpers, [
                        f'9000 MS$="{alg}": GOSUB DoMoves',
                        f'9010 IF {FULL_BOTTOM} THEN PRINT "BOTTOM OK" ELSE PRINT "BOTTOM BAD"',
                        f'9020 IF {BR_CHK} THEN PRINT "BR SAME" ELSE PRINT "BR CHANGED"',
                        '9030 END',
                    ])
                    bottom = 'OK' if any('BOTTOM OK' in t for t in out) else 'BAD'
                    br = 'same' if any('BR SAME' in t for t in out) else 'changed'
                    marker = ' *** CORRECT ***' if bottom == 'OK' and br == 'changed' else ''
                    print(f"  {label:40s} {alg:8s}: bottom={bottom}, BR={br}{marker}")

    def test_bl_from_left(self, basic, helpers):
        """Standard BL from left: U' B' U B U L U' L' (or similar)
        Trying pattern: ubUBULul with swaps."""
        print("\n=== BL from left: standard left-insert with F→B ===")
        # The standard left-insert is U' L' U L U F U' F'. Sub F→B:
        # U' L' U L U B U' B' = pattern: ulULUBub
        for swap_u in [False, True]:
            for swap_l in [False, True]:
                for swap_b in [False, True]:
                    alg = _make_alg_3("ulULUBub", 'U', swap_u, 'L', swap_l, 'B', swap_b)
                    label = f"swapU={swap_u} swapL={swap_l} swapB={swap_b}"
                    out = _run(basic, helpers, [
                        f'9000 MS$="{alg}": GOSUB DoMoves',
                        f'9010 IF {FULL_BOTTOM} THEN PRINT "BOTTOM OK" ELSE PRINT "BOTTOM BAD"',
                        f'9020 IF {BL_CHK} THEN PRINT "BL SAME" ELSE PRINT "BL CHANGED"',
                        '9030 END',
                    ])
                    bottom = 'OK' if any('BOTTOM OK' in t for t in out) else 'BAD'
                    bl = 'same' if any('BL SAME' in t for t in out) else 'changed'
                    marker = ' *** CORRECT ***' if bottom == 'OK' and bl == 'changed' else ''
                    print(f"  {label:40s} {alg:8s}: bottom={bottom}, BL={bl}{marker}")

    def test_bl_from_back(self, basic, helpers):
        """Standard BL from back: U B U' B' U' L' U L
        Pattern: UBubulUL with swaps."""
        print("\n=== BL from back ===")
        for swap_u in [False, True]:
            for swap_l in [False, True]:
                for swap_b in [False, True]:
                    alg = _make_alg_3("UBubulUL", 'U', swap_u, 'L', swap_l, 'B', swap_b)
                    label = f"swapU={swap_u} swapL={swap_l} swapB={swap_b}"
                    out = _run(basic, helpers, [
                        f'9000 MS$="{alg}": GOSUB DoMoves',
                        f'9010 IF {FULL_BOTTOM} THEN PRINT "BOTTOM OK" ELSE PRINT "BOTTOM BAD"',
                        f'9020 IF {BL_CHK} THEN PRINT "BL SAME" ELSE PRINT "BL CHANGED"',
                        '9030 END',
                    ])
                    bottom = 'OK' if any('BOTTOM OK' in t for t in out) else 'BAD'
                    bl = 'same' if any('BL SAME' in t for t in out) else 'changed'
                    marker = ' *** CORRECT ***' if bottom == 'OK' and bl == 'changed' else ''
                    print(f"  {label:40s} {alg:8s}: bottom={bottom}, BL={bl}{marker}")
