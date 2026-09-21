"""The web client in a real browser (headless Chrome): real canvas, real
fonts, real Socket.IO traffic to the live server."""

import pytest

pytestmark = [pytest.mark.browser, pytest.mark.slow]

BLACK, GREEN, RED = (0, 0, 0), (0, 255, 0), (255, 0, 0)
PALETTE = {(0, 0, 0), (0, 255, 0), (255, 255, 0), (0, 0, 255), (255, 0, 0),
           (255, 170, 136), (0, 255, 255), (255, 0, 255), (255, 136, 0)}


def test_command_runs_and_output_appears(basic_page):
    basic_page.run('PRINT 2+2')
    lines = [l.rstrip() for l in basic_page.lines()]
    assert lines[lines.index('> PRINT 2+2') + 1] == ' 4'


def test_typed_command_stays_in_scrollback(basic_page):
    basic_page.run('PRINT "HELLO"')
    lines = [l.rstrip() for l in basic_page.lines()]
    assert '> PRINT "HELLO"' in lines
    assert 'HELLO' in lines


def test_long_command_wraps_at_80_columns(basic_page):
    command = 'PRINT "' + 'X' * 100 + '"'
    basic_page.run(command)
    lines = basic_page.lines()
    start = lines.index(('> ' + command)[:80])
    assert lines[start + 1].rstrip() == ('> ' + command)[80:]
    # The printed output wraps at 80 columns too
    assert lines[start + 2] == 'X' * 80
    assert lines[start + 3].rstrip() == 'X' * 20


def test_circle_is_crisp_and_paint_stays_inside(basic_page):
    basic_page.run('PMODE 4,1: SCREEN 1,1: PCLS')
    basic_page.run('CIRCLE(128,96),40,1: PAINT(128,96),4,1')
    assert basic_page.basic_pixel(128, 96) == RED
    assert basic_page.basic_pixel(128 + 60, 96) == BLACK   # outside: not flooded
    assert basic_page.basic_pixel(128 + 40, 96) == GREEN   # the circle itself
    # No antialiased in-between colors anywhere around the circle
    around = basic_page.canvas_colors(2 * 80, 2 * 48, 2 * 176, 2 * 144)
    assert around <= PALETTE, around - PALETTE


def test_gprint_symbols_are_not_question_marks(basic_page):
    basic_page.run('PMODE 4,1: SCREEN 1,1: PCLS')
    basic_page.run('GPRINT(10,10),"#": GPRINT(20,10),"?"')
    hash_glyph = [basic_page.basic_pixel(10 + dx, 10 + dy) for dy in range(6) for dx in range(4)]
    question = [basic_page.basic_pixel(20 + dx, 10 + dy) for dy in range(6) for dx in range(4)]
    assert GREEN in hash_glyph
    assert hash_glyph != question
