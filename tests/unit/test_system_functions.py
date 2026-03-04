#!/usr/bin/env python3

"""
Unit tests for system functions (MEM, FRE) and PCLEAR command.
"""

import pytest


class TestMemFunction:
    """Test cases for MEM function"""

    def test_mem_returns_million(self, basic):
        """MEM returns 1000000"""
        result = basic.evaluate_expression("MEM")
        assert result == 1000000

    def test_mem_in_expression(self, basic):
        """MEM can be used in expressions"""
        result = basic.evaluate_expression("MEM + 1")
        assert result == 1000001

    def test_mem_in_print(self, basic, helpers):
        """PRINT MEM outputs 1000000"""
        result = basic.process_command("PRINT MEM")
        text = helpers.get_text_output(result)
        assert text == [" 1000000 "]

    def test_mem_no_args(self, basic, helpers):
        """MEM takes no arguments"""
        helpers.assert_error_output(basic, "PRINT MEM(1)")

    def test_mem_reserved_name(self, basic, helpers):
        """MEM cannot be used as a variable name"""
        helpers.assert_error_output(basic, "MEM = 5", "reserved function name")
        helpers.assert_error_output(basic, "LET MEM = 5", "reserved function name")


class TestFreFunction:
    """Test cases for FRE function"""

    def test_fre_returns_million(self, basic):
        """FRE(0) returns 1000000"""
        result = basic.evaluate_expression("FRE(0)")
        assert result == 1000000

    def test_fre_with_string_arg(self, basic):
        """FRE accepts a string argument"""
        result = basic.evaluate_expression('FRE("")')
        assert result == 1000000

    def test_fre_in_expression(self, basic):
        """FRE can be used in expressions"""
        result = basic.evaluate_expression("FRE(0) + 1")
        assert result == 1000001

    def test_fre_in_print(self, basic, helpers):
        """PRINT FRE(0) outputs 1000000"""
        result = basic.process_command("PRINT FRE(0)")
        text = helpers.get_text_output(result)
        assert text == [" 1000000 "]

    def test_fre_requires_argument(self, basic, helpers):
        """FRE requires exactly one argument"""
        helpers.assert_error_output(basic, "PRINT FRE()")

    def test_fre_reserved_name(self, basic, helpers):
        """FRE cannot be used as a variable name"""
        helpers.assert_error_output(basic, "FRE = 5", "reserved function name")


class TestPclearCommand:
    """Test cases for PCLEAR command"""

    def test_pclear_valid_pages(self, basic):
        """PCLEAR accepts values 1 through 8"""
        for n in range(1, 9):
            result = basic.process_command(f"PCLEAR {n}")
            assert result[0]['type'] == 'text'
            assert result[0]['text'] == 'OK'

    def test_pclear_zero(self, basic, helpers):
        """PCLEAR 0 is out of range"""
        helpers.assert_error_output(basic, "PCLEAR 0")

    def test_pclear_nine(self, basic, helpers):
        """PCLEAR 9 is out of range"""
        helpers.assert_error_output(basic, "PCLEAR 9")

    def test_pclear_negative(self, basic, helpers):
        """PCLEAR with negative value is out of range"""
        helpers.assert_error_output(basic, "PCLEAR -1")

    def test_pclear_no_arg(self, basic, helpers):
        """PCLEAR requires an argument"""
        helpers.assert_error_output(basic, "PCLEAR")

    def test_pclear_expression(self, basic):
        """PCLEAR accepts an expression"""
        basic.variables['N'] = 4
        result = basic.process_command("PCLEAR N")
        assert result[0]['type'] == 'text'
        assert result[0]['text'] == 'OK'

    def test_pclear_in_program(self, basic, helpers):
        """PCLEAR works in a program"""
        result = helpers.execute_program(basic, [
            '10 PCLEAR 4',
            '20 PRINT "DONE"',
        ])
        text = helpers.get_text_output(result)
        assert "DONE" in text
