"""Tests for graphics coordinate parsing edge cases and error paths.

Covers _parse_coord_pair error handling and coordinate parsing
in PSET, LINE, and CIRCLE commands.
"""

import pytest


class TestCoordinateParsingErrors:
    """Test error handling in coordinate parsing for graphics commands."""

    def setup_method(self):
        """Enable graphics mode for all tests."""
        pass

    def _setup_graphics(self, basic):
        basic.process_command('PMODE 4,1')

    def test_pset_missing_parentheses(self, basic, helpers):
        self._setup_graphics(basic)
        result = basic.process_command('PSET 100')
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0, "PSET with single number should error"

    def test_pset_missing_closing_paren(self, basic, helpers):
        self._setup_graphics(basic)
        result = basic.process_command('PSET(100,50')
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0, "PSET with missing closing paren should error"

    def test_pset_too_many_coords(self, basic, helpers):
        self._setup_graphics(basic)
        result = basic.process_command('PSET(10,20,30)')
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0, "PSET with 3 coords should error"

    def test_pset_single_coord(self, basic, helpers):
        self._setup_graphics(basic)
        result = basic.process_command('PSET(100)')
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0, "PSET with 1 coord should error"

    def test_pset_empty_parens(self, basic, helpers):
        self._setup_graphics(basic)
        result = basic.process_command('PSET()')
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0, "PSET with empty parens should error"

    def test_circle_missing_radius(self, basic, helpers):
        self._setup_graphics(basic)
        result = basic.process_command('CIRCLE(100,100)')
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0, "CIRCLE without radius should error"

    def test_line_missing_second_point(self, basic, helpers):
        self._setup_graphics(basic)
        result = basic.process_command('LINE(10,20)')
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0, "LINE with only one point should error"


class TestCoordinateExpressions:
    """Test coordinate parsing with various expression types."""

    def _setup_graphics(self, basic):
        basic.process_command('PMODE 4,1')

    def test_pset_with_arithmetic(self, basic, helpers):
        self._setup_graphics(basic)
        basic.process_command('X = 50')
        result = basic.process_command('PSET(X+10, X*2)')
        errors = helpers.get_error_messages(result)
        assert errors == []

    def test_pset_with_negative_coords(self, basic, helpers):
        """Negative coords should not crash — they may be clipped or errored."""
        self._setup_graphics(basic)
        result = basic.process_command('PSET(-1, -1)')
        # Just verify it doesn't crash — behavior may vary
        assert isinstance(result, list)

    def test_line_with_expressions(self, basic, helpers):
        self._setup_graphics(basic)
        basic.process_command('X1 = 10')
        basic.process_command('Y1 = 20')
        result = basic.process_command('LINE(X1,Y1)-(X1+50,Y1+50)')
        errors = helpers.get_error_messages(result)
        assert errors == []

    def test_circle_with_expression_radius(self, basic, helpers):
        self._setup_graphics(basic)
        basic.process_command('R = 25')
        result = basic.process_command('CIRCLE(128,96),R*2')
        errors = helpers.get_error_messages(result)
        assert errors == []

    def test_pset_with_function_call_in_coords(self, basic, helpers):
        self._setup_graphics(basic)
        result = basic.process_command('PSET(ABS(-50), INT(75.9))')
        errors = helpers.get_error_messages(result)
        assert errors == []

    def test_nested_parens_in_coords(self, basic, helpers):
        """Coordinates containing nested parentheses (function calls)."""
        self._setup_graphics(basic)
        result = basic.process_command('PSET(INT(128), INT(96))')
        errors = helpers.get_error_messages(result)
        assert errors == []


class TestLineCoordinatePairSyntax:
    """Test LINE command with (x1,y1)-(x2,y2) coordinate pair syntax.

    Regression tests for a bug where spaces around the dash separator
    (e.g. '(0,96) - (255,96)') were not recognized.
    """

    def _setup_graphics(self, basic):
        basic.process_command('PMODE 4,1')

    def test_line_compact_syntax(self, basic, helpers):
        """LINE (x1,y1)-(x2,y2) with no spaces around dash."""
        self._setup_graphics(basic)
        result = basic.process_command('LINE (0,96)-(255,96)')
        errors = helpers.get_error_messages(result)
        assert errors == []
        assert any(item.get('type') == 'line' for item in result)

    def test_line_spaces_around_dash(self, basic, helpers):
        """LINE (x1,y1) - (x2,y2) with spaces around dash."""
        self._setup_graphics(basic)
        result = basic.process_command('LINE (0, 96) - (255, 96)')
        errors = helpers.get_error_messages(result)
        assert errors == []
        line_item = next(item for item in result if item.get('type') == 'line')
        assert line_item['x1'] == 0
        assert line_item['y1'] == 96
        assert line_item['x2'] == 255
        assert line_item['y2'] == 96

    def test_line_with_pset_mode(self, basic, helpers):
        """LINE (x1,y1)-(x2,y2), PSET mode flag."""
        self._setup_graphics(basic)
        result = basic.process_command('LINE (10,10)-(50,50), PSET')
        errors = helpers.get_error_messages(result)
        assert errors == []
        line_item = next(item for item in result if item.get('type') == 'line')
        assert line_item['mode'] == 'PSET'

    def test_line_with_preset_mode(self, basic, helpers):
        """LINE (x1,y1)-(x2,y2), PRESET mode flag."""
        self._setup_graphics(basic)
        result = basic.process_command('LINE (10,10)-(50,50), PRESET')
        errors = helpers.get_error_messages(result)
        assert errors == []
        line_item = next(item for item in result if item.get('type') == 'line')
        assert line_item['mode'] == 'PRESET'

    def test_line_with_color_number(self, basic, helpers):
        """LINE (x1,y1)-(x2,y2), color as a number."""
        self._setup_graphics(basic)
        result = basic.process_command('LINE (10,10)-(50,50), 3')
        errors = helpers.get_error_messages(result)
        assert errors == []
        line_item = next(item for item in result if item.get('type') == 'line')
        assert line_item['color'] == 3

    def test_line_spaces_with_expressions(self, basic, helpers):
        """LINE with variable expressions and spaces around dash."""
        self._setup_graphics(basic)
        basic.process_command('X1 = 10')
        basic.process_command('Y1 = 20')
        result = basic.process_command('LINE (X1, Y1) - (X1+50, Y1+50)')
        errors = helpers.get_error_messages(result)
        assert errors == []
        line_item = next(item for item in result if item.get('type') == 'line')
        assert line_item['x1'] == 10
        assert line_item['y1'] == 20
        assert line_item['x2'] == 60
        assert line_item['y2'] == 70


class TestLineBoxModes:
    """Test LINE command with B (box) and BF (filled box) modifiers."""

    def _setup_graphics(self, basic):
        basic.process_command('PMODE 4,1')

    def _get_line_item(self, result):
        return next(item for item in result if item.get('type') == 'line')

    def test_box_with_pset(self, basic, helpers):
        self._setup_graphics(basic)
        result = basic.process_command('LINE (10,10)-(50,50), PSET, B')
        assert helpers.get_error_messages(result) == []
        item = self._get_line_item(result)
        assert item['box_type'] == 'B'
        assert item['mode'] == 'PSET'

    def test_filled_box_with_pset(self, basic, helpers):
        self._setup_graphics(basic)
        result = basic.process_command('LINE (10,10)-(50,50), PSET, BF')
        assert helpers.get_error_messages(result) == []
        item = self._get_line_item(result)
        assert item['box_type'] == 'BF'

    def test_box_with_color(self, basic, helpers):
        self._setup_graphics(basic)
        result = basic.process_command('LINE (10,10)-(50,50), 3, B')
        assert helpers.get_error_messages(result) == []
        item = self._get_line_item(result)
        assert item['color'] == 3
        assert item['box_type'] == 'B'

    def test_box_without_mode(self, basic, helpers):
        """LINE (x1,y1)-(x2,y2), B — box with no explicit mode."""
        self._setup_graphics(basic)
        result = basic.process_command('LINE (10,10)-(50,50), B')
        assert helpers.get_error_messages(result) == []
        item = self._get_line_item(result)
        assert item['box_type'] == 'B'

    def test_filled_box_without_mode(self, basic, helpers):
        """LINE (x1,y1)-(x2,y2), BF — filled box with no explicit mode."""
        self._setup_graphics(basic)
        result = basic.process_command('LINE (10,10)-(50,50), BF')
        assert helpers.get_error_messages(result) == []
        item = self._get_line_item(result)
        assert item['box_type'] == 'BF'

    def test_plain_line_has_no_box_type(self, basic, helpers):
        """Plain LINE without B/BF should have box_type=None."""
        self._setup_graphics(basic)
        result = basic.process_command('LINE (10,10)-(50,50)')
        assert helpers.get_error_messages(result) == []
        item = self._get_line_item(result)
        assert item['box_type'] is None

    def test_box_with_spaces_around_dash(self, basic, helpers):
        self._setup_graphics(basic)
        result = basic.process_command('LINE (10, 10) - (50, 50), PSET, B')
        assert helpers.get_error_messages(result) == []
        item = self._get_line_item(result)
        assert item['box_type'] == 'B'
        assert item['x1'] == 10
        assert item['x2'] == 50
