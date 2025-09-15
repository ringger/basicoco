#!/usr/bin/env python3

"""
Unit tests for variable assignment and retrieval
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from test_base import BaseTestCase


class VariableTest(BaseTestCase):
    """Test cases for variable operations"""

    def test_basic_functionality(self):
        """Test basic variable assignment"""
        self.basic.execute_command('A = 5')
        self.assert_variable_equals('A', 5)

    def test_numeric_variables(self):
        """Test numeric variable assignment and retrieval"""
        # Integer values
        self.basic.execute_command('A = 42')
        self.assert_variable_equals('A', 42)
        self.assert_text_output('PRINT A', '42')
        
        # Float values  
        self.basic.execute_command('B = 3.14')
        self.assert_variable_equals('B', 3.14)
        self.assert_text_output('PRINT B', '3.14')
        
        # Negative values
        self.basic.execute_command('C = -7')
        self.assert_variable_equals('C', -7)
        self.assert_text_output('PRINT C', '-7')

    def test_string_variables(self):
        """Test string variable assignment and retrieval"""
        # Basic string assignment
        self.basic.execute_command('A$ = "HELLO"')
        self.assert_variable_equals('A$', 'HELLO')
        self.assert_text_output('PRINT A$', 'HELLO')
        
        # Empty string
        self.basic.execute_command('B$ = ""')
        self.assert_variable_equals('B$', '')
        self.assert_text_output('PRINT B$', '')
        
        # String with spaces
        self.basic.execute_command('C$ = "HELLO WORLD"')
        self.assert_variable_equals('C$', 'HELLO WORLD')
        self.assert_text_output('PRINT C$', 'HELLO WORLD')

    def test_variable_overwrite(self):
        """Test overwriting variable values"""
        # Numeric overwrite
        self.basic.execute_command('A = 5')
        self.assert_variable_equals('A', 5)
        self.basic.execute_command('A = 10')
        self.assert_variable_equals('A', 10)
        
        # String overwrite
        self.basic.execute_command('B$ = "FIRST"')
        self.assert_variable_equals('B$', 'FIRST')
        self.basic.execute_command('B$ = "SECOND"')
        self.assert_variable_equals('B$', 'SECOND')

    def test_variable_expressions(self):
        """Test assigning expressions to variables"""
        # Mathematical expressions
        self.basic.execute_command('A = 2 + 3')
        self.assert_variable_equals('A', 5)
        
        self.basic.execute_command('B = 10 - 4')
        self.assert_variable_equals('B', 6)
        
        self.basic.execute_command('C = 3 * 4')
        self.assert_variable_equals('C', 12)
        
        self.basic.execute_command('D = 15 / 3')
        self.assert_variable_equals('D', 5)

    def test_variable_references(self):
        """Test using variables in expressions"""
        # Set up initial variables
        self.basic.execute_command('A = 10')
        self.basic.execute_command('B = 5')
        
        # Use variables in expressions
        self.basic.execute_command('C = A + B')
        self.assert_variable_equals('C', 15)
        
        self.basic.execute_command('D = A - B')
        self.assert_variable_equals('D', 5)
        
        self.basic.execute_command('E = A * B')
        self.assert_variable_equals('E', 50)

    def test_let_command(self):
        """Test explicit LET command"""
        # Basic LET usage
        self.basic.execute_command('LET A = 42')
        self.assert_variable_equals('A', 42)
        
        self.basic.execute_command('LET B$ = "HELLO"')
        self.assert_variable_equals('B$', 'HELLO')

    def test_variable_case_sensitivity(self):
        """Test variable name case handling"""
        # TRS-80 BASIC should be case insensitive
        self.basic.execute_command('a = 5')
        self.basic.execute_command('PRINT A')  # Should work if case insensitive
        
        # The exact behavior may depend on implementation

    def test_invalid_variable_names(self):
        """Test error handling for invalid variable names"""
        # These should produce errors
        try:
            result = self.basic.execute_command('123 = 5')  # Number as variable name
            # Should produce error or be rejected
        except:
            pass
        
        try:
            result = self.basic.execute_command('A B = 5')  # Space in variable name
            # Should produce error or be rejected
        except:
            pass

    def test_multiple_variable_assignment(self):
        """Test multiple variables in one line"""
        # Multi-statement assignment
        program = ['10 A = 5: B = 10: C$ = "HELLO"']
        self.execute_program(program)
        
        self.assert_variable_equals('A', 5)
        self.assert_variable_equals('B', 10)
        self.assert_variable_equals('C$', 'HELLO')

    def test_variables_in_program(self):
        """Test variables within program execution"""
        program = [
            '10 A = 10',
            '20 B = 20', 
            '30 C = A + B',
            '40 PRINT C'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Should print the sum
        self.assertTrue(any('30' in output for output in text_outputs))

    def test_let_reserved_function_name_conflicts(self):
        """Test that LET cannot use reserved function names as variables"""
        # Test numeric functions
        self.assert_error_output('LET LEN = 5', 'reserved function name')
        self.assert_error_output('LET ABS = 3', 'reserved function name')
        self.assert_error_output('LET INT = 10', 'reserved function name')
        self.assert_error_output('LET RND = 2', 'reserved function name')
        self.assert_error_output('LET SQR = 4', 'reserved function name')
        self.assert_error_output('LET SIN = 5', 'reserved function name')
        self.assert_error_output('LET COS = 5', 'reserved function name')
        self.assert_error_output('LET TAN = 5', 'reserved function name')
        self.assert_error_output('LET ATN = 5', 'reserved function name')
        self.assert_error_output('LET EXP = 5', 'reserved function name')
        self.assert_error_output('LET LOG = 5', 'reserved function name')
        self.assert_error_output('LET VAL = 5', 'reserved function name')
        
        # Test string functions
        self.assert_error_output('LET LEFT$ = "TEST"', 'reserved function name')
        self.assert_error_output('LET RIGHT$ = "TEST"', 'reserved function name')
        self.assert_error_output('LET MID$ = "TEST"', 'reserved function name')
        self.assert_error_output('LET CHR$ = "TEST"', 'reserved function name')
        self.assert_error_output('LET ASC = 5', 'reserved function name')  # ASC doesn't end with $
        self.assert_error_output('LET STR$ = "TEST"', 'reserved function name')
        self.assert_error_output('LET INKEY$ = "TEST"', 'reserved function name')
        
        # Test implicit assignment (without LET keyword)
        self.assert_error_output('LEN = 5', 'reserved function name')
        self.assert_error_output('STR$ = "TEST"', 'reserved function name')
        
        # Test array element assignments with reserved names (should also fail)
        self.basic.execute_command('DIM VALID(5)')  # Create a valid array first
        self.assert_error_output('STR$(0) = "TEST"', 'reserved function name')
        self.assert_error_output('LEN(0) = 5', 'reserved function name')
        
        # Test that similar but non-reserved names still work
        self.basic.execute_command('LET LENS = 42')  # Not LEN
        self.assert_variable_equals('LENS', 42)
        
        self.basic.execute_command('LET STRINGS$ = "HELLO"')  # Not STR$
        self.assert_variable_equals('STRINGS$', 'HELLO')
        
        # Test that the functions still work normally after validation
        self.assert_text_output('PRINT LEN("TEST")', '4')
        self.assert_text_output('PRINT STR$(123)', ' 123')  # STR$ adds leading space
        
        # Test that our valid variables work
        self.assert_text_output('PRINT LENS', '42')
        self.assert_text_output('PRINT STRINGS$', 'HELLO')

    def test_complex_nested_function_expressions(self):
        """Test complex mathematical expressions with nested functions"""
        # Set up test variables
        self.basic.execute_command('A = 9')
        self.basic.execute_command('B = 16')
        self.basic.execute_command('S$ = "HELLO WORLD"')
        
        # Test nested mathematical functions
        self.assert_text_output('PRINT SQR(A) + SQR(B)', '7')  # 3 + 4 = 7
        self.assert_text_output('PRINT ABS(SIN(0)) + ABS(COS(0))', '1')  # 0 + 1 = 1
        self.assert_text_output('PRINT INT(SQR(A)) * INT(SQR(B))', '12')  # 3 * 4 = 12
        
        # Test nested string and conversion functions
        self.assert_text_output('PRINT LEN(STR$(123))', '4')  # " 123" has 4 chars (with leading space)
        self.assert_text_output('PRINT VAL(STR$(456))', '456')  # Convert number to string back to number
        self.assert_text_output('PRINT ASC(CHR$(65))', '65')  # Convert to char back to ASCII
        
        # Test complex string function nesting
        self.assert_text_output('PRINT LEN(LEFT$(S$, 5))', '5')  # Length of "HELLO"
        self.assert_text_output('PRINT LEFT$(MID$(S$, 7, 5), 3)', 'WOR')  # Left 3 chars of "WORLD"
        self.assert_text_output('PRINT RIGHT$(LEFT$(S$, 8), 3)', ' WO')  # Right 3 of "HELLO WO"
        
        # Test mathematical expressions with string length
        self.assert_text_output('PRINT LEN(S$) - 5', '6')  # 11 - 5 = 6
        self.assert_text_output('PRINT SQR(LEN("TEST"))', '2')  # SQR(4) = 2
        
        # Test deeply nested expressions
        self.basic.execute_command('X = 25')
        self.assert_text_output('PRINT INT(SQR(X)) + LEN(STR$(X))', '8')  # 5 + 3 = 8 (25 -> " 25" = 3 chars)
        
        # Test complex conditional-like expressions (using mathematical comparisons)
        self.assert_text_output('PRINT ABS(SQR(A) - 3)', '0')  # |3 - 3| = 0
        self.assert_text_output('PRINT INT(LEN(S$) / 2)', '5')  # INT(11/2) = INT(5.5) = 5
        
        # Test function chains with variables
        self.basic.execute_command('Y = LEN(S$)')
        self.assert_text_output('PRINT SQR(Y - 2)', '3')  # SQR(11-2) = SQR(9) = 3


if __name__ == '__main__':
    test = VariableTest("Variable Tests")
    results = test.run_all_tests()
    from test_base import print_test_results
    print_test_results(results, verbose=True)