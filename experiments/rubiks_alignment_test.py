"""
Test U-turn alignment code in isolation.
Place a piece at a known top position, call alignment routine, verify it moves to target.
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


def _run(basic, helpers, lines):
    program = [
        '5 SAFETY OFF',
        '10 PMODE 4: SCREEN 1',
        '20 MERGE "lib_rubiks_engine"',
        '25 MERGE "lib_rubiks_solver"',
        '30 GOSUB InitCube',
        '35 AN=0',
    ] + lines
    helpers.load_program(basic, program)
    results = helpers.run_to_completion(basic, max_frames=10000)
    errors = helpers.get_error_messages(results)
    assert errors == [], f"Errors: {errors}"
    return helpers.get_text_output(results)


class TestEdgeAlignment:
    """Test AlignTop: move edge from current EP to target TI+4."""

    @pytest.mark.slow
    @pytest.mark.parametrize("start_ep,target_ti,u_moves", [
        # Edge starts at EP, target is TI, should need specific U turns
        (4, 0, 0),  # EP4 -> TI0 (target EP4): no move needed
        (4, 1, 1),  # EP4 -> TI1 (target EP5): 1 CW
        (4, 2, 2),  # EP4 -> TI2 (target EP6): 2 turns
        (4, 3, 3),  # EP4 -> TI3 (target EP7): 1 CCW
        (5, 0, 3),  # EP5 -> TI0 (target EP4): 1 CCW
        (7, 2, 1),  # EP7 -> TI2 (target EP6): 1 CW
        (6, 0, 2),  # EP6 -> TI0 (target EP4): 2 turns
    ])
    def test_align_top_edge(self, basic, helpers, start_ep, target_ti, u_moves):
        """AlignTop moves edge from start_ep to target TI+4."""
        # Move a known edge to start_ep using U turns from EP4
        setup_moves = {4: "", 5: "U", 6: "UU", 7: "u"}
        setup = setup_moves[start_ep]
        target_ep = target_ti + 4

        out = _run(basic, helpers, [
            # Use front edge (TC1=7, TC2=4) which starts at EP4 (bottom) -> kick to top
            f'40 MS$="FF": GOSUB DoMoves',  # kick front edge to EP4
            f'45 IF LEN("{setup}")>0 THEN MS$="{setup}": GOSUB DoMoves' if setup else '45 REM no setup',
            # Now edge is at start_ep. Set up FindEdge params and find it
            f'50 TC1=7: TC2=4: GOSUB FindEdge',
            f'55 PRINT "BEFORE: EP=";EP',
            # Set TI and EO=0 for aligned case, call AlignTop
            f'60 TI={target_ti}: EO=0: GOSUB AlignTop',
            # Re-find to verify
            f'70 TC1=7: TC2=4: GOSUB FindEdge',
            f'80 PRINT "AFTER: EP=";EP',
            f'90 IF EP={target_ep} THEN PRINT "ALIGN OK" ELSE PRINT "ALIGN FAIL"',
            '100 END',
        ])
        assert any('ALIGN OK' in t for t in out), f"Alignment failed: {out}"


class TestCornerAlignment:
    """Test AlignCornerTop: move corner from current CP to target CI+4."""

    @pytest.mark.slow
    @pytest.mark.parametrize("start_cp,target_ci", [
        (4, 0),  # CP4 -> CI0 (target CP4): no move
        (4, 1),  # CP4 -> CI1 (target CP5): need U turns
        (4, 2),  # CP4 -> CI2 (target CP6): need U turns
        (4, 3),  # CP4 -> CI3 (target CP7): need U turns
        (5, 0),  # CP5 -> CI0 (target CP4)
        (6, 1),  # CP6 -> CI1 (target CP5)
        (7, 0),  # CP7 -> CI0 (target CP4)
    ])
    def test_align_corner(self, basic, helpers, start_cp, target_ci):
        """AlignCornerTop moves corner from start_cp to target CI+4."""
        # Extract BFR corner (TC1=7,TC2=4,TC3=3) to top using standard R' U R'
        # With new engine: r = R' (CCW), U = U (CW). Standard extraction: R' U R = rUR...
        # but we need to find empirically. Use RuR (which is R U' R in standard = extracts)
        # Actually just try the standard white-corner extraction: R U R' = Rur
        # Corner cycle: 4->6->7->5->4
        u_from_4 = {4: "", 5: "uuu", 6: "U", 7: "UU"}
        setup = u_from_4[start_cp]
        target_cp = target_ci + 4

        out = _run(basic, helpers, [
            # Try multiple extractions to find one that works
            # Standard: R' U R (extract BFR up) = rUR in engine
            # Or: R U' R' (also extracts) = Rur in engine
            f'40 MS$="Rur": GOSUB DoMoves',
            f'45 TC1=7: TC2=4: TC3=3: GOSUB FindCorner',
            f'46 PRINT "EXTRACTED: CP=";CP',
            # Move to start_cp using U turns
            f'47 IF CP<4 THEN MS$="rUR": GOSUB DoMoves',
            f'48 TC1=7: TC2=4: TC3=3: GOSUB FindCorner',
            f'49 PRINT "EXTRACTED2: CP=";CP',
            # Now position at start_cp from wherever it landed
            # Find where it is and compute needed U turns
            f'50 IF LEN("{setup}")>0 THEN MS$="{setup}": GOSUB DoMoves' if setup else '50 REM no setup',
            f'55 TC1=7: TC2=4: TC3=3: GOSUB FindCorner',
            f'56 PRINT "SETUP: CP=";CP',
            # Call AlignCornerTop
            f'60 CI={target_ci}: GOSUB AlignCornerTop',
            # Verify
            f'70 TC1=7: TC2=4: TC3=3: GOSUB FindCorner',
            f'80 PRINT "AFTER: CP=";CP',
            f'90 IF CP={target_cp} THEN PRINT "ALIGN OK" ELSE PRINT "ALIGN FAIL"',
            '100 END',
        ])
        assert any('ALIGN OK' in t for t in out), f"Alignment failed: {out}"


class TestMidEdgeAlignment:
    """Test AlignMidEdge: align top edge so side sticker matches center."""

    @pytest.mark.slow
    @pytest.mark.parametrize("tc1,tc2,ei,expected_ep_eo0", [
        # FR edge: TC1=4(front), TC2=3(right), EI=0
        # EO=0 -> side=TC2=3(right) -> target EP5
        (4, 3, 0, 5),
        # FL edge: TC1=4(front), TC2=6(left), EI=1
        # EO=0 -> side=TC2=6(left) -> target EP7
        (4, 6, 1, 7),
        # BR edge: TC1=5(back), TC2=3(right), EI=2
        # EO=0 -> side=TC2=3(right) -> target EP5
        (5, 3, 2, 5),
        # BL edge: TC1=5(back), TC2=6(left), EI=3
        # EO=0 -> side=TC2=6(left) -> target EP7
        (5, 6, 3, 7),
    ])
    def test_align_mid_edge(self, basic, helpers, tc1, tc2, ei, expected_ep_eo0):
        """AlignMidEdge rotates U until side sticker matches face center."""
        # Extract the target edge to top, then call AlignMidEdge
        extract_algs = {0: "UruRufUF", 1: "uLUlUFuf", 2: "UBubuRUr", 3: "UluLubUB"}
        extract = extract_algs[ei]

        out = _run(basic, helpers, [
            f'40 MS$="{extract}": GOSUB DoMoves',
            f'50 TC1={tc1}: TC2={tc2}: GOSUB FindEdge',
            f'55 PRINT "BEFORE: EP=";EP;" EO=";EO',
            f'60 EI={ei}: GOSUB AlignMidEdge',
            f'70 TC1={tc1}: TC2={tc2}: GOSUB FindEdge',
            f'80 PRINT "AFTER: EP=";EP;" EO=";EO',
            f'90 IF EP={expected_ep_eo0} AND EO=0 THEN PRINT "ALIGN OK"',
            f'91 IF EO=1 THEN PRINT "ALIGN OK"',
            f'92 IF EP<>{expected_ep_eo0} AND EO=0 THEN PRINT "ALIGN FAIL"',
            '100 END',
        ])
        assert any('ALIGN OK' in t for t in out), f"Alignment failed: {out}"
