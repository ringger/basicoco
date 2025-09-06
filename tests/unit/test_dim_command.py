#!/usr/bin/env python3

"""
Unit tests for DIM command - array declarations and operations.
Tests array creation, bounds checking, and multi-dimensional arrays.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from test_base import BaseTestCase


class DimCommandTest(BaseTestCase):
    """Test cases for DIM command and array operations"""

    def test_basic_functionality(self):
        """Test basic DIM command functionality"""
        # Test simple array declaration
        result = self.basic.execute_command('DIM A(10)')
        self.assertTrue(len(result) == 0 or (len(result) == 1 and result[0].get('type') == 'text'))

    def test_1d_numeric_array(self):
        """Test 1D numeric array operations"""
        # Declare array
        self.basic.execute_command('DIM A(10)')
        
        # Set and get array element
        self.basic.execute_command('A(5) = 42')
        self.assert_text_output('PRINT A(5)', '42')

    def test_1d_string_array(self):
        """Test 1D string array operations"""
        # Declare string array
        self.basic.execute_command('DIM B$(5)')
        
        # Set and get string array element
        self.basic.execute_command('B$(3) = "HELLO"')
        self.assert_text_output('PRINT B$(3)', 'HELLO')

    def test_2d_array(self):
        """Test 2D array operations"""
        # Declare 2D array
        self.basic.execute_command('DIM C(3,4)')
        
        # Set and get 2D array element
        self.basic.execute_command('C(2,3) = 99')
        self.assert_text_output('PRINT C(2,3)', '99')

    def test_multiple_arrays_in_one_dim(self):
        """Test declaring multiple arrays in one DIM statement"""
        result = self.basic.execute_command('DIM X(5), Y$(3), Z(2,2)')
        
        # Should succeed without error
        self.assertFalse(any(item.get('type') == 'error' for item in result))
        
        # Test that all arrays work
        self.basic.execute_command('X(3) = 10')
        self.assert_text_output('PRINT X(3)', '10')
        
        self.basic.execute_command('Y$(1) = "TEST"')
        self.assert_text_output('PRINT Y$(1)', 'TEST')
        
        self.basic.execute_command('Z(1,1) = 55')
        self.assert_text_output('PRINT Z(1,1)', '55')

    def test_array_bounds_checking(self):
        """Test array bounds error handling"""
        # Declare array with 10 elements (0-9)
        self.basic.execute_command('DIM A(10)')
        
        # Try to access out of bounds element
        self.assert_error_output('A(15) = 10', 'BAD SUBSCRIPT')
        self.assert_error_output('PRINT A(-1)', 'BAD SUBSCRIPT')
        self.assert_error_output('PRINT A(11)', 'BAD SUBSCRIPT')

    def test_undimensioned_array_error(self):
        """Test accessing undimensioned array produces error"""
        self.assert_error_output('PRINT D(5)', "UNDIM'D ARRAY")
        self.assert_error_output('D(0) = 5', "UNDIM'D ARRAY")

    def test_redimensioning_array_error(self):
        """Test that redimensioning an array produces an error"""
        # Dimension array first time
        self.basic.execute_command('DIM A(5)')
        
        # Try to dimension again - should fail
        self.assert_error_output('DIM A(10)', 'REDIM\'D ARRAY')

    def test_array_default_values(self):
        """Test that array elements have default values"""
        # Declare arrays
        self.basic.execute_command('DIM NUM(5)')
        self.basic.execute_command('DIM STR$(3)')
        
        # Check default values (should be 0 for numeric, empty string for string)
        self.assert_text_output('PRINT NUM(0)', '0')
        self.assert_text_output('PRINT STR$(0)', '')

    def test_array_in_expressions(self):
        """Test using array elements in expressions"""
        self.basic.execute_command('DIM A(5)')
        self.basic.execute_command('A(1) = 10')
        self.basic.execute_command('A(2) = 5')
        
        # Use in arithmetic
        self.assert_text_output('PRINT A(1) + A(2)', '15')
        self.assert_text_output('PRINT A(1) * 2', '20')

    def test_array_with_variables_as_indices(self):
        """Test using variables as array indices"""
        self.basic.execute_command('DIM A(10)')
        self.basic.execute_command('I = 3')
        self.basic.execute_command('A(I) = 42')
        
        self.assert_text_output('PRINT A(3)', '42')
        
        # Use expression as index
        self.basic.execute_command('J = 2')
        self.assert_text_output('PRINT A(I)', '42')  # I=3
        self.assert_text_output('PRINT A(J+1)', '42')  # J+1=3

    def test_string_array_operations(self):
        """Test string array specific operations"""
        self.basic.execute_command('DIM NAMES$(3)')
        self.basic.execute_command('NAMES$(0) = "ALICE"')
        self.basic.execute_command('NAMES$(1) = "BOB"')
        self.basic.execute_command('NAMES$(2) = "CHARLIE"')
        
        # Test string concatenation with array elements
        result = self.basic.execute_command('PRINT "HELLO " + NAMES$(0)')
        self.assertTrue(any('HELLO ALICE' in str(item) for item in result))

    def test_large_array_dimensions(self):
        """Test arrays with larger dimensions"""
        # Test larger 1D array
        result = self.basic.execute_command('DIM BIG(100)')
        self.assertFalse(any(item.get('type') == 'error' for item in result))
        
        # Test accessing elements
        self.basic.execute_command('BIG(99) = 123')
        self.assert_text_output('PRINT BIG(99)', '123')

    def test_dim_syntax_errors(self):
        """Test DIM command syntax error handling"""
        # Missing parentheses
        self.assert_error_output('DIM A 10', 'SYNTAX ERROR')
        
        # Missing array size
        self.assert_error_output('DIM A()', 'SYNTAX ERROR')
        
        # Invalid array size
        self.assert_error_output('DIM A(-5)', 'SYNTAX ERROR')
        self.assert_error_output('DIM A(0)', 'SYNTAX ERROR')

    def test_array_in_program(self):
        """Test array usage within a program"""
        program = [
            '10 DIM NUMS(5), NAMES$(3)',
            '20 FOR I = 0 TO 4',
            '30 NUMS(I) = I * 10',
            '40 NEXT I',
            '50 NAMES$(0) = "FIRST"',
            '60 NAMES$(1) = "SECOND"', 
            '70 NAMES$(2) = "THIRD"',
            '80 FOR I = 0 TO 4',
            '90 PRINT "NUMS("; I; ") = "; NUMS(I)',
            '100 NEXT I',
            '110 FOR I = 0 TO 2',
            '120 PRINT "NAMES$("; I; ") = "; NAMES$(I)',
            '130 NEXT I'
        ]
        
        results = self.execute_program(program)
        errors = self.get_error_messages(results)
        
        # Should run without errors
        self.assertEqual(len(errors), 0, f"Program should run without errors: {errors}")
        
        # Should have text outputs for array values
        text_outputs = self.get_text_output(results)
        self.assertTrue(len(text_outputs) > 0, "Program should produce output")


if __name__ == '__main__':
    test = DimCommandTest("DIM Command Tests")
    results = test.run_all_tests()
    from test_base import print_test_results
    print_test_results(results, verbose=True)