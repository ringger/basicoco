#!/usr/bin/env python3

"""
Tests for error handling and malformed input parsing.
Ensures the parser handles invalid syntax gracefully.
"""

import pytest


class TestErrorHandling:
    """Test cases for error handling and malformed input"""

    def test_basic_functionality(self, basic, helpers):
        """Test basic error handling functionality"""
        helpers.assert_error_output(basic, 'INVALID_COMMAND')

    def test_syntax_errors(self, basic, helpers):
        """Test various syntax error conditions"""
        # Missing THEN in IF statement
        helpers.assert_error_output(basic, 'IF X > 5 PRINT "ERROR"', 'SYNTAX ERROR')

        # Missing TO in FOR statement
        helpers.assert_error_output(basic, 'FOR I = 1 5', 'SYNTAX ERROR')

        # Invalid assignment (no variable name)
        helpers.assert_error_output(basic, '= 5', 'Unrecognized command')

    def test_array_errors(self, basic, helpers):
        """Test array-related error handling"""
        # Undimensioned array auto-dimensions to 10, so 11 is out of range
        helpers.assert_error_output(basic, 'PRINT A(11)', 'BAD SUBSCRIPT')

        # Bad subscript
        basic.process_command('DIM B(10)')
        helpers.assert_error_output(basic, 'PRINT B(15)', 'Error evaluating PRINT expression')
        helpers.assert_error_output(basic, 'PRINT B(-1)', 'Error evaluating PRINT expression')

    def test_for_loop_errors(self, basic, helpers):
        """Test FOR loop error conditions"""
        # NEXT without FOR
        helpers.assert_error_output(basic, 'NEXT I', 'NEXT WITHOUT FOR')

    def test_gosub_return_errors(self, basic, helpers):
        """Test GOSUB/RETURN error conditions"""
        # RETURN without GOSUB
        helpers.assert_error_output(basic, 'RETURN', 'RETURN WITHOUT GOSUB')

        # GOSUB to an undefined line from the prompt is an UNDEFINED LINE error
        helpers.assert_error_output(basic, 'GOSUB 9999', 'UNDEFINED LINE')
