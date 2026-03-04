#!/usr/bin/env python3

"""
Comprehensive tests for Phase 3 Enhanced Control Flow features.

Tests WHILE/WEND loops, DO/LOOP variants, EXIT FOR statements, and advanced control structures.
"""

import pytest
from emulator.core import CoCoBasic


class TestEnhancedControlFlow:
    """Test cases for Phase 3 enhanced control flow functionality"""

    def test_basic_functionality(self, basic, helpers):
        """Test basic enhanced control flow functionality"""
        result = basic.process_command('PRINT "ENHANCED CONTROL FLOW"')
        text_output = helpers.get_text_output(result)
        assert text_output == ['ENHANCED CONTROL FLOW']

    def test_basic_while_loop(self, basic, helpers):
        """Test basic WHILE/WEND functionality"""
        program = [
            '10 X = 3',
            '20 WHILE X > 0',
            '30 PRINT X',
            '40 X = X - 1',
            '50 WEND',
            '60 PRINT "DONE"'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        # Should print 3, 2, 1, DONE
        assert '3' in ' '.join(text_outputs)
        assert '2' in ' '.join(text_outputs)
        assert '1' in ' '.join(text_outputs)
        assert 'DONE' in ' '.join(text_outputs)

    def test_while_loop_false_condition(self, basic, helpers):
        """Test WHILE loop with false initial condition"""
        program = [
            '10 X = 0',
            '20 WHILE X > 0',
            '30 PRINT "NEVER"',
            '40 WEND',
            '50 PRINT "AFTER"'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        # Should only print AFTER, never NEVER
        assert 'NEVER' not in ' '.join(text_outputs)
        assert 'AFTER' in ' '.join(text_outputs)

    def test_while_string_condition(self, basic, helpers):
        """Test WHILE loop with string condition"""
        program = [
            '10 A$ = "YES"',
            '20 WHILE A$ = "YES"',
            '30 PRINT A$',
            '40 A$ = "NO"',
            '50 WEND',
            '60 PRINT "END"'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        assert 'YES' in ' '.join(text_outputs)
        assert 'END' in ' '.join(text_outputs)

    def test_exit_for_basic(self, basic, helpers):
        """Test basic EXIT FOR functionality"""
        program = [
            '10 FOR I = 1 TO 10',
            '20 PRINT I',
            '30 IF I = 3 THEN EXIT FOR',
            '40 NEXT I',
            '50 PRINT "DONE"'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        # Should print 1, 2, 3, DONE but not 4 or higher
        assert '1' in ' '.join(text_outputs)
        assert '2' in ' '.join(text_outputs)
        assert '3' in ' '.join(text_outputs)
        assert '4' not in ' '.join(text_outputs)
        assert 'DONE' in ' '.join(text_outputs)

    def test_do_loop_infinite(self, basic, helpers):
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
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        # Should print 1, 2, 3, EXIT
        assert '1' in ' '.join(text_outputs)
        assert '2' in ' '.join(text_outputs)
        assert '3' in ' '.join(text_outputs)
        assert 'EXIT' in ' '.join(text_outputs)

    def test_do_while_loop(self, basic, helpers):
        """Test DO WHILE loop"""
        program = [
            '10 X = 3',
            '20 DO WHILE X > 0',
            '30 PRINT X',
            '40 X = X - 1',
            '50 LOOP',
            '60 PRINT "FINISHED"'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        # Should print 3, 2, 1, FINISHED
        assert '3' in ' '.join(text_outputs)
        assert '2' in ' '.join(text_outputs)
        assert '1' in ' '.join(text_outputs)
        assert 'FINISHED' in ' '.join(text_outputs)

    def test_do_until_loop(self, basic, helpers):
        """Test DO UNTIL loop"""
        program = [
            '10 X = 1',
            '20 DO UNTIL X > 3',
            '30 PRINT X',
            '40 X = X + 1',
            '50 LOOP',
            '60 PRINT "COMPLETE"'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        # Should print 1, 2, 3, COMPLETE
        assert '1' in ' '.join(text_outputs)
        assert '2' in ' '.join(text_outputs)
        assert '3' in ' '.join(text_outputs)
        assert 'COMPLETE' in ' '.join(text_outputs)

    def test_loop_while_condition(self, basic, helpers):
        """Test DO/LOOP WHILE variant"""
        program = [
            '10 X = 0',
            '20 DO',
            '30 X = X + 1',
            '40 PRINT X',
            '50 LOOP WHILE X < 3',
            '60 PRINT "STOP"'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        # Should print 1, 2, 3, STOP
        assert '1' in ' '.join(text_outputs)
        assert '2' in ' '.join(text_outputs)
        assert '3' in ' '.join(text_outputs)
        assert 'STOP' in ' '.join(text_outputs)

    def test_loop_until_condition(self, basic, helpers):
        """Test DO/LOOP UNTIL variant"""
        program = [
            '10 X = 0',
            '20 DO',
            '30 X = X + 1',
            '40 PRINT X',
            '50 LOOP UNTIL X >= 3',
            '60 PRINT "FINAL"'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        # Should print 1, 2, 3, FINAL
        assert '1' in ' '.join(text_outputs)
        assert '2' in ' '.join(text_outputs)
        assert '3' in ' '.join(text_outputs)
        assert 'FINAL' in ' '.join(text_outputs)

    def test_nested_while_loops(self, basic, helpers):
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
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        # Should print 1,1  1,2  2,1  2,2  NESTED
        assert 'NESTED' in ' '.join(text_outputs)

    def test_mixed_control_structures(self, basic, helpers):
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
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        assert 'MIXED' in ' '.join(text_outputs)

    def test_error_handling_wend_without_while(self, basic, helpers):
        """Test error handling for WEND without WHILE"""
        program = [
            '10 PRINT "START"',
            '20 WEND',
            '30 PRINT "NEVER"'
        ]
        
        results = helpers.execute_program(basic, program)
        errors = [r for r in results if r.get('type') == 'error']
        
        assert len(errors) > 0
        assert 'WEND without matching WHILE' in str(errors[0])

    def test_error_handling_loop_without_do(self, basic, helpers):
        """Test error handling for LOOP without DO"""
        program = [
            '10 PRINT "START"',
            '20 LOOP',
            '30 PRINT "NEVER"'
        ]
        
        results = helpers.execute_program(basic, program)
        errors = [r for r in results if r.get('type') == 'error']
        
        assert len(errors) > 0
        assert 'LOOP without matching DO' in str(errors[0])

    def test_error_handling_exit_for_without_for(self, basic, helpers):
        """Test error handling for EXIT FOR without FOR"""
        program = [
            '10 PRINT "START"',
            '20 EXIT FOR',
            '30 PRINT "NEVER"'
        ]
        
        results = helpers.execute_program(basic, program)
        errors = [r for r in results if r.get('type') == 'error']
        
        assert len(errors) > 0
        assert 'EXIT FOR without matching FOR' in str(errors[0])

    def test_complex_integration_scenario(self, basic, helpers):
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
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        assert 'COMPLEX TEST' in ' '.join(text_outputs)
        assert 'INTEGRATED' in ' '.join(text_outputs)

    def test_multiline_if_then_endif(self, basic, helpers):
        """Test multi-line IF/THEN/ENDIF structure"""
        program = [
            '10 X = 5',
            '20 IF X > 3 THEN',
            '30 PRINT "GREATER"', 
            '40 PRINT "THAN 3"',
            '50 ENDIF',
            '60 PRINT "DONE"'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        assert 'GREATER' in ' '.join(text_outputs)
        assert 'THAN 3' in ' '.join(text_outputs)
        assert 'DONE' in ' '.join(text_outputs)

    def test_multiline_if_else_endif(self, basic, helpers):
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
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        assert 'BIG' not in ' '.join(text_outputs)
        assert 'SMALL' in ' '.join(text_outputs)
        assert 'END' in ' '.join(text_outputs)

    def test_nested_multiline_if(self, basic, helpers):
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
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        assert 'BOTH POSITIVE' in ' '.join(text_outputs)
        assert 'A POSITIVE, B NOT' not in ' '.join(text_outputs)
        assert 'A NOT POSITIVE' not in ' '.join(text_outputs)
        assert 'COMPLETE' in ' '.join(text_outputs)

    def test_multiline_if_with_loops(self, basic, helpers):
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
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        assert '1' in ' '.join(text_outputs)
        assert '2' in ' '.join(text_outputs)
        assert '3' in ' '.join(text_outputs)
        assert 'DIFFERENT MODE' not in ' '.join(text_outputs)
        assert 'FINISHED' in ' '.join(text_outputs)

    def test_multiline_if_error_handling(self, basic, helpers):
        """Test error handling for mismatched IF/ELSE/ENDIF"""
        # ELSE without IF
        program1 = [
            '10 PRINT "START"',
            '20 ELSE',
            '30 PRINT "NEVER"'
        ]
        
        results1 = helpers.execute_program(basic, program1)
        errors1 = [r for r in results1 if r.get('type') == 'error']
        assert len(errors1) > 0
        assert 'ELSE without matching IF' in str(errors1[0])

        # ENDIF without IF
        program2 = [
            '10 PRINT "START"',
            '20 ENDIF',
            '30 PRINT "NEVER"'
        ]
        
        results2 = helpers.execute_program(basic, program2)
        errors2 = [r for r in results2 if r.get('type') == 'error']
        assert len(errors2) > 0
        assert 'ENDIF without matching IF' in str(errors2[0])
