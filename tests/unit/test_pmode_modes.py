"""PMODE 0-4 (#79). Every mode uses the CoCo's 0-255 x 0-191 coordinates;
lower modes only have coarser pixels (PMODE 0/1: 2x2 coordinates per pixel,
PMODE 2/3: 2x1, PMODE 4: 1x1). PMODE 0 is a real graphics mode, not text."""

import pytest


def ppoint(basic, x, y):
    return basic.evaluate_expression(f'PPOINT({x},{y})')


def graphics(basic, mode):
    basic.process_command(f'PMODE {mode},1')
    basic.process_command('SCREEN 1,1')
    basic.process_command('PCLS')


class TestPmodeZero:
    def test_pmode_0_allows_drawing(self, basic, helpers):
        graphics(basic, 0)
        result = basic.process_command('PSET(10,10),1')
        assert helpers.get_error_messages(result) == []
        assert any(r.get('type') == 'pset' for r in result)
        assert ppoint(basic, 10, 10) == 1

    def test_no_pmode_yet_is_still_an_error(self, basic, helpers):
        errors = helpers.get_error_messages(basic.process_command('PSET(10,10),1'))
        assert errors and 'ILLEGAL FUNCTION CALL' in errors[0]

    def test_ppoint_without_pmode_is_an_error(self, basic):
        with pytest.raises(ValueError, match='graphics mode'):
            ppoint(basic, 0, 0)

    def test_new_program_run_leaves_graphics_off_until_pmode(self, basic, helpers):
        graphics(basic, 0)
        helpers.load_program(basic, ['10 PSET(1,1),1'])
        results = helpers.run_to_completion(basic)
        errors = helpers.get_error_messages(results)
        assert errors and 'ILLEGAL FUNCTION CALL' in errors[0]


class TestCoarsePixels:
    @pytest.mark.parametrize('mode,lit,unlit', [
        (0, [(0, 0), (1, 0), (0, 1)], [(2, 0), (0, 2)]),
        (1, [(0, 0), (1, 0), (0, 1)], [(2, 0), (0, 2)]),
        (2, [(0, 1), (1, 1)], [(0, 0), (2, 1)]),
        (3, [(0, 1), (1, 1)], [(0, 0), (2, 1)]),
        (4, [(1, 1)], [(0, 0), (0, 1), (1, 0)]),
    ])
    def test_pset_lights_the_modes_whole_pixel(self, basic, mode, lit, unlit):
        graphics(basic, mode)
        basic.process_command('PSET(1,1),1')
        assert [ppoint(basic, x, y) for x, y in lit] == [1] * len(lit)
        assert [ppoint(basic, x, y) for x, y in unlit] == [0] * len(unlit)

    @pytest.mark.parametrize('mode', [0, 1, 2, 3, 4])
    def test_full_coordinate_range_in_every_mode(self, basic, helpers, mode):
        graphics(basic, mode)
        result = basic.process_command('PSET(255,191),1')
        assert helpers.get_error_messages(result) == []
        assert ppoint(basic, 255, 191) == 1
