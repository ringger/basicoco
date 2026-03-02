#!/usr/bin/env python3

"""
Integration tests for cross-command interactions and edge cases.
Tests scenarios discovered during debugging of command interaction issues.
"""

import pytest


class TestCrossCommandInteraction:
    """Test cases for cross-command interactions and edge cases"""

    def test_basic_functionality(self, basic, helpers):
        """Test basic cross-command functionality"""
        basic.process_command('A = 5')
        result = basic.process_command('PRINT A')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 5 ']

    def test_inkey_with_program_vs_immediate_mode(self, basic, helpers):
        """Test INKEY$ behavior in program vs immediate mode"""
        # Test immediate mode
        basic.keyboard_buffer = ['X']
        result1 = basic.process_command('PRINT INKEY$')
        text1 = helpers.get_text_output(result1)
        assert 'X' in text1
        assert len(basic.keyboard_buffer) == 0
        
        # Test program mode (separate test since execute_program calls NEW which clears keyboard_buffer)
        program = ['10 PRINT INKEY$']
        helpers.load_program(basic, program)
        basic.keyboard_buffer = ['Y']  # Set key buffer after loading program
        results2 = basic.process_command('RUN')
        text2 = helpers.get_text_output(results2)
        assert 'Y' in ' '.join(text2)
        assert len(basic.keyboard_buffer) == 0

    def test_array_access_in_different_contexts(self, basic, helpers):
        """Test array access in various command contexts"""
        # Set up array in immediate mode
        basic.process_command('DIM A(5)')
        basic.process_command('A(3) = 42')
        
        # Direct access
        result = basic.process_command('PRINT A(3)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 42 ']

        # In expression
        result = basic.process_command('PRINT A(3) + 8')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 50 ']
        
        # In FOR loop - test with program that includes its own DIM
        program = [
            '5 DIM A(5)',  # Program needs its own DIM since NEW clears arrays
            '10 FOR I = 0 TO 3',
            '20 A(I) = I * 10',
            '30 NEXT I',
            '40 PRINT A(2)',
            '50 IF A(2) = 20 THEN PRINT "CORRECT"'  # Test IF statement within same program
        ]
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        assert '20' in ' '.join(text_outputs)
        assert 'CORRECT' in ' '.join(text_outputs)

    def test_string_functions_with_variables_and_arrays(self, basic, helpers):
        """Test string functions with mixed variable types"""
        # Set up string variables and arrays
        basic.process_command('A$ = "HELLO"')
        basic.process_command('DIM B$(3)')
        basic.process_command('B$(1) = "WORLD"')
        
        # String functions with variables
        result = basic.process_command('PRINT LEN(A$)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 5 ']
        result = basic.process_command("PRINT LEFT$(A$, 3)")
        text_output = helpers.get_text_output(result)
        assert text_output == ["HEL"]
        
        # String functions with array elements
        result = basic.process_command('PRINT LEN(B$(1))')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 5 ']
        result = basic.process_command('PRINT B$(1) + "!"')
        text_output = helpers.get_text_output(result)
        assert text_output == ['WORLD!']

    def test_math_functions_with_variable_expressions(self, basic, helpers):
        """Test math functions with complex variable expressions"""
        basic.process_command('A = 9')
        basic.process_command('B = 16')
        
        # Nested function calls
        result = basic.process_command('PRINT SQR(A) + SQR(B)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 7 ']

        # Functions in expressions
        result = basic.process_command('PRINT INT(SQR(A) * 2.5)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 7 ']

        # Functions with array elements
        basic.process_command('DIM C(5)')
        basic.process_command('C(2) = 25')
        result = basic.process_command('PRINT SQR(C(2))')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 5 ']

    def test_data_read_with_different_variable_types(self, basic, helpers):
        """Test DATA/READ with mixed numeric and string variables/arrays"""
        program = [
            '10 DIM A$(3), B(3)',
            '20 DATA "TEST", 42, "HELLO", 99',
            '30 READ A$(1), B(1), A$(2), B(2)',
            '40 PRINT A$(1); B(1); A$(2); B(2)'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        combined = ' '.join(text_outputs)
        assert 'TEST' in combined
        assert '42' in combined
        assert 'HELLO' in combined
        assert '99' in combined

    def test_for_loop_with_array_bounds_and_functions(self, basic, helpers):
        """Test FOR loop with array bounds checking and function calls"""
        program = [
            '10 DIM A(10)',
            '20 FOR I = 0 TO 5',
            '30 A(I) = I * I',
            '40 NEXT I',
            '50 FOR J = 0 TO 5',
            '60 PRINT SQR(A(J))',
            '70 NEXT J'
        ]
        
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        
        # Should execute without array bounds errors
        assert len(errors) == 0
        
        # Should print square roots (which should equal the original indices)
        text_outputs = helpers.get_text_output(results)
        combined = ' '.join(text_outputs)
        assert '0' in combined  # sqrt(0) = 0
        assert '1' in combined  # sqrt(1) = 1
        assert '2' in combined  # sqrt(4) = 2

    def test_input_with_array_elements(self, basic, helpers):
        """Test INPUT command with array elements"""
        # This would require input simulation, but test the parsing at least
        basic.process_command('DIM A$(3)')
        
        # Test that INPUT with array elements parses correctly
        # (This mainly tests that the parser handles array subscripts in INPUT)
        result = basic.process_command('INPUT "NAME"; A$(1)')
        
        # Should create input request, not error
        has_input_request = any(item.get('type') == 'input_request' for item in result)
        errors = [item for item in result if item.get('type') == 'error']
        
        assert has_input_request or len(errors) == 0

    def test_gosub_return_with_array_and_loop_interaction(self, basic, helpers):
        """Test GOSUB/RETURN with arrays and loops"""
        program = [
            '10 DIM A(5)',
            '20 FOR I = 1 TO 3',
            '30 GOSUB 100',
            '40 NEXT I',
            '50 PRINT "FINAL: "; A(3)',
            '60 END',
            '100 A(I) = I * 10',
            '110 RETURN'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        # Should complete without errors and show final value
        errors = helpers.get_error_messages(results)
        assert len(errors) == 0
        
        combined = ' '.join(text_outputs)
        assert 'FINAL:  30 ' in combined  # A(3) should be 3 * 10 = 30

    def test_error_recovery_across_commands(self, basic, helpers):
        """Test error recovery and state after command errors"""
        # Cause an error
        result1 = basic.process_command('PRINT A(5)')  # Undimensioned array
        errors1 = helpers.get_error_messages(result1)
        assert len(errors1) > 0
        
        # Subsequent commands should work normally
        basic.process_command('A = 42')
        helpers.assert_variable_equals(basic, 'A', 42)
        
        # Can now dimension the array and use it
        basic.process_command('DIM A(10)')
        basic.process_command('A(5) = 99')
        result = basic.process_command('PRINT A(5)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 99 ']

    def test_graphics_commands_with_variable_expressions(self, basic, helpers):
        """Test graphics commands with complex variable expressions"""
        # Set up variables
        basic.process_command('X = 50')
        basic.process_command('Y = 75')
        basic.process_command('R = 25')
        
        # Graphics commands should accept variable expressions
        result1 = basic.process_command('PMODE 1,1')
        result2 = basic.process_command('PSET(X, Y)')
        result3 = basic.process_command('CIRCLE(X, Y), R')
        
        # Should produce graphics output, not errors
        errors = []
        for result in [result1, result2, result3]:
            errors.extend(helpers.get_error_messages(result))
        
        assert len(errors) == 0
