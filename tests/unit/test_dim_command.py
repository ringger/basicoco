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
        # Declare arrays (avoid reserved function names like STR$)
        self.basic.execute_command('DIM NUM(5)')
        self.basic.execute_command('DIM STRINGS$(3)')
        
        # Check default values (should be 0 for numeric, empty string for string)
        self.assert_text_output('PRINT NUM(0)', '0')
        self.assert_text_output('PRINT STRINGS$(0)', '')

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

    def test_reserved_function_name_conflicts(self):
        """Test that arrays cannot use reserved function names"""
        # Test numeric functions
        self.assert_error_output('DIM LEN(5)', 'SYNTAX ERROR')
        self.assert_error_output('DIM ABS(3)', 'SYNTAX ERROR')
        self.assert_error_output('DIM INT(10)', 'SYNTAX ERROR')
        self.assert_error_output('DIM RND(2)', 'SYNTAX ERROR')
        self.assert_error_output('DIM SQR(4)', 'SYNTAX ERROR')
        self.assert_error_output('DIM SIN(5)', 'SYNTAX ERROR')
        self.assert_error_output('DIM COS(5)', 'SYNTAX ERROR')
        self.assert_error_output('DIM TAN(5)', 'SYNTAX ERROR')
        self.assert_error_output('DIM ATN(5)', 'SYNTAX ERROR')
        self.assert_error_output('DIM EXP(5)', 'SYNTAX ERROR')
        self.assert_error_output('DIM LOG(5)', 'SYNTAX ERROR')
        self.assert_error_output('DIM VAL(5)', 'SYNTAX ERROR')
        
        # Test string functions
        self.assert_error_output('DIM LEFT$(5)', 'SYNTAX ERROR')
        self.assert_error_output('DIM RIGHT$(5)', 'SYNTAX ERROR')
        self.assert_error_output('DIM MID$(5)', 'SYNTAX ERROR')
        self.assert_error_output('DIM CHR$(5)', 'SYNTAX ERROR')
        self.assert_error_output('DIM ASC(5)', 'SYNTAX ERROR')  # ASC doesn't end with $
        self.assert_error_output('DIM STR$(5)', 'SYNTAX ERROR')
        self.assert_error_output('DIM INKEY$(5)', 'SYNTAX ERROR')
        
        # Test that similar but non-reserved names still work
        self.basic.execute_command('DIM LENS(5)')  # Not LEN
        self.assertTrue('LENS' in self.basic.arrays)
        
        self.basic.execute_command('DIM STRINGS$(3)')  # Not STR$
        self.assertTrue('STRINGS$' in self.basic.arrays)
        
        # Test that the functions still work normally
        self.assert_text_output('PRINT LEN("TEST")', '4')
        self.assert_text_output('PRINT STR$(123)', ' 123')  # STR$ adds leading space for positive numbers
        
        # Test that our arrays work
        self.basic.execute_command('LENS(0) = 42')
        self.assert_text_output('PRINT LENS(0)', '42')
        
        self.basic.execute_command('STRINGS$(0) = "HELLO"')
        self.assert_text_output('PRINT STRINGS$(0)', 'HELLO')

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

    def test_authentic_array_dimensioning(self):
        """Test that DIM A(N) creates N+1 elements with indices 0 to N"""
        test_cases = [(1, 2), (5, 6), (10, 11)]  # (declared_size, expected_elements)
        
        for declared_size, expected_elements in test_cases:
            self.basic.execute_command('NEW')
            self.basic.execute_command(f'DIM A({declared_size})')
            
            # Should have expected number of elements
            self.assertEqual(len(self.basic.arrays['A']), expected_elements,
                           f"DIM A({declared_size}) should create {expected_elements} elements")
            
            # Valid boundary accesses should work
            self.basic.execute_command(f'A(0) = 100')
            self.basic.execute_command(f'A({declared_size}) = 200')
            
            # Check the values were set correctly
            self.assertEqual(self.basic.arrays['A'][0], 100)
            self.assertEqual(self.basic.arrays['A'][declared_size], 200)
            
            # Out of bounds should fail
            self.assert_error_output(f'A({declared_size + 1}) = 999', 'BAD SUBSCRIPT')
            self.assert_error_output(f'A(-1) = 999', 'BAD SUBSCRIPT')

    def test_array_bounds_violation_halts_execution(self):
        """Test that array bounds errors stop program execution"""
        program = [
            '10 DIM A(3)',  # Creates indices 0-3
            '20 A(0) = 10',
            '30 A(3) = 30', 
            '40 A(4) = 40',  # Should trigger BAD SUBSCRIPT
            '50 PRINT "SHOULD NOT REACH HERE"'
        ]
        
        results = self.execute_program(program)
        errors = self.get_error_messages(results)
        text_outputs = self.get_text_output(results)
        
        # Should have BAD SUBSCRIPT error
        self.assertTrue(any('BAD SUBSCRIPT' in error for error in errors),
                       f"Expected BAD SUBSCRIPT error, got: {errors}")
        
        # Should NOT reach line 50
        self.assertFalse(any('SHOULD NOT REACH HERE' in output for output in text_outputs),
                        "Program should halt at BAD SUBSCRIPT error")
        
        # Program should stop at line 40
        self.assertEqual(self.basic.current_line, 40,
                        f"Expected program to stop at line 40, stopped at {self.basic.current_line}")
        
        # Array should retain valid values
        self.assertEqual(self.basic.arrays['A'][0], 10)
        self.assertEqual(self.basic.arrays['A'][3], 30)

    def test_multidimensional_array_bounds(self):
        """Test bounds checking for multi-dimensional arrays"""
        # Test 2D array
        self.basic.execute_command('DIM B(2, 3)')  # Should be 3x4 matrix (indices 0-2, 0-3)
        
        # Check actual dimensions
        self.assertEqual(len(self.basic.arrays['B']), 3, "First dimension should be 3 elements")
        self.assertEqual(len(self.basic.arrays['B'][0]), 4, "Second dimension should be 4 elements")
        
        # Valid corner cases
        valid_cases = [(0, 0), (2, 3), (1, 1)]
        for i, j in valid_cases:
            result = self.basic.execute_command(f'B({i}, {j}) = {i * 10 + j}')
            self.assertEqual(len([r for r in result if r.get('type') == 'error']), 0,
                           f"B({i}, {j}) should be valid access")
            self.assertEqual(self.basic.arrays['B'][i][j], i * 10 + j)
        
        # Invalid cases should all fail
        invalid_cases = [(3, 0), (0, 4), (-1, 0), (0, -1), (3, 4)]
        for i, j in invalid_cases:
            self.assert_error_output(f'B({i}, {j}) = 999', 'BAD SUBSCRIPT')
        
        # Test 3D array
        self.basic.execute_command('NEW')
        self.basic.execute_command('DIM C(1, 2, 1)')  # Should be 2x3x2 (indices 0-1, 0-2, 0-1)
        
        # Valid 3D access
        self.basic.execute_command('C(0, 1, 0) = 123')
        self.assertEqual(self.basic.arrays['C'][0][1][0], 123)
        
        # Invalid 3D access
        self.assert_error_output('C(2, 0, 0) = 999', 'BAD SUBSCRIPT')
        self.assert_error_output('C(0, 3, 0) = 999', 'BAD SUBSCRIPT')
        self.assert_error_output('C(0, 0, 2) = 999', 'BAD SUBSCRIPT')

    def test_string_array_bounds(self):
        """Test bounds checking for string arrays"""
        self.basic.execute_command('DIM S$(1, 2)')  # Should create 2x3 string matrix
        
        # Check dimensions
        self.assertEqual(len(self.basic.arrays['S$']), 2)
        self.assertEqual(len(self.basic.arrays['S$'][0]), 3)
        
        # Valid accesses
        result1 = self.basic.execute_command('S$(0, 0) = "HELLO"')
        result2 = self.basic.execute_command('S$(1, 2) = "WORLD"')
        
        self.assertEqual(len([r for r in result1 if r.get('type') == 'error']), 0)
        self.assertEqual(len([r for r in result2 if r.get('type') == 'error']), 0)
        self.assertEqual(self.basic.arrays['S$'][0][0], "HELLO")
        self.assertEqual(self.basic.arrays['S$'][1][2], "WORLD")
        
        # Invalid access
        self.assert_error_output('S$(2, 0) = "ERROR"', 'BAD SUBSCRIPT')

    def test_redimed_array_halts_execution(self):
        """Test that REDIM'D ARRAY error stops program execution"""
        program = [
            '10 DIM A(5)',
            '20 A(0) = 100',
            '30 DIM A(10)',  # Should trigger REDIM'D ARRAY
            '40 PRINT "SHOULD NOT REACH HERE"'
        ]
        
        results = self.execute_program(program)
        errors = self.get_error_messages(results)
        text_outputs = self.get_text_output(results)
        
        # Should have REDIM'D ARRAY error
        self.assertTrue(any("REDIM'D ARRAY" in error for error in errors),
                       f"Expected REDIM'D ARRAY error, got: {errors}")
        
        # Should NOT reach line 40
        self.assertFalse(any('SHOULD NOT REACH HERE' in output for output in text_outputs),
                        "Program should halt at REDIM'D ARRAY error")
        
        # Array should retain original size and values
        self.assertEqual(len(self.basic.arrays['A']), 6, "Original DIM A(5) should create 6 elements")
        self.assertEqual(self.basic.arrays['A'][0], 100, "Original array values should be preserved")
        
        # Program should stop at line 30
        self.assertEqual(self.basic.current_line, 30,
                        f"Expected program to stop at line 30, stopped at {self.basic.current_line}")

    def test_array_bounds_in_loops(self):
        """Test array bounds checking within FOR loops"""
        program = [
            '10 DIM A(3)',  # indices 0-3
            '20 FOR I = 0 TO 5',  # Loop goes beyond array bounds
            '30 A(I) = I * 10',  # Should fail at I=4
            '40 NEXT I',
            '50 PRINT "COMPLETED"'
        ]
        
        results = self.execute_program(program)
        errors = self.get_error_messages(results)
        text_outputs = self.get_text_output(results)
        
        # Should get BAD SUBSCRIPT error
        self.assertTrue(any('BAD SUBSCRIPT' in error for error in errors))
        
        # Should not complete the loop
        self.assertFalse(any('COMPLETED' in output for output in text_outputs))
        
        # Should have set valid array elements before error
        self.assertEqual(self.basic.arrays['A'][0], 0)
        self.assertEqual(self.basic.arrays['A'][1], 10)
        self.assertEqual(self.basic.arrays['A'][2], 20)
        self.assertEqual(self.basic.arrays['A'][3], 30)

    def test_undimensioned_array_error(self):
        """Test that undimensioned arrays produce UNDIM'D ARRAY error"""
        # Use array without declaring it should produce error
        self.assert_error_output('B(5) = 42', "UNDIM'D ARRAY")
        self.assert_error_output('PRINT B(10)', "UNDIM'D ARRAY")
        
        # Array should not be created
        self.assertNotIn('B', self.basic.arrays)
        
        # After explicit DIM, should work
        self.basic.execute_command('DIM B(10)')
        self.basic.execute_command('B(5) = 42')
        self.basic.execute_command('B(10) = 100')
        
        # Now array should exist and work
        self.assertEqual(self.basic.arrays['B'][5], 42)
        self.assertEqual(self.basic.arrays['B'][10], 100)
        
        # But out of bounds should still fail
        self.assert_error_output('B(11) = 999', 'BAD SUBSCRIPT')


if __name__ == '__main__':
    test = DimCommandTest("DIM Command Tests")
    results = test.run_all_tests()
    from test_base import print_test_results
    print_test_results(results, verbose=True)