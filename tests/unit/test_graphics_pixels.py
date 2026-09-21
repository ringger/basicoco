"""Server-side pixel tracking for PPOINT, DRAW M and PCLS color (task #8)."""

import pytest


@pytest.fixture
def gfx(basic):
    basic.process_command('PMODE 4,1')
    basic.process_command('SCREEN 1,1')
    return basic


def ppoint(basic, x, y):
    return basic.evaluate_expression(f'PPOINT({x},{y})')


def test_ppoint_sees_line(gfx):
    gfx.process_command('LINE (0,0)-(10,0),PSET')
    assert ppoint(gfx, 5, 0) == 1
    assert ppoint(gfx, 5, 1) == 0


def test_ppoint_sees_circle_outline(gfx):
    gfx.process_command('CIRCLE (50,50),10')
    assert ppoint(gfx, 60, 50) == 1
    assert ppoint(gfx, 50, 40) == 1
    assert ppoint(gfx, 50, 50) == 0  # centre is not drawn


def test_ppoint_sees_filled_and_outline_boxes(gfx):
    gfx.process_command('LINE (100,100)-(110,110),PSET,BF')
    assert ppoint(gfx, 105, 105) == 1
    gfx.process_command('LINE (20,20)-(30,30),PSET,B')
    assert ppoint(gfx, 25, 20) == 1
    assert ppoint(gfx, 25, 25) == 0


def test_line_preset_erases(gfx):
    gfx.process_command('LINE (0,5)-(10,5),PSET')
    gfx.process_command('LINE (0,5)-(10,5),PRESET')
    assert ppoint(gfx, 5, 5) == 0


def test_draw_m_draws_and_bm_does_not(gfx):
    result = gfx.process_command('DRAW "BM10,10M20,20"')
    lines = [r for r in result if r.get('type') == 'line']
    assert len(lines) == 1
    assert (lines[0]['x1'], lines[0]['y1'], lines[0]['x2'], lines[0]['y2']) == (10, 10, 20, 20)
    assert ppoint(gfx, 15, 15) == 1
    assert ppoint(gfx, 5, 5) == 0


def test_pcls_color(gfx):
    result = gfx.process_command('PCLS 3')
    assert result[0] == {'type': 'pcls', 'color': 3}
    assert ppoint(gfx, 1, 1) == 3
    gfx.process_command('PRESET(1,1)')
    assert ppoint(gfx, 1, 1) == 0  # PRESET sets the background colour, not PCLS's (#124)


def test_huge_coordinates_are_fast(gfx):
    gfx.process_command('LINE (0,0)-(1E9,0),PSET')
    gfx.process_command('CIRCLE (0,0),1E9')
    assert len(gfx.graphics.pixel_buffer) == 0


class TestPaintAndGprint:
    """#85: PPOINT sees what PAINT fills and GPRINT writes, with the
    client's rules (flood fill of mode pixels, 4-connected; the font from
    dual_monitor.js)."""

    def test_paint_fills_inside_a_box_only(self, gfx):
        gfx.process_command('LINE (20,20)-(40,40),PSET,B')
        gfx.process_command('PAINT (30,30),3,1')
        assert ppoint(gfx, 30, 30) == 3
        assert ppoint(gfx, 21, 39) == 3
        assert ppoint(gfx, 20, 30) == 1     # the border stays
        assert ppoint(gfx, 50, 50) == 0     # outside untouched

    def test_paint_without_a_border_fills_the_start_colour_region(self, gfx):
        gfx.process_command('LINE (20,20)-(40,40),PSET,B')
        gfx.process_command('PAINT (30,30),2')
        assert ppoint(gfx, 30, 30) == 2
        assert ppoint(gfx, 20, 30) == 1
        assert ppoint(gfx, 50, 50) == 0

    def test_paint_with_another_border_colour_crosses_other_lines(self, gfx):
        gfx.process_command('LINE (20,20)-(40,40),PSET,B')      # colour 1
        gfx.process_command('LINE (30,20)-(30,40),2')             # colour 2 divider
        gfx.process_command('PAINT (25,30),3,1')
        assert ppoint(gfx, 35, 30) == 3     # the colour-2 line isn't a border
        assert ppoint(gfx, 30, 30) == 3     # and is painted over

    def test_paint_in_pmode_1_fills_whole_mode_pixels(self, basic):
        basic.process_command('PMODE 1,1')
        basic.process_command('LINE (20,20)-(40,40),2,B')
        basic.process_command('PAINT (30,30),3,2')
        assert ppoint(basic, 31, 31) == 3

    def test_gprint_strokes_are_seen(self, gfx):
        # 'A' is rows 0110 / 1001 / 1111 / 1001 / 1001 in the GPRINT font
        gfx.process_command('GPRINT (10,20),"A",2')
        assert ppoint(gfx, 11, 20) == 2 and ppoint(gfx, 12, 20) == 2
        assert ppoint(gfx, 10, 20) == 0
        assert [ppoint(gfx, x, 22) for x in range(10, 14)] == [2, 2, 2, 2]
        assert ppoint(gfx, 11, 23) == 0

    def test_gprint_font_comes_from_the_client(self):
        from emulator.graphics import gprint_font
        font = gprint_font()
        assert font[65] == [6, 9, 15, 9, 9, 0]
        assert all(len(rows) == 6 for rows in font.values())
        assert set(range(ord('A'), ord('Z') + 1)) <= set(font)


class TestColourState:
    """#124: the server's pixel record follows the same colour rules as the
    canvas: COLOR sets the drawing and background colours, PRESET uses the
    background, and clearing the screen fills with the background unless a
    colour is given."""

    def test_color_sets_the_drawing_colour(self, gfx):
        gfx.process_command('COLOR 4')
        gfx.process_command('PSET(10,10): LINE(0,20)-(5,20),PSET: CIRCLE(50,50),5')
        assert ppoint(gfx, 10, 10) == 4 and ppoint(gfx, 2, 20) == 4 and ppoint(gfx, 55, 50) == 4

    def test_color_with_a_background_clears_to_it(self, gfx):
        gfx.process_command('PSET(10,10)')
        gfx.process_command('COLOR 2,3')
        assert ppoint(gfx, 10, 10) == 3 and ppoint(gfx, 100, 100) == 3

    def test_preset_uses_the_background(self, gfx):
        gfx.process_command('COLOR 1,3')
        gfx.process_command('PCLS 2: PRESET(10,10): LINE(0,20)-(5,20),PRESET')
        assert ppoint(gfx, 10, 10) == 3 and ppoint(gfx, 2, 20) == 3
        assert ppoint(gfx, 50, 50) == 2

    def test_pcls_without_a_colour_clears_to_the_background(self, gfx):
        gfx.process_command('COLOR 1,4: PSET(10,10): PCLS')
        assert ppoint(gfx, 10, 10) == 4

    def test_pmode_clears_the_screen(self, gfx):
        gfx.process_command('PSET(10,10): PMODE 4,1')
        assert ppoint(gfx, 10, 10) == 0


class TestCircleRatioAndArcs:
    """#84: CIRCLE(x,y),r,c,ratio,start,end. The ratio scales the height
    (y radius = r * ratio); start and end are fractions of a turn,
    clockwise from 3 o'clock."""

    def test_ratio_squashes_the_circle(self, gfx):
        gfx.process_command('CIRCLE(100,100),20,1,.5')
        assert ppoint(gfx, 120, 100) == 1 and ppoint(gfx, 80, 100) == 1
        assert ppoint(gfx, 100, 110) == 1 and ppoint(gfx, 100, 90) == 1
        assert ppoint(gfx, 100, 120) == 0

    def test_a_ratio_above_one_stretches_it(self, gfx):
        gfx.process_command('CIRCLE(100,100),20,1,2')
        assert ppoint(gfx, 100, 140) == 1 and ppoint(gfx, 120, 100) == 1

    def test_quarter_arc_from_3_to_6_oclock(self, gfx):
        gfx.process_command('CIRCLE(100,100),20,1,1,0,.25')
        assert ppoint(gfx, 120, 100) == 1 and ppoint(gfx, 100, 120) == 1
        assert ppoint(gfx, 80, 100) == 0 and ppoint(gfx, 100, 80) == 0

    def test_an_arc_can_wrap_past_3_oclock(self, gfx):
        gfx.process_command('CIRCLE(100,100),20,1,1,.75,.25')   # 12 -> 3 -> 6 o'clock
        assert ppoint(gfx, 100, 80) == 1 and ppoint(gfx, 120, 100) == 1
        assert ppoint(gfx, 100, 120) == 1 and ppoint(gfx, 80, 100) == 0

    def test_ratio_one_with_no_arc_is_the_midpoint_circle(self, gfx, basic):
        gfx.process_command('CIRCLE(100,100),20,1')
        plain = dict(gfx.graphics.pixel_buffer)
        gfx.process_command('PCLS')
        gfx.process_command('CIRCLE(100,100),20,1,1,0,1')
        assert gfx.graphics.pixel_buffer == plain

    def test_the_client_gets_ratio_and_arc(self, gfx):
        out = gfx.process_command('CIRCLE(100,100),20,3,.5,.25,.5')
        circle = next(o for o in out if o['type'] == 'circle')
        assert (circle['ratio'], circle['start'], circle['end']) == (.5, .25, .5)

    @pytest.mark.parametrize('args', ['20,1,-1', '20,1,5', '20,1,1,-.1', '20,1,1,0,1.5'])
    def test_out_of_range_ratio_or_arc_is_illegal(self, gfx, helpers, args):
        errors = helpers.get_error_messages(gfx.process_command(f'CIRCLE(100,100),{args}'))
        assert len(errors) == 1 and 'ILLEGAL FUNCTION CALL' in errors[0], errors


def test_offscreen_pixels_are_not_stored(gfx):
    gfx.process_command('PSET(99999,-99999)')
    gfx.process_command('LINE (-1000,-1000)-(-900,-900),PSET')
    assert gfx.graphics.pixel_buffer == {}
