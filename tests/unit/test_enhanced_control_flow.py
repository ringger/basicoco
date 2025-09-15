#!/usr/bin/env python3

"""
Comprehensive tests for Phase 3 Enhanced Control Flow features.

Tests WHILE/WEND loops, DO/LOOP variants, EXIT FOR statements, and advanced control structures.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from test_base import BaseTestCase
from emulator.core import CoCoBasic


class EnhancedControlFlowTest(BaseTestCase):
    """Test cases for Phase 3 enhanced control flow functionality"""

    def test_basic_functionality(self):
        """Test basic enhanced control flow functionality"""
        self.assert_text_output('PRINT "ENHANCED CONTROL FLOW"', 'ENHANCED CONTROL FLOW')

    def test_basic_while_loop(self):
        """Test basic WHILE/WEND functionality"""
        program = [
            '10 X = 3',
            '20 WHILE X > 0',
            '30 PRINT X',
            '40 X = X - 1',
            '50 WEND',
            '60 PRINT "DONE"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Should print 3, 2, 1, DONE
        self.assertIn('3', ' '.join(text_outputs))
        self.assertIn('2', ' '.join(text_outputs))
        self.assertIn('1', ' '.join(text_outputs))
        self.assertIn('DONE', ' '.join(text_outputs))

    def test_while_loop_false_condition(self):
        """Test WHILE loop with false initial condition"""
        program = [
            '10 X = 0',
            '20 WHILE X > 0',
            '30 PRINT "NEVER"',
            '40 WEND',
            '50 PRINT "AFTER"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Should only print AFTER, never NEVER
        self.assertNotIn('NEVER', ' '.join(text_outputs))
        self.assertIn('AFTER', ' '.join(text_outputs))

    def test_while_string_condition(self):
        """Test WHILE loop with string condition"""
        program = [
            '10 A$ = "YES"',
            '20 WHILE A$ = "YES"',
            '30 PRINT A$',
            '40 A$ = "NO"',
            '50 WEND',
            '60 PRINT "END"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        self.assertIn('YES', ' '.join(text_outputs))
        self.assertIn('END', ' '.join(text_outputs))

    def test_exit_for_basic(self):
        """Test basic EXIT FOR functionality"""
        program = [
            '10 FOR I = 1 TO 10',
            '20 PRINT I',
            '30 IF I = 3 THEN EXIT FOR',
            '40 NEXT I',
            '50 PRINT "DONE"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Should print 1, 2, 3, DONE but not 4 or higher
        self.assertIn('1', ' '.join(text_outputs))
        self.assertIn('2', ' '.join(text_outputs))
        self.assertIn('3', ' '.join(text_outputs))
        self.assertNotIn('4', ' '.join(text_outputs))
        self.assertIn('DONE', ' '.join(text_outputs))

    def test_do_loop_infinite(self):
        """Test basic DO/LOOP with break condition"""
        program = [
            '10 X = 1',
            '20 DO',
            '30 PRINT X',
            '40 X = X + 1',
            '50 IF X > 3 THEN GOTO 70',
            '60 LOOP',
            '70 PRINT "EXIT"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Should print 1, 2, 3, EXIT
        self.assertIn('1', ' '.join(text_outputs))
        self.assertIn('2', ' '.join(text_outputs))
        self.assertIn('3', ' '.join(text_outputs))
        self.assertIn('EXIT', ' '.join(text_outputs))

    def test_do_while_loop(self):
        """Test DO WHILE loop"""
        program = [
            '10 X = 3',
            '20 DO WHILE X > 0',
            '30 PRINT X',
            '40 X = X - 1',
            '50 LOOP',
            '60 PRINT "FINISHED"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Should print 3, 2, 1, FINISHED
        self.assertIn('3', ' '.join(text_outputs))
        self.assertIn('2', ' '.join(text_outputs))
        self.assertIn('1', ' '.join(text_outputs))
        self.assertIn('FINISHED', ' '.join(text_outputs))

    def test_do_until_loop(self):
        """Test DO UNTIL loop"""
        program = [
            '10 X = 1',
            '20 DO UNTIL X > 3',
            '30 PRINT X',
            '40 X = X + 1',
            '50 LOOP',
            '60 PRINT "COMPLETE"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Should print 1, 2, 3, COMPLETE
        self.assertIn('1', ' '.join(text_outputs))
        self.assertIn('2', ' '.join(text_outputs))
        self.assertIn('3', ' '.join(text_outputs))
        self.assertIn('COMPLETE', ' '.join(text_outputs))

    def test_loop_while_condition(self):
        """Test DO/LOOP WHILE variant"""
        program = [
            '10 X = 0',
            '20 DO',
            '30 X = X + 1',
            '40 PRINT X',
            '50 LOOP WHILE X < 3',
            '60 PRINT "STOP"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Should print 1, 2, 3, STOP
        self.assertIn('1', ' '.join(text_outputs))
        self.assertIn('2', ' '.join(text_outputs))
        self.assertIn('3', ' '.join(text_outputs))
        self.assertIn('STOP', ' '.join(text_outputs))

    def test_loop_until_condition(self):
        """Test DO/LOOP UNTIL variant"""
        program = [
            '10 X = 0',
            '20 DO',
            '30 X = X + 1',
            '40 PRINT X',
            '50 LOOP UNTIL X >= 3',
            '60 PRINT "FINAL"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Should print 1, 2, 3, FINAL
        self.assertIn('1', ' '.join(text_outputs))
        self.assertIn('2', ' '.join(text_outputs))
        self.assertIn('3', ' '.join(text_outputs))
        self.assertIn('FINAL', ' '.join(text_outputs))

    def test_nested_while_loops(self):
        """Test nested WHILE loops"""
        program = [
            '10 I = 1',
            '20 WHILE I <= 2',
            '30 J = 1',
            '40 WHILE J <= 2',
            '50 PRINT I; ","; J',
            '60 J = J + 1',
            '70 WEND',
            '80 I = I + 1',
            '90 WEND',
            '100 PRINT "NESTED"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Should print 1,1  1,2  2,1  2,2  NESTED
        self.assertIn('NESTED', ' '.join(text_outputs))

    def test_mixed_control_structures(self):
        """Test mixing FOR, WHILE, and DO loops"""
        program = [
            '10 FOR I = 1 TO 2',
            '20 X = 1',
            '30 WHILE X <= 1',
            '40 DO',
            '50 PRINT I; X',
            '60 X = X + 1',
            '70 LOOP WHILE X <= 1',
            '80 WEND',
            '90 NEXT I',
            '100 PRINT "MIXED"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        self.assertIn('MIXED', ' '.join(text_outputs))

    def test_error_handling_wend_without_while(self):
        """Test error handling for WEND without WHILE"""
        program = [
            '10 PRINT "START"',
            '20 WEND',
            '30 PRINT "NEVER"'
        ]
        
        results = self.execute_program(program)
        errors = [r for r in results if r.get('type') == 'error']
        
        self.assertTrue(len(errors) > 0)
        self.assertIn('WEND without matching WHILE', str(errors[0]))

    def test_error_handling_loop_without_do(self):
        """Test error handling for LOOP without DO"""
        program = [
            '10 PRINT "START"',
            '20 LOOP',
            '30 PRINT "NEVER"'
        ]
        
        results = self.execute_program(program)
        errors = [r for r in results if r.get('type') == 'error']
        
        self.assertTrue(len(errors) > 0)
        self.assertIn('LOOP without matching DO', str(errors[0]))

    def test_error_handling_exit_for_without_for(self):
        """Test error handling for EXIT FOR without FOR"""
        program = [
            '10 PRINT "START"',
            '20 EXIT FOR',
            '30 PRINT "NEVER"'
        ]
        
        results = self.execute_program(program)
        errors = [r for r in results if r.get('type') == 'error']
        
        self.assertTrue(len(errors) > 0)
        self.assertIn('EXIT FOR without matching FOR', str(errors[0]))

    def test_complex_integration_scenario(self):
        """Test complex integration of all new control structures"""
        program = [
            '10 PRINT "COMPLEX TEST"',
            '20 FOR OUTER = 1 TO 2',
            '30 COUNT = 0',
            '40 WHILE COUNT < 2',
            '50 COUNT = COUNT + 1',
            '60 PRINT "LOOP"; COUNT',
            '70 WEND',
            '80 IF OUTER = 1 THEN EXIT FOR',
            '90 NEXT OUTER',
            '100 PRINT "INTEGRATED"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        self.assertIn('COMPLEX TEST', ' '.join(text_outputs))
        self.assertIn('INTEGRATED', ' '.join(text_outputs))

    def test_multiline_if_then_endif(self):
        """Test multi-line IF/THEN/ENDIF structure"""
        program = [
            '10 X = 5',
            '20 IF X > 3 THEN',
            '30 PRINT "GREATER"', 
            '40 PRINT "THAN 3"',
            '50 ENDIF',
            '60 PRINT "DONE"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        self.assertIn('GREATER', ' '.join(text_outputs))
        self.assertIn('THAN 3', ' '.join(text_outputs))
        self.assertIn('DONE', ' '.join(text_outputs))

    def test_multiline_if_else_endif(self):
        """Test multi-line IF/ELSE/ENDIF structure"""
        program = [
            '10 X = 2',
            '20 IF X > 5 THEN',
            '30 PRINT "BIG"',
            '40 ELSE',
            '50 PRINT "SMALL"',
            '60 ENDIF',
            '70 PRINT "END"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        self.assertNotIn('BIG', ' '.join(text_outputs))
        self.assertIn('SMALL', ' '.join(text_outputs))
        self.assertIn('END', ' '.join(text_outputs))

    def test_nested_multiline_if(self):
        """Test nested multi-line IF statements"""
        program = [
            '10 A = 5',
            '20 B = 3',
            '30 IF A > 0 THEN',
            '40 IF B > 0 THEN',
            '50 PRINT "BOTH POSITIVE"',
            '60 ELSE',
            '70 PRINT "A POSITIVE, B NOT"',
            '80 ENDIF',
            '90 ELSE',
            '100 PRINT "A NOT POSITIVE"',
            '110 ENDIF',
            '120 PRINT "COMPLETE"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        self.assertIn('BOTH POSITIVE', ' '.join(text_outputs))
        self.assertNotIn('A POSITIVE, B NOT', ' '.join(text_outputs))
        self.assertNotIn('A NOT POSITIVE', ' '.join(text_outputs))
        self.assertIn('COMPLETE', ' '.join(text_outputs))

    def test_multiline_if_with_loops(self):
        """Test multi-line IF with loops inside"""
        program = [
            '10 MODE = 1',
            '20 IF MODE = 1 THEN',
            '30 FOR I = 1 TO 3',
            '40 PRINT I',
            '50 NEXT I',
            '60 ELSE',
            '70 PRINT "DIFFERENT MODE"',
            '80 ENDIF',
            '90 PRINT "FINISHED"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        self.assertIn('1', ' '.join(text_outputs))
        self.assertIn('2', ' '.join(text_outputs))
        self.assertIn('3', ' '.join(text_outputs))
        self.assertNotIn('DIFFERENT MODE', ' '.join(text_outputs))
        self.assertIn('FINISHED', ' '.join(text_outputs))

    def test_multiline_if_error_handling(self):
        """Test error handling for mismatched IF/ELSE/ENDIF"""
        # ELSE without IF
        program1 = [
            '10 PRINT "START"',
            '20 ELSE',
            '30 PRINT "NEVER"'
        ]
        
        results1 = self.execute_program(program1)
        errors1 = [r for r in results1 if r.get('type') == 'error']
        self.assertTrue(len(errors1) > 0)
        self.assertIn('ELSE without matching IF', str(errors1[0]))

        # ENDIF without IF
        program2 = [
            '10 PRINT "START"',
            '20 ENDIF',
            '30 PRINT "NEVER"'
        ]
        
        results2 = self.execute_program(program2)
        errors2 = [r for r in results2 if r.get('type') == 'error']
        self.assertTrue(len(errors2) > 0)
        self.assertIn('ENDIF without matching IF', str(errors2[0]))


if __name__ == '__main__':
    test = EnhancedControlFlowTest("Enhanced Control Flow Tests")
    results = test.run_all_tests()
    from test_base import print_test_results
    print_test_results(results, verbose=True)