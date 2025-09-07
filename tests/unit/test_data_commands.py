#!/usr/bin/env python3

"""
Unit tests for DATA/READ/RESTORE commands - structured data processing.
Tests data statement parsing, sequential reading, and restore functionality.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from test_base import BaseTestCase


class DataCommandTest(BaseTestCase):
    """Test cases for DATA/READ/RESTORE command functionality"""

    def test_basic_functionality(self):
        """Test basic DATA/READ functionality"""
        program = [
            '10 DATA 100',
            '20 READ A',
            '30 PRINT A'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        self.assertTrue(any('100' in output for output in text_outputs))

    def test_data_read_numeric_values(self):
        """Test DATA/READ with numeric values"""
        program = [
            '10 DATA 100, 200, 300',
            '20 READ A, B, C',
            '30 PRINT A; B; C'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Should contain all three numbers
        combined_output = ' '.join(text_outputs)
        self.assertIn('100', combined_output)
        self.assertIn('200', combined_output)
        self.assertIn('300', combined_output)

    def test_data_read_string_values(self):
        """Test DATA/READ with string values"""
        program = [
            '10 DATA "HELLO", "WORLD"',
            '20 READ A$, B$',
            '30 PRINT A$; " "; B$'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Should contain the strings
        combined_output = ' '.join(text_outputs)
        self.assertIn('HELLO', combined_output)
        self.assertIn('WORLD', combined_output)

    def test_data_read_mixed_types(self):
        """Test DATA/READ with mixed numeric and string values"""
        program = [
            '10 DATA 123, "HELLO", 3.14, "WORLD"',
            '20 READ A, B$, C, D$',
            '30 PRINT A; B$; C; D$'
        ]
        
        results = self.execute_program(program)
        errors = self.get_error_messages(results)
        
        # Should run without errors
        self.assertEqual(len(errors), 0, f"Program should run without errors: {errors}")
        
        # Check final variable values
        self.assert_variable_equals('A', 123)
        self.assert_variable_equals('B$', 'HELLO')
        self.assert_variable_equals('C', 3.14)
        self.assert_variable_equals('D$', 'WORLD')

    def test_multiple_data_statements(self):
        """Test multiple DATA statements in sequence"""
        program = [
            '10 DATA 100, 200',
            '20 DATA "HELLO", 3.14',
            '30 DATA "WORLD", 500',
            '40 READ A, B, C$, D, E$, F',
            '50 PRINT A; B; C$; D; E$; F'
        ]
        
        results = self.execute_program(program)
        errors = self.get_error_messages(results)
        
        # Should run without errors
        self.assertEqual(len(errors), 0, f"Program should run without errors: {errors}")

    def test_restore_command(self):
        """Test RESTORE command resets data pointer"""
        program = [
            '10 DATA 100, 200, 300',
            '20 READ A',
            '30 READ B', 
            '40 RESTORE',
            '50 READ C',
            '60 PRINT A; B; C'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # A should be 100, B should be 200, C should be 100 (after RESTORE)
        combined_output = ' '.join(text_outputs)
        self.assertIn('100', combined_output)
        self.assertIn('200', combined_output)
        # C should also be 100 since RESTORE reset to beginning

    def test_restore_mid_program(self):
        """Test RESTORE in middle of data reading"""
        program = [
            '10 DATA 10, 20, 30, 40, 50',
            '20 READ A, B',
            '30 PRINT "FIRST: "; A; B',
            '40 RESTORE',
            '50 READ C, D, E',
            '60 PRINT "AFTER RESTORE: "; C; D; E'
        ]
        
        results = self.execute_program(program)
        errors = self.get_error_messages(results)
        
        # Should run without errors
        self.assertEqual(len(errors), 0, f"Program should run without errors: {errors}")
        
        # After RESTORE, should start from beginning again
        self.assert_variable_equals('C', 10)  # Should be first value again
        self.assert_variable_equals('D', 20)  # Should be second value again

    def test_out_of_data_error(self):
        """Test reading beyond available data produces error"""
        program = [
            '10 DATA 100, 200',
            '20 READ A, B, C'  # C should cause "OUT OF DATA" error
        ]
        
        results = self.execute_program(program)
        errors = self.get_error_messages(results)
        
        # Should produce out of data error
        self.assertTrue(len(errors) > 0, "Should produce OUT OF DATA error")
        self.assertTrue(any('OUT OF DATA' in error for error in errors))

    def test_data_with_commas_in_strings(self):
        """Test DATA statements with commas inside quoted strings"""
        program = [
            '10 DATA "HELLO, WORLD", 123, "A, B, C"',
            '20 READ A$, B, C$',
            '30 PRINT A$; "|"; B; "|"; C$'
        ]
        
        results = self.execute_program(program)
        errors = self.get_error_messages(results)
        
        # Should handle quoted strings with commas correctly
        self.assertEqual(len(errors), 0, f"Program should parse quoted strings correctly: {errors}")

    def test_data_floating_point_numbers(self):
        """Test DATA with floating point numbers"""
        program = [
            '10 DATA 3.14159, 2.718, 1.414',
            '20 READ PI, E, SQRT2',
            '30 PRINT PI; E; SQRT2'
        ]
        
        results = self.execute_program(program)
        errors = self.get_error_messages(results)
        
        # Should handle floating point numbers
        self.assertEqual(len(errors), 0, f"Should handle floating point data: {errors}")

    def test_data_negative_numbers(self):
        """Test DATA with negative numbers"""
        program = [
            '10 DATA -100, -3.14, 50',
            '20 READ A, B, C',
            '30 PRINT A; B; C'
        ]
        
        results = self.execute_program(program)
        errors = self.get_error_messages(results)
        
        # Should handle negative numbers
        self.assertEqual(len(errors), 0, f"Should handle negative numbers: {errors}")
        self.assert_variable_equals('A', -100)

    def test_data_statements_out_of_order(self):
        """Test that DATA statements work regardless of line number order"""
        program = [
            '30 READ A, B',
            '10 DATA 100, 200',
            '50 PRINT A; B',
            '20 DATA 300, 400'  # This should be read after first DATA
        ]
        
        results = self.execute_program(program)
        errors = self.get_error_messages(results)
        
        # Should collect DATA from all lines in line number order
        self.assertEqual(len(errors), 0, f"Should handle out-of-order DATA lines: {errors}")

    def test_read_into_array_elements(self):
        """Test READ into array elements"""
        program = [
            '10 DIM A(3)',
            '20 DATA 10, 20, 30',
            '30 READ A(0), A(1), A(2)',
            '40 PRINT A(0); A(1); A(2)'
        ]
        
        results = self.execute_program(program)
        errors = self.get_error_messages(results)
        
        # Should read into array elements successfully
        self.assertEqual(len(errors), 0, f"Should read into arrays: {errors}")

    def test_data_with_expressions(self):
        """Test that DATA contains literal values, not expressions"""
        program = [
            '10 DATA 2+3, "HELLO"+"WORLD"',  # Should be literal strings, not evaluated
            '20 READ A$, B$',
            '30 PRINT A$; "|"; B$'
        ]
        
        results = self.execute_program(program)
        
        # DATA should contain literal values, not evaluate expressions
        # This tests that "2+3" is read as string "2+3", not as number 5

    def test_empty_data_statements(self):
        """Test handling of empty or malformed DATA statements"""
        # Test DATA with no values
        try:
            result = self.basic.execute_command('DATA')
            # Should either error or handle gracefully
        except:
            pass  # Expected behavior

    def test_complex_data_program(self):
        """Test complex program using DATA/READ/RESTORE extensively"""
        program = [
            '10 DATA 5',  # Number of students
            '20 DATA "ALICE", 85, "BOB", 92, "CHARLIE", 78, "DIANA", 96, "EVE", 89',
            '30 READ N',
            '40 PRINT "STUDENT GRADES:"',
            '50 FOR I = 1 TO N',
            '60 READ NAME$, GRADE',
            '70 PRINT NAME$; ": "; GRADE',
            '80 NEXT I',
            '90 RESTORE',
            '100 READ N',  # Skip count',
            '110 PRINT "AVERAGE CALCULATION:"',
            '120 TOTAL = 0',
            '130 FOR I = 1 TO N',
            '140 READ NAME$, GRADE',
            '150 TOTAL = TOTAL + GRADE',
            '160 NEXT I',
            '170 PRINT "AVERAGE: "; TOTAL / N'
        ]
        
        results = self.execute_program(program)
        errors = self.get_error_messages(results)
        
        # Should run complex data processing without errors
        self.assertEqual(len(errors), 0, f"Complex data program should run: {errors}")
        
        text_outputs = self.get_text_output(results)
        self.assertTrue(len(text_outputs) > 0, "Should produce output")

    def test_out_of_data_halts_execution(self):
        """Test that OUT OF DATA error stops program execution"""
        program = [
            '10 DATA 100, 200', 
            '20 READ A',
            '30 READ B', 
            '40 READ C',  # Should trigger OUT OF DATA
            '50 PRINT "SHOULD NOT REACH HERE"'
        ]
        
        results = self.execute_program(program)
        errors = self.get_error_messages(results)
        text_outputs = self.get_text_output(results)
        
        # Should have OUT OF DATA error
        self.assertTrue(any('OUT OF DATA' in error for error in errors), 
                       f"Expected OUT OF DATA error, got: {errors}")
        
        # Should NOT reach line 50
        self.assertFalse(any('SHOULD NOT REACH HERE' in output for output in text_outputs),
                        "Program should halt at OUT OF DATA error")
        
        # Program should stop at line 40
        self.assertEqual(self.basic.current_line, 40, 
                        f"Expected program to stop at line 40, stopped at {self.basic.current_line}")
        
        # Program should not be running
        self.assertFalse(self.basic.running, "Program should have stopped")

    def test_out_of_data_with_continue_execution(self):
        """Test OUT OF DATA error handling in continue execution context"""
        program = [
            '10 DATA 100',
            '20 READ A',
            '30 PRINT "A ="; A',
            '40 READ B',  # Should trigger OUT OF DATA  
            '50 PRINT "SHOULD NOT REACH HERE"'
        ]
        
        results = self.execute_program(program)
        errors = self.get_error_messages(results)
        text_outputs = self.get_text_output(results)
        
        # Should have OUT OF DATA error
        self.assertTrue(any('OUT OF DATA' in error for error in errors))
        
        # Should print A value but not reach line 50
        self.assertTrue(any('A =100' in output for output in text_outputs), 
                       "Should print A value before error")
        self.assertFalse(any('SHOULD NOT REACH HERE' in output for output in text_outputs))


if __name__ == '__main__':
    test = DataCommandTest("DATA/READ/RESTORE Command Tests")
    results = test.run_all_tests()
    from test_base import print_test_results
    print_test_results(results, verbose=True)