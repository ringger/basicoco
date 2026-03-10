"""
Tests for Rubik's cube solver — Steps 1-2.

Scrambles the cube with known move sequences, runs the solver,
and verifies each step's invariant holds.
"""

import os
import shutil
import pytest


@pytest.fixture(autouse=True)
def setup_solver(temp_programs_dir):
    """Copy rubiks_engine.bas and rubiks_solver.bas into the temp programs dir."""
    programs_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'programs')
    for fname in ('rubiks_engine.bas', 'rubiks_solver.bas'):
        src = os.path.abspath(os.path.join(programs_dir, fname))
        shutil.copy(src, os.path.join(temp_programs_dir, fname))


def _build_solver_test(scramble_moves, max_frames=20000):
    """Build a program that scrambles, solves cross, and verifies."""
    return [
        '5 SAFETY OFF',
        '10 PMODE 4: SCREEN 1',
        '20 MERGE "rubiks_engine"',
        '25 MERGE "rubiks_solver"',
        '30 GOSUB InitCube',
        '35 AN=0',
        f'40 MS$="{scramble_moves}": GOSUB DoMoves',
        '50 GOSUB SolveBottomCross',
        '60 GOSUB CheckBottomCross',
        '70 PRINT "SOLVED"',
        '80 END',
    ]


def _run_solver_test(basic, helpers, scramble_moves, max_frames=20000):
    """Scramble, solve cross, verify."""
    program = _build_solver_test(scramble_moves, max_frames)
    helpers.load_program(basic, program)
    results = helpers.run_to_completion(basic, max_frames=max_frames)
    errors = helpers.get_error_messages(results)
    assert errors == [], f"Errors after scramble '{scramble_moves}': {errors}"
    texts = helpers.get_text_output(results)
    assert any('SOLVED' in t or 'CROSS OK' in t for t in texts), \
        f"Cross not solved after scramble '{scramble_moves}'. Output: {texts}"


@pytest.mark.slow
class TestBottomCross:
    """Test bottom cross solver on various scrambles."""

    def test_already_solved(self, basic, helpers):
        """Solved cube — solver should do nothing."""
        _run_solver_test(basic, helpers, "")

    def test_single_move_R(self, basic, helpers):
        """Single R move scramble."""
        _run_solver_test(basic, helpers, "R")

    def test_single_move_F(self, basic, helpers):
        """Single F move scramble."""
        _run_solver_test(basic, helpers, "F")

    def test_single_move_U(self, basic, helpers):
        """Single U move scramble — only top layer affected."""
        _run_solver_test(basic, helpers, "U")

    def test_single_move_L(self, basic, helpers):
        """Single L move scramble."""
        _run_solver_test(basic, helpers, "L")

    def test_single_move_D(self, basic, helpers):
        """Single D move scramble."""
        _run_solver_test(basic, helpers, "D")

    def test_single_move_B(self, basic, helpers):
        """Single B move scramble."""
        _run_solver_test(basic, helpers, "B")

    def test_two_moves_RF(self, basic, helpers):
        """Two-move scramble."""
        _run_solver_test(basic, helpers, "RF")

    def test_two_moves_RU(self, basic, helpers):
        """Two-move scramble involving top layer."""
        _run_solver_test(basic, helpers, "RU")

    def test_sexy_move(self, basic, helpers):
        """Sexy move (R U R' U') scramble."""
        _run_solver_test(basic, helpers, "RUru")

    def test_triple_sexy(self, basic, helpers):
        """3x sexy move scramble."""
        _run_solver_test(basic, helpers, "RUruRUruRUru")

    def test_all_faces(self, basic, helpers):
        """Scramble touching all 6 faces."""
        _run_solver_test(basic, helpers, "RUFBLD")

    def test_deeper_scramble(self, basic, helpers):
        """8-move scramble."""
        _run_solver_test(basic, helpers, "RUFBLDru")

    def test_ten_move_scramble(self, basic, helpers):
        """10-move scramble."""
        _run_solver_test(basic, helpers, "RUFRUFrufl")

    def test_flipped_edges(self, basic, helpers):
        """Scramble designed to create flipped edges."""
        _run_solver_test(basic, helpers, "FRFRfr")

    def test_counter_clockwise(self, basic, helpers):
        """All counter-clockwise scramble."""
        _run_solver_test(basic, helpers, "rufldb")


def _build_corners_test(scramble_moves, max_frames=40000):
    """Build a program that scrambles, solves cross + corners, and verifies."""
    return [
        '5 SAFETY OFF',
        '10 PMODE 4: SCREEN 1',
        '20 MERGE "rubiks_engine"',
        '25 MERGE "rubiks_solver"',
        '30 GOSUB InitCube',
        '35 AN=0',
        f'40 MS$="{scramble_moves}": GOSUB DoMoves',
        '50 GOSUB SolveBottomCross',
        '55 GOSUB CheckBottomCross',
        '60 GOSUB SolveBottomCorners',
        '65 GOSUB CheckBottomCorners',
        '70 PRINT "SOLVED"',
        '80 END',
    ]


def _run_corners_test(basic, helpers, scramble_moves, max_frames=40000):
    """Scramble, solve cross + corners, verify."""
    program = _build_corners_test(scramble_moves, max_frames)
    helpers.load_program(basic, program)
    results = helpers.run_to_completion(basic, max_frames=max_frames)
    errors = helpers.get_error_messages(results)
    assert errors == [], f"Errors after scramble '{scramble_moves}': {errors}"
    texts = helpers.get_text_output(results)
    assert any('CORNERS OK' in t for t in texts), \
        f"Corners not solved after scramble '{scramble_moves}'. Output: {texts}"
    # Also verify cross is still intact
    assert any('CROSS OK' in t for t in texts), \
        f"Cross broken after corners solve, scramble '{scramble_moves}'. Output: {texts}"


@pytest.mark.slow
class TestBottomCorners:
    """Test bottom corners solver on various scrambles."""

    def test_already_solved(self, basic, helpers):
        """Solved cube — solver should do nothing."""
        _run_corners_test(basic, helpers, "")

    def test_single_move_R(self, basic, helpers):
        _run_corners_test(basic, helpers, "R")

    def test_single_move_F(self, basic, helpers):
        _run_corners_test(basic, helpers, "F")

    def test_single_move_U(self, basic, helpers):
        _run_corners_test(basic, helpers, "U")

    def test_single_move_L(self, basic, helpers):
        _run_corners_test(basic, helpers, "L")

    def test_single_move_D(self, basic, helpers):
        _run_corners_test(basic, helpers, "D")

    def test_single_move_B(self, basic, helpers):
        _run_corners_test(basic, helpers, "B")

    def test_two_moves_RF(self, basic, helpers):
        _run_corners_test(basic, helpers, "RF")

    def test_sexy_move(self, basic, helpers):
        _run_corners_test(basic, helpers, "RUru")

    def test_triple_sexy(self, basic, helpers):
        _run_corners_test(basic, helpers, "RUruRUruRUru")

    def test_all_faces(self, basic, helpers):
        _run_corners_test(basic, helpers, "RUFBLD")

    def test_deeper_scramble(self, basic, helpers):
        _run_corners_test(basic, helpers, "RUFBLDru")

    def test_ten_move_scramble(self, basic, helpers):
        _run_corners_test(basic, helpers, "RUFRUFrufl")

    def test_counter_clockwise(self, basic, helpers):
        _run_corners_test(basic, helpers, "rufldb")

    def test_fifteen_moves(self, basic, helpers):
        _run_corners_test(basic, helpers, "RUFBLDrufbldRUF")

    def test_twenty_moves(self, basic, helpers):
        _run_corners_test(basic, helpers, "RUFBLDrufbldRUFBLDru")
