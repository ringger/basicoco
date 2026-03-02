#!/usr/bin/env python3

"""
Integration tests for program execution flow and statement expansion.
Tests scenarios discovered during debugging of execution order issues.
"""

import pytest


class TestProgramExecutionFlow:
    """Test cases for program execution flow and statement expansion"""

    def test_basic_functionality(self, basic, helpers):
        """Test basic program execution"""
        program = ['10 PRINT "TEST"']
        results = helpers.execute_program(basic, program)
        assert len(results) > 0
        text_outputs = helpers.get_text_output(results)
        assert "TEST" in text_outputs

    def test_multi_statement_line_execution_order(self, basic, helpers):
        """Test that multi-statement lines execute in correct order"""
        program = [
            '10 A = 1: B = 2: C = A + B: PRINT C'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        assert ' 3 ' in text_outputs

    def test_statement_expansion_verification(self, basic, helpers):
        """Test that complex statements are expanded correctly"""
        # This verifies the fix for statement splitting issues
        program = [
            '10 PRINT "START": FOR I = 1 TO 2: PRINT I: NEXT I: PRINT "END"'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        combined = ' '.join(text_outputs)
        assert 'START' in combined
        assert '1' in combined
        assert '2' in combined
        assert 'END' in combined

    def test_jump_target_resolution(self, basic, helpers):
        """Test that GOTO targets are resolved correctly across statement boundaries"""
        program = [
            '10 GOTO 30',
            '20 PRINT "SKIPPED"',
            '30 PRINT "TARGET": GOTO 50',
            '40 PRINT "ALSO SKIPPED"',
            '50 PRINT "FINAL"'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        combined = ' '.join(text_outputs)
        assert 'TARGET' in combined
        assert 'FINAL' in combined
        assert 'SKIPPED' not in combined
        assert 'ALSO SKIPPED' not in combined

    def test_for_loop_with_complex_body(self, basic, helpers):
        """Test FOR loop with multi-statement body"""
        program = [
            '10 FOR I = 1 TO 3',
            '20 PRINT "LOOP"; I: A = I * 2: PRINT "DOUBLE"; A',
            '30 NEXT I'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        combined = ' '.join(text_outputs)
        # Should see loop iterations and doubled values (semicolon concatenates without spaces)
        assert 'LOOP 1 ' in combined
        assert 'DOUBLE 2 ' in combined
        assert 'LOOP 3 ' in combined
        assert 'DOUBLE 6 ' in combined

    def test_gosub_return_with_multi_statements(self, basic, helpers):
        """Test GOSUB/RETURN with multi-statement lines"""
        program = [
            '10 GOSUB 30: PRINT "RETURNED"',
            '20 END',
            '30 PRINT "IN SUB": A = 42: PRINT A: RETURN'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        combined = ' '.join(text_outputs)
        assert 'IN SUB' in combined
        assert '42' in combined
        assert 'RETURNED' in combined

    def test_program_line_order_independence(self, basic, helpers):
        """Test that program lines execute in numeric order regardless of entry order"""
        # Load lines in non-sequential order
        basic.process_command('30 PRINT "THREE"')
        basic.process_command('10 PRINT "ONE"')  
        basic.process_command('20 PRINT "TWO"')
        
        results = basic.process_command('RUN')
        text_outputs = helpers.get_text_output(results)
        
        # Should execute in order: ONE, TWO, THREE
        combined = ' '.join(text_outputs)
        one_pos = combined.find('ONE')
        two_pos = combined.find('TWO') 
        three_pos = combined.find('THREE')
        
        assert one_pos < two_pos < three_pos, \
                       f"Execution order wrong: {combined}"

    def test_data_read_across_statement_boundaries(self, basic, helpers):
        """Test DATA/READ operations across complex statement boundaries"""
        program = [
            '10 DATA 1, 2, 3, 4',
            '20 READ A: PRINT A: READ B, C: PRINT B; C',
            '30 READ D: PRINT "LAST"; D'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        combined = ' '.join(text_outputs)
        assert '1' in combined
        assert '2' in combined 
        assert '3' in combined
        assert 'LAST 4 ' in combined  # Semicolon joins; numbers carry spaces

    def test_error_handling_across_statements(self, basic, helpers):
        """Test division by zero handling in multi-statement lines"""
        program = [
            '10 A = 5: B = A / 0: PRINT "AFTER DIVISION: "; B'  # Division by zero should error
        ]

        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)

        # TRS-80 BASIC produces an error for division by zero
        assert len(errors) > 0  # Should generate error
        assert any("DIVISION" in error.upper() or "DIVIDE" in error.upper() or
                  "ERROR" in error.upper() or "ZERO" in error.upper() for error in errors), \
               f"Expected division by zero error, got: {errors}"
