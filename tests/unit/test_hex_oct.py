"""Tests for HEX$ and OCT$ functions."""

import pytest


class TestHexFunction:
    """Tests for HEX$(n) — hexadecimal string conversion."""

    def test_hex_zero(self, basic, helpers):
        result = basic.process_command('PRINT HEX$(0)')
        assert helpers.get_text_output(result) == ['0']

    def test_hex_small_number(self, basic, helpers):
        result = basic.process_command('PRINT HEX$(15)')
        assert helpers.get_text_output(result) == ['F']

    def test_hex_255(self, basic, helpers):
        result = basic.process_command('PRINT HEX$(255)')
        assert helpers.get_text_output(result) == ['FF']

    def test_hex_256(self, basic, helpers):
        result = basic.process_command('PRINT HEX$(256)')
        assert helpers.get_text_output(result) == ['100']

    def test_hex_4096(self, basic, helpers):
        result = basic.process_command('PRINT HEX$(4096)')
        assert helpers.get_text_output(result) == ['1000']

    def test_hex_max_value(self, basic, helpers):
        result = basic.process_command('PRINT HEX$(65535)')
        assert helpers.get_text_output(result) == ['FFFF']

    def test_hex_negative_error(self, basic, helpers):
        result = basic.process_command('PRINT HEX$(-1)')
        errors = helpers.get_error_messages(result)
        assert any('out of range' in e.lower() for e in errors)

    def test_hex_too_large_error(self, basic, helpers):
        result = basic.process_command('PRINT HEX$(65536)')
        errors = helpers.get_error_messages(result)
        assert any('out of range' in e.lower() for e in errors)

    def test_hex_with_expression(self, basic, helpers):
        result = basic.process_command('PRINT HEX$(10+5)')
        assert helpers.get_text_output(result) == ['F']

    def test_hex_in_string_concat(self, basic, helpers):
        result = basic.process_command('PRINT "VALUE: " + HEX$(255)')
        assert helpers.get_text_output(result) == ['VALUE: FF']

    def test_hex_type_error(self, basic, helpers):
        result = basic.process_command('PRINT HEX$("ABC")')
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0


class TestOctFunction:
    """Tests for OCT$(n) — octal string conversion."""

    def test_oct_zero(self, basic, helpers):
        result = basic.process_command('PRINT OCT$(0)')
        assert helpers.get_text_output(result) == ['0']

    def test_oct_seven(self, basic, helpers):
        result = basic.process_command('PRINT OCT$(7)')
        assert helpers.get_text_output(result) == ['7']

    def test_oct_eight(self, basic, helpers):
        result = basic.process_command('PRINT OCT$(8)')
        assert helpers.get_text_output(result) == ['10']

    def test_oct_255(self, basic, helpers):
        result = basic.process_command('PRINT OCT$(255)')
        assert helpers.get_text_output(result) == ['377']

    def test_oct_max_value(self, basic, helpers):
        result = basic.process_command('PRINT OCT$(65535)')
        assert helpers.get_text_output(result) == ['177777']

    def test_oct_negative_error(self, basic, helpers):
        result = basic.process_command('PRINT OCT$(-1)')
        errors = helpers.get_error_messages(result)
        assert any('out of range' in e.lower() for e in errors)

    def test_oct_too_large_error(self, basic, helpers):
        result = basic.process_command('PRINT OCT$(65536)')
        errors = helpers.get_error_messages(result)
        assert any('out of range' in e.lower() for e in errors)

    def test_oct_with_expression(self, basic, helpers):
        result = basic.process_command('PRINT OCT$(3+5)')
        assert helpers.get_text_output(result) == ['10']


class TestHexOctInProgram:
    """Tests for HEX$ and OCT$ within program execution."""

    def test_hex_in_program(self, basic, helpers):
        result = helpers.execute_program(basic, [
            '10 FOR I = 0 TO 3',
            '20 PRINT HEX$(I * 16)',
            '30 NEXT I',
        ])
        output = helpers.get_text_output(result)
        assert output == ['0', '10', '20', '30']

    def test_oct_in_program(self, basic, helpers):
        result = helpers.execute_program(basic, [
            '10 A = 64',
            '20 PRINT OCT$(A)',
        ])
        assert helpers.get_text_output(result) == ['100']

    def test_hex_oct_combined(self, basic, helpers):
        result = basic.process_command('PRINT HEX$(255) + " " + OCT$(255)')
        assert helpers.get_text_output(result) == ['FF 377']
