"""
Verify that R, U, L CW directions match standard Rubik's notation.

Standard R CW (viewed from right): front->top->back->bottom->front
Standard U CW (viewed from top):   front->right->back->left->front
Standard L CW (viewed from left):  front->bottom->back->top->front

On a solved cube:
- Front face (z=0) = color 4 (green)
- Back face (z=2)  = color 5 (cyan)
- Right face (x=2) = color 3 (red)
- Left face (x=0)  = color 6 (blue)
- Top face (y=0)   = color 2 (yellow)
- Bottom face (y=2) = color 7 (magenta)
"""

import os
import shutil
import pytest


@pytest.fixture(autouse=True)
def setup_engine(temp_programs_dir):
    src = os.path.join(os.path.dirname(__file__), '..', '..', 'programs', 'lib_rubiks_engine.bas')
    shutil.copy(os.path.abspath(src), os.path.join(temp_programs_dir, 'lib_rubiks_engine.bas'))


def _run(basic, helpers, moves, checks):
    """Apply moves to solved cube, print sticker values for checking."""
    lines = [
        '5 SAFETY OFF',
        '10 PMODE 4: SCREEN 1',
        '20 MERGE "lib_rubiks_engine"',
        '30 GOSUB InitCube',
        '35 AN=0',
        f'40 MS$="{moves}": GOSUB DoMoves',
    ]
    line_num = 100
    for label, expr in checks:
        lines.append(f'{line_num} PRINT "{label}=";{expr}')
        line_num += 10
    lines.append(f'{line_num} END')

    helpers.load_program(basic, lines)
    results = helpers.run_to_completion(basic, max_frames=5000)
    errors = helpers.get_error_messages(results)
    assert errors == [], f"Errors: {errors}"
    texts = helpers.get_text_output(results)
    return {t.split('=')[0].strip(): t.split('=')[1].strip() for t in texts if '=' in t}


class TestStandardDirections:
    """Test that engine CW directions match standard Rubik's notation."""

    @pytest.mark.slow
    def test_r_cw_direction(self, basic, helpers):
        """Standard R CW: front->top->back->bottom->front."""
        vals = _run(basic, helpers, "R", [
            ("FRM_F0", "CL(2,1,0,0)"),   # front-right-middle front sticker
            ("TRM_F4", "CL(2,0,1,4)"),   # top-right-middle top sticker
            ("BRM_F1", "CL(2,1,2,1)"),   # back-right-middle back sticker
            ("DRM_F5", "CL(2,2,1,5)"),   # bottom-right-middle bottom sticker
        ])
        assert vals["TRM_F4"] == "4", f"Top should have green(4) from front, got {vals['TRM_F4']}"
        assert vals["BRM_F1"] == "2", f"Back should have yellow(2) from top, got {vals['BRM_F1']}"
        assert vals["DRM_F5"] == "5", f"Bottom should have cyan(5) from back, got {vals['DRM_F5']}"
        assert vals["FRM_F0"] == "7", f"Front should have magenta(7) from bottom, got {vals['FRM_F0']}"

    @pytest.mark.slow
    def test_u_cw_direction(self, basic, helpers):
        """Standard U CW (viewed from above): F->L, R->F, B->R, L->B.

        CW from above maps like clock: Back(12)->Right(3)->Front(6)->Left(9).
        Pieces at Front move to Left; what appears at Front is what was at Right.
        """
        vals = _run(basic, helpers, "U", [
            ("FTM_F0", "CL(1,0,0,0)"),   # front-top-middle front sticker
            ("LTM_F3", "CL(0,0,1,3)"),   # left-top-middle left sticker
            ("BTM_F1", "CL(1,0,2,1)"),   # back-top-middle back sticker
            ("RTM_F2", "CL(2,0,1,2)"),   # right-top-middle right sticker
        ])
        # After U CW: F shows old R(3), R shows old B(5), B shows old L(6), L shows old F(4)
        assert vals["FTM_F0"] == "3", f"Front should have blue(3) from right, got {vals['FTM_F0']}"
        assert vals["RTM_F2"] == "5", f"Right should have buff(5) from back, got {vals['RTM_F2']}"
        assert vals["BTM_F1"] == "6", f"Back should have cyan(6) from left, got {vals['BTM_F1']}"
        assert vals["LTM_F3"] == "4", f"Left should have red(4) from front, got {vals['LTM_F3']}"

    @pytest.mark.slow
    def test_l_cw_direction(self, basic, helpers):
        """Standard L CW: front->bottom->back->top->front."""
        vals = _run(basic, helpers, "L", [
            ("FLM_F0", "CL(0,1,0,0)"),   # front-left-middle front sticker
            ("DLM_F5", "CL(0,2,1,5)"),   # bottom-left-middle bottom sticker
            ("BLM_F1", "CL(0,1,2,1)"),   # back-left-middle back sticker
            ("TLM_F4", "CL(0,0,1,4)"),   # top-left-middle top sticker
        ])
        assert vals["DLM_F5"] == "4", f"Bottom should have green(4) from front, got {vals['DLM_F5']}"
        assert vals["BLM_F1"] == "7", f"Back should have magenta(7) from bottom, got {vals['BLM_F1']}"
        assert vals["TLM_F4"] == "5", f"Top should have cyan(5) from back, got {vals['TLM_F4']}"
        assert vals["FLM_F0"] == "2", f"Front should have yellow(2) from top, got {vals['FLM_F0']}"
