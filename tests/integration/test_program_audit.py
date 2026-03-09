#!/usr/bin/env python3
"""
Audit all .bas programs via pexpect on the standalone CLI (basicoco.py).

Each test loads a program, runs it, and verifies it starts without errors.
Interactive programs receive appropriate input to exercise their main paths.
Programs with PAUSE-based animations use pexpect.TIMEOUT as an acceptable
outcome since they block in real-time delays.
"""

import pexpect
import pytest
import os
import tempfile

BASICOCO = os.path.join(os.path.dirname(__file__), '..', '..', 'basicoco.py')
BASEDIR = os.path.join(os.path.dirname(__file__), '..', '..')
PROMPT = '> '
TIMEOUT = 10


def spawn_basic(cwd=None):
    """Start a fresh basicoco.py REPL session."""
    child = pexpect.spawn(
        f'python {BASICOCO}',
        encoding='utf-8',
        timeout=TIMEOUT,
        cwd=cwd or BASEDIR,
    )
    child.expect('INSPIRED BY TANDY/RADIO SHACK')
    child.expect(PROMPT)
    return child


def load_and_run(child, program_name):
    """Load a program and RUN it."""
    child.sendline(f'LOAD "{program_name}"')
    child.expect('LOADED')
    child.expect(PROMPT)
    child.sendline('RUN')
    return child


def check_no_error(before_text):
    """Assert no ERROR in the captured output."""
    assert 'ERROR' not in (before_text or ''), f"Unexpected error: {before_text}"


class TestNonInteractivePrograms:
    """Programs that run to completion without INPUT."""

    def test_blue_circle(self):
        child = spawn_basic()
        load_and_run(child, 'blue_circle')
        child.expect(PROMPT)
        check_no_error(child.before)
        child.close()


@pytest.mark.slow
class TestPausePrograms:
    """Programs that use PAUSE for animation — may not finish in test time."""

    def test_spiral(self):
        child = spawn_basic()
        load_and_run(child, 'spiral')
        # Spiral has multiple PAUSE calls; just verify it starts without error
        index = child.expect([PROMPT, pexpect.TIMEOUT], timeout=15)
        check_no_error(child.before)
        child.close()

    def test_qix_beam(self):
        child = spawn_basic()
        load_and_run(child, 'qix_beam')
        index = child.expect([PROMPT, pexpect.TIMEOUT], timeout=15)
        check_no_error(child.before)
        child.close()

    def test_bounce_pause(self):
        child = spawn_basic()
        load_and_run(child, 'bounce_pause')
        index = child.expect([PROMPT, pexpect.TIMEOUT], timeout=15)
        check_no_error(child.before)
        child.close()


class TestInteractivePrograms:
    """Programs that require INPUT — feed them valid responses."""

    def test_guess_number(self):
        child = spawn_basic()
        load_and_run(child, 'guess_number')
        child.expect('GUESS')
        for guess in [50, 25, 75, 10, 90]:
            child.sendline(str(guess))
            index = child.expect(['GUESS', 'GOT IT', 'PLAY AGAIN', PROMPT])
            if index >= 1:
                break
        check_no_error(child.before)
        child.close()

    def test_bar_chart(self):
        child = spawn_basic()
        load_and_run(child, 'bar_chart')
        # First prompt is CHART TITLE
        child.expect('TITLE')
        child.sendline('TEST')
        child.expect('HOW MANY')
        child.sendline('2')
        # Two items: label + value each
        for i in range(2):
            child.expect('LABEL')
            child.sendline(f'X{i+1}')
            child.expect('VALUE')
            child.sendline(str((i + 1) * 10))
        child.expect('Y/N')
        child.sendline('N')
        child.expect(PROMPT, timeout=TIMEOUT)
        check_no_error(child.before)
        child.close()

    def test_simple_lunar(self):
        child = spawn_basic()
        load_and_run(child, 'simple_lunar')
        child.expect('THRUST')
        for thrust in [10, 10, 10, 5, 5, 3, 2, 1, 0, 0, 0, 0, 0, 0, 0]:
            child.sendline(str(thrust))
            index = child.expect(['THRUST', 'LANDED', 'CRASHED', PROMPT])
            if index >= 1:
                break
        check_no_error(child.before)
        child.close()

    def test_lunar_lander(self):
        child = spawn_basic()
        load_and_run(child, 'lunar_lander')
        child.expect('THRUST')
        for thrust in [15, 12, 8, 5, 2, 0, 0, 0, 0, 0, 0]:
            child.sendline(str(thrust))
            index = child.expect(['THRUST', 'LANDED', 'CRASHED', PROMPT])
            if index >= 1:
                break
        check_no_error(child.before)
        child.close()

    def test_math_quiz(self):
        child = spawn_basic()
        load_and_run(child, 'math_quiz')
        # First question appears as "= " (e.g., "5 + 3 = ")
        child.expect('= ')
        child.sendline('0')
        # After answer, expect next question or continue prompt
        index = child.expect(['= ', 'Y/N', PROMPT])
        if index == 1:
            child.sendline('N')
        child.expect(PROMPT, timeout=TIMEOUT)
        check_no_error(child.before)
        child.close()

    def test_sorting_demo(self):
        child = spawn_basic()
        load_and_run(child, 'sorting_demo')
        child.expect('CHOICE')
        child.sendline('1')  # Sort numbers
        child.expect(PROMPT, timeout=TIMEOUT)
        check_no_error(child.before)
        child.close()

    def test_string_lab(self):
        child = spawn_basic()
        load_and_run(child, 'string_lab')
        child.expect('CHOOSE')
        child.sendline('1')  # Caesar cipher
        child.expect('TEXT')
        child.sendline('HELLO')
        child.expect('SHIFT')
        child.sendline('3')
        # Should show result and loop back to menu
        child.expect('CHOOSE', timeout=TIMEOUT)
        check_no_error(child.before)
        child.sendline('4')  # Quit
        child.expect(PROMPT, timeout=TIMEOUT)
        child.close()

    def test_math_plotter(self):
        child = spawn_basic()
        load_and_run(child, 'math_plotter')
        child.expect(['CHOOSE', 'SELECT', '\\?'])
        child.sendline('1')  # First plot
        # Should draw and return to menu or finish
        child.expect(['CHOOSE', 'SELECT', '\\?', PROMPT], timeout=TIMEOUT)
        check_no_error(child.before)
        child.close()

    def test_address_book(self):
        child = spawn_basic()
        load_and_run(child, 'address_book')
        child.expect(['CHOOSE', 'MENU', 'SELECT', '\\?'])
        child.sendline('5')  # Quit
        child.expect(PROMPT, timeout=TIMEOUT)
        check_no_error(child.before)
        child.close()

    def test_graph_chart(self):
        child = spawn_basic(cwd=tempfile.mkdtemp())
        load_and_run(child, 'graph_chart')
        child.expect('CHOOSE')
        child.sendline('5')  # Create sample file
        child.expect('CREATED')
        child.expect('CHOOSE')
        child.sendline('1')  # Load from file
        child.expect('LOADED')
        child.expect('CHOOSE')
        child.sendline('4')  # Draw chart
        child.expect('SCALE')
        check_no_error(child.before)
        child.expect('CHOOSE')
        child.sendline('6')  # Quit
        child.expect(PROMPT, timeout=TIMEOUT)
        child.close()
