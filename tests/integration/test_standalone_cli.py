"""The standalone CLI (basicoco.py) as a user runs it: commands on stdin,
everything it prints on stdout and stderr."""

import os
import subprocess
import sys

import pytest

BASICOCO = os.path.join(os.path.dirname(__file__), '..', '..', 'basicoco.py')


def run_cli(tmp_path, *commands):
    os.makedirs(tmp_path / 'programs', exist_ok=True)
    result = subprocess.run([sys.executable, BASICOCO], input='\n'.join(commands + ('EXIT',)) + '\n',
                            capture_output=True, text=True, cwd=tmp_path, timeout=20)
    return result.stdout, result.stderr


@pytest.mark.parametrize('program, message', [
    ('10 PRINT 1/0', 'Division by zero'),
    ('10 GOTO 10', 'TOO MANY ITERATIONS'),
])
def test_a_runtime_error_is_shown_once(tmp_path, program, message):
    """#98: the interpreter's WARNING log line used to repeat every error on stderr."""
    stdout, stderr = run_cli(tmp_path, program, 'RUN')
    both = stdout + stderr
    assert both.upper().count(message.upper()) == 1, both
    assert stderr == ''
