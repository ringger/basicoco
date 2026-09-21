"""Web-client rendering checks (task #34), run in Node without a browser.

tests/client/dual_monitor_harness.js loads the real static/dual_monitor.js
against a fake canvas that keeps real pixels. This test records the pixels
the *server* draws for a CIRCLE and hands them to the harness, so client and
server rasterization are checked against each other.
"""

import json
import os
import shutil
import subprocess

import pytest

ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
HARNESS = os.path.join(ROOT, 'tests', 'client', 'dual_monitor_harness.js')
CLIENT = os.path.join(ROOT, 'static', 'dual_monitor.js')

NODE = shutil.which('node')


@pytest.mark.skipif(NODE is None, reason='Node.js is not installed')
def test_client_rendering_harness(basic, tmp_path):
    basic.process_command('PMODE 4,1')
    basic.process_command('SCREEN 1,1')
    basic.process_command('CIRCLE(100,90),23,1')
    circle = {'cx': 100, 'cy': 90, 'r': 23,
              'pixels': [list(p) for p, c in basic.graphics.pixel_buffer.items() if c == 1]}
    assert circle['pixels'], 'server recorded no circle pixels'
    circle_file = tmp_path / 'server_circle.json'
    circle_file.write_text(json.dumps(circle))

    result = subprocess.run([NODE, HARNESS, CLIENT, str(circle_file)],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert '0 failed' in result.stdout
