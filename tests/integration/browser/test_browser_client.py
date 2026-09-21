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


CANVAS_COLOR_INDEX_JS = """([x, y]) => {
    const g = window.dualMonitor.displayManager.graphicsDisplay;
    const d = g.ctx.getImageData(x * 2, y * 2, 1, 1).data;
    const hex = '#' + [d[0], d[1], d[2]].map(v => v.toString(16).padStart(2, '0')).join('');
    return g.colors.indexOf(hex);
}"""


@pytest.mark.parametrize('commands', [
    ['COLOR 4,3', 'PSET(10,10): LINE(0,30)-(40,40),PSET: LINE(0,20)-(40,20),PRESET',
     'CIRCLE(100,100),20: PAINT(100,100),2,4: PRESET(100,100)', 'GPRINT(150,50),"HI",1'],
    ['COLOR 2,1', 'PCLS 6', 'LINE(10,10)-(60,60),PSET,BF: LINE(20,20)-(50,50),PRESET,B'],
    ['PSET(10,10)', 'PMODE 4,1', 'COLOR 7', 'PSET(30,30): PCLS: PSET(40,40)'],
    # #106: GET a block, PUT it back with every action
    ['LINE(10,10)-(40,10),2: LINE(10,10)-(10,40),6: CIRCLE(25,25),8,5', 'GET(10,10)-(40,40),S',
     'LINE(100,100)-(100,130),3: LINE(100,120)-(130,120),1', 'COLOR 4',
     'PUT(100,100),S,PSET: PUT(150,100),S,PRESET: PUT(100,20),S,OR',
     'LINE(150,20)-(180,40),3,BF: PUT(150,20),S,AND: PUT(20,100),S,NOT'],
], ids=['draw-and-preset', 'pcls-colour-and-boxes', 'pmode-and-pcls', 'get-and-put'])
def test_ppoint_matches_the_canvas(basic_page, commands):
    """#124: PPOINT (the server's record) and the canvas (what the client
    drew) agree after COLOR, PRESET, LINE...PRESET, PCLS and PMODE."""
    basic_page.run('PMODE 4,1: SCREEN 1,1')
    for command in commands:
        basic_page.run(command)
    points = [(x, y) for x in (0, 10, 20, 25, 35, 40, 55, 100, 105, 120, 150, 151, 200)
              for y in (10, 20, 25, 30, 35, 40, 50, 100, 105, 150)]
    canvas = [basic_page.page.evaluate(CANVAS_COLOR_INDEX_JS, [x, y]) for x, y in points]
    for start in range(0, len(points), 10):
        chunk = points[start:start + 10]
        basic_page.run('PRINT ' + ';'.join(f'PPOINT({x},{y})' for x, y in chunk))
        ppoint = [int(v) for v in basic_page.lines()[-2].split()]
        for (x, y), server, shown in zip(chunk, ppoint, canvas[start:start + 10]):
            assert server == shown, f'({x},{y}): PPOINT {server}, canvas {shown}'


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
