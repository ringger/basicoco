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
    assert ppoint(gfx, 1, 1) == 3  # PRESET restores the clear color


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


def test_offscreen_pixels_are_not_stored(gfx):
    gfx.process_command('PSET(99999,-99999)')
    gfx.process_command('LINE (-1000,-1000)-(-900,-900),PSET')
    assert gfx.graphics.pixel_buffer == {}
