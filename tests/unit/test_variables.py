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


if __name__ == '__main__':
    test = VariableTest("Variable Tests")
    results = test.run_all_tests()
    from test_base import print_test_results
    print_test_results(results, verbose=True)