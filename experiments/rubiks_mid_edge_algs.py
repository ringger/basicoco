"""
Experiment: Find correct middle edge insertion algorithms.

The FR/FL algorithms work. BR/BL do not, because our engine's
U CW direction (F→L→B→R) is opposite standard (F→R→B→L).
Face substitution from FR/FL to BR/BL fails for this reason.

Strategy: For each slot, set up a controlled position (bottom solved,
target edge in top layer at the expected alignment position), try
candidate algorithms, and check the result.
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


def _run(basic, helpers, lines, max_frames=30000):
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


class TestDiagnoseBRBL:
    """Diagnose what happens with BR and BL insertion."""

    def test_D_scramble_edge_states(self, basic, helpers):
        """After 'D' scramble + bottom solve, print all mid edge states."""
        out = _run(basic, helpers, [
            '9000 MS$="D": GOSUB DoMoves',
            '9010 GOSUB SolveBottomCross',
            '9020 GOSUB CheckBottomCross',
            '9030 GOSUB SolveBottomCorners',
            '9040 GOSUB CheckBottomCorners',
            # Now check all 4 middle edges
            '9050 TC1=4: TC2=3: GOSUB FindEdge: PRINT "FR: EP=";EP;" EO=";EO',
            '9060 TC1=4: TC2=6: GOSUB FindEdge: PRINT "FL: EP=";EP;" EO=";EO',
            '9070 TC1=5: TC2=3: GOSUB FindEdge: PRINT "BR: EP=";EP;" EO=";EO',
            '9080 TC1=5: TC2=6: GOSUB FindEdge: PRINT "BL: EP=";EP;" EO=";EO',
            '9090 END',
        ])
        for t in out:
            print(t)

    def test_D_scramble_step_through_BL(self, basic, helpers):
        """Step through BL insertion after D scramble."""
        out = _run(basic, helpers, [
            '9000 MS$="D": GOSUB DoMoves',
            '9010 GOSUB SolveBottomCross',
            '9015 GOSUB CheckBottomCross',
            '9020 GOSUB SolveBottomCorners',
            '9025 GOSUB CheckBottomCorners',
            # Solve FR, FL, BR first
            '9030 TC1=4: TC2=3: EI=0: GOSUB SolveMidEdge',
            '9035 TC1=4: TC2=6: EI=1: GOSUB SolveMidEdge',
            '9040 TC1=5: TC2=3: EI=2: GOSUB SolveMidEdge',
            # Now trace BL
            '9050 TC1=5: TC2=6: EI=3',
            '9055 GOSUB FindEdge: PRINT "BL BEFORE: EP=";EP;" EO=";EO',
            # If in middle, extract
            '9060 IF EP<8 OR EP>11 THEN 9070',
            '9062 PRINT "  EXTRACTING FROM EP=";EP',
            '9065 GOSUB ExtractMidEdge',
            '9067 GOSUB FindEdge: PRINT "  AFTER EXTRACT: EP=";EP;" EO=";EO',
            # Align
            '9070 GOSUB AlignMidEdge',
            '9075 GOSUB FindEdge: PRINT "  AFTER ALIGN: EP=";EP;" EO=";EO',
            # Try insertion
            '9080 PRINT "  INSERTING (EI=3, EP=";EP;")"',
            '9085 GOSUB InsertMidEdge',
            '9090 GOSUB FindEdge: PRINT "  AFTER INSERT: EP=";EP;" EO=";EO',
            # Check
            '9100 IF EP=11 AND EO=0 THEN PRINT "BL SOLVED!": END',
            # Try again
            '9110 PRINT "  RETRY..."',
            '9115 IF EP>=8 AND EP<=11 THEN GOSUB ExtractMidEdge',
            '9120 GOSUB FindEdge: PRINT "  AFTER RE-EXTRACT: EP=";EP;" EO=";EO',
            '9125 GOSUB AlignMidEdge',
            '9130 GOSUB FindEdge: PRINT "  AFTER RE-ALIGN: EP=";EP;" EO=";EO',
            '9135 GOSUB InsertMidEdge',
            '9140 GOSUB FindEdge: PRINT "  AFTER RE-INSERT: EP=";EP;" EO=";EO',
            '9145 IF EP=11 AND EO=0 THEN PRINT "BL SOLVED!": END',
            '9150 PRINT "BL STILL NOT SOLVED"',
            '9160 END',
        ])
        for t in out:
            print(t)


class TestBruteForceAlgorithms:
    """Try all plausible 8-move insertion algorithms for BR and BL."""

    def _test_insert_alg(self, basic, helpers, scramble, target_slot,
                         tc1, tc2, ei, target_ep, alg_name, alg_moves):
        """Set up position, try algorithm, check result."""
        # Target middle slot sticker checks
        checks = {
            8:  'CL(2,1,0,0)={tc1} AND CL(2,1,0,2)={tc2}',   # FR
            9:  'CL(0,1,0,0)={tc1} AND CL(0,1,0,3)={tc2}',   # FL
            10: 'CL(2,1,2,1)={tc1} AND CL(2,1,2,2)={tc2}',   # BR
            11: 'CL(0,1,2,1)={tc1} AND CL(0,1,2,3)={tc2}',   # BL
        }
        check = checks[target_ep].format(tc1=tc1, tc2=tc2)
        # Bottom integrity check
        cross = ('CL(1,2,0,5)=7 AND CL(1,2,0,0)=4 AND '
                 'CL(2,2,1,5)=7 AND CL(2,2,1,2)=3 AND '
                 'CL(1,2,2,5)=7 AND CL(1,2,2,1)=5 AND '
                 'CL(0,2,1,5)=7 AND CL(0,2,1,3)=6')
        corners = ('CL(2,2,0,5)=7 AND CL(2,2,0,0)=4 AND CL(2,2,0,2)=3 AND '
                   'CL(0,2,0,5)=7 AND CL(0,2,0,0)=4 AND CL(0,2,0,3)=6 AND '
                   'CL(2,2,2,5)=7 AND CL(2,2,2,1)=5 AND CL(2,2,2,2)=3 AND '
                   'CL(0,2,2,5)=7 AND CL(0,2,2,1)=5 AND CL(0,2,2,3)=6')

        out = _run(basic, helpers, [
            f'9000 MS$="{scramble}": GOSUB DoMoves',
            '9010 GOSUB SolveBottomCross',
            '9015 GOSUB CheckBottomCross',
            '9020 GOSUB SolveBottomCorners',
            '9025 GOSUB CheckBottomCorners',
            # Find edge and align
            f'9030 TC1={tc1}: TC2={tc2}: EI={ei}',
            '9035 GOSUB FindEdge',
            '9037 IF EP>=8 AND EP<=11 THEN GOSUB ExtractMidEdge',
            '9038 GOSUB FindEdge',
            '9040 GOSUB AlignMidEdge',
            '9045 GOSUB FindEdge',
            '9050 PRINT "PRE: EP=";EP;" EO=";EO',
            # Apply test algorithm
            f'9060 MS$="{alg_moves}": GOSUB DoMoves',
            # Check edge
            f'9070 TC1={tc1}: TC2={tc2}: GOSUB FindEdge',
            '9075 PRINT "POST: EP=";EP;" EO=";EO',
            f'9080 IF {check} THEN PRINT "EDGE OK" ELSE PRINT "EDGE BAD"',
            f'9090 IF {cross} THEN PRINT "CROSS OK" ELSE PRINT "CROSS BAD"',
            f'9100 IF {corners} THEN PRINT "CORNERS OK" ELSE PRINT "CORNERS BAD"',
            '9110 END',
        ])
        return out

    def test_BR_candidates(self, basic, helpers):
        """Test BR insertion algorithms with various scrambles."""
        # BR: TC1=5(buff), TC2=3(blue), EI=2, target EP=10
        # After align: EP=5 (side on right, EO=0) or EP=6 (side on back, EO=1)
        #
        # Candidates derived by face substitution F→R, R→B from FR:
        #   FR EP=4: URurufUF → BR EP=5: UBuburUR
        #   FR EP=5: ufUFURur → BR EP=6: urURUBub
        #
        # Additional candidates with swapped U/u (for reversed engine direction):
        #   BR EP=5: uBUbURur  (swap all U↔u)
        #   BR EP=6: URurubUB  (swap all U↔u)
        #
        # By F→B, R→R substitution from FR:
        #   FR EP=4: URurufUF → BR EP=?: URuruBUb
        #   FR EP=5: ufUFURur → BR EP=?: uBUbURur
        #
        # By complete reflection (F↔B, swap U↔u):
        #   FR EP=4: URurufUF → BR EP=?: uRUrUFuf   (reflect)
        #   FR EP=5: ufUFURur → BR EP=?: UFufuRUr   (reflect)

        candidates = [
            # face sub F→R, R→B
            ("sub_FR_ep4", "UBuburUR"),
            ("sub_FR_ep5", "urURUBub"),
            # swap U/u in above
            ("swap_ep4", "uBUbURur"),
            ("swap_ep5", "URurubUB"),
            # sub F→B, R→R
            ("sub_FB_ep4", "URuruBUb"),
            ("sub_FB_ep5", "uBUbURur"),
            # reflection
            ("reflect_ep4", "uRUrUFuf"),
            ("reflect_ep5", "UFufuRUr"),
            # sub F→R, R→B with swapped direction
            ("dir_swap1", "ubUBurUR"),
            ("dir_swap2", "URuruBUb"),
        ]

        scrambles = ["D", "B", "RUru"]
        for scramble in scrambles:
            print(f"\n=== BR after scramble '{scramble}' ===")
            for name, moves in candidates:
                out = self._test_insert_alg(
                    basic, helpers, scramble, "BR",
                    5, 3, 2, 10, name, moves
                )
                pre = [t for t in out if 'PRE:' in t]
                post = [t for t in out if 'POST:' in t]
                edge = [t for t in out if 'EDGE' in t and 'EDGE' != 'MERGED']
                cross = [t for t in out if 'CROSS' in t and 'MERGED' not in t and 'STEP' not in t]
                corners_out = [t for t in out if 'CORNERS' in t and 'MERGED' not in t and 'STEP' not in t]
                pre_s = pre[0].strip() if pre else "?"
                post_s = post[0].strip() if post else "?"
                edge_s = edge[-1].strip() if edge else "?"
                cross_s = cross[-1].strip() if cross else "?"
                corners_s = corners_out[-1].strip() if corners_out else "?"
                print(f"  {name:15s} ({moves:8s}): {pre_s} → {post_s} | {edge_s} {cross_s} {corners_s}")

    def test_BL_candidates(self, basic, helpers):
        """Test BL insertion algorithms with various scrambles."""
        # BL: TC1=5(buff), TC2=6(cyan), EI=3, target EP=11
        # After align: EP=7 (side on left, EO=0) or EP=6 (side on back, EO=1)
        #
        # Candidates derived by face substitution F→L, L→B from FL:
        #   FL EP=4: ulULUFuf → BL EP=7: ubUBULul
        #   FL EP=7: UFufulUL → BL EP=6: ULulubuB  (THIS IS SUSPECTED BAD)
        #
        # Additional candidates:
        #   swap U/u: UbubulUL, uLUlUBUb
        #   sub F→B: ubUBULul, UBubuLUl

        candidates = [
            # face sub F→L, L→B from FL
            ("sub_FL_ep4", "ubUBULul"),
            ("sub_FL_ep7", "ULulubuB"),
            # swap U/u in above
            ("swap_ep4", "UbubulUL"),
            ("swap_ep7", "uLUlUBUb"),
            # sub F→B, L→L from FL
            ("sub_FB_ep4", "ulULUBub"),
            ("sub_FB_ep7", "UBubulUL"),
            # reverse of FL alg
            ("rev_FL_ep4", "UBubULul"),
            ("rev_FL_ep7", "ulULubUB"),
            # try BR's working pair, adapted
            ("from_BR_1", "ubUBulUL"),
            ("from_BR_2", "ULulUBub"),
        ]

        scrambles = ["D", "B", "RUru"]
        for scramble in scrambles:
            print(f"\n=== BL after scramble '{scramble}' ===")
            for name, moves in candidates:
                out = self._test_insert_alg(
                    basic, helpers, scramble, "BL",
                    5, 6, 3, 11, name, moves
                )
                pre = [t for t in out if 'PRE:' in t]
                post = [t for t in out if 'POST:' in t]
                edge = [t for t in out if 'EDGE' in t and 'MERGED' not in t]
                cross = [t for t in out if 'CROSS' in t and 'MERGED' not in t and 'STEP' not in t]
                corners_out = [t for t in out if 'CORNERS' in t and 'MERGED' not in t and 'STEP' not in t]
                pre_s = pre[0].strip() if pre else "?"
                post_s = post[0].strip() if post else "?"
                edge_s = edge[-1].strip() if edge else "?"
                cross_s = cross[-1].strip() if cross else "?"
                corners_s = corners_out[-1].strip() if corners_out else "?"
                print(f"  {name:15s} ({moves:8s}): {pre_s} → {post_s} | {edge_s} {cross_s} {corners_s}")
