"""
Determine the U CW edge and corner cycles empirically.
Place a known piece at each top position, do U CW, see where it ends up.
"""

import os
import shutil
import pytest


@pytest.fixture(autouse=True)
def setup_engine(temp_programs_dir):
    src = os.path.join(os.path.dirname(__file__), '..', 'programs', 'lib_rubiks_engine.bas')
    shutil.copy(os.path.abspath(src), os.path.join(temp_programs_dir, 'lib_rubiks_engine.bas'))


def _run(basic, helpers, lines):
    helpers.load_program(basic, [
        '5 SAFETY OFF',
        '10 PMODE 4: SCREEN 1',
        '20 MERGE "lib_rubiks_engine"',
        '30 GOSUB InitCube',
        '35 AN=0',
    ] + lines)
    results = helpers.run_to_completion(basic, max_frames=5000)
    errors = helpers.get_error_messages(results)
    assert errors == [], f"Errors: {errors}"
    return helpers.get_text_output(results)


class TestUCycle:
    @pytest.mark.slow
    def test_edge_cycle(self, basic, helpers):
        """After U CW, which EP does each top edge move to?"""
        # Place unique colors at each top edge, do U, read positions
        out = _run(basic, helpers, [
            # Mark each top edge with a unique color on face A (top face)
            # EP4: (1,0,0) F4 - front top edge
            # EP5: (2,0,1) F4 - right top edge
            # EP6: (1,0,2) F4 - back top edge
            # EP7: (0,0,1) F4 - left top edge
            # After U, check where each side sticker went
            # Use the side stickers which are unique per edge on solved cube:
            # EP4 side: CL(1,0,0,0) = 4 (front/green)
            # EP5 side: CL(2,0,1,2) = 3 (right/red)
            # EP6 side: CL(1,0,2,1) = 5 (back/cyan)
            # EP7 side: CL(0,0,1,3) = 6 (left/blue)
            '40 MS$="U": GOSUB DoMoves',
            # Now check where each color ended up
            '50 PRINT "EP4_SIDE=";CL(1,0,0,0)',  # front edge side sticker
            '60 PRINT "EP5_SIDE=";CL(2,0,1,2)',  # right edge side sticker
            '70 PRINT "EP6_SIDE=";CL(1,0,2,1)',  # back edge side sticker
            '80 PRINT "EP7_SIDE=";CL(0,0,1,3)',  # left edge side sticker
            '90 END',
        ])
        vals = {t.split('=')[0].strip(): t.split('=')[1].strip() for t in out if '=' in t}
        # Print the cycle
        # If EP4 (front,green=4) moved to EP5 (right), then EP5_SIDE would be 4
        print(f"\nAfter U CW:")
        print(f"  EP4(front) side now has: {vals['EP4_SIDE']} (was 4/green)")
        print(f"  EP5(right) side now has: {vals['EP5_SIDE']} (was 3/red)")
        print(f"  EP6(back)  side now has: {vals['EP6_SIDE']} (was 5/cyan)")
        print(f"  EP7(left)  side now has: {vals['EP7_SIDE']} (was 6/blue)")

        # Determine cycle: which position now holds which original color
        cycle = {}
        for pos, orig in [('EP4', '4'), ('EP5', '3'), ('EP6', '5'), ('EP7', '6')]:
            val = vals[f"{pos}_SIDE"]
            src = {4: 'EP4(front)', 3: 'EP5(right)', 5: 'EP6(back)', 6: 'EP7(left)'}[int(val)]
            cycle[pos] = src
        print(f"\nEdge cycle (what moved TO each position):")
        for k, v in cycle.items():
            print(f"  {k} <- {v}")

    @pytest.mark.slow
    def test_corner_cycle(self, basic, helpers):
        """After U CW, which CP does each top corner move to?"""
        out = _run(basic, helpers, [
            # Corner positions and their front/back stickers (unique per corner on solved cube):
            # CP4 TFR (2,0,0): F0=4(front), F2=3(right)
            # CP5 TFL (0,0,0): F0=4(front), F3=6(left)
            # CP6 TBR (2,0,2): F1=5(back), F2=3(right)
            # CP7 TBL (0,0,2): F1=5(back), F3=6(left)
            '40 MS$="U": GOSUB DoMoves',
            # Check the front/back sticker at each corner position
            '50 PRINT "CP4_F0=";CL(2,0,0,0);",F2=";CL(2,0,0,2)',
            '60 PRINT "CP5_F0=";CL(0,0,0,0);",F3=";CL(0,0,0,3)',
            '70 PRINT "CP6_F1=";CL(2,0,2,1);",F2=";CL(2,0,2,2)',
            '80 PRINT "CP7_F1=";CL(0,0,2,1);",F3=";CL(0,0,2,3)',
            '90 END',
        ])
        print("\nAfter U CW, corner stickers:")
        for t in out:
            print(f"  {t.strip()}")
        # CP4(TFR) originally had F0=4,F2=3 (front+right)
        # CP5(TFL) originally had F0=4,F3=6 (front+left)
        # CP6(TBR) originally had F1=5,F2=3 (back+right)
        # CP7(TBL) originally had F1=5,F3=6 (back+left)
        # After U CW, see which corner's colors are at each position
