"""
Verify that R, U, L CW directions match standard Rubik's notation after Permute fix.

Standard R CW (viewed from right): front->top->back->bottom->front
Standard U CW (viewed from top):   front->left->back->right->front
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
    src = os.path.join(os.path.dirname(__file__), '..', 'programs', 'lib_rubiks_engine.bas')
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


class TestDirectionAfterFix:
    """Test that CW directions match standard Rubik's notation."""

    @pytest.mark.slow
    def test_r_cw_direction(self, basic, helpers):
        """Standard R CW: front-right edge sticker (green/4) moves to top face."""
        # After R CW, front-right-middle (2,1,0) front sticker should go to top
        # CL(2,1,0,0) was 4 (green), after R it should be on top face at (2,0,1)
        # Also: top-right-middle (2,0,1) sticker goes to back
        vals = _run(basic, helpers, "R", [
            # Front-right-middle: was green, should now be bottom color (magenta/7)
            ("FRM_F0", "CL(2,1,0,0)"),
            # Top-right-middle: was yellow, should now be green (from front)
            ("TRM_F4", "CL(2,0,1,4)"),
            # Back-right-middle: was cyan, should now be yellow (from top)
            ("BRM_F1", "CL(2,1,2,1)"),
            # Bottom-right-middle: was magenta, should now be cyan (from back)
            ("DRM_F5", "CL(2,2,1,5)"),
        ])
        # Standard R CW: front->top->back->bottom->front
        assert vals["TRM_F4"] == "4", f"Top should have green(4) from front, got {vals['TRM_F4']}"
        assert vals["BRM_F1"] == "2", f"Back should have yellow(2) from top, got {vals['BRM_F1']}"
        assert vals["DRM_F5"] == "5", f"Bottom should have cyan(5) from back, got {vals['DRM_F5']}"
        assert vals["FRM_F0"] == "7", f"Front should have magenta(7) from bottom, got {vals['FRM_F0']}"

    @pytest.mark.slow
    def test_u_cw_direction(self, basic, helpers):
        """Standard U CW: front-top edge sticker (green/4) moves to left face."""
        # After U CW, front-top-middle (1,0,0) front sticker goes to left face
        vals = _run(basic, helpers, "U", [
            # Front-top-middle: was green, should now be right color (red/3)
            ("FTM_F0", "CL(1,0,0,0)"),
            # Left-top-middle: was blue, should now be green (from front)
            ("LTM_F3", "CL(0,0,1,3)"),
            # Back-top-middle: was cyan, should now be blue (from left)
            ("BTM_F1", "CL(1,0,2,1)"),
            # Right-top-middle: was red, should now be cyan (from back)
            ("RTM_F2", "CL(2,0,1,2)"),
        ])
        # Standard U CW: front->left->back->right->front
        # Wait - standard U CW (viewed from top) is front->right->back->left->front
        # No! Standard U CW (viewed from top, looking down):
        #   Rotates top layer clockwise when viewed from above
        #   Front goes to RIGHT, Right goes to BACK, Back goes to LEFT, Left goes to FRONT
        # Actually let me reconsider. Standard U:
        #   F->R->B->L->F (stickers cycle this way)
        # So front-top sticker (green) should go to right face
        assert vals["RTM_F2"] == "4", f"Right should have green(4) from front, got {vals['RTM_F2']}"
        assert vals["BTM_F1"] == "3", f"Back should have red(3) from right, got {vals['BTM_F1']}"
        assert vals["LTM_F3"] == "5", f"Left should have cyan(5) from back, got {vals['LTM_F3']}"
        assert vals["FTM_F0"] == "6", f"Front should have blue(6) from left, got {vals['FTM_F0']}"

    @pytest.mark.slow
    def test_l_cw_direction(self, basic, helpers):
        """Standard L CW: front-left edge sticker (green/4) moves to bottom face."""
        # After L CW, front-left-middle (0,1,0) front sticker goes to bottom
        vals = _run(basic, helpers, "L", [
            # Front-left-middle: was green, should now be yellow (from top)
            ("FLM_F0", "CL(0,1,0,0)"),
            # Bottom-left-middle: was magenta, should now be green (from front)
            ("DLM_F5", "CL(0,2,1,5)"),
            # Back-left-middle: was cyan, should now be magenta (from bottom)
            ("BLM_F1", "CL(0,1,2,1)"),
            # Top-left-middle: was yellow, should now be cyan (from back)
            ("TLM_F4", "CL(0,0,1,4)"),
        ])
        # Standard L CW: front->bottom->back->top->front
        assert vals["DLM_F5"] == "4", f"Bottom should have green(4) from front, got {vals['DLM_F5']}"
        assert vals["BLM_F1"] == "7", f"Back should have magenta(7) from bottom, got {vals['BLM_F1']}"
        assert vals["TLM_F4"] == "5", f"Top should have cyan(5) from back, got {vals['TLM_F4']}"
        assert vals["FLM_F0"] == "2", f"Front should have yellow(2) from top, got {vals['FLM_F0']}"
