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
    def pixels(color):
        return [list(p) for p, c in basic.graphics.pixel_buffer.items() if c == color]

    circle = {'cx': 100, 'cy': 90, 'r': 23, 'pixels': pixels(1)}
    assert circle['pixels'], 'server recorded no circle pixels'
    # PAINT inside it and GPRINT beside it: the harness checks the client
    # draws exactly the pixels the server recorded (#85)
    basic.process_command('PAINT(100,90),4,1')
    circle['painted'] = pixels(4)
    basic.process_command('GPRINT(140,30),"AB?~",2')
    circle['gprint'] = {'x': 140, 'y': 30, 'text': 'AB?~', 'color': 2, 'pixels': pixels(2)}
    assert circle['painted'] and circle['gprint']['pixels']
    # A fan of LINEs from one point: every slope class, including the
    # Bresenham ties where server and client once stepped differently (#107)
    basic.process_command('PCLS')
    fan_ends = [[128 + dx, 96 + dy] for dx in range(-24, 25, 4) for dy in (-18, -7, 0, 7, 18)]
    for x2, y2 in fan_ends:
        basic.process_command(f'LINE(128,96)-({x2},{y2}),PSET')
    circle['fan'] = {'ends': fan_ends, 'pixels': pixels(basic.current_draw_color)}
    basic.process_command('PCLS')
    # An ellipse and a wrapping arc, in clear parts of the screen (#84)
    circle['arcs'] = []
    for args, color in (((60, 150, 30, .5, 0, 1), 5), ((200, 140, 25, 1.4, .8, .3), 6)):
        x, y, r, ratio, start, end = args
        basic.process_command(f'CIRCLE({x},{y}),{r},{color},{ratio},{start},{end}')
        circle['arcs'].append({'args': list(args), 'color': color, 'pixels': pixels(color)})
        assert circle['arcs'][-1]['pixels']
    circle_file = tmp_path / 'server_circle.json'
    circle_file.write_text(json.dumps(circle))

    result = subprocess.run([NODE, HARNESS, CLIENT, str(circle_file)],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert '0 failed' in result.stdout
