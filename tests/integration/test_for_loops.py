#!/usr/bin/env python3

"""
Integration tests for FOR/NEXT loops
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from test_base import BaseTestCase


class ForLoopTest(BaseTestCase):
    """Test cases for FOR/NEXT loop functionality"""

    def test_basic_functionality(self):
        """Test basic FOR/NEXT loop"""
        program = [
            '10 FOR I = 1 TO 3',
            '20 PRINT I',
            '30 NEXT I'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Should print 1, 2, 3
        self.assertTrue(len(text_outputs) >= 3)
        self.assertIn('1', text_outputs[0])
        self.assertIn('2', text_outputs[1])
        self.assertIn('3', text_outputs[2])

    def test_for_loop_step(self):
        """Test FOR/NEXT loop with STEP"""
        program = [
            '10 FOR I = 2 TO 10 STEP 2',
            '20 PRINT I',
            '30 NEXT I'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Should print 2, 4, 6, 8, 10
        expected_values = ['2', '4', '6', '8', '10']
        self.assertTrue(len(text_outputs) >= len(expected_values))
        
        for i, expected in enumerate(expected_values):
            if i < len(text_outputs):
                self.assertIn(expected, text_outputs[i])

    def test_for_loop_negative_step(self):
        """Test FOR/NEXT loop with negative STEP"""
        program = [
            '10 FOR I = 10 TO 2 STEP -2',
            '20 PRINT I',
            '30 NEXT I'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Should print 10, 8, 6, 4, 2
        expected_values = ['10', '8', '6', '4', '2']
        self.assertTrue(len(text_outputs) >= len(expected_values))

    def test_nested_for_loops(self):
        """Test nested FOR/NEXT loops"""
        program = [
            '10 FOR I = 1 TO 2',
            '20 FOR J = 1 TO 2',
            '30 PRINT I; J',
            '40 NEXT J',
            '50 NEXT I'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Should have multiple outputs
        self.assertTrue(len(text_outputs) >= 4)

    def test_for_loop_with_calculations(self):
        """Test FOR loop with calculations in the loop"""
        program = [
            '10 TOTAL = 0',
            '20 FOR I = 1 TO 5',
            '30 TOTAL = TOTAL + I',
            '40 NEXT I',
            '50 PRINT TOTAL'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Should calculate sum 1+2+3+4+5 = 15
        self.assertTrue(any('15' in output for output in text_outputs))

    def test_for_loop_variable_modification(self):
        """Test FOR loop where loop variable is modified"""
        program = [
            '10 FOR I = 1 TO 10',
            '20 PRINT I',
            '30 IF I >= 3 THEN I = 10',
            '40 NEXT I'
        ]
        
        # This tests the behavior when loop variable is modified
        results = self.execute_program(program)
        # The exact behavior may depend on implementation

    def test_for_loop_zero_iterations(self):
        """Test FOR loop that should not execute"""
        program = [
            '10 FOR I = 5 TO 1',  # End < Start with positive step
            '20 PRINT "SHOULD NOT PRINT"',
            '30 NEXT I',
            '40 PRINT "DONE"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Should only print "DONE", not the loop content
        self.assertTrue(any('DONE' in output for output in text_outputs))
        self.assertFalse(any('SHOULD NOT PRINT' in output for output in text_outputs))

    def test_for_loop_floating_point(self):
        """Test FOR loop with floating point values"""
        program = [
            '10 FOR I = 0.5 TO 2.5 STEP 0.5',
            '20 PRINT I',
            '30 NEXT I'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Should handle floating point loop variables
        self.assertTrue(len(text_outputs) >= 4)  # 0.5, 1.0, 1.5, 2.0, 2.5

    def test_for_next_variable_mismatch(self):
        """Test FOR/NEXT with mismatched variables"""
        program = [
            '10 FOR I = 1 TO 3',
            '20 PRINT I',
            '30 NEXT J'  # Wrong variable
        ]
        
        results = self.execute_program(program)
        errors = self.get_error_messages(results)
        
        # Should produce some kind of error or warning
        # Exact behavior depends on implementation

    def test_multiple_for_loops_sequential(self):
        """Test multiple FOR loops in sequence"""
        program = [
            '10 FOR I = 1 TO 2',
            '20 PRINT "FIRST"; I',
            '30 NEXT I',
            '40 FOR I = 3 TO 4',
            '50 PRINT "SECOND"; I',
            '60 NEXT I'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Should execute both loops
        self.assertTrue(len(text_outputs) >= 4)


if __name__ == '__main__':
    test = ForLoopTest("FOR/NEXT Loop Tests")
    results = test.run_all_tests()
    from test_base import print_test_results
    print_test_results(results, verbose=True)