"""
Tests for Rubik's cube solver Step 4 — Top Cross (OLL Edges).

Verifies that FRUruf (F R U R' U' F') correctly transitions:
dot -> L-shape -> line -> cross on the top face edge stickers,
without disrupting F2L.
"""

import os
import shutil
import pytest


@pytest.fixture(autouse=True)
def setup_engine(temp_programs_dir):
    """Copy lib_rubiks_engine.bas into the temp programs dir."""
    src = os.path.join(os.path.dirname(__file__), '..', '..', 'programs', 'lib_rubiks_engine.bas')
    shutil.copy(os.path.abspath(src), os.path.join(temp_programs_dir, 'lib_rubiks_engine.bas'))


def _run_top_cross_program(basic, helpers, program_lines, max_frames=10000):
    """Run a program and return (errors, texts)."""
    helpers.load_program(basic, program_lines)
    results = helpers.run_to_completion(basic, max_frames=max_frames)
    errors = helpers.get_error_messages(results)
    texts = helpers.get_text_output(results)
    return errors, texts


def _make_diagnostic_program(setup_moves):
    """Build program that shows top edge yellow pattern after setup moves."""
    return [
        '5 SAFETY OFF',
        '10 PMODE 4: SCREEN 1',
        '20 MERGE "lib_rubiks_engine"',
        '30 GOSUB InitCube',
        f'40 MS$="{setup_moves}": GOSUB DoMoves',
        '50 YC=0',
        '60 IF CL(1,0,0,4)=2 THEN YC=YC+1',
        '70 IF CL(2,0,1,4)=2 THEN YC=YC+1',
        '80 IF CL(1,0,2,4)=2 THEN YC=YC+1',
        '90 IF CL(0,0,1,4)=2 THEN YC=YC+1',
        # Print individual edges: F, R, B, L
        '100 F1=0: R1=0: B1=0: L1=0',
        '110 IF CL(1,0,0,4)=2 THEN F1=1',
        '120 IF CL(2,0,1,4)=2 THEN R1=1',
        '130 IF CL(1,0,2,4)=2 THEN B1=1',
        '140 IF CL(0,0,1,4)=2 THEN L1=1',
        '150 PRINT "YC=";YC;" F=";F1;" R=";R1;" B=";B1;" L=";L1',
        '160 END',
    ]


ALGO = "FRUruf"  # F R U R' U' F'


@pytest.mark.slow
class TestTopCrossAlgorithm:
    """Verify F R U R' U' F' algorithm behavior."""

    def test_solved_has_four_yellow(self, basic, helpers):
        """Solved cube has 4 yellow top edges."""
        errors, texts = _run_top_cross_program(basic, helpers,
            _make_diagnostic_program(""))
        assert errors == [], f"Errors: {errors}"
        assert any('YC= 4' in t for t in texts), f"Expected YC=4: {texts}"

    def test_algo_preserves_f2l(self, basic, helpers):
        """FRUruf preserves F2L — all bottom corners and middle edges stay intact."""
        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "lib_rubiks_engine"',
            '30 GOSUB InitCube',
            f'40 MS$="{ALGO}": GOSUB DoMoves',
            # Check all 4 bottom corners
            '50 IF CL(2,2,0,5)=7 AND CL(2,2,0,0)=4 AND CL(2,2,0,2)=3 THEN PRINT "BFR OK" ELSE PRINT "BFR MOVED"',
            '60 IF CL(0,2,0,5)=7 AND CL(0,2,0,0)=4 AND CL(0,2,0,3)=6 THEN PRINT "BFL OK" ELSE PRINT "BFL MOVED"',
            '70 IF CL(2,2,2,5)=7 AND CL(2,2,2,1)=5 AND CL(2,2,2,2)=3 THEN PRINT "BBR OK" ELSE PRINT "BBR MOVED"',
            '80 IF CL(0,2,2,5)=7 AND CL(0,2,2,1)=5 AND CL(0,2,2,3)=6 THEN PRINT "BBL OK" ELSE PRINT "BBL MOVED"',
            # Check all 4 middle edges
            '90 IF CL(2,1,0,0)=4 AND CL(2,1,0,2)=3 THEN PRINT "FR OK" ELSE PRINT "FR MOVED"',
            '100 IF CL(0,1,0,0)=4 AND CL(0,1,0,3)=6 THEN PRINT "FL OK" ELSE PRINT "FL MOVED"',
            '110 IF CL(2,1,2,1)=5 AND CL(2,1,2,2)=3 THEN PRINT "BR OK" ELSE PRINT "BR MOVED"',
            '120 IF CL(0,1,2,1)=5 AND CL(0,1,2,3)=6 THEN PRINT "BL OK" ELSE PRINT "BL MOVED"',
            # Check bottom cross
            '130 IF CL(1,2,0,5)=7 AND CL(1,2,0,0)=4 THEN PRINT "DF OK" ELSE PRINT "DF MOVED"',
            '140 IF CL(2,2,1,5)=7 AND CL(2,2,1,2)=3 THEN PRINT "DR OK" ELSE PRINT "DR MOVED"',
            '150 IF CL(1,2,2,5)=7 AND CL(1,2,2,1)=5 THEN PRINT "DB OK" ELSE PRINT "DB MOVED"',
            '160 IF CL(0,2,1,5)=7 AND CL(0,2,1,3)=6 THEN PRINT "DL OK" ELSE PRINT "DL MOVED"',
            '200 END',
        ]
        errors, texts = _run_top_cross_program(basic, helpers, program)
        assert errors == [], f"Errors: {errors}"
        # ALL F2L pieces should be intact
        for piece in ['BFR', 'BFL', 'BBR', 'BBL', 'FR', 'FL', 'BR', 'BL', 'DF', 'DR', 'DB', 'DL']:
            assert any(f'{piece} OK' in t for t in texts), f"{piece} should be intact: {texts}"

    def test_algo_only_affects_top_edges(self, basic, helpers):
        """After applying FRUruf to solved cube, YC should be 0 or 2 (not 1 or 3)."""
        errors, texts = _run_top_cross_program(basic, helpers,
            _make_diagnostic_program(ALGO))
        assert errors == [], f"Errors: {errors}"
        # Extract YC value
        yc_line = [t for t in texts if 'YC=' in t][0]
        # YC should be even (0, 2, or 4)
        for val in ['YC= 0', 'YC= 2', 'YC= 4']:
            if val in yc_line:
                break
        else:
            assert False, f"Expected YC=0/2/4 but got: {yc_line}"

    def test_algo_order_six(self, basic, helpers):
        """FRUruf applied 6 times returns cube to identity (standard order for this OLL algorithm)."""
        algo_6 = ALGO * 6
        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "lib_rubiks_engine"',
            '30 GOSUB InitCube',
            f'40 MS$="{algo_6}": GOSUB DoMoves',
            # Check representative pieces for identity
            '50 IF CL(1,0,0,4)=2 AND CL(1,0,0,0)=4 THEN PRINT "TF OK" ELSE PRINT "TF MOVED"',
            '60 IF CL(2,0,1,4)=2 AND CL(2,0,1,2)=3 THEN PRINT "TR OK" ELSE PRINT "TR MOVED"',
            '70 IF CL(0,0,0,4)=2 AND CL(0,0,0,0)=4 AND CL(0,0,0,3)=6 THEN PRINT "TFL OK" ELSE PRINT "TFL MOVED"',
            '80 IF CL(2,2,0,5)=7 AND CL(2,2,0,0)=4 AND CL(2,2,0,2)=3 THEN PRINT "BFR OK" ELSE PRINT "BFR MOVED"',
            '90 END',
        ]
        errors, texts = _run_top_cross_program(basic, helpers, program, max_frames=50000)
        assert errors == [], f"Errors: {errors}"
        for piece in ['TF', 'TR', 'TFL', 'BFR']:
            assert any(f'{piece} OK' in t for t in texts), f"{piece} should be intact: {texts}"

    def test_dot_to_cross_pipeline(self, basic, helpers):
        """Full dot->L->line->cross pipeline using FRUruf with correct U pre-rotations."""
        program = [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "lib_rubiks_engine"',
            '30 GOSUB InitCube',
            # Step 4 algorithm
            f'35 A$="{ALGO}"',
            # Apply algo 3 times to solved to scramble top edges
            f'40 MS$="{ALGO}{ALGO}{ALGO}": GOSUB DoMoves',
            # Count yellow top edges
            '50 YC=0',
            '60 IF CL(1,0,0,4)=2 THEN YC=YC+1',
            '70 IF CL(2,0,1,4)=2 THEN YC=YC+1',
            '80 IF CL(1,0,2,4)=2 THEN YC=YC+1',
            '90 IF CL(0,0,1,4)=2 THEN YC=YC+1',
            '100 PRINT "START:";YC',
            # Now implement the Step 4 loop (up to 4 algo applications)
            '110 FOR IT=1 TO 4',
            '120 YC=0',
            '130 IF CL(1,0,0,4)=2 THEN YC=YC+1',
            '140 IF CL(2,0,1,4)=2 THEN YC=YC+1',
            '150 IF CL(1,0,2,4)=2 THEN YC=YC+1',
            '160 IF CL(0,0,1,4)=2 THEN YC=YC+1',
            '170 IF YC=4 THEN PRINT "CROSS DONE AT IT=";IT: GOTO 500',
            # Dot case (YC=0): apply directly
            '180 IF YC=0 THEN PRINT "DOT": MS$=A$: GOSUB DoMoves: GOTO 400',
            # YC=2: distinguish L-shape from line
            '190 IF YC<>2 THEN PRINT "UNEXPECTED YC=";YC: GOTO 500',
            # Check if L-shape (adjacent) or line (opposite)
            '200 TF1=CL(1,0,0,4): TR1=CL(2,0,1,4): TB1=CL(1,0,2,4): TL1=CL(0,0,1,4)',
            # Line: front+back or left+right
            '210 IF TF1=2 AND TB1=2 THEN GOTO 300',
            '220 IF TL1=2 AND TR1=2 THEN GOTO 300',
            # L-shape: rotate U until back+left are yellow
            '230 PRINT "L-SHAPE"',
            '240 FOR J=1 TO 4',
            '250 IF CL(1,0,2,4)=2 AND CL(0,0,1,4)=2 THEN GOTO 280',
            '260 MS$="U": GOSUB DoMoves',
            '270 NEXT J',
            '280 MS$=A$: GOSUB DoMoves: GOTO 400',
            # Line: rotate U until left+right are yellow
            '300 PRINT "LINE"',
            '310 FOR J=1 TO 4',
            '320 IF CL(2,0,1,4)=2 AND CL(0,0,1,4)=2 THEN GOTO 350',
            '330 MS$="U": GOSUB DoMoves',
            '340 NEXT J',
            '350 MS$=A$: GOSUB DoMoves: GOTO 400',
            '400 NEXT IT',
            '410 PRINT "FAILED AFTER 4 ITERATIONS"',
            '500 END',
        ]
        errors, texts = _run_top_cross_program(basic, helpers, program, max_frames=20000)
        assert errors == [], f"Errors: {errors}"
        assert any('CROSS DONE' in t for t in texts), \
            f"Did not achieve cross. Output: {texts}"
