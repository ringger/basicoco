"""
Tests for Rubik's cube engine L/D/B moves and DoMoves subroutine.

Verifies that new face turns (LEFT, DOWN, BACK) and the move-string
executor produce correct permutations.
"""

import os
import shutil
import pytest


@pytest.fixture(autouse=True)
def setup_engine(temp_programs_dir):
    """Copy lib_rubiks_engine.bas into the temp programs dir."""
    src = os.path.join(os.path.dirname(__file__), '..', '..', 'programs', 'lib_rubiks_engine.bas')
    shutil.copy(os.path.abspath(src), os.path.join(temp_programs_dir, 'lib_rubiks_engine.bas'))


def _run_move_test(basic, helpers, moves, expect_solved=True):
    """Init cube, apply moves, check if solved. Returns output texts."""
    program = [
        '5 SAFETY OFF',
        '10 PMODE 4: SCREEN 1',
        '20 MERGE "lib_rubiks_engine"',
        '30 GOSUB InitCube',
        f'40 MS$="{moves}": GOSUB DoMoves',
        '50 OK=1',
        '60 FOR IX=0 TO 2: FOR IY=0 TO 2',
        '70 IF CL(IX,IY,0,0)<>4 THEN OK=0',
        '80 IF CL(IX,IY,2,1)<>5 THEN OK=0',
        '90 NEXT IY: NEXT IX',
        '100 FOR IY=0 TO 2: FOR IZ=0 TO 2',
        '110 IF CL(2,IY,IZ,2)<>3 THEN OK=0',
        '120 IF CL(0,IY,IZ,3)<>6 THEN OK=0',
        '130 NEXT IZ: NEXT IY',
        '140 FOR IX=0 TO 2: FOR IZ=0 TO 2',
        '150 IF CL(IX,0,IZ,4)<>2 THEN OK=0',
        '160 IF CL(IX,2,IZ,5)<>7 THEN OK=0',
        '170 NEXT IZ: NEXT IX',
        '180 PRINT OK',
        '190 END',
    ]
    helpers.load_program(basic, program)
    results = helpers.run_to_completion(basic, max_frames=5000)
    errors = helpers.get_error_messages(results)
    assert errors == [], f"Errors: {errors}"
    texts = helpers.get_text_output(results)
    if expect_solved:
        assert any('1' in t for t in texts), f"Cube not solved after '{moves}'. Output: {texts}"
    else:
        assert any('0' in t for t in texts), f"Cube unexpectedly solved after '{moves}'. Output: {texts}"


class TestNewMoves:
    """Test L/D/B permutations via full program execution."""

    @pytest.mark.slow
    def test_left_four_times(self, basic, helpers):
        """L applied 4 times returns to solved state."""
        _run_move_test(basic, helpers, "LLLL")

    @pytest.mark.slow
    def test_down_four_times(self, basic, helpers):
        """D applied 4 times returns to solved state."""
        _run_move_test(basic, helpers, "DDDD")

    @pytest.mark.slow
    def test_back_four_times(self, basic, helpers):
        """B applied 4 times returns to solved state."""
        _run_move_test(basic, helpers, "BBBB")

    @pytest.mark.slow
    def test_left_cw_ccw_identity(self, basic, helpers):
        """L followed by L' returns to solved state."""
        _run_move_test(basic, helpers, "Ll")

    @pytest.mark.slow
    def test_down_cw_ccw_identity(self, basic, helpers):
        """D followed by D' returns to solved state."""
        _run_move_test(basic, helpers, "Dd")

    @pytest.mark.slow
    def test_back_cw_ccw_identity(self, basic, helpers):
        """B followed by B' returns to solved state."""
        _run_move_test(basic, helpers, "Bb")

    @pytest.mark.slow
    def test_all_moves_cw_ccw(self, basic, helpers):
        """Every move followed by its inverse returns to solved."""
        _run_move_test(basic, helpers, "RrUuFfLlDdBb")

    @pytest.mark.slow
    def test_sexy_move_six_times(self, basic, helpers):
        """R U R' U' applied 6 times returns to solved."""
        _run_move_test(basic, helpers, "RUruRUruRUruRUruRUruRUru")

    @pytest.mark.slow
    def test_left_changes_state(self, basic, helpers):
        """L once should NOT leave cube solved."""
        _run_move_test(basic, helpers, "L", expect_solved=False)

    @pytest.mark.slow
    def test_t_perm_twice_identity(self, basic, helpers):
        """T-perm applied twice is identity."""
        t_perm = "RUrurFRRuruRUrf"
        _run_move_test(basic, helpers, t_perm + t_perm)
