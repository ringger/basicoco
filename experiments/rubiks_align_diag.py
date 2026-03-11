"""
Diagnose AlignMidEdge: trace each step for BR edge.
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


class TestAlignDiag:
    @pytest.mark.slow
    def test_br_align_trace(self, basic, helpers):
        """Trace AlignMidEdge step by step for BR edge."""
        out = _run(basic, helpers, [
            # Scramble with D, solve cross+corners
            '40 MS$="D": GOSUB DoMoves',
            '50 GOSUB SolveBottomCross',
            '55 GOSUB SolveBottomCorners',
            # Find BR edge
            '60 TC1=5: TC2=3: GOSUB FindEdge',
            '65 PRINT "FOUND: EP=";EP;" EO=";EO',
            # Manually trace AlignMidEdge logic
            '70 IF EO=0 THEN SC=TC2 ELSE SC=TC1',
            '72 PRINT "SC=";SC',
            '73 IF SC=4 THEN TP=4',
            '74 IF SC=3 THEN TP=5',
            '75 IF SC=5 THEN TP=6',
            '76 IF SC=6 THEN TP=7',
            '77 PRINT "TP=";TP',
            # Compute U turns
            '80 IF EP=4 THEN CP=0',
            '81 IF EP=5 THEN CP=1',
            '82 IF EP=6 THEN CP=2',
            '83 IF EP=7 THEN CP=3',
            '84 IF TP=4 THEN DP=0',
            '85 IF TP=5 THEN DP=1',
            '86 IF TP=6 THEN DP=2',
            '87 IF TP=7 THEN DP=3',
            '88 NU=(DP-CP+4) MOD 4',
            '89 PRINT "CP=";CP;" DP=";DP;" NU=";NU',
            # Do the U turn
            '90 IF NU=1 THEN MS$="U": GOSUB DoMoves',
            '91 IF NU=2 THEN MS$="UU": GOSUB DoMoves',
            '92 IF NU=3 THEN MS$="u": GOSUB DoMoves',
            # Find edge again
            '95 TC1=5: TC2=3: GOSUB FindEdge',
            '96 PRINT "AFTER ALIGN: EP=";EP;" EO=";EO',
            # Also check all top edge stickers
            '100 PRINT "EP4: F4=";CL(1,0,0,4);" F0=";CL(1,0,0,0)',
            '101 PRINT "EP5: F4=";CL(2,0,1,4);" F2=";CL(2,0,1,2)',
            '102 PRINT "EP6: F4=";CL(1,0,2,4);" F1=";CL(1,0,2,1)',
            '103 PRINT "EP7: F4=";CL(0,0,1,4);" F3=";CL(0,0,1,3)',
            '110 END',
        ])
        for t in out:
            t = t.strip()
            if t and not t.startswith('SAFETY') and not t.startswith('(HARD') and not t.startswith('MERGED') and not t.startswith('STEP') and not t.startswith('  ') and not t.startswith('CROSS') and not t.startswith('CORNERS'):
                print(f"  {t}")
