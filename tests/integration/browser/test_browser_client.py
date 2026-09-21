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


def test_circle_ratio_and_arc_on_the_canvas(basic_page):
    """#84: an ellipse (ratio .5) and the lower half of a circle, and the
    canvas agrees with PPOINT."""
    basic_page.run('PMODE 4,1: SCREEN 1,1: PCLS')
    basic_page.run('CIRCLE(128,96),40,1,.5: CIRCLE(128,96),30,4,1,0,.5')
    assert basic_page.basic_pixel(168, 96) == GREEN       # ellipse: full width
    assert basic_page.basic_pixel(128, 116) == GREEN      # ... half height
    assert basic_page.basic_pixel(128, 136) == BLACK
    assert basic_page.basic_pixel(128, 126) == RED        # arc: bottom of the half
    assert basic_page.basic_pixel(128, 66) == BLACK       # no top half
    basic_page.run('PRINT PPOINT(128,116);PPOINT(128,126);PPOINT(128,66)')
    assert basic_page.lines()[-2].rstrip() == ' 1  4  0'


@pytest.mark.parametrize('mode,block', [(0, (4, 4)), (1, (4, 4)), (3, (4, 2)), (4, (2, 2))])
def test_pmode_pixels_land_where_the_coco_puts_them(basic_page, mode, block):
    """#79: every PMODE uses 0-255 x 0-191; lower modes draw coarser pixels
    on the same screen, and the server's PPOINT sees the same pixel."""
    basic_page.run(f'PMODE {mode},1: SCREEN 1,1: PCLS')
    basic_page.run('PSET(200,50),4: PSET(255,191),4')
    w, h = block
    assert basic_page.canvas_pixel(400, 100) == RED
    assert basic_page.canvas_pixel(400 + w - 1, 100 + h - 1) == RED
    assert basic_page.canvas_pixel(400 + w, 100) == BLACK
    assert basic_page.canvas_pixel(511, 383) == RED          # bottom-right corner is on screen
    basic_page.run('PRINT PPOINT(201,50)')
    lines = [l.rstrip() for l in basic_page.lines()]
    expected = ' 4' if mode != 4 else ' 0'   # (201,50) shares (200,50)'s pixel below PMODE 4
    assert lines[lines.index('> PRINT PPOINT(201,50)') + 1] == expected


def test_gprint_symbols_are_not_question_marks(basic_page):
    basic_page.run('PMODE 4,1: SCREEN 1,1: PCLS')
    basic_page.run('GPRINT(10,10),"#": GPRINT(20,10),"?"')
    hash_glyph = [basic_page.basic_pixel(10 + dx, 10 + dy) for dy in range(6) for dx in range(4)]
    question = [basic_page.basic_pixel(20 + dx, 10 + dy) for dy in range(6) for dx in range(4)]
    assert GREEN in hash_glyph
    assert hash_glyph != question
