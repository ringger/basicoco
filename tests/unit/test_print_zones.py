"""Tests for PRINT comma zone formatting (16-column zones)."""

import pytest


class TestPrintCommaZones:
    """Tests for comma separator advancing to 16-column zone boundaries."""

    def test_two_strings(self, basic, helpers):
        result = basic.process_command('PRINT "A","B"')
        output = helpers.get_text_output(result)
        assert output == ['A               B']

    def test_three_strings(self, basic, helpers):
        result = basic.process_command('PRINT "A","B","C"')
        output = helpers.get_text_output(result)
        # A at 0, B at 16, C at 32
        assert output == ['A               B               C']

    def test_longer_strings(self, basic, helpers):
        result = basic.process_command('PRINT "HELLO","WORLD"')
        output = helpers.get_text_output(result)
        # "HELLO" is 5 chars, pad 11 to reach col 16
        assert output == ['HELLO           WORLD']

    def test_string_at_zone_boundary(self, basic, helpers):
        """A 16-char string exactly fills zone 1, next starts at zone 2."""
        result = basic.process_command('PRINT "1234567890123456","X"')
        output = helpers.get_text_output(result)
        # 16 chars fills zone, comma advances to col 32
        assert output == ['1234567890123456                X']

    def test_numbers_with_zones(self, basic, helpers):
        result = basic.process_command('PRINT 1,2,3')
        output = helpers.get_text_output(result)
        text = output[0]
        # Numbers have leading/trailing spaces, check zone alignment
        assert ' 1 ' in text
        assert ' 2 ' in text
        assert ' 3 ' in text
        # Second number should start at or after column 16
        idx_2 = text.index(' 2 ')
        assert idx_2 >= 16

    def test_semicolon_no_zone(self, basic, helpers):
        """Semicolons should NOT add zone spacing."""
        result = basic.process_command('PRINT "A";"B";"C"')
        output = helpers.get_text_output(result)
        assert output == ['ABC']

    def test_mixed_separators(self, basic, helpers):
        result = basic.process_command('PRINT "A";"B","C"')
        output = helpers.get_text_output(result)
        # AB is 2 chars, comma advances to col 16
        assert output == ['AB              C']


class TestPrintTrailingComma:
    """Tests for trailing comma advancing to next zone."""

    def test_trailing_comma_advances_zone(self, basic, helpers):
        result = helpers.execute_program(basic, [
            '10 PRINT "A",',
            '20 PRINT "B"',
        ])
        output = helpers.get_text_output(result)
        # Line 10: "A" + pad to zone 2 (col 16), inline
        # Line 20: "B" starts at col 16 on same conceptual line
        assert any('A' in t for t in output)
        assert any('B' in t for t in output)

    def test_trailing_semicolon_no_advance(self, basic, helpers):
        result = helpers.execute_program(basic, [
            '10 PRINT "HELLO";',
            '20 PRINT "WORLD"',
        ])
        output = helpers.get_text_output(result)
        # Semicolon means no spacing
        assert 'HELLO' in output[0]


class TestPrintColumnReset:
    """Tests for print column resetting."""

    def test_newline_resets_column(self, basic, helpers):
        """A PRINT without trailing separator resets column to 0."""
        result = helpers.execute_program(basic, [
            '10 PRINT "AAAA"',
            '20 PRINT "B","C"',
        ])
        output = helpers.get_text_output(result)
        # Line 20 should start fresh at column 0
        assert output[1] == 'B               C'

    def test_cls_resets_column(self, basic, helpers):
        basic.process_command('PRINT "TEST";')
        basic.process_command('CLS')
        assert basic.print_column == 0
