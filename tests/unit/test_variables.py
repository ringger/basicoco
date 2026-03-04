#!/usr/bin/env python3

"""
Unit tests for variable assignment and retrieval
"""

import pytest


class TestVariables:
    """Test cases for variable operations"""

    def test_basic_functionality(self, basic, helpers):
        """Test basic variable assignment"""
        basic.process_command('A = 5')
        helpers.assert_variable_equals(basic, 'A', 5)

    def test_numeric_variables(self, basic, helpers):
        """Test numeric variable assignment and retrieval"""
        # Integer values
        basic.process_command('A = 42')
        helpers.assert_variable_equals(basic, 'A', 42)
        result = basic.process_command('PRINT A')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 42 ']

        # Float values
        basic.process_command('B = 3.14')
        helpers.assert_variable_equals(basic, 'B', 3.14)
        result = basic.process_command('PRINT B')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 3.14 ']

        # Negative values
        basic.process_command('C = -7')
        helpers.assert_variable_equals(basic, 'C', -7)
        result = basic.process_command('PRINT C')
        text_output = helpers.get_text_output(result)
        assert text_output == ['-7 ']

    def test_string_variables(self, basic, helpers):
        """Test string variable assignment and retrieval"""
        # Basic string assignment
        basic.process_command('A$ = "HELLO"')
        helpers.assert_variable_equals(basic, 'A$', 'HELLO')
        result = basic.process_command('PRINT A$')
        text_output = helpers.get_text_output(result)
        assert text_output == ['HELLO']

        # Empty string
        basic.process_command('B$ = ""')
        helpers.assert_variable_equals(basic, 'B$', '')
        result = basic.process_command('PRINT B$')
        text_output = helpers.get_text_output(result)
        assert text_output == ['']

        # String with spaces
        basic.process_command('C$ = "HELLO WORLD"')
        helpers.assert_variable_equals(basic, 'C$', 'HELLO WORLD')
        result = basic.process_command('PRINT C$')
        text_output = helpers.get_text_output(result)
        assert text_output == ['HELLO WORLD']

    def test_variable_overwrite(self, basic, helpers):
        """Test overwriting variable values"""
        # Numeric overwrite
        basic.process_command('A = 5')
        helpers.assert_variable_equals(basic, 'A', 5)
        basic.process_command('A = 10')
        helpers.assert_variable_equals(basic, 'A', 10)

        # String overwrite
        basic.process_command('B$ = "FIRST"')
        helpers.assert_variable_equals(basic, 'B$', 'FIRST')
        basic.process_command('B$ = "SECOND"')
        helpers.assert_variable_equals(basic, 'B$', 'SECOND')

    def test_variable_expressions(self, basic, helpers):
        """Test assigning expressions to variables"""
        # Mathematical expressions
        basic.process_command('A = 2 + 3')
        helpers.assert_variable_equals(basic, 'A', 5)

        basic.process_command('B = 10 - 4')
        helpers.assert_variable_equals(basic, 'B', 6)

        basic.process_command('C = 3 * 4')
        helpers.assert_variable_equals(basic, 'C', 12)

        basic.process_command('D = 15 / 3')
        helpers.assert_variable_equals(basic, 'D', 5)

    def test_variable_references(self, basic, helpers):
        """Test using variables in expressions"""
        # Set up initial variables
        basic.process_command('A = 10')
        basic.process_command('B = 5')

        # Use variables in expressions
        basic.process_command('C = A + B')
        helpers.assert_variable_equals(basic, 'C', 15)

        basic.process_command('D = A - B')
        helpers.assert_variable_equals(basic, 'D', 5)

        basic.process_command('E = A * B')
        helpers.assert_variable_equals(basic, 'E', 50)

    def test_let_command(self, basic, helpers):
        """Test explicit LET command"""
        # Basic LET usage
        basic.process_command('LET A = 42')
        helpers.assert_variable_equals(basic, 'A', 42)

        basic.process_command('LET B$ = "HELLO"')
        helpers.assert_variable_equals(basic, 'B$', 'HELLO')

    def test_variable_case_sensitivity(self, basic, helpers):
        """Test variable name case handling"""
        # TRS-80 BASIC should be case insensitive
        basic.process_command('a = 5')
        basic.process_command('PRINT A')  # Should work if case insensitive

        # The exact behavior may depend on implementation

    def test_multiple_variable_assignment(self, basic, helpers):
        """Test multiple variables in one line"""
        # Multi-statement assignment
        program = ['10 A = 5: B = 10: C$ = "HELLO"']
        helpers.execute_program(basic, program)

        helpers.assert_variable_equals(basic, 'A', 5)
        helpers.assert_variable_equals(basic, 'B', 10)
        helpers.assert_variable_equals(basic, 'C$', 'HELLO')

    def test_variables_in_program(self, basic, helpers):
        """Test variables within program execution"""
        program = [
            '10 A = 10',
            '20 B = 20',
            '30 C = A + B',
            '40 PRINT C'
        ]

        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)

        # Should print the sum
        assert any('30' in output for output in text_outputs)

    def test_let_reserved_function_name_conflicts(self, basic, helpers):
        """Test that LET cannot use reserved function names as variables"""
        # Test numeric functions
        helpers.assert_error_output(basic, 'LET LEN = 5', 'reserved function name')
        helpers.assert_error_output(basic, 'LET ABS = 3', 'reserved function name')
        helpers.assert_error_output(basic, 'LET INT = 10', 'reserved function name')
        helpers.assert_error_output(basic, 'LET RND = 2', 'reserved function name')
        helpers.assert_error_output(basic, 'LET SQR = 4', 'reserved function name')
        helpers.assert_error_output(basic, 'LET SIN = 5', 'reserved function name')
        helpers.assert_error_output(basic, 'LET COS = 5', 'reserved function name')
        helpers.assert_error_output(basic, 'LET TAN = 5', 'reserved function name')
        helpers.assert_error_output(basic, 'LET ATN = 5', 'reserved function name')
        helpers.assert_error_output(basic, 'LET EXP = 5', 'reserved function name')
        helpers.assert_error_output(basic, 'LET LOG = 5', 'reserved function name')
        helpers.assert_error_output(basic, 'LET VAL = 5', 'reserved function name')

        # Test string functions
        helpers.assert_error_output(basic, 'LET LEFT$ = "TEST"', 'reserved function name')
        helpers.assert_error_output(basic, 'LET RIGHT$ = "TEST"', 'reserved function name')
        helpers.assert_error_output(basic, 'LET MID$ = "TEST"', 'reserved function name')
        helpers.assert_error_output(basic, 'LET CHR$ = "TEST"', 'reserved function name')
        helpers.assert_error_output(basic, 'LET ASC = 5', 'reserved function name')  # ASC doesn't end with $
        helpers.assert_error_output(basic, 'LET STR$ = "TEST"', 'reserved function name')
        helpers.assert_error_output(basic, 'LET INKEY$ = "TEST"', 'reserved function name')

        # Test implicit assignment (without LET keyword)
        helpers.assert_error_output(basic, 'LEN = 5', 'reserved function name')
        helpers.assert_error_output(basic, 'STR$ = "TEST"', 'reserved function name')

        # Test array element assignments with reserved names (should also fail)
        basic.process_command('DIM VALID(5)')  # Create a valid array first
        helpers.assert_error_output(basic, 'STR$(0) = "TEST"', 'reserved function name')
        helpers.assert_error_output(basic, 'LEN(0) = 5', 'reserved function name')

        # Test that similar but non-reserved names still work
        basic.process_command('LET LENS = 42')  # Not LEN
        helpers.assert_variable_equals(basic, 'LENS', 42)

        basic.process_command('LET STRINGS$ = "HELLO"')  # Not STR$
        helpers.assert_variable_equals(basic, 'STRINGS$', 'HELLO')

        # Test that the functions still work normally after validation
        result = basic.process_command('PRINT LEN("TEST")')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 4 ']

        result = basic.process_command('PRINT STR$(123)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 123']  # STR$ adds leading space

        # Test that our valid variables work
        result = basic.process_command('PRINT LENS')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 42 ']

        result = basic.process_command('PRINT STRINGS$')
        text_output = helpers.get_text_output(result)
        assert text_output == ['HELLO']

    def test_complex_nested_function_expressions(self, basic, helpers):
        """Test complex mathematical expressions with nested functions"""
        # Set up test variables
        basic.process_command('A = 9')
        basic.process_command('B = 16')
        basic.process_command('S$ = "HELLO WORLD"')

        # Test nested mathematical functions
        result = basic.process_command('PRINT SQR(A) + SQR(B)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 7 ']  # 3 + 4 = 7

        result = basic.process_command('PRINT ABS(SIN(0)) + ABS(COS(0))')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 1 ']  # 0 + 1 = 1

        result = basic.process_command('PRINT INT(SQR(A)) * INT(SQR(B))')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 12 ']  # 3 * 4 = 12

        # Test nested string and conversion functions
        result = basic.process_command('PRINT LEN(STR$(123))')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 4 ']  # " 123" has 4 chars (with leading space)

        result = basic.process_command('PRINT VAL(STR$(456))')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 456 ']  # Convert number to string back to number

        result = basic.process_command('PRINT ASC(CHR$(65))')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 65 ']  # Convert to char back to ASCII

        # Test complex string function nesting
        result = basic.process_command('PRINT LEN(LEFT$(S$, 5))')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 5 ']  # Length of "HELLO"

        result = basic.process_command('PRINT LEFT$(MID$(S$, 7, 5), 3)')
        text_output = helpers.get_text_output(result)
        assert text_output == ['WOR']  # Left 3 chars of "WORLD"

        result = basic.process_command('PRINT RIGHT$(LEFT$(S$, 8), 3)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' WO']  # Right 3 of "HELLO WO"

        # Test mathematical expressions with string length
        result = basic.process_command('PRINT LEN(S$) - 5')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 6 ']  # 11 - 5 = 6

        result = basic.process_command('PRINT SQR(LEN("TEST"))')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 2 ']  # SQR(4) = 2

        # Test deeply nested expressions
        basic.process_command('X = 25')
        result = basic.process_command('PRINT INT(SQR(X)) + LEN(STR$(X))')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 8 ']  # 5 + 3 = 8 (25 -> " 25" = 3 chars)

        # Test complex conditional-like expressions (using mathematical comparisons)
        result = basic.process_command('PRINT ABS(SQR(A) - 3)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 0 ']  # |3 - 3| = 0

        result = basic.process_command('PRINT INT(LEN(S$) / 2)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 5 ']  # INT(11/2) = INT(5.5) = 5

        # Test function chains with variables
        basic.process_command('Y = LEN(S$)')
        result = basic.process_command('PRINT SQR(Y - 2)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 3 ']  # SQR(11-2) = SQR(9) = 3

