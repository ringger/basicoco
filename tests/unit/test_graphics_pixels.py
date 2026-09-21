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


def test_offscreen_pixels_are_not_stored(gfx):
    gfx.process_command('PSET(99999,-99999)')
    gfx.process_command('LINE (-1000,-1000)-(-900,-900),PSET')
    assert gfx.graphics.pixel_buffer == {}
