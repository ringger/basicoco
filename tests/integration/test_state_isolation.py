#!/usr/bin/env python3

"""
Integration tests for state isolation and cleanup between operations.
Tests scenarios that revealed state bleedover issues during debugging.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from test_base import BaseTestCase


class StateIsolationTest(BaseTestCase):
    """Test cases for state isolation and cleanup"""

    def test_basic_functionality(self):
        """Test basic state isolation"""
        self.basic.execute_command('A = 5')
        self.assert_variable_equals('A', 5)

    def test_new_command_clears_all_state(self):
        """Test that NEW command properly clears all state"""
        # Set up various state
        self.basic.execute_command('A = 42')
        self.basic.execute_command('DIM B(10)')
        self.basic.execute_command('B(5) = 99')
        self.basic.execute_command('10 PRINT "TEST"')
        self.basic.key_buffer = ['X', 'Y', 'Z']
        
        # Verify state is set
        self.assert_variable_equals('A', 42)
        self.assertTrue('B' in self.basic.arrays)
        self.assertTrue(10 in self.basic.program)
        self.assertTrue(len(self.basic.key_buffer) == 3)
        
        # Clear with NEW
        result = self.basic.execute_command('NEW')
        
        # Verify everything is cleared
        self.assertNotIn('A', self.basic.variables)
        self.assertNotIn('B', self.basic.arrays)
        self.assertEqual(len(self.basic.program), 0)
        self.assertEqual(len(self.basic.key_buffer), 0)
        
        # Should return READY message
        self.assertTrue(any(item.get('text') == 'READY' for item in result))

    def test_key_buffer_persistence_across_commands(self):
        """Test key buffer behavior across different command contexts"""
        # Set up key buffer
        self.basic.key_buffer = ['A', 'B', 'C']
        
        # INKEY$ should consume keys
        result1 = self.basic.execute_command('PRINT INKEY$')
        self.assertEqual(len(self.basic.key_buffer), 2)
        
        # Variable assignment should not affect buffer
        self.basic.execute_command('X = 5')
        self.assertEqual(len(self.basic.key_buffer), 2)
        
        # Another INKEY$ should consume next key
        result2 = self.basic.execute_command('PRINT INKEY$')
        self.assertEqual(len(self.basic.key_buffer), 1)

    def test_array_state_after_redim_error(self):
        """Test array state after REDIM'D ARRAY error"""
        # Create array
        self.basic.execute_command('DIM A(5)')
        self.basic.execute_command('A(3) = 42')
        
        # Verify array exists and has value
        self.assertTrue('A' in self.basic.arrays)
        self.assert_variable_equals('A(3)', 42)
        
        # Try to redimension (should error)
        result = self.basic.execute_command('DIM A(10)')
        errors = [item for item in result if item.get('type') == 'error']
        self.assertTrue(len(errors) > 0)
        
        # Original array should still exist and retain values
        self.assertTrue('A' in self.basic.arrays)
        self.assert_variable_equals('A(3)', 42)

    def test_for_loop_stack_cleanup_on_error(self):
        """Test FOR loop stack cleanup when errors occur"""
        program = [
            '10 FOR I = 1 TO 5',
            '20 A = 10 / I',  # Will error when I = 0 (shouldn't happen, but test edge case)
            '30 PRINT A',
            '40 NEXT I'
        ]
        
        # Verify no FOR stack initially
        self.assertEqual(len(self.basic.for_stack), 0)
        
        results = self.execute_program(program)
        
        # FOR stack should be clean after program execution
        self.assertEqual(len(self.basic.for_stack), 0)

    def test_variable_scoping_with_gosub(self):
        """Test variable state across GOSUB/RETURN boundaries"""
        program = [
            '10 A = 10',
            '20 GOSUB 100',
            '30 PRINT "MAIN A:"; A',
            '40 END',
            '100 PRINT "SUB A:"; A',
            '110 A = 20',
            '120 B = 30',
            '130 RETURN'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Variables should be shared between main and subroutine
        combined = ' '.join(text_outputs)
        self.assertIn('SUB A:10', combined)  # A starts as 10 (semicolon concatenates without spaces)
        self.assertIn('MAIN A:20', combined)  # A modified to 20 in subroutine
        
        # B should exist after return
        self.assert_variable_equals('B', 30)

    def test_data_pointer_state_across_operations(self):
        """Test DATA pointer state across different operations"""
        program = [
            '10 DATA 1, 2, 3, 4, 5',
            '20 READ A, B',
            '30 PRINT A; B'
        ]
        
        results = self.execute_program(program)
        
        # Data pointer should be at position 2 (after reading 2 items)
        self.assertEqual(self.basic.data_pointer, 2)
        
        # Additional READ should continue from where we left off
        result = self.basic.execute_command('READ C')
        self.assert_variable_equals('C', 3)
        self.assertEqual(self.basic.data_pointer, 3)

    def test_program_state_after_stop_and_cont(self):
        """Test program state preservation with STOP/CONT"""
        program = [
            '10 A = 1',
            '20 PRINT A',
            '30 STOP',
            '40 A = 2',
            '50 PRINT A'
        ]
        
        results1 = self.execute_program(program)
        
        # Should stop at line 30
        self.assertFalse(self.basic.running)
        self.assertTrue(self.basic.stopped_position is not None)
        
        # Variables should be preserved
        self.assert_variable_equals('A', 1)
        
        # CONT should resume
        results2 = self.basic.execute_command('CONT')
        
        # Should have completed execution
        self.assert_variable_equals('A', 2)

    def test_graphics_mode_state_persistence(self):
        """Test graphics mode state across operations"""
        # Set graphics mode
        self.basic.execute_command('PMODE 1,1')
        initial_mode = self.basic.graphics_mode
        
        # Graphics mode should persist across other commands
        self.basic.execute_command('A = 5')
        self.basic.execute_command('PRINT A')
        
        self.assertEqual(self.basic.graphics_mode, initial_mode)
        
        # NEW should reset graphics mode
        self.basic.execute_command('NEW')
        self.assertEqual(self.basic.graphics_mode, 0)  # Reset to text mode


if __name__ == '__main__':
    test = StateIsolationTest("State Isolation Tests")
    results = test.run_all_tests()
    from test_base import print_test_results
    print_test_results(results, verbose=True)