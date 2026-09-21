"""Graphics argument parsing (task #75): coordinate pairs/ranges are matched
by parenthesis depth, so expressions with commas and parentheses work."""

import pytest


@pytest.fixture
def gfx(basic):
    basic.process_command('PMODE 4,1')
    basic.process_command('SCREEN 1,1')
    basic.process_command('DIM C(2),P(2)')
    basic.process_command('C(1)=3: P(1)=7')
    return basic


def first(result, kind):
    return next(r for r in result if r.get('type') == kind)


class TestLine:
    def test_array_color_argument(self, gfx):
        line = first(gfx.process_command('LINE(0,0)-(10,10),C(1)'), 'line')
        assert (line['x1'], line['y1'], line['x2'], line['y2'], line['color']) == (0, 0, 10, 10, 3)

    def test_array_inside_coordinate(self, gfx):
        line = first(gfx.process_command('LINE(P(1)-(2),0)-(10,10),PSET'), 'line')
        assert (line['x1'], line['y1']) == (5, 0)
        assert line['mode'] == 'PSET'

    def test_relative_start(self, gfx):
        gfx.process_command('LINE(0,0)-(10,12)')
        line = first(gfx.process_command('LINE -(20,20),PSET'), 'line')
        assert (line['x1'], line['y1'], line['x2'], line['y2']) == (10, 12, 20, 20)

    def test_box_options(self, gfx):
        line = first(gfx.process_command('LINE(0,0)-(5,5),PSET,BF'), 'line')
        assert line['box_type'] == 'BF'

    def test_spaces_around_dash(self, gfx):
        line = first(gfx.process_command('LINE (1, 2) - (3, 4)'), 'line')
        assert (line['x1'], line['y1'], line['x2'], line['y2']) == (1, 2, 3, 4)

    def test_2d_array_coordinates(self, gfx):
        # Ported from the removed CommandRegistry.parse_line_coordinates tests
        gfx.process_command('DIM GX(2,2),GY(2,2)')
        gfx.process_command('R=1: C=0: GX(1,0)=4: GY(1,0)=6: GX(1,1)=8: GY(1,1)=9')
        line = first(gfx.process_command('LINE(GX(R,C),GY(R,C))-(GX(R,C+1),GY(R,C+1)),PSET'), 'line')
        assert (line['x1'], line['y1'], line['x2'], line['y2']) == (4, 6, 8, 9)

    def test_missing_dash_is_syntax_error(self, gfx, helpers):
        errors = helpers.get_error_messages(gfx.process_command('LINE(0,0)(5,5)'))
        assert errors and 'SYNTAX' in errors[0]


class TestGetPut:
    @pytest.mark.parametrize('command', ['GET(0,0)-(5,5),A', 'GET(0,0)-(5,5),A,G', 'GET (0,0)-(5,5), A'])
    def test_get_forms(self, gfx, command):
        get = first(gfx.process_command(command), 'get')
        assert (get['x1'], get['y1'], get['x2'], get['y2'], get['array']) == (0, 0, 5, 5, 'A')

    def test_get_without_array_is_error(self, gfx, helpers):
        assert helpers.get_error_messages(gfx.process_command('GET(0,0)-(5,5)'))

    @pytest.mark.parametrize('action', ['PSET', 'PRESET', 'AND', 'OR', 'NOT'])
    def test_put_actions(self, gfx, action):
        put = first(gfx.process_command(f'PUT(10,20),A,{action}'), 'put')
        assert (put['x'], put['y'], put['array'], put['action']) == (10, 20, 'A', action)

    def test_put_default_action_is_pset(self, gfx):
        assert first(gfx.process_command('PUT(10,20),A'), 'put')['action'] == 'PSET'

    def test_put_unknown_action_is_error(self, gfx, helpers):
        errors = helpers.get_error_messages(gfx.process_command('PUT(10,20),A,BOGUS'))
        assert errors and 'SYNTAX ERROR' in errors[0]

    def test_get_put_need_graphics_mode(self, basic, helpers):
        for command in ['GET(0,0)-(5,5),A', 'PUT(0,0),A']:
            errors = helpers.get_error_messages(basic.process_command(command))
            assert errors and 'ILLEGAL FUNCTION CALL' in errors[0]


class TestGprint:
    def test_text_and_default_color(self, gfx):
        gtext = first(gfx.process_command('GPRINT(10,5),"HELLO"'), 'gtext')
        assert gtext == {'type': 'gtext', 'x': 10, 'y': 5, 'text': 'HELLO', 'color': 1}

    def test_expression_text_and_color(self, gfx):
        gfx.process_command('N$="CUBE": S=3')
        gtext = first(gfx.process_command('GPRINT(C(1),5),N$+"!",P(1)'), 'gtext')
        assert (gtext['x'], gtext['text'], gtext['color']) == (3, 'CUBE!', 7)

    def test_lowercase_is_uppercased(self, gfx):
        # The 4x6 font (like the CoCo's) has no lowercase glyphs
        assert first(gfx.process_command('GPRINT(0,0),"Solved!"'), 'gtext')['text'] == 'SOLVED!'

    @pytest.mark.parametrize('expr,text', [('42', '42'), ('4/2', '2'), ('1/4', '.25'), ('-3', '-3')])
    def test_number_is_printed_as_text(self, gfx, expr, text):
        assert first(gfx.process_command(f'GPRINT(0,0),{expr}'), 'gtext')['text'] == text

    @pytest.mark.parametrize('command', ['GPRINT(10,5)', 'GPRINT(10,5),', 'GPRINT 10,5,"X"'])
    def test_malformed_is_syntax_error(self, gfx, helpers, command):
        errors = helpers.get_error_messages(gfx.process_command(command))
        assert errors and 'SYNTAX ERROR' in errors[0], errors


class TestOtherCommands:
    def test_quoted_parenthesis_inside_pset(self, gfx, helpers):
        result = gfx.process_command('PSET(LEN(")"),5)')
        assert helpers.get_error_messages(result) == []

    def test_screen_argument_with_comma_expression(self, gfx, helpers):
        gfx.process_command('DIM X(2,2): X(1,1)=1')
        result = gfx.process_command('SCREEN X(1,1)')
        assert helpers.get_error_messages(result) == []

    def test_color_background_only(self, gfx):
        color = first(gfx.process_command('COLOR ,2'), 'set_color')
        assert color['fg'] is None and color['bg'] == 2


class TestArgumentRanges:
    """#12: out-of-range mode/color arguments are ILLEGAL FUNCTION CALL, and
    a string where a number belongs is TYPE MISMATCH, never a Python error."""

    @pytest.mark.parametrize('command', [
        'COLOR 99', 'COLOR 1,-5', 'COLOR -1', 'PMODE 4,99', 'PMODE 4,0', 'PMODE 5',
    ])
    def test_out_of_range_is_fc_error(self, gfx, helpers, command):
        errors = helpers.get_error_messages(gfx.process_command(command))
        assert errors and 'ILLEGAL FUNCTION CALL' in errors[0]

    @pytest.mark.parametrize('command', ['COLOR 0,8', 'COLOR 8', 'PMODE 0,1', 'PMODE 4,8'])
    def test_in_range_accepted(self, gfx, helpers, command):
        assert helpers.get_error_messages(gfx.process_command(command)) == []

    def test_screen_color_set_nonzero_means_one(self, gfx):
        # As on the CoCo, any nonzero color-set argument selects set 1
        screen = first(gfx.process_command('SCREEN 1,77'), 'set_screen')
        assert screen['page'] == 1
        screen = first(gfx.process_command('SCREEN 1,0'), 'set_screen')
        assert screen['page'] == 0

    @pytest.mark.parametrize('command', ['PSET(A$,1)', 'PMODE A$', 'COLOR A$', 'LINE(0,0)-(A$,5)'])
    def test_string_argument_is_type_mismatch(self, gfx, helpers, command):
        gfx.process_command('A$="X"')
        errors = helpers.get_error_messages(gfx.process_command(command))
        assert errors and 'TYPE MISMATCH' in errors[0]
        assert 'int()' not in errors[0]
