#!/usr/bin/env python3

"""
Integration tests for cross-command interactions and edge cases.
Tests scenarios discovered during debugging of command interaction issues.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from test_base import BaseTestCase


class CrossCommandInteractionTest(BaseTestCase):
    """Test cases for cross-command interactions and edge cases"""

    def test_basic_functionality(self):
        """Test basic cross-command functionality"""
        self.basic.execute_command('A = 5')
        self.assert_text_output('PRINT A', '5')

    def test_inkey_with_program_vs_immediate_mode(self):
        """Test INKEY$ behavior in program vs immediate mode"""
        # Test immediate mode
        self.basic.key_buffer = ['X']
        result1 = self.basic.execute_command('PRINT INKEY$')
        text1 = self.get_text_output(result1)
        self.assertIn('X', text1)
        self.assertEqual(len(self.basic.key_buffer), 0)
        
        # Test program mode (separate test since execute_program calls NEW which clears key_buffer)
        program = ['10 PRINT INKEY$']
        self.load_program(program)
        self.basic.key_buffer = ['Y']  # Set key buffer after loading program
        results2 = self.basic.execute_command('RUN')
        text2 = self.get_text_output(results2)
        self.assertIn('Y', ' '.join(text2))
        self.assertEqual(len(self.basic.key_buffer), 0)

    def test_array_access_in_different_contexts(self):
        """Test array access in various command contexts"""
        # Set up array in immediate mode
        self.basic.execute_command('DIM A(5)')
        self.basic.execute_command('A(3) = 42')
        
        # Direct access
        self.assert_text_output('PRINT A(3)', '42')
        
        # In expression
        self.assert_text_output('PRINT A(3) + 8', '50')
        
        # In FOR loop - test with program that includes its own DIM
        program = [
            '5 DIM A(5)',  # Program needs its own DIM since NEW clears arrays
            '10 FOR I = 0 TO 3',
            '20 A(I) = I * 10',
            '30 NEXT I',
            '40 PRINT A(2)',
            '50 IF A(2) = 20 THEN PRINT "CORRECT"'  # Test IF statement within same program
        ]
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        self.assertIn('20', ' '.join(text_outputs))
        self.assertIn('CORRECT', ' '.join(text_outputs))

    def test_string_functions_with_variables_and_arrays(self):
        """Test string functions with mixed variable types"""
        # Set up string variables and arrays
        self.basic.execute_command('A$ = "HELLO"')
        self.basic.execute_command('DIM B$(3)')
        self.basic.execute_command('B$(1) = "WORLD"')
        
        # String functions with variables
        self.assert_text_output('PRINT LEN(A$)', '5')
        self.assert_text_output('PRINT LEFT$(A$, 3)', 'HEL')
        
        # String functions with array elements
        self.assert_text_output('PRINT LEN(B$(1))', '5')
        self.assert_text_output('PRINT B$(1) + "!"', 'WORLD!')

    def test_math_functions_with_variable_expressions(self):
        """Test math functions with complex variable expressions"""
        self.basic.execute_command('A = 9')
        self.basic.execute_command('B = 16')
        
        # Nested function calls
        self.assert_text_output('PRINT SQR(A) + SQR(B)', '7')
        
        # Functions in expressions
        self.assert_text_output('PRINT INT(SQR(A) * 2.5)', '7')
        
        # Functions with array elements
        self.basic.execute_command('DIM C(5)')
        self.basic.execute_command('C(2) = 25')
        self.assert_text_output('PRINT SQR(C(2))', '5')

    def test_data_read_with_different_variable_types(self):
        """Test DATA/READ with mixed numeric and string variables/arrays"""
        program = [
            '10 DIM A$(3), B(3)',
            '20 DATA "TEST", 42, "HELLO", 99',
            '30 READ A$(1), B(1), A$(2), B(2)',
            '40 PRINT A$(1); B(1); A$(2); B(2)'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        combined = ' '.join(text_outputs)
        self.assertIn('TEST', combined)
        self.assertIn('42', combined)
        self.assertIn('HELLO', combined)
        self.assertIn('99', combined)

    def test_for_loop_with_array_bounds_and_functions(self):
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
        
        results = self.execute_program(program)
        errors = self.get_error_messages(results)
        
        # Should execute without array bounds errors
        self.assertEqual(len(errors), 0)
        
        # Should print square roots (which should equal the original indices)
        text_outputs = self.get_text_output(results)
        combined = ' '.join(text_outputs)
        self.assertIn('0', combined)  # sqrt(0) = 0
        self.assertIn('1', combined)  # sqrt(1) = 1
        self.assertIn('2', combined)  # sqrt(4) = 2

    def test_input_with_array_elements(self):
        """Test INPUT command with array elements"""
        # This would require input simulation, but test the parsing at least
        self.basic.execute_command('DIM A$(3)')
        
        # Test that INPUT with array elements parses correctly
        # (This mainly tests that the parser handles array subscripts in INPUT)
        result = self.basic.execute_command('INPUT "NAME"; A$(1)')
        
        # Should create input request, not error
        has_input_request = any(item.get('type') == 'input_request' for item in result)
        errors = [item for item in result if item.get('type') == 'error']
        
        self.assertTrue(has_input_request or len(errors) == 0)

    def test_gosub_return_with_array_and_loop_interaction(self):
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
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Should complete without errors and show final value
        errors = self.get_error_messages(results)
        self.assertEqual(len(errors), 0)
        
        combined = ' '.join(text_outputs)
        self.assertIn('FINAL: 30', combined)  # A(3) should be 3 * 10 = 30

    def test_error_recovery_across_commands(self):
        """Test error recovery and state after command errors"""
        # Cause an error
        result1 = self.basic.execute_command('PRINT A(5)')  # Undimensioned array
        errors1 = self.get_error_messages(result1)
        self.assertTrue(len(errors1) > 0)
        
        # Subsequent commands should work normally
        self.basic.execute_command('A = 42')
        self.assert_variable_equals('A', 42)
        
        # Can now dimension the array and use it
        self.basic.execute_command('DIM A(10)')
        self.basic.execute_command('A(5) = 99')
        self.assert_text_output('PRINT A(5)', '99')

    def test_graphics_commands_with_variable_expressions(self):
        """Test graphics commands with complex variable expressions"""
        # Set up variables
        self.basic.execute_command('X = 50')
        self.basic.execute_command('Y = 75')
        self.basic.execute_command('R = 25')
        
        # Graphics commands should accept variable expressions
        result1 = self.basic.execute_command('PMODE 1,1')
        result2 = self.basic.execute_command('PSET(X, Y)')
        result3 = self.basic.execute_command('CIRCLE(X, Y), R')
        
        # Should produce graphics output, not errors
        errors = []
        for result in [result1, result2, result3]:
            errors.extend(self.get_error_messages(result))
        
        self.assertEqual(len(errors), 0)


if __name__ == '__main__':
    test = CrossCommandInteractionTest("Cross-Command Interaction Tests")
    results = test.run_all_tests()
    from test_base import print_test_results
    print_test_results(results, verbose=True)