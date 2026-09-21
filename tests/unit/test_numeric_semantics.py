"""Unit tests for CoCo numeric semantics: number formatting, VAL prefix
parsing, operator precedence/associativity, MOD, and ^ edge cases."""

import pytest

from emulator.ast_nodes import format_basic_number
from emulator.functions import basic_number_prefix


class TestFormatBasicNumber:
    @pytest.mark.parametrize('value,expected', [
        (0, '0'), (3, '3'), (-3, '-3'), (2.0, '2'),
        (0.5, '.5'), (-0.5, '-.5'), (1 / 3, '.333333333'),
        (0.1 + 0.2, '.3'), (0.01, '.01'), (0.001, '1E-03'), (-0.001, '-1E-03'),
        (12345.6789012, '12345.6789'), (999999999, '999999999'),
        (1234567890, '1.23456789E+09'), (1e20, '1E+20'), (2 ** 100, '1.2676506E+30'),
        (True, '-1'), (False, '0'),
    ])
    def test_format(self, value, expected):
        assert format_basic_number(value) == expected

    def test_print_uses_sign_space(self, basic, helpers):
        assert helpers.get_text_output(basic.process_command('PRINT 1/3')) == [' .333333333 ']
        assert helpers.get_text_output(basic.process_command('PRINT -1/2')) == ['-.5 ']

    def test_str_dollar_matches_print(self, basic):
        assert basic.evaluate_expression('STR$(1/3)') == ' .333333333'
        assert basic.evaluate_expression('STR$(-2.5)') == '-2.5'
        assert basic.evaluate_expression('STR$(7)') == ' 7'


class TestBasicNumberPrefix:
    @pytest.mark.parametrize('text,expected', [
        ('12', 12), ('  -3.5', -3.5), ('12ABC', 12), ('1 2', 12), ('&HFF', 255),
        ('&O17', 15), ('1_000', 1), ('ABC', 0), ('', 0), ('.5', 0.5), ('1E3', 1000.0),
        ('+7', 7), ('.', 0),
    ])
    def test_prefix(self, text, expected):
        assert basic_number_prefix(text) == expected

    def test_overflow(self):
        with pytest.raises(OverflowError):
            basic_number_prefix('1E999')


class TestPrecedence:
    @pytest.mark.parametrize('expr,expected', [
        ('2+3*4', 14), ('(2+3)*4', 20), ('2^3^2', 64), ('-2^2', -4), ('2^-1', 0.5),
        ('10-5-2', 3), ('12/2/3', 2), ('10 MOD 3*2', 4), ('-7 MOD 3', -1), ('7 MOD -3', 1),
        ('7.6 MOD 2', 0), ('1+2=3', -1), ('5=5<1', -1), ('NOT 0', -1), ('NOT 3=5', -1),
        ('1 OR 0 AND 0', 1), ('3 =< 3', -1), ('4 => 5', 0), ('1 >< 2', -1),
        ('&HFF AND 15', 15),
    ])
    def test_expression(self, basic, expr, expected):
        assert basic.evaluate_expression(expr) == expected


class TestPowerEdgeCases:
    def test_integer_power_stays_integer(self, basic):
        value = basic.evaluate_expression('2^10')
        assert value == 1024 and isinstance(value, int)

    def test_power_tower_is_left_associative_and_fast(self, basic):
        # (9^9)^9 is about 1.97E+77: computed in floats, instantly
        assert basic.evaluate_expression('9^9^9') == pytest.approx(387420489.0 ** 9)

    @pytest.mark.parametrize('expr', ['9^9^9^9', '10^400', '1E308*10'])
    def test_overflow_is_basic_error(self, basic, helpers, expr):
        errors = helpers.get_error_messages(basic.process_command(f'PRINT {expr}'))
        assert errors and 'OVERFLOW' in errors[0].upper()

    def test_negative_base_fractional_power(self, basic, helpers):
        errors = helpers.get_error_messages(basic.process_command('PRINT (-8)^(1/3)'))
        assert errors and 'ILLEGAL FUNCTION CALL' in errors[0]

    def test_zero_to_negative_power(self, basic, helpers):
        errors = helpers.get_error_messages(basic.process_command('PRINT 0^-1'))
        assert errors
