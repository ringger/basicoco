#!/usr/bin/env python3

"""
Comprehensive unit tests for IF THEN statement contexts.
Tests all variations of THEN clauses to prevent parsing regressions.
"""

import sys
import os

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from test_base import BaseTestCase


class IfThenComprehensiveTest(BaseTestCase):
    """Comprehensive test cases for IF THEN statement contexts"""

    def test_basic_functionality(self):
        """Test basic IF THEN functionality"""
        result = self.basic.execute_command('A = 1: IF A = 1 THEN PRINT "BASIC"')
        text_outputs = self.get_text_output(result)
        self.assertIn('BASIC', ' '.join(text_outputs))

    def test_then_with_line_numbers(self):
        """Test IF THEN with line number jumps"""
        # Simple line number
        program = [
            '10 A = 5',
            '20 IF A = 5 THEN 50',
            '30 PRINT "SKIP"',
            '40 END',
            '50 PRINT "JUMPED"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        self.assertIn('JUMPED', ' '.join(text_outputs))
        self.assertNotIn('SKIP', ' '.join(text_outputs))

    def test_then_with_line_number_expressions(self):
        """Test IF THEN with line number expressions"""
        program = [
            '10 A = 5',
            '20 B = 10', 
            '30 IF A = 5 THEN A * B',  # Should jump to line 50
            '40 PRINT "SKIP"',
            '50 PRINT "EXPRESSION JUMP"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        self.assertIn('EXPRESSION JUMP', ' '.join(text_outputs))
        self.assertNotIn('SKIP', ' '.join(text_outputs))

    def test_then_with_print_commands(self):
        """Test IF THEN with PRINT commands"""
        # Simple PRINT
        result = self.basic.execute_command('A = 1: IF A = 1 THEN PRINT "TRUE"')
        text_outputs = self.get_text_output(result)
        self.assertIn('TRUE', ' '.join(text_outputs))
        
        # PRINT with expressions
        result = self.basic.execute_command('X = 10: IF X > 5 THEN PRINT "LARGE"; X')
        text_outputs = self.get_text_output(result)
        self.assertIn('LARGE', ' '.join(text_outputs))
        self.assertIn('10', ' '.join(text_outputs))

    def test_then_with_assignment_commands(self):
        """Test IF THEN with variable assignments"""
        # Direct assignment
        self.basic.execute_command('A = 1')
        self.basic.execute_command('IF A = 1 THEN B = 99')
        self.assertEqual(self.basic.variables.get('B'), 99)
        
        # LET assignment
        self.basic.execute_command('C = 1') 
        self.basic.execute_command('IF C = 1 THEN LET D = 88')
        self.assertEqual(self.basic.variables.get('D'), 88)

    def test_then_with_goto_commands(self):
        """Test IF THEN with GOTO commands"""
        program = [
            '10 A = 1',
            '20 IF A = 1 THEN GOTO 50',
            '30 PRINT "SKIP"',
            '40 END',
            '50 PRINT "GOTO WORKED"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        self.assertIn('GOTO WORKED', ' '.join(text_outputs))
        self.assertNotIn('SKIP', ' '.join(text_outputs))

    def test_then_with_gosub_commands(self):
        """Test IF THEN with GOSUB commands"""
        program = [
            '10 A = 1',
            '20 IF A = 1 THEN GOSUB 100',
            '30 PRINT "MAIN"',
            '40 END',
            '100 PRINT "SUBROUTINE"',
            '110 RETURN'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        self.assertIn('SUBROUTINE', ' '.join(text_outputs))
        self.assertIn('MAIN', ' '.join(text_outputs))

    def test_then_with_exit_for(self):
        """Test IF THEN with EXIT FOR commands"""
        program = [
            '10 FOR I = 1 TO 10',
            '20 PRINT I',
            '30 IF I = 3 THEN EXIT FOR',
            '40 NEXT I',
            '50 PRINT "DONE"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        self.assertIn('1', ' '.join(text_outputs))
        self.assertIn('2', ' '.join(text_outputs))
        self.assertIn('3', ' '.join(text_outputs))
        self.assertIn('DONE', ' '.join(text_outputs))
        self.assertNotIn('4', ' '.join(text_outputs))

    def test_then_with_end_stop_commands(self):
        """Test IF THEN with END and STOP commands"""
        # END command
        program = [
            '10 A = 1',
            '20 IF A = 1 THEN END',
            '30 PRINT "NEVER"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        self.assertNotIn('NEVER', ' '.join(text_outputs))
        
        # STOP command
        program = [
            '10 B = 1',
            '20 IF B = 1 THEN STOP',
            '30 PRINT "NEVER"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        self.assertNotIn('NEVER', ' '.join(text_outputs))

    def test_then_with_multi_statement(self):
        """Test IF THEN with multiple statements"""
        program = [
            '10 A = 1',
            '20 IF A = 1 THEN PRINT "FIRST": PRINT "SECOND": B = 99',
            '30 PRINT B'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        self.assertIn('FIRST', ' '.join(text_outputs))
        self.assertIn('SECOND', ' '.join(text_outputs))
        self.assertIn('99', ' '.join(text_outputs))

    def test_then_with_for_loop_commands(self):
        """Test IF THEN with FOR loop commands"""
        program = [
            '10 A = 1',
            '20 IF A = 1 THEN FOR I = 1 TO 3: PRINT I: NEXT I',
            '30 PRINT "DONE"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        self.assertIn('1', ' '.join(text_outputs))
        self.assertIn('2', ' '.join(text_outputs))
        self.assertIn('3', ' '.join(text_outputs))
        self.assertIn('DONE', ' '.join(text_outputs))

    def test_then_with_input_commands(self):
        """Test IF THEN with INPUT commands (should handle input requests)"""
        # This would normally wait for input, but we test that it generates proper input request
        result = self.basic.execute_command('A = 1: IF A = 1 THEN INPUT "Enter value"; X')
        
        # Should generate input request
        has_input_request = any(item.get('type') == 'input_request' for item in result)
        self.assertTrue(has_input_request)

    def test_then_with_on_commands(self):
        """Test IF THEN with ON GOTO/GOSUB commands"""
        program = [
            '10 A = 1',
            '20 B = 2', 
            '30 IF A = 1 THEN ON B GOTO 100, 200',
            '40 PRINT "SKIP"',
            '50 END',
            '100 PRINT "OPTION 1"',
            '110 END',
            '200 PRINT "OPTION 2"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        self.assertIn('OPTION 2', ' '.join(text_outputs))
        self.assertNotIn('OPTION 1', ' '.join(text_outputs))
        self.assertNotIn('SKIP', ' '.join(text_outputs))

    def test_then_false_conditions(self):
        """Test IF THEN when condition is false (should skip THEN clause)"""
        # False condition with line number
        program = [
            '10 A = 1',
            '20 IF A = 2 THEN 100',
            '30 PRINT "CONTINUED"',
            '40 END',
            '100 PRINT "JUMPED"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        self.assertIn('CONTINUED', ' '.join(text_outputs))
        self.assertNotIn('JUMPED', ' '.join(text_outputs))
        
        # False condition with command
        result = self.basic.execute_command('A = 1: IF A = 2 THEN PRINT "FALSE"')
        text_outputs = self.get_text_output(result)
        self.assertNotIn('FALSE', ' '.join(text_outputs))

    def test_then_with_string_conditions(self):
        """Test IF THEN with string conditions"""
        # String equality
        result = self.basic.execute_command('A$ = "TEST": IF A$ = "TEST" THEN PRINT "MATCH"')
        text_outputs = self.get_text_output(result)
        self.assertIn('MATCH', ' '.join(text_outputs))
        
        # String inequality
        result = self.basic.execute_command('B$ = "X": IF B$ <> "Y" THEN PRINT "DIFFERENT"')
        text_outputs = self.get_text_output(result)
        self.assertIn('DIFFERENT', ' '.join(text_outputs))

    def test_then_with_complex_expressions(self):
        """Test IF THEN with complex conditional expressions"""
        # Mathematical expressions
        result = self.basic.execute_command('A = 5: B = 3: IF A * B = 15 THEN PRINT "MATH"')
        text_outputs = self.get_text_output(result)
        self.assertIn('MATH', ' '.join(text_outputs))
        
        # Function calls
        result = self.basic.execute_command('A = -5: IF ABS(A) = 5 THEN PRINT "FUNCTION"')
        text_outputs = self.get_text_output(result)
        self.assertIn('FUNCTION', ' '.join(text_outputs))

    def test_then_edge_cases(self):
        """Test IF THEN edge cases that might cause parsing issues"""
        # THEN with whitespace
        result = self.basic.execute_command('A = 1: IF A = 1 THEN   PRINT "SPACE"')
        text_outputs = self.get_text_output(result)
        self.assertIn('SPACE', ' '.join(text_outputs))
        
        # THEN with line number 0 (should error)
        result = self.basic.execute_command('A = 1: IF A = 1 THEN 0')
        errors = self.get_error_messages(result)
        self.assertTrue(len(errors) > 0)  # Should produce error
        
        # THEN with negative line number (should error or handle gracefully)
        result = self.basic.execute_command('A = 1: IF A = 1 THEN -10')
        # Behavior may vary - either error or handle gracefully

    def test_nested_if_then(self):
        """Test nested IF THEN statements"""
        program = [
            '10 A = 1',
            '20 B = 2',
            '30 IF A = 1 THEN IF B = 2 THEN PRINT "NESTED"',
            '40 PRINT "DONE"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        self.assertIn('NESTED', ' '.join(text_outputs))
        self.assertIn('DONE', ' '.join(text_outputs))

    def test_multiline_if_then_endif(self):
        """Test multi-line IF THEN ENDIF structure"""
        program = [
            '10 A = 1',
            '20 IF A = 1 THEN',
            '30 PRINT "INSIDE IF"',
            '40 B = 99',
            '50 ENDIF',
            '60 PRINT B'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        self.assertIn('INSIDE IF', ' '.join(text_outputs))
        self.assertIn('99', ' '.join(text_outputs))


if __name__ == '__main__':
    test = IfThenComprehensiveTest("IF THEN Comprehensive Tests")
    results = test.run_all_tests()
    from test_base import print_test_results
    print_test_results(results, verbose=True)