"""Regression tests for the Rubik's cube programs, from the Sept 2026 audit.

The per-step tests in test_rubiks_solver.py use 16 hand-picked scrambles each
and run with animation off. These tests close the gaps the audit found:

- TestRandomScrambleSolve: full solves of seeded random scrambles plus every
  single face turn, verified twice: by the BASIC solver's own
  CheckFullSolve / CheckCubeIntegrity AND independently by replaying the
  scramble + logged solution in pycuber (task #63, #64).
- TestScramble: the engine's Scramble routine must use face turns only; whole
  cube rotations move the centers, which the solver cannot handle (task #65).
- TestAnimationConsistency: the last animated frame of a turn must match a
  static redraw after the turn is applied (task #67: R/L animate backwards).
- TestRenderScaleStable: frames drawn mid-solve must keep the render scale;
  a PRIVATE SC in the solver shrank the cube (task #51).

The lib files are copied into a temp programs dir; DoTurn in the COPY is
instrumented to PRINT each move so the solution can be replayed in pycuber.
"""

import os
import random
import re

import pytest
import pycuber as pc

PROGRAMS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'programs')
LIBS = ('lib_rubiks_engine.bas', 'lib_rubiks_solver.bas')

# DoTurn's TF codes → move letter; DR=-1 means counter-clockwise.
TF_LETTERS = {1: 'R', 2: 'U', 3: 'F', 4: 'X', 5: 'Y', 6: 'Z', 7: 'L', 8: 'D', 9: 'B'}
# Engine X turns the same way as L (standard x'); Y follows U, Z follows F.
PYCUBER_MOVES = {'R': "R", 'U': "U", 'F': "F", 'L': "L", 'D': "D", 'B': "B",
                 'X': "x'", 'Y': "y", 'Z': "z"}
FACE_LETTERS = 'RUFLDB'

SOLVE_STEPS = ['SolveBottomCross', 'SolveBottomCorners', 'SolveMiddleEdges',
               'SolveTopCross', 'SolveTopEdgeAlign', 'SolveTopCornerPos',
               'SolveTopCornerOrient']

MOVE_LOG_RE = re.compile(r'MV:\s*(-?\d+)\s+(-?\d+)')


def _random_scramble(seed, length=25):
    """Face-turn-only scramble (engine notation: lowercase = CCW)."""
    rng = random.Random(seed)
    moves, last = [], None
    while len(moves) < length:
        face = rng.choice(FACE_LETTERS)
        if face == last:
            continue
        last = face
        moves.append(face if rng.random() < 0.5 else face.lower())
    return ''.join(moves)


SINGLE_TURNS = [m for f in FACE_LETTERS for m in (f, f.lower(), f + f)]
RANDOM_SEEDS = list(range(100))


@pytest.fixture(autouse=True)
def rubiks_libs(temp_programs_dir):
    """Copy the libs into the temp programs dir, instrumenting DoTurn."""
    for fname in LIBS:
        with open(os.path.join(PROGRAMS_DIR, fname)) as f:
            text = f.read()
        if fname == 'lib_rubiks_engine.bas':
            marker = 'DoTurn:\n  PRIVATE RA\n'
            assert marker in text, 'DoTurn header changed; update the instrumentation'
            text = text.replace(marker, marker + '  PRINT "MV:";TF;DR\n', 1)
        with open(os.path.join(temp_programs_dir, fname), 'w') as f:
            f.write(text)


def _logged_moves(texts, after='BEGIN'):
    """Move letters PRINTed by the instrumented DoTurn after the marker line."""
    moves, started = [], False
    for t in texts:
        if t.startswith(after):
            started = True
            continue
        m = MOVE_LOG_RE.match(t)
        if m and started:
            tf, dr = int(m.group(1)), int(m.group(2))
            letter = TF_LETTERS.get(tf)
            assert letter, f'Unexpected turn code TF={tf}'
            moves.append(letter if dr > 0 else letter.lower())
    return moves


def _pycuber_formula(moves):
    return ' '.join(PYCUBER_MOVES[m.upper()] + ("'" if m.islower() else '')
                    for m in moves).replace("''", '')


def _is_solved(cube):
    return all(len({sq.colour for row in cube.get_face(face) for sq in row}) == 1
               for face in 'LURDFB')


def _solve(basic, helpers, scramble, max_frames=200000):
    program = [
        '5 SAFETY OFF',
        '10 PMODE 4: SCREEN 1',
        '20 MERGE "lib_rubiks_engine"',
        '25 MERGE "lib_rubiks_solver"',
        '30 GOSUB InitCube',
        '35 AN=0',
        f'40 MS$="{scramble}": GOSUB DoMoves',
        '45 PRINT "BEGIN"',
    ]
    program += [f'{50 + i * 10} GOSUB {step}' for i, step in enumerate(SOLVE_STEPS)]
    program += ['150 GOSUB CheckFullSolve', '160 GOSUB CheckCubeIntegrity',
                '170 PRINT "DONE"', '180 END']
    helpers.load_program(basic, program)
    results = helpers.run_to_completion(basic, max_frames=max_frames)
    return helpers.get_text_output(results), helpers.get_error_messages(results)


def _assert_full_solve(basic, helpers, scramble):
    texts, errors = _solve(basic, helpers, scramble)
    assert errors == [], f'Scramble {scramble!r}: errors {errors}'
    assert any('FULL SOLVE OK' in t for t in texts), \
        f'Scramble {scramble!r}: solver reported failure. Tail: {texts[-8:]}'
    assert any(t.startswith('DONE') for t in texts), \
        f'Scramble {scramble!r}: program stopped early. Tail: {texts[-8:]}'

    solution = _logged_moves(texts)
    cube = pc.Cube()
    if scramble:
        cube(_pycuber_formula(list(scramble)))
    if solution:
        cube(_pycuber_formula(solution))
    assert _is_solved(cube), \
        f'Scramble {scramble!r}: pycuber replay of the {len(solution)}-move solution ' \
        f'does not solve the cube'


@pytest.mark.slow
class TestRandomScrambleSolve:
    """Full solves beyond the hand-picked scrambles, cross-checked in pycuber."""

    def test_solved_cube(self, basic, helpers):
        _assert_full_solve(basic, helpers, '')

    @pytest.mark.parametrize('scramble', SINGLE_TURNS)
    def test_single_turn(self, basic, helpers, scramble):
        _assert_full_solve(basic, helpers, scramble)

    @pytest.mark.parametrize('seed', RANDOM_SEEDS)
    def test_random_scramble(self, basic, helpers, seed):
        _assert_full_solve(basic, helpers, _random_scramble(seed))


@pytest.mark.slow
class TestScramble:
    """The engine's Scramble routine feeds rubiks_solve.bas."""

    def _run_scramble(self, basic, helpers, seed):
        helpers.load_program(basic, [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "lib_rubiks_engine"',
            '30 GOSUB InitCube',
            '35 AN=0',
            f'40 X=RND(-{seed}): NM=20',
            '45 PRINT "BEGIN"',
            '50 GOSUB Scramble',
            '60 END',
        ])
        texts = helpers.get_text_output(helpers.run_to_completion(basic))
        return texts, _logged_moves(texts)

    @pytest.mark.parametrize('seed', [1, 2, 3])
    def test_scramble_uses_face_turns_only(self, basic, helpers, seed):
        _, moves = self._run_scramble(basic, helpers, seed)
        assert len(moves) == 20
        rotations = [m for m in moves if m.upper() in 'XYZ']
        assert rotations == [], f'Scramble applied whole-cube rotations: {"".join(moves)}'

    @pytest.mark.parametrize('seed', [1, 2, 3])
    def test_scramble_covers_all_six_faces_eventually(self, basic, helpers, seed):
        _, moves = self._run_scramble(basic, helpers, seed)
        faces = {m.upper() for m in moves}
        assert faces <= set(FACE_LETTERS)
        assert len(faces) >= 4, f'Scramble uses too few faces: {"".join(moves)}'


def _frames(results):
    """Split graphics output into frames at each PCLS."""
    ops = [r for r in results if r.get('type') in ('line', 'paint', 'pcls')]
    starts = [i for i, op in enumerate(ops) if op['type'] == 'pcls']
    return [ops[s:(starts[k + 1] if k + 1 < len(starts) else len(ops))]
            for k, s in enumerate(starts)]


def _paint_seeds(frame):
    return [(op['x'], op['y'], op['fill_color']) for op in frame if op['type'] == 'paint']


@pytest.mark.slow
class TestAnimationConsistency:
    """The final animated frame of a turn should already show the turned cube."""

    @pytest.mark.parametrize('move', list('RUFLDBrufldb'))
    def test_last_animation_frame_matches_static_redraw(self, basic, helpers, move):
        helpers.load_program(basic, [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "lib_rubiks_engine"',
            '30 GOSUB InitCube',
            '35 AN=0',
            '40 MS$="RUFBLDrufbldRUF": GOSUB DoMoves',
            '45 AN=1',
            f'50 MS$="{move}": GOSUB DoMoves',
            '55 GOSUB ShowCube',
            '60 END',
        ])
        frames = _frames(helpers.run_to_completion(basic))
        assert len(frames) >= 2
        last_animated, static = _paint_seeds(frames[-2]), _paint_seeds(frames[-1])
        unmatched = [p for p in static
                     if not any(abs(p[0] - q[0]) <= 2 and abs(p[1] - q[1]) <= 2 and p[2] == q[2]
                                for q in last_animated)]
        assert unmatched == [], \
            f'{move}: {len(unmatched)} of {len(static)} stickers differ between the ' \
            f'last animation frame and the static redraw (animation turns the wrong way?)'


def _frame_width(frame):
    xs = [x for op in frame if op['type'] == 'line' for x in (op['x1'], op['x2'])]
    return max(xs) - min(xs) if xs else 0


@pytest.mark.slow
class TestRenderScaleStable:
    """Animated frames during a solve must all be drawn at the normal scale."""

    def test_middle_edge_step_keeps_render_scale(self, basic, helpers):
        helpers.load_program(basic, [
            '5 SAFETY OFF',
            '10 PMODE 4: SCREEN 1',
            '20 MERGE "lib_rubiks_engine"',
            '25 MERGE "lib_rubiks_solver"',
            '30 GOSUB InitCube',
            '35 AN=0',
            '40 MS$="RUFBLDrufbldRUF": GOSUB DoMoves',
            '50 GOSUB SolveBottomCross: GOSUB SolveBottomCorners',
            '60 GOSUB ShowCube',
            '70 AN=1: GOSUB SolveMiddleEdges',
            '80 END',
        ])
        frames = _frames(helpers.run_to_completion(basic, max_frames=200000))
        reference = _frame_width(frames[0])
        assert reference > 0
        shrunk = [i for i, f in enumerate(frames) if _frame_width(f) < 0.8 * reference]
        assert shrunk == [], \
            f'{len(shrunk)} of {len(frames)} frames drawn much smaller than the static cube ' \
            f'(render scale SC clobbered?)'


@pytest.mark.slow
class TestInteractiveMenu:
    """#69: rubiks_interactive.bas offers every face turn, including L/D/B."""

    @staticmethod
    def _through_pauses(basic, output):
        """Continue past auto-yield pauses (as helpers.run_to_completion does)."""
        while basic.waiting_for_pause_continuation:
            basic.waiting_for_pause_continuation = False
            basic.running = True
            output.extend(basic.continue_program_execution())

    def test_menu_choices_reach_the_engine(self, basic, helpers):
        with open(os.path.join(PROGRAMS_DIR, 'rubiks_interactive.bas')) as f:
            helpers.load_program(basic, f.read().splitlines())
        answers = ['7', '8', '-9', '1', '10', '0']  # 10 is out of range: menu again
        output = basic.process_command('RUN')
        self._through_pauses(basic, output)
        for answer in answers:
            assert basic.waiting_for_input, helpers.get_error_messages(output)
            basic.store_input_value(basic.input_variables[0], answer)
            basic.clear_input_state()
            output.extend(basic.continue_program_execution())
            self._through_pauses(basic, output)
        assert helpers.get_error_messages(output) == []
        turns = [t.split()[1:] for t in helpers.get_text_output(output) if t.startswith('MV:')]
        assert turns == [['7', '1'], ['8', '1'], ['9', '-1'], ['1', '1']]
        assert 'LEFT' in ' '.join(helpers.get_text_output(output))
