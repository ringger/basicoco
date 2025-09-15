#!/usr/bin/env python3

"""
Unit tests for error recovery and state consistency.
Tests that errors don't leave the interpreter in inconsistent states.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from test_base import BaseTestCase


class ErrorRecoveryTest(BaseTestCase):
    """Test cases for error recovery and state consistency"""

    def test_basic_functionality(self):
        """Basic test to ensure error recovery tests work"""
        # Simple error that should be handled
        result = self.basic.execute_command('PRINT 1 / 0')  # Division by zero
        # Should handle gracefully (returns infinity in authentic BASIC)
        self.assertTrue(len(result) > 0)

    def test_error_recovery_state_consistency(self):
        """Test interpreter state after various errors"""
        # Test each error type leaves clean state
        error_tests = [
            ('READ X', 'OUT OF DATA'),  # No DATA statements
            ('DIM A(5): DIM A(10)', "already dimensioned"),
            ('UNDIM(999) = 5', "UNDIM'D ARRAY")  # Undimensioned array error
        ]
        
        for command, expected_error in error_tests:
            self.basic.execute_command('NEW')  # Start fresh
            result = self.basic.execute_command(command)
            
            # Should have expected error
            self.assertTrue(any(expected_error in item.get('message', '') 
                              for item in result if item.get('type') == 'error'),
                           f"Expected {expected_error} for command: {command}")
            
            # Interpreter should be in clean state
            self.assertFalse(self.basic.running, f"Program should not be running after error: {command}")
            self.assertIsNone(self.basic.program_counter, f"Program counter should be None after error: {command}")

    def test_program_error_state_recovery(self):
        """Test state consistency after program errors"""
        # Program with multiple errors
        program = [
            '10 DIM A(3)',
            '20 A(0) = 10',
            '30 A(5) = 50',  # BAD SUBSCRIPT error
            '40 PRINT "UNREACHABLE"'
        ]
        
        # Execute program
        results = self.execute_program(program)
        errors = self.get_error_messages(results)
        
        # Should have BAD SUBSCRIPT error  
        self.assertTrue(any("BAD SUBSCRIPT" in error for error in errors))
        
        # State should be consistent
        self.assertFalse(self.basic.running)
        self.assertEqual(self.basic.current_line, 30)  # Stopped at error line
        
        # Array should have valid values set before error
        self.assertEqual(self.basic.arrays['A'][0], 10)
        
        # Should be able to execute new commands after error
        result = self.basic.execute_command('PRINT "RECOVERY TEST"')
        self.assertTrue(any('RECOVERY TEST' in item.get('text', '') 
                          for item in result if item.get('type') == 'text'))

    def test_nested_error_recovery(self):
        """Test recovery from nested errors in complex programs"""
        program = [
            '10 DIM A(5)',
            '20 FOR I = 1 TO 10',  # Loop beyond array bounds
            '30 A(I) = I * 10',   # This will fail when I > 5 (BAD SUBSCRIPT)
            '40 PRINT "SET A("; I; ") ="; A(I)',
            '50 NEXT I',
            '60 PRINT "COMPLETED"'
        ]
        
        results = self.execute_program(program)
        errors = self.get_error_messages(results)
        text_outputs = self.get_text_output(results)
        
        # Should get BAD SUBSCRIPT error when I exceeds array bounds
        self.assertTrue(any("BAD SUBSCRIPT" in error for error in errors),
                       f"Expected BAD SUBSCRIPT error, got: {errors}")
        
        # Should not complete the loop
        self.assertFalse(any('COMPLETED' in output for output in text_outputs),
                        "Should not complete loop after error")
        
        # Should have executed some iterations successfully (I = 1 to 5)
        successful_outputs = [output for output in text_outputs if 'SET A(' in output]
        self.assertGreater(len(successful_outputs), 0, "Should have some successful iterations")
        self.assertLess(len(successful_outputs), 10, "Should not complete all 10 iterations")
        
        # FOR stack should be cleared after error  
        self.assertEqual(len(self.basic.for_stack), 0, "FOR stack should be empty after error")

    def test_error_in_gosub_recovery(self):
        """Test recovery from errors in GOSUB subroutines"""
        program = [
            '10 PRINT "MAIN START"',
            '20 GOSUB 100',
            '30 PRINT "BACK IN MAIN"',  # Should not reach here
            '40 END',
            '100 PRINT "IN SUBROUTINE"',
            '110 UNDIM(999) = 5',  # UNDIM'D ARRAY error
            '120 PRINT "AFTER ERROR"',  # Should not reach here
            '130 RETURN'
        ]
        
        results = self.execute_program(program)
        errors = self.get_error_messages(results)
        text_outputs = self.get_text_output(results)
        
        # Should have UNDIM'D ARRAY error
        self.assertTrue(any("UNDIM'D ARRAY" in error for error in errors))
        
        # Should reach subroutine but not return
        self.assertTrue(any('IN SUBROUTINE' in output for output in text_outputs))
        self.assertFalse(any('BACK IN MAIN' in output for output in text_outputs))
        self.assertFalse(any('AFTER ERROR' in output for output in text_outputs))
        
        # Call stack should be cleared after error
        self.assertEqual(len(self.basic.call_stack), 0, "Call stack should be empty after error")

    def test_data_pointer_consistency_after_error(self):
        """Test DATA pointer consistency after READ errors"""
        program = [
            '10 DATA 100, 200, 300',
            '20 READ A',
            '30 READ B', 
            '40 READ C',
            '50 READ D',  # Should trigger OUT OF DATA
            '60 PRINT "UNREACHABLE"'
        ]
        
        results = self.execute_program(program)
        errors = self.get_error_messages(results)
        
        # Should have OUT OF DATA error
        self.assertTrue(any('OUT OF DATA' in error for error in errors))
        
        # Data pointer should be at end
        self.assertEqual(self.basic.data_pointer, len(self.basic.data_statements))
        
        # Variables should have been set before error
        self.assertEqual(self.basic.variables.get('A'), 100)
        self.assertEqual(self.basic.variables.get('B'), 200)
        self.assertEqual(self.basic.variables.get('C'), 300)
        self.assertNotIn('D', self.basic.variables)  # D should not be set

    def test_syntax_error_recovery(self):
        """Test recovery from syntax errors"""
        # Test various syntax errors and runtime errors
        error_tests = [
            ('FOR I = 1 TO', 'Invalid FOR statement'),  # Incomplete FOR
            ('IF THEN 10', 'Empty condition'),  # Missing condition
            ('DIM A()', 'Invalid array declaration'),  # Empty dimensions
            ('GOSUB', 'Missing line number'),  # Missing line number
            ('NEXT I', 'NEXT WITHOUT FOR'),  # NEXT without matching FOR (runtime error)
        ]
        
        for bad_command, expected_error in error_tests:
            self.basic.execute_command('NEW')  # Fresh start
            result = self.basic.execute_command(bad_command)
            
            # Should produce expected error
            has_expected_error = any(expected_error in item.get('message', '') 
                                   for item in result if item.get('type') == 'error')
            self.assertTrue(has_expected_error, f"Expected {expected_error} for: {bad_command}")
            
            # Should be able to execute valid command after error
            recovery_result = self.basic.execute_command('PRINT "OK"')
            self.assertTrue(any('OK' in item.get('text', '') 
                              for item in recovery_result if item.get('type') == 'text'),
                           f"Should recover after error: {bad_command}")

    def test_memory_consistency_after_errors(self):
        """Test that memory structures remain consistent after errors"""
        # Create some initial state
        setup_commands = [
            'A = 42',
            'B$ = "HELLO"',
            'DIM C(5)',
            'C(0) = 100'
        ]
        
        for cmd in setup_commands:
            self.basic.execute_command(cmd)
        
        initial_var_count = len(self.basic.variables)
        initial_array_count = len(self.basic.arrays)
        
        # Try to cause various errors
        error_commands = [
            'READ X',  # OUT OF DATA
            'D(999) = 5',  # UNDIM'D ARRAY error
            'DIM C(10)',  # REDIM'D ARRAY
        ]
        
        for error_cmd in error_commands:
            self.basic.execute_command(error_cmd)
        
        # Original variables and arrays should still exist and be valid
        self.assertEqual(self.basic.variables.get('A'), 42)
        self.assertEqual(self.basic.variables.get('B$'), 'HELLO')
        self.assertEqual(self.basic.arrays['C'][0], 100)
        
        # Memory structures should not have grown unexpectedly from errors
        # (though new undimensioned arrays might be created)
        self.assertGreaterEqual(len(self.basic.variables), initial_var_count)
        self.assertGreaterEqual(len(self.basic.arrays), initial_array_count)

    def test_program_counter_reset_after_error(self):
        """Test that program counter is properly reset after errors"""
        program = [
            '10 PRINT "LINE 10"',
            '20 UNDIM(999) = 5',  # UNDIM'D ARRAY
            '30 PRINT "LINE 30"'  # Should not reach
        ]
        
        results = self.execute_program(program)
        errors = self.get_error_messages(results)
        
        # Should have error
        self.assertTrue(any("UNDIM'D ARRAY" in error for error in errors))
        
        # Program counter should be reset
        self.assertIsNone(self.basic.program_counter)
        self.assertFalse(self.basic.running)
        
        # Should be able to run a different program
        new_program = ['10 PRINT "NEW PROGRAM"']
        new_results = self.execute_program(new_program)
        new_text = self.get_text_output(new_results)
        
        self.assertTrue(any('NEW PROGRAM' in output for output in new_text))

    def test_state_consistency_after_multiple_errors(self):
        """Test state consistency after multiple consecutive errors"""
        # Generate multiple errors in sequence
        error_commands = [
            'READ X',  # OUT OF DATA
            'UNDIM(999) = 5',  # UNDIM'D ARRAY
            'DIM A(5): DIM A(10)',  # REDIM'D ARRAY
        ]
        
        for i, cmd in enumerate(error_commands):
            result = self.basic.execute_command(cmd)
            
            # Each should produce an error
            errors = [item for item in result if item.get('type') == 'error']
            self.assertTrue(len(errors) > 0, f"Command {i+1} should produce error: {cmd}")
            
            # State should remain consistent
            self.assertFalse(self.basic.running, f"Should not be running after error {i+1}")
            self.assertIsNone(self.basic.program_counter, f"Program counter should be None after error {i+1}")
        
        # Should be able to execute valid command after all errors
        result = self.basic.execute_command('PRINT "RECOVERY SUCCESSFUL"')
        text_outputs = self.get_text_output(result)
        self.assertTrue(any('RECOVERY SUCCESSFUL' in output for output in text_outputs))


if __name__ == '__main__':
    test = ErrorRecoveryTest("Error Recovery Tests")
    results = test.run_all_tests()
    from test_base import print_test_results
    print_test_results(results, verbose=True)