#!/usr/bin/env python3

"""
Integration tests for complex IF/THEN statement constructs.
Tests multi-statement THEN clauses and edge cases discovered during debugging.
"""

import pytest


class TestComplexIfThen:
    """Test cases for complex IF/THEN statement functionality"""

    def test_basic_functionality(self, basic, helpers):
        """Test basic IF/THEN functionality"""
        result = basic.process_command('IF 1 = 1 THEN PRINT "TRUE"')
        text_output = helpers.get_text_output(result)
        assert text_output == ['TRUE']

    def test_if_then_with_multiple_statements(self, basic, helpers):
        """Test IF/THEN with multiple statements separated by colons"""
        program = [
            '10 A = 5',
            '20 IF A = 5 THEN PRINT "MATCH": PRINT "CONFIRMED": A = 10',
            '30 PRINT A'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        # Should print "MATCH", "CONFIRMED", and "10"
        assert 'MATCH' in ' '.join(text_outputs)
        assert 'CONFIRMED' in ' '.join(text_outputs)
        assert '10' in ' '.join(text_outputs)

    def test_if_then_goto_with_print(self, basic, helpers):
        """Test IF/THEN with PRINT and GOTO combination"""
        program = [
            '10 A$ = "TEST"',
            '20 IF A$ = "TEST" THEN PRINT "FOUND: "; A$: GOTO 40',
            '30 PRINT "NOT REACHED"',
            '40 PRINT "END"'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        # Should print "FOUND: TEST" and "END", but not "NOT REACHED"
        combined = ' '.join(text_outputs)
        assert 'FOUND:' in combined
        assert 'TEST' in combined
        assert 'END' in combined
        assert 'NOT REACHED' not in combined

    def test_if_then_with_string_concatenation(self, basic, helpers):
        """Test IF/THEN with string operations in THEN clause"""
        program = [
            '10 A$ = "HELLO"',
            '20 B$ = "WORLD"',
            '30 IF A$ <> "" THEN PRINT A$; " "; B$: A$ = A$ + "!"',
            '40 PRINT A$'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        combined = ' '.join(text_outputs)
        assert 'HELLO' in combined
        assert 'WORLD' in combined
        assert 'HELLO!' in combined

    def test_nested_if_then_statements(self, basic, helpers):
        """Test nested IF/THEN constructs"""
        program = [
            '10 A = 5',
            '20 B = 10',
            '30 IF A = 5 THEN IF B = 10 THEN PRINT "BOTH TRUE": GOTO 50',
            '40 PRINT "NOT REACHED"',
            '50 PRINT "SUCCESS"'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        combined = ' '.join(text_outputs)
        assert 'BOTH TRUE' in combined
        assert 'SUCCESS' in combined
        assert 'NOT REACHED' not in combined

    def test_if_then_with_variable_assignment_and_jump(self, basic, helpers):
        """Test IF/THEN with variable assignment followed by GOTO"""
        program = [
            '10 SCORE = 85',
            '20 IF SCORE >= 90 THEN GRADE$ = "A": GOTO 50',
            '30 IF SCORE >= 80 THEN GRADE$ = "B": GOTO 50',
            '40 GRADE$ = "C"',
            '50 PRINT "GRADE: "; GRADE$'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        combined = ' '.join(text_outputs)
        assert 'GRADE:' in combined
        assert 'B' in combined

    def test_if_then_with_for_loop_interaction(self, basic, helpers):
        """Test IF/THEN inside FOR loop with GOTO"""
        program = [
            '10 FOR I = 1 TO 10',
            '20 IF I = 5 THEN PRINT "FOUND 5": GOTO 40',
            '30 NEXT I',
            '40 PRINT "DONE"'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        combined = ' '.join(text_outputs)
        assert 'FOUND 5' in combined
        assert 'DONE' in combined

    def test_if_then_with_function_calls(self, basic, helpers):
        """Test IF/THEN with function calls in condition and action"""
        program = [
            '10 A$ = "HELLO"',
            '20 IF LEN(A$) = 5 THEN PRINT "LENGTH: "; LEN(A$): A$ = LEFT$(A$, 3)',
            '30 PRINT A$'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        combined = ' '.join(text_outputs)
        assert 'LENGTH:' in combined
        assert '5' in combined
        assert 'HEL' in combined

    def test_if_then_statement_boundary_parsing(self, basic, helpers):
        """Test that IF/THEN statements are properly parsed as single units"""
        # This tests the fix for the statement splitting issue
        program = [
            '10 FLAG = 1',
            '20 IF FLAG = 1 THEN PRINT "BEFORE": FLAG = 0: PRINT "AFTER"',
            '30 PRINT "FINAL: "; FLAG'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        combined = ' '.join(text_outputs)
        assert 'BEFORE' in combined
        assert 'AFTER' in combined
        assert 'FINAL:' in combined
        assert '0' in combined
