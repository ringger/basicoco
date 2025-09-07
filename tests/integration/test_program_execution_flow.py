#!/usr/bin/env python3

"""
Integration tests for program execution flow and statement expansion.
Tests scenarios discovered during debugging of execution order issues.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from test_base import BaseTestCase


class ProgramExecutionFlowTest(BaseTestCase):
    """Test cases for program execution flow and statement expansion"""

    def test_basic_functionality(self):
        """Test basic program execution"""
        program = ['10 PRINT "TEST"']
        results = self.execute_program(program)
        self.assertTrue(len(results) > 0)

    def test_multi_statement_line_execution_order(self):
        """Test that multi-statement lines execute in correct order"""
        program = [
            '10 A = 1: B = 2: C = A + B: PRINT C'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        self.assertIn('3', text_outputs)

    def test_statement_expansion_verification(self):
        """Test that complex statements are expanded correctly"""
        # This verifies the fix for statement splitting issues
        program = [
            '10 PRINT "START": FOR I = 1 TO 2: PRINT I: NEXT I: PRINT "END"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        combined = ' '.join(text_outputs)
        self.assertIn('START', combined)
        self.assertIn('1', combined)
        self.assertIn('2', combined)
        self.assertIn('END', combined)

    def test_jump_target_resolution(self):
        """Test that GOTO targets are resolved correctly across statement boundaries"""
        program = [
            '10 GOTO 30',
            '20 PRINT "SKIPPED"',
            '30 PRINT "TARGET": GOTO 50',
            '40 PRINT "ALSO SKIPPED"',
            '50 PRINT "FINAL"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        combined = ' '.join(text_outputs)
        self.assertIn('TARGET', combined)
        self.assertIn('FINAL', combined)
        self.assertNotIn('SKIPPED', combined)
        self.assertNotIn('ALSO SKIPPED', combined)

    def test_for_loop_with_complex_body(self):
        """Test FOR loop with multi-statement body"""
        program = [
            '10 FOR I = 1 TO 3',
            '20 PRINT "LOOP"; I: A = I * 2: PRINT "DOUBLE"; A',
            '30 NEXT I'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        combined = ' '.join(text_outputs)
        # Should see loop iterations and doubled values (semicolon concatenates without spaces)
        self.assertIn('LOOP1', combined)
        self.assertIn('DOUBLE2', combined)
        self.assertIn('LOOP3', combined)
        self.assertIn('DOUBLE6', combined)

    def test_gosub_return_with_multi_statements(self):
        """Test GOSUB/RETURN with multi-statement lines"""
        program = [
            '10 GOSUB 30: PRINT "RETURNED"',
            '20 END',
            '30 PRINT "IN SUB": A = 42: PRINT A: RETURN'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        combined = ' '.join(text_outputs)
        self.assertIn('IN SUB', combined)
        self.assertIn('42', combined)
        self.assertIn('RETURNED', combined)

    def test_program_line_order_independence(self):
        """Test that program lines execute in numeric order regardless of entry order"""
        # Load lines in non-sequential order
        self.basic.execute_command('30 PRINT "THREE"')
        self.basic.execute_command('10 PRINT "ONE"')  
        self.basic.execute_command('20 PRINT "TWO"')
        
        results = self.basic.execute_command('RUN')
        text_outputs = self.get_text_output(results)
        
        # Should execute in order: ONE, TWO, THREE
        combined = ' '.join(text_outputs)
        one_pos = combined.find('ONE')
        two_pos = combined.find('TWO') 
        three_pos = combined.find('THREE')
        
        self.assertTrue(one_pos < two_pos < three_pos, 
                       f"Execution order wrong: {combined}")

    def test_data_read_across_statement_boundaries(self):
        """Test DATA/READ operations across complex statement boundaries"""
        program = [
            '10 DATA 1, 2, 3, 4',
            '20 READ A: PRINT A: READ B, C: PRINT B; C',
            '30 READ D: PRINT "LAST"; D'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        combined = ' '.join(text_outputs)
        self.assertIn('1', combined)
        self.assertIn('2', combined) 
        self.assertIn('3', combined)
        self.assertIn('LAST4', combined)  # Semicolon concatenates without spaces

    def test_error_handling_across_statements(self):
        """Test division by zero handling in multi-statement lines"""
        program = [
            '10 A = 5: B = A / 0: PRINT "AFTER DIVISION: "; B'  # Division by zero returns infinity
        ]
        
        results = self.execute_program(program)
        errors = self.get_error_messages(results)
        
        # In authentic BASIC, division by zero returns infinity and continues execution
        self.assertEqual(len(errors), 0)  # No errors should be generated
        text_outputs = self.get_text_output(results)
        combined = ' '.join(text_outputs)
        self.assertIn('AFTER DIVISION:', combined)  # Should continue execution
        self.assertIn('inf', combined.lower())  # Should show infinity


if __name__ == '__main__':
    test = ProgramExecutionFlowTest("Program Execution Flow Tests")
    results = test.run_all_tests()
    from test_base import print_test_results
    print_test_results(results, verbose=True)