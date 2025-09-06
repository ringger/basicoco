#!/usr/bin/env python3

"""
Integration tests for complex IF/THEN statement constructs.
Tests multi-statement THEN clauses and edge cases discovered during debugging.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from test_base import BaseTestCase


class ComplexIfThenTest(BaseTestCase):
    """Test cases for complex IF/THEN statement functionality"""

    def test_basic_functionality(self):
        """Test basic IF/THEN functionality"""
        self.assert_text_output('IF 1 = 1 THEN PRINT "TRUE"', 'TRUE')

    def test_if_then_with_multiple_statements(self):
        """Test IF/THEN with multiple statements separated by colons"""
        program = [
            '10 A = 5',
            '20 IF A = 5 THEN PRINT "MATCH": PRINT "CONFIRMED": A = 10',
            '30 PRINT A'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Should print "MATCH", "CONFIRMED", and "10"
        self.assertIn('MATCH', ' '.join(text_outputs))
        self.assertIn('CONFIRMED', ' '.join(text_outputs))
        self.assertIn('10', ' '.join(text_outputs))

    def test_if_then_goto_with_print(self):
        """Test IF/THEN with PRINT and GOTO combination"""
        program = [
            '10 A$ = "TEST"',
            '20 IF A$ = "TEST" THEN PRINT "FOUND: "; A$: GOTO 40',
            '30 PRINT "NOT REACHED"',
            '40 PRINT "END"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Should print "FOUND: TEST" and "END", but not "NOT REACHED"
        combined = ' '.join(text_outputs)
        self.assertIn('FOUND:', combined)
        self.assertIn('TEST', combined)
        self.assertIn('END', combined)
        self.assertNotIn('NOT REACHED', combined)

    def test_if_then_with_string_concatenation(self):
        """Test IF/THEN with string operations in THEN clause"""
        program = [
            '10 A$ = "HELLO"',
            '20 B$ = "WORLD"',
            '30 IF A$ <> "" THEN PRINT A$; " "; B$: A$ = A$ + "!"',
            '40 PRINT A$'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        combined = ' '.join(text_outputs)
        self.assertIn('HELLO', combined)
        self.assertIn('WORLD', combined)
        self.assertIn('HELLO!', combined)

    def test_nested_if_then_statements(self):
        """Test nested IF/THEN constructs"""
        program = [
            '10 A = 5',
            '20 B = 10',
            '30 IF A = 5 THEN IF B = 10 THEN PRINT "BOTH TRUE": GOTO 50',
            '40 PRINT "NOT REACHED"',
            '50 PRINT "SUCCESS"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        combined = ' '.join(text_outputs)
        self.assertIn('BOTH TRUE', combined)
        self.assertIn('SUCCESS', combined)
        self.assertNotIn('NOT REACHED', combined)

    def test_if_then_with_variable_assignment_and_jump(self):
        """Test IF/THEN with variable assignment followed by GOTO"""
        program = [
            '10 SCORE = 85',
            '20 IF SCORE >= 90 THEN GRADE$ = "A": GOTO 50',
            '30 IF SCORE >= 80 THEN GRADE$ = "B": GOTO 50',
            '40 GRADE$ = "C"',
            '50 PRINT "GRADE: "; GRADE$'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        combined = ' '.join(text_outputs)
        self.assertIn('GRADE:', combined)
        self.assertIn('B', combined)

    def test_if_then_with_for_loop_interaction(self):
        """Test IF/THEN inside FOR loop with GOTO"""
        program = [
            '10 FOR I = 1 TO 10',
            '20 IF I = 5 THEN PRINT "FOUND 5": GOTO 40',
            '30 NEXT I',
            '40 PRINT "DONE"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        combined = ' '.join(text_outputs)
        self.assertIn('FOUND 5', combined)
        self.assertIn('DONE', combined)

    def test_if_then_with_function_calls(self):
        """Test IF/THEN with function calls in condition and action"""
        program = [
            '10 A$ = "HELLO"',
            '20 IF LEN(A$) = 5 THEN PRINT "LENGTH: "; LEN(A$): A$ = LEFT$(A$, 3)',
            '30 PRINT A$'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        combined = ' '.join(text_outputs)
        self.assertIn('LENGTH:', combined)
        self.assertIn('5', combined)
        self.assertIn('HEL', combined)

    def test_if_then_statement_boundary_parsing(self):
        """Test that IF/THEN statements are properly parsed as single units"""
        # This tests the fix for the statement splitting issue
        program = [
            '10 FLAG = 1',
            '20 IF FLAG = 1 THEN PRINT "BEFORE": FLAG = 0: PRINT "AFTER"',
            '30 PRINT "FINAL: "; FLAG'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        combined = ' '.join(text_outputs)
        self.assertIn('BEFORE', combined)
        self.assertIn('AFTER', combined)
        self.assertIn('FINAL:', combined)
        self.assertIn('0', combined)


if __name__ == '__main__':
    test = ComplexIfThenTest("Complex IF/THEN Tests")
    results = test.run_all_tests()
    from test_base import print_test_results
    print_test_results(results, verbose=True)