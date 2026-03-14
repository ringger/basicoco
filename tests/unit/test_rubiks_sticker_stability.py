"""Tests for sticker-level correctness after every individual move.

Applies a scramble sequence one move at a time through the BASIC engine,
dumping all 54 stickers after each move. Compares against pycuber as the
reference oracle. This catches any permutation or face-remap bugs that
color-count checks would miss.
"""

import os
import shutil
import pytest
import pycuber

# Reuse the validate_moves infrastructure
from tools.validate_moves import (
    parse_engine_output,
    pycuber_faces,
    compare_faces,
    ENGINE_TO_PYCOLOR,
)


# Engine move char → pycuber move notation
MOVE_MAP = {
    'R': "R", 'r': "R'",
    'U': "U", 'u': "U'",
    'F': "F", 'f': "F'",
    'L': "L", 'l': "L'",
    'D': "D", 'd': "D'",
    'B': "B", 'b': "B'",
}


@pytest.fixture(autouse=True)
def setup_engine(temp_programs_dir):
    programs_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'programs')
    src = os.path.abspath(os.path.join(programs_dir, 'lib_rubiks_engine.bas'))
    shutil.copy(src, os.path.join(temp_programs_dir, 'lib_rubiks_engine.bas'))


def _build_per_move_dump_program(scramble):
    """Build a BASIC program that dumps all 54 stickers after each move."""
    # Sticker dump subroutine (reusable)
    dump_sub = [
        '1000 REM DUMP ALL STICKERS',
        '1010 PRINT "F:";CL(0,0,0,0);CL(1,0,0,0);CL(2,0,0,0);CL(0,1,0,0);CL(1,1,0,0);CL(2,1,0,0);CL(0,2,0,0);CL(1,2,0,0);CL(2,2,0,0)',
        '1020 PRINT "B:";CL(2,0,2,1);CL(1,0,2,1);CL(0,0,2,1);CL(2,1,2,1);CL(1,1,2,1);CL(0,1,2,1);CL(2,2,2,1);CL(1,2,2,1);CL(0,2,2,1)',
        '1030 PRINT "R:";CL(2,0,0,2);CL(2,0,1,2);CL(2,0,2,2);CL(2,1,0,2);CL(2,1,1,2);CL(2,1,2,2);CL(2,2,0,2);CL(2,2,1,2);CL(2,2,2,2)',
        '1040 PRINT "L:";CL(0,0,2,3);CL(0,0,1,3);CL(0,0,0,3);CL(0,1,2,3);CL(0,1,1,3);CL(0,1,0,3);CL(0,2,2,3);CL(0,2,1,3);CL(0,2,0,3)',
        '1050 PRINT "U:";CL(0,0,2,4);CL(1,0,2,4);CL(2,0,2,4);CL(0,0,1,4);CL(1,0,1,4);CL(2,0,1,4);CL(0,0,0,4);CL(1,0,0,4);CL(2,0,0,4)',
        '1060 PRINT "D:";CL(0,2,0,5);CL(1,2,0,5);CL(2,2,0,5);CL(0,2,1,5);CL(1,2,1,5);CL(2,2,1,5);CL(0,2,2,5);CL(1,2,2,5);CL(2,2,2,5)',
        '1070 RETURN',
    ]

    lines = [
        '5 SAFETY OFF',
        '10 PMODE 4: SCREEN 1',
        '20 MERGE "lib_rubiks_engine"',
        '30 GOSUB InitCube',
        '35 AN=0',
    ]

    # Apply each move individually and dump state
    line_num = 100
    for i, move_char in enumerate(scramble):
        lines.append(f'{line_num} MS$="{move_char}": GOSUB DoMoves')
        line_num += 10
        lines.append(f'{line_num} PRINT "AFTER MOVE {i+1}: {move_char}"')
        line_num += 10
        lines.append(f'{line_num} GOSUB 1000')
        line_num += 10

    lines.append(f'{line_num} END')
    lines.extend(dump_sub)
    return lines


def _parse_per_move_output(texts):
    """Parse output into list of (label, faces_dict) tuples."""
    results = []
    current_label = None
    current_lines = []

    for t in texts:
        t = t.strip()
        if t.startswith('AFTER MOVE'):
            # Save previous block
            if current_label and current_lines:
                faces = parse_engine_output(current_lines)
                results.append((current_label, faces))
            current_label = t
            current_lines = []
        elif ':' in t and t[0] in 'FBRLUDM':
            current_lines.append(t)

    # Save last block
    if current_label and current_lines:
        faces = parse_engine_output(current_lines)
        results.append((current_label, faces))

    return results


def _run_sticker_stability_test(basic, helpers, scramble, max_frames=20000):
    """Apply scramble one move at a time, verify all 54 stickers after each move."""
    program = _build_per_move_dump_program(scramble)
    helpers.load_program(basic, program)
    results = helpers.run_to_completion(basic, max_frames=max_frames)
    errors = helpers.get_error_messages(results)
    assert errors == [], f"BASIC errors: {errors}"
    texts = helpers.get_text_output(results)

    move_results = _parse_per_move_output(texts)
    assert len(move_results) == len(scramble), \
        f"Expected {len(scramble)} dumps, got {len(move_results)}"

    # Build pycuber reference incrementally
    cube = pycuber.Cube()
    all_diffs = []

    for i, (label, engine_faces) in enumerate(move_results):
        move_char = scramble[i]
        py_move = MOVE_MAP.get(move_char)
        assert py_move is not None, f"Unknown move: {move_char}"
        cube(py_move)

        pyc = pycuber_faces(cube)
        diffs = compare_faces(engine_faces, pyc, label)
        if diffs:
            all_diffs.append((label, diffs))

    assert all_diffs == [], \
        f"Sticker mismatches found:\n" + \
        "\n".join(f"{label}: {diffs}" for label, diffs in all_diffs)


@pytest.mark.slow
class TestStickerStability:
    """Verify exact sticker positions after every individual move."""

    def test_single_R(self, basic, helpers):
        """Single R move."""
        _run_sticker_stability_test(basic, helpers, "R")

    def test_all_six_faces(self, basic, helpers):
        """One CW turn of each face."""
        _run_sticker_stability_test(basic, helpers, "RUFBLD")

    def test_all_twelve_moves(self, basic, helpers):
        """All 6 CW and 6 CCW face turns."""
        _run_sticker_stability_test(basic, helpers, "RrUuFfBbLlDd")

    def test_scramble_10(self, basic, helpers):
        """10-move scramble, every sticker checked after each move."""
        _run_sticker_stability_test(basic, helpers, "RUFbLdRuFB")

    def test_scramble_20(self, basic, helpers):
        """20-move scramble, every sticker checked after each move."""
        _run_sticker_stability_test(basic, helpers, "RUFBLDrufbldRUFBLDru")

    def test_double_moves(self, basic, helpers):
        """Double moves (XX = 180-degree turn)."""
        _run_sticker_stability_test(basic, helpers, "RRUURRUUFFBB")

    def test_identity_sequences(self, basic, helpers):
        """Known identity: R R R R = solved, then U U U U = solved."""
        _run_sticker_stability_test(basic, helpers, "RRRRUUUU")

    def test_sexy_move_six_times(self, basic, helpers):
        """(R U R' U')×6 = identity."""
        _run_sticker_stability_test(basic, helpers, "RUru" * 6)
