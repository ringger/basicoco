#!/usr/bin/env python3

"""
Unit tests for DIM command - array declarations and operations.
Tests array creation, bounds checking, and multi-dimensional arrays.
"""

import pytest


class TestDimCommand:
    """Test cases for DIM command and array operations"""

    def test_basic_functionality(self, basic, helpers):
        """Test basic DIM command functionality"""
        # Test simple array declaration
        result = basic.process_command('DIM A(10)')
        assert len(result) == 0 or (len(result) == 1 and result[0].get('type') == 'text')

    def test_1d_numeric_array(self, basic, helpers):
        """Test 1D numeric array operations"""
        # Declare array
        basic.process_command('DIM A(10)')
        
        # Set and get array element
        basic.process_command('A(5) = 42')
        result = basic.process_command('PRINT A(5)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 42 ']

    def test_1d_string_array(self, basic, helpers):
        """Test 1D string array operations"""
        # Declare string array
        basic.process_command('DIM B$(5)')
        
        # Set and get string array element
        basic.process_command('B$(3) = "HELLO"')
        result = basic.process_command('PRINT B$(3)')
        text_output = helpers.get_text_output(result)
        assert text_output == ['HELLO']

    def test_2d_array(self, basic, helpers):
        """Test 2D array operations"""
        # Declare 2D array
        basic.process_command('DIM C(3,4)')
        
        # Set and get 2D array element
        basic.process_command('C(2,3) = 99')
        result = basic.process_command('PRINT C(2,3)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 99 ']

    def test_multiple_arrays_in_one_dim(self, basic, helpers):
        """Test declaring multiple arrays in one DIM statement"""
        result = basic.process_command('DIM X(5), Y$(3), Z(2,2)')
        
        # Should succeed without error
        assert not any(item.get('type') == 'error' for item in result)
        
        # Test that all arrays work
        basic.process_command('X(3) = 10')
        result = basic.process_command('PRINT X(3)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 10 ']
        
        basic.process_command('Y$(1) = "TEST"')
        result = basic.process_command('PRINT Y$(1)')
        text_output = helpers.get_text_output(result)
        assert text_output == ['TEST']
        
        basic.process_command('Z(1,1) = 55')
        result = basic.process_command('PRINT Z(1,1)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 55 ']

    def test_array_bounds_checking(self, basic, helpers):
        """Test array bounds error handling"""
        # Declare array with 10 elements (0-9)
        basic.process_command('DIM A(10)')
        
        # Try to access out of bounds element - expect enhanced error messages
        helpers.assert_error_output(basic, 'A(15) = 10', 'BAD SUBSCRIPT')
        helpers.assert_error_output(basic, 'PRINT A(-1)', 'Error evaluating PRINT expression')
        helpers.assert_error_output(basic, 'PRINT A(11)', 'Error evaluating PRINT expression')

    def test_undimensioned_array_error(self, basic, helpers):
        """Test accessing undimensioned array produces error"""
        helpers.assert_error_output(basic, 'PRINT D(5)', "Error evaluating PRINT expression")
        helpers.assert_error_output(basic, 'D(0) = 5', "UNDIM'D ARRAY")

    def test_redimensioning_array_error(self, basic, helpers):
        """Test that redimensioning an array produces an error"""
        # Dimension array first time
        basic.process_command('DIM A(5)')
        
        # Try to dimension again - should fail
        helpers.assert_error_output(basic, 'DIM A(10)', 'already dimensioned')

    def test_array_default_values(self, basic, helpers):
        """Test that array elements have default values"""
        # Declare arrays (avoid reserved function names like STR$)
        basic.process_command('DIM NUM(5)')
        basic.process_command('DIM STRINGS$(3)')
        
        # Check default values (should be 0 for numeric, empty string for string)
        result = basic.process_command('PRINT NUM(0)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 0 ']
        result = basic.process_command('PRINT STRINGS$(0)')
        text_output = helpers.get_text_output(result)
        assert text_output == ['']

    def test_array_in_expressions(self, basic, helpers):
        """Test using array elements in expressions"""
        basic.process_command('DIM A(5)')
        basic.process_command('A(1) = 10')
        basic.process_command('A(2) = 5')
        
        # Use in arithmetic
        result = basic.process_command('PRINT A(1) + A(2)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 15 ']
        result = basic.process_command('PRINT A(1) * 2')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 20 ']

    def test_array_with_variables_as_indices(self, basic, helpers):
        """Test using variables as array indices"""
        basic.process_command('DIM A(10)')
        basic.process_command('I = 3')
        basic.process_command('A(I) = 42')
        
        result = basic.process_command('PRINT A(3)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 42 ']

        # Use expression as index
        basic.process_command('J = 2')
        result = basic.process_command('PRINT A(I)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 42 ']  # I=3
        result = basic.process_command('PRINT A(J+1)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 42 ']  # J+1=3

    def test_string_array_operations(self, basic, helpers):
        """Test string array specific operations"""
        basic.process_command('DIM NAMES$(3)')
        basic.process_command('NAMES$(0) = "ALICE"')
        basic.process_command('NAMES$(1) = "BOB"')
        basic.process_command('NAMES$(2) = "CHARLIE"')
        
        # Test string concatenation with array elements
        result = basic.process_command('PRINT "HELLO " + NAMES$(0)')
        text_output = helpers.get_text_output(result)
        assert any('HELLO ALICE' in output for output in text_output)

    def test_large_array_dimensions(self, basic, helpers):
        """Test arrays with larger dimensions"""
        # Test larger 1D array
        result = basic.process_command('DIM BIG(100)')
        assert not any(item.get('type') == 'error' for item in result)
        
        # Test accessing elements
        basic.process_command('BIG(99) = 123')
        result = basic.process_command('PRINT BIG(99)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 123 ']

    def test_dim_syntax_errors(self, basic, helpers):
        """Test DIM command syntax error handling"""
        # Missing parentheses
        helpers.assert_error_output(basic, 'DIM A 10', 'Invalid array declaration')
        
        # Missing array size
        helpers.assert_error_output(basic, 'DIM A()', 'Invalid array declaration')
        
        # Invalid array size
        helpers.assert_error_output(basic, 'DIM A(-5)', 'Array dimension must be positive')
        helpers.assert_error_output(basic, 'DIM A(0)', 'Array dimension must be positive')

    def test_reserved_function_name_conflicts(self, basic, helpers):
        """Test that arrays cannot use reserved function names"""
        # Test numeric functions
        helpers.assert_error_output(basic, 'DIM LEN(5)', 'reserved function name')
        helpers.assert_error_output(basic, 'DIM ABS(3)', 'reserved function name')
        helpers.assert_error_output(basic, 'DIM INT(10)', 'reserved function name')
        helpers.assert_error_output(basic, 'DIM RND(2)', 'reserved function name')
        helpers.assert_error_output(basic, 'DIM SQR(4)', 'reserved function name')
        helpers.assert_error_output(basic, 'DIM SIN(5)', 'reserved function name')
        helpers.assert_error_output(basic, 'DIM COS(5)', 'reserved function name')
        helpers.assert_error_output(basic, 'DIM TAN(5)', 'reserved function name')
        helpers.assert_error_output(basic, 'DIM ATN(5)', 'reserved function name')
        helpers.assert_error_output(basic, 'DIM EXP(5)', 'reserved function name')
        helpers.assert_error_output(basic, 'DIM LOG(5)', 'reserved function name')
        helpers.assert_error_output(basic, 'DIM VAL(5)', 'reserved function name')
        
        # Test string functions
        helpers.assert_error_output(basic, 'DIM LEFT$(5)', 'reserved function name')
        helpers.assert_error_output(basic, 'DIM RIGHT$(5)', 'reserved function name')
        helpers.assert_error_output(basic, 'DIM MID$(5)', 'reserved function name')
        helpers.assert_error_output(basic, 'DIM CHR$(5)', 'reserved function name')
        helpers.assert_error_output(basic, 'DIM ASC(5)', 'reserved function name')  # ASC doesn't end with $
        helpers.assert_error_output(basic, 'DIM STR$(5)', 'reserved function name')
        helpers.assert_error_output(basic, 'DIM INKEY$(5)', 'reserved function name')
        
        # Test that similar but non-reserved names still work
        basic.process_command('DIM LENS(5)')  # Not LEN
        assert 'LENS' in basic.arrays
        
        basic.process_command('DIM STRINGS$(3)')  # Not STR$
        assert 'STRINGS$' in basic.arrays
        
        # Test that the functions still work normally
        result = basic.process_command('PRINT LEN("TEST")')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 4 ']
        result = basic.process_command('PRINT STR$(123)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 123']  # STR$ adds leading space for positive numbers
        
        # Test that our arrays work
        basic.process_command('LENS(0) = 42')
        result = basic.process_command('PRINT LENS(0)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 42 ']

        basic.process_command('STRINGS$(0) = "HELLO"')
        result = basic.process_command('PRINT STRINGS$(0)')
        text_output = helpers.get_text_output(result)
        assert text_output == ['HELLO']

    def test_array_in_program(self, basic, helpers):
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
        
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)

        # Should run without errors
        assert len(errors) == 0, f"Program should run without errors: {errors}"

        # Should have text outputs for array values
        text_outputs = helpers.get_text_output(results)
        assert len(text_outputs) > 0, "Program should produce output"

    def test_authentic_array_dimensioning(self, basic, helpers):
        """Test that DIM A(N) creates N+1 elements with indices 0 to N"""
        test_cases = [(1, 2), (5, 6), (10, 11)]  # (declared_size, expected_elements)
        
        for declared_size, expected_elements in test_cases:
            basic.process_command('NEW')
            basic.process_command(f'DIM A({declared_size})')
            
            # Should have expected number of elements
            assert len(basic.arrays['A']) == expected_elements, \
                           f"DIM A({declared_size}) should create {expected_elements} elements"
            
            # Valid boundary accesses should work
            basic.process_command(f'A(0) = 100')
            basic.process_command(f'A({declared_size}) = 200')
            
            # Check the values were set correctly
            assert basic.arrays['A'][0] == 100
            assert basic.arrays['A'][declared_size] == 200
            
            # Out of bounds should fail
            helpers.assert_error_output(basic, f'A({declared_size + 1}) = 999', 'BAD SUBSCRIPT')
            helpers.assert_error_output(basic, f'A(-1) = 999', 'BAD SUBSCRIPT')

    def test_array_bounds_violation_halts_execution(self, basic, helpers):
        """Test that array bounds errors stop program execution"""
        program = [
            '10 DIM A(3)',  # Creates indices 0-3
            '20 A(0) = 10',
            '30 A(3) = 30', 
            '40 A(4) = 40',  # Should trigger BAD SUBSCRIPT
            '50 PRINT "SHOULD NOT REACH HERE"'
        ]
        
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        text_outputs = helpers.get_text_output(results)

        # Should have BAD SUBSCRIPT error
        assert any('BAD SUBSCRIPT' in error for error in errors), \
                       f"Expected BAD SUBSCRIPT error, got: {errors}"

        # Should NOT reach line 50
        assert not any('SHOULD NOT REACH HERE' in output for output in text_outputs), \
                        "Program should halt at BAD SUBSCRIPT error"

        # Program should stop at line 40
        assert basic.current_line == 40, \
                        f"Expected program to stop at line 40, stopped at {basic.current_line}"
        
        # Array should retain valid values
        assert basic.arrays['A'][0] == 10
        assert basic.arrays['A'][3] == 30

    def test_multidimensional_array_bounds(self, basic, helpers):
        """Test bounds checking for multi-dimensional arrays"""
        # Test 2D array
        basic.process_command('DIM B(2, 3)')  # Should be 3x4 matrix (indices 0-2, 0-3)
        
        # Check actual dimensions
        assert len(basic.arrays['B']) == 3, "First dimension should be 3 elements"
        assert len(basic.arrays['B'][0]) == 4, "Second dimension should be 4 elements"
        
        # Valid corner cases
        valid_cases = [(0, 0), (2, 3), (1, 1)]
        for i, j in valid_cases:
            result = basic.process_command(f'B({i}, {j}) = {i * 10 + j}')
            assert len([r for r in result if r.get('type') == 'error']) == 0, \
                           f"B({i}, {j}) should be valid access"
            assert basic.arrays['B'][i][j] == i * 10 + j
        
        # Invalid cases should all fail
        invalid_cases = [(3, 0), (0, 4), (-1, 0), (0, -1), (3, 4)]
        for i, j in invalid_cases:
            helpers.assert_error_output(basic, f'B({i}, {j}) = 999', 'BAD SUBSCRIPT')
        
        # Test 3D array
        basic.process_command('NEW')
        basic.process_command('DIM C(1, 2, 1)')  # Should be 2x3x2 (indices 0-1, 0-2, 0-1)
        
        # Valid 3D access
        basic.process_command('C(0, 1, 0) = 123')
        assert basic.arrays['C'][0][1][0] == 123
        
        # Invalid 3D access
        helpers.assert_error_output(basic, 'C(2, 0, 0) = 999', 'BAD SUBSCRIPT')
        helpers.assert_error_output(basic, 'C(0, 3, 0) = 999', 'BAD SUBSCRIPT')
        helpers.assert_error_output(basic, 'C(0, 0, 2) = 999', 'BAD SUBSCRIPT')

    def test_string_array_bounds(self, basic, helpers):
        """Test bounds checking for string arrays"""
        basic.process_command('DIM S$(1, 2)')  # Should create 2x3 string matrix
        
        # Check dimensions
        assert len(basic.arrays['S$']) == 2
        assert len(basic.arrays['S$'][0]) == 3
        
        # Valid accesses
        result1 = basic.process_command('S$(0, 0) = "HELLO"')
        result2 = basic.process_command('S$(1, 2) = "WORLD"')
        
        assert len([r for r in result1 if r.get('type') == 'error']) == 0
        assert len([r for r in result2 if r.get('type') == 'error']) == 0
        assert basic.arrays['S$'][0][0] == "HELLO"
        assert basic.arrays['S$'][1][2] == "WORLD"
        
        # Invalid access
        helpers.assert_error_output(basic, 'S$(2, 0) = "ERROR"', 'BAD SUBSCRIPT')

    def test_redimed_array_halts_execution(self, basic, helpers):
        """Test that array redimensioning error stops program execution"""
        program = [
            '10 DIM A(5)',
            '20 A(0) = 100',
            '30 DIM A(10)',  # Should trigger redimensioning error
            '40 PRINT "SHOULD NOT REACH HERE"'
        ]
        
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        text_outputs = helpers.get_text_output(results)

        # Should have redimensioning error
        assert any("already dimensioned" in error for error in errors), \
                       f"Expected redimensioning error, got: {errors}"
        
        # Should NOT reach line 40
        assert not any('SHOULD NOT REACH HERE' in output for output in text_outputs), \
                        "Program should halt at redimensioning error"

        # Array should retain original size and values
        assert len(basic.arrays['A']) == 6, "Original DIM A(5) should create 6 elements"
        assert basic.arrays['A'][0] == 100, "Original array values should be preserved"

        # Program should stop at line 30
        assert basic.current_line == 30, \
                        f"Expected program to stop at line 30, stopped at {basic.current_line}"

    def test_array_bounds_in_loops(self, basic, helpers):
        """Test array bounds checking within FOR loops"""
        program = [
            '10 DIM A(3)',  # indices 0-3
            '20 FOR I = 0 TO 5',  # Loop goes beyond array bounds
            '30 A(I) = I * 10',  # Should fail at I=4
            '40 NEXT I',
            '50 PRINT "COMPLETED"'
        ]
        
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        text_outputs = helpers.get_text_output(results)
        
        # Should get BAD SUBSCRIPT error
        assert any('BAD SUBSCRIPT' in error for error in errors)
        
        # Should not complete the loop
        assert not any('COMPLETED' in output for output in text_outputs)
        
        # Should have set valid array elements before error
        assert basic.arrays['A'][0] == 0
        assert basic.arrays['A'][1] == 10
        assert basic.arrays['A'][2] == 20
        assert basic.arrays['A'][3] == 30

    def test_undimensioned_array_error(self, basic, helpers):
        """Test that undimensioned arrays produce UNDIM'D ARRAY error"""
        # Use array without declaring it should produce error
        helpers.assert_error_output(basic, 'B(5) = 42', "UNDIM'D ARRAY")
        helpers.assert_error_output(basic, 'PRINT B(10)', "Error evaluating PRINT expression")
        
        # Array should not be created
        assert 'B' not in basic.arrays
        
        # After explicit DIM, should work
        basic.process_command('DIM B(10)')
        basic.process_command('B(5) = 42')
        basic.process_command('B(10) = 100')
        
        # Now array should exist and work
        assert basic.arrays['B'][5] == 42
        assert basic.arrays['B'][10] == 100
        
        # But out of bounds should still fail
        helpers.assert_error_output(basic, 'B(11) = 999', 'BAD SUBSCRIPT')
