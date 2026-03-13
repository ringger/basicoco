"""Validate engine's 6 basic face moves against pycuber.

Runs each move through the actual BASIC engine (via test harness)
and compares every sticker against pycuber.

Usage: python -m pytest tools/validate_moves.py -m slow -s
"""

import os
import shutil
import sys
import pytest
import pycuber

# Add project root to path so we can import from tests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def setup_engine(temp_programs_dir):
    src = os.path.join(os.path.dirname(__file__), '..', 'programs', 'lib_rubiks_engine.bas')
    shutil.copy(os.path.abspath(src), os.path.join(temp_programs_dir, 'lib_rubiks_engine.bas'))


def _dump_all_stickers_program(move_str):
    """Build BASIC program that applies move_str and prints all visible stickers.

    Prints each face as 9 color values in reading order (top-left to bottom-right).
    Format: FACE:c00,c01,c02,c10,c11,c12,c20,c21,c22
    """
    lines = [
        '5 SAFETY OFF',
        '10 PMODE 4: SCREEN 1',
        '20 MERGE "lib_rubiks_engine"',
        '30 GOSUB InitCube',
    ]
    if move_str:
        lines.append(f'40 MS$="{move_str}": GOSUB DoMoves')

    # Front face (iz=0, face 0): row=iy, col=ix
    lines.append('100 PRINT "F:";CL(0,0,0,0);CL(1,0,0,0);CL(2,0,0,0);CL(0,1,0,0);CL(1,1,0,0);CL(2,1,0,0);CL(0,2,0,0);CL(1,2,0,0);CL(2,2,0,0)')
    # Back face (iz=2, face 1): row=iy, col=ix (from behind: col reversed = 2-ix)
    lines.append('110 PRINT "B:";CL(2,0,2,1);CL(1,0,2,1);CL(0,0,2,1);CL(2,1,2,1);CL(1,1,2,1);CL(0,1,2,1);CL(2,2,2,1);CL(1,2,2,1);CL(0,2,2,1)')
    # Right face (ix=2, face 2): row=iy, col=iz
    lines.append('120 PRINT "R:";CL(2,0,0,2);CL(2,0,1,2);CL(2,0,2,2);CL(2,1,0,2);CL(2,1,1,2);CL(2,1,2,2);CL(2,2,0,2);CL(2,2,1,2);CL(2,2,2,2)')
    # Left face (ix=0, face 3): row=iy, col=iz (from left side: col reversed = 2-iz)
    lines.append('130 PRINT "L:";CL(0,0,2,3);CL(0,0,1,3);CL(0,0,0,3);CL(0,1,2,3);CL(0,1,1,3);CL(0,1,0,3);CL(0,2,2,3);CL(0,2,1,3);CL(0,2,0,3)')
    # Top face (iy=0, face 4): pycuber row 0=back(iz=2), row 2=front(iz=0), col=ix
    lines.append('140 PRINT "U:";CL(0,0,2,4);CL(1,0,2,4);CL(2,0,2,4);CL(0,0,1,4);CL(1,0,1,4);CL(2,0,1,4);CL(0,0,0,4);CL(1,0,0,4);CL(2,0,0,4)')
    # Bottom face (iy=2, face 5): row=iz (front first), col=ix
    lines.append('150 PRINT "D:";CL(0,2,0,5);CL(1,2,0,5);CL(2,2,0,5);CL(0,2,1,5);CL(1,2,1,5);CL(2,2,1,5);CL(0,2,2,5);CL(1,2,2,5);CL(2,2,2,5)')

    lines.append('200 END')
    return lines


# Engine color number → pycuber color name
# Engine: 2=yellow(top), 3=right, 4=green(front), 5=blue(back), 6=left, 7=white(bottom)
# pycuber: U=yellow, D=white, F=green, B=blue, R=orange, L=red
# Need to determine: engine 3 (right) = ? and engine 6 (left) = ?
# From InitColors: right face (ix=2) gets color 3, left face (ix=0) gets color 6
# pycuber solved: R=orange, L=red
# So engine 3 → orange, engine 6 → red
# BUT WAIT — that assumes our engine's "right" is pycuber's "right".
# We need to verify this by checking the solved state match.

ENGINE_TO_PYCOLOR = {
    2: 'yellow',
    7: 'white',
    4: 'green',
    5: 'blue',
    3: 'orange',  # right face — to be verified
    6: 'red',     # left face — to be verified
}


def parse_engine_output(texts):
    """Parse engine sticker dump into dict of face → 3x3 color grid."""
    faces = {}
    for t in texts:
        t = t.strip()
        for face_name in ['F', 'B', 'R', 'L', 'U', 'D']:
            prefix = face_name + ':'
            if t.startswith(prefix):
                # Values are space-separated integers after the prefix
                vals_str = t[len(prefix):]
                # BASIC PRINT with semicolons produces space-separated ints
                vals = [int(x) for x in vals_str.split()]
                grid = []
                for row in range(3):
                    grid.append([ENGINE_TO_PYCOLOR[vals[row*3 + col]] for col in range(3)])
                faces[face_name] = grid
    return faces


def pycuber_faces(cube):
    """Extract all faces from pycuber as dict of face → 3x3 color grid."""
    faces = {}
    for face_name in ['F', 'B', 'R', 'L', 'U', 'D']:
        face = cube.get_face(face_name)
        grid = []
        for row in range(3):
            grid.append([str(face[row][col].colour) for col in range(3)])
        faces[face_name] = grid
    return faces


def compare_faces(engine_faces, pyc_faces, label):
    """Compare and return list of differences."""
    diffs = []
    for face_name in ['F', 'B', 'R', 'L', 'U', 'D']:
        eng = engine_faces.get(face_name)
        pyc = pyc_faces.get(face_name)
        if eng is None:
            diffs.append(f"  {face_name}: missing from engine output")
            continue
        for r in range(3):
            for c in range(3):
                if eng[r][c] != pyc[r][c]:
                    diffs.append(f"  {face_name}[{r}][{c}]: engine={eng[r][c]}, pycuber={pyc[r][c]}")
    if diffs:
        print(f"\nMISMATCH after {label}:")
        for d in diffs:
            print(d)
    else:
        print(f"MATCH after {label}")
    return diffs


@pytest.mark.slow
class TestValidateMoves:

    def _run(self, basic, helpers, program, max_frames=10000):
        helpers.load_program(basic, program)
        results = helpers.run_to_completion(basic, max_frames=max_frames)
        errors = helpers.get_error_messages(results)
        texts = helpers.get_text_output(results)
        assert errors == [], f"BASIC errors: {errors}"
        return texts

    def test_solved_matches(self, basic, helpers):
        """Solved state should match between engine and pycuber."""
        texts = self._run(basic, helpers, _dump_all_stickers_program(""))
        eng = parse_engine_output(texts)
        pyc = pycuber_faces(pycuber.Cube())
        diffs = compare_faces(eng, pyc, "solved")
        assert diffs == [], f"Solved state mismatch"

    def test_move_R(self, basic, helpers):
        texts = self._run(basic, helpers, _dump_all_stickers_program("R"))
        eng = parse_engine_output(texts)
        c = pycuber.Cube(); c("R")
        diffs = compare_faces(eng, pycuber_faces(c), "R")
        assert diffs == [], f"R move mismatch"

    def test_move_U(self, basic, helpers):
        texts = self._run(basic, helpers, _dump_all_stickers_program("U"))
        eng = parse_engine_output(texts)
        c = pycuber.Cube(); c("U")
        diffs = compare_faces(eng, pycuber_faces(c), "U")
        assert diffs == [], f"U move mismatch"

    def test_move_F(self, basic, helpers):
        texts = self._run(basic, helpers, _dump_all_stickers_program("F"))
        eng = parse_engine_output(texts)
        c = pycuber.Cube(); c("F")
        diffs = compare_faces(eng, pycuber_faces(c), "F")
        assert diffs == [], f"F move mismatch"

    def test_move_L(self, basic, helpers):
        texts = self._run(basic, helpers, _dump_all_stickers_program("L"))
        eng = parse_engine_output(texts)
        c = pycuber.Cube(); c("L")
        diffs = compare_faces(eng, pycuber_faces(c), "L")
        assert diffs == [], f"L move mismatch"

    def test_move_D(self, basic, helpers):
        texts = self._run(basic, helpers, _dump_all_stickers_program("D"))
        eng = parse_engine_output(texts)
        c = pycuber.Cube(); c("D")
        diffs = compare_faces(eng, pycuber_faces(c), "D")
        assert diffs == [], f"D move mismatch"

    def test_move_B(self, basic, helpers):
        texts = self._run(basic, helpers, _dump_all_stickers_program("B"))
        eng = parse_engine_output(texts)
        c = pycuber.Cube(); c("B")
        diffs = compare_faces(eng, pycuber_faces(c), "B")
        assert diffs == [], f"B move mismatch"

    def test_FRUruf(self, basic, helpers):
        """The full F R U R' U' F' algorithm."""
        texts = self._run(basic, helpers, _dump_all_stickers_program("FRUruf"))
        eng = parse_engine_output(texts)
        c = pycuber.Cube(); c("F R U R' U' F'")
        diffs = compare_faces(eng, pycuber_faces(c), "F R U R' U' F'")
        assert diffs == [], f"FRUruf mismatch"

    def test_RUrURUUrU(self, basic, helpers):
        """Step 5 algorithm: R U R' U R U2 R' U (edge swap)."""
        texts = self._run(basic, helpers, _dump_all_stickers_program("RUrURUUrU"))
        eng = parse_engine_output(texts)
        c = pycuber.Cube(); c("R U R' U R U2 R' U")
        diffs = compare_faces(eng, pycuber_faces(c), "R U R' U R U2 R' U")
        assert diffs == [], f"RUrURUUrU mismatch"

    def test_URulUruL(self, basic, helpers):
        """Step 6 algorithm: U R U' L' U R' U' L (corner 3-cycle)."""
        texts = self._run(basic, helpers, _dump_all_stickers_program("URulUruL"))
        eng = parse_engine_output(texts)
        c = pycuber.Cube(); c("U R U' L' U R' U' L")
        diffs = compare_faces(eng, pycuber_faces(c), "U R U' L' U R' U' L")
        assert diffs == [], f"URulUruL mismatch"
