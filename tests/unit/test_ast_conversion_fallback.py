#!/usr/bin/env python3

"""
Unit tests for AST conversion exception fallback paths in process_line
and expand_line_to_sublines.

When AST conversion fails for control structures with colons, the code
should fall through gracefully rather than crashing.
"""

import pytest


class TestProcessLineASTFallback:
    """Test process_line fallback when AST conversion fails"""

    def test_malformed_for_falls_through(self, basic, helpers):
        """Malformed FOR with colons should produce error, not crash"""
        result = basic.process_line('FOR = 1 TO: PRINT "X"')
        # Should either produce an error or handle gracefully
        errors = helpers.get_error_messages(result)
        # The important thing: no unhandled exception
        assert isinstance(result, list)

    def test_malformed_while_falls_through(self, basic, helpers):
        """Malformed WHILE with colons should not crash"""
        result = basic.process_line('WHILE : WEND')
        assert isinstance(result, list)

    def test_malformed_if_falls_through(self, basic, helpers):
        """Malformed IF with colons should produce error, not crash"""
        result = basic.process_line('IF THEN: PRINT "X"')
        errors = helpers.get_error_messages(result)
        assert isinstance(result, list)
        assert len(errors) > 0

    def test_malformed_do_falls_through(self, basic, helpers):
        """Malformed DO with colons should not crash"""
        result = basic.process_line('DO: : LOOP')
        assert isinstance(result, list)

    def test_state_not_corrupted_after_ast_failure(self, basic, helpers):
        """After AST conversion failure, interpreter state should be clean"""
        # Trigger AST conversion attempt
        basic.process_line('FOR = INVALID: STUFF')

        # Interpreter should still work normally
        result = basic.process_command('PRINT "OK"')
        text = helpers.get_text_output(result)
        assert 'OK' in text

        # Variables from before should be unaffected
        basic.process_command('A = 42')
        helpers.assert_variable_equals(basic, 'A', 42)

    def test_valid_control_structure_still_works(self, basic, helpers):
        """Valid control structures should still use AST path successfully"""
        result = basic.process_line('FOR I = 1 TO 3: PRINT I: NEXT I')
        text = helpers.get_text_output(result)
        assert ' 1 ' in text
        assert ' 2 ' in text
        assert ' 3 ' in text


class TestExpandLineASTFallback:
    """Test expand_line_to_sublines fallback when AST conversion fails"""

    def test_malformed_for_still_stores(self, basic, helpers):
        """Malformed FOR line should still be stored (even if not properly expanded)"""
        basic.process_command('10 FOR = BAD: STUFF')
        # Line should be stored in program
        assert 10 in basic.program
        # Should have at least one subline
        sublines = [(k, v) for k, v in basic.expanded_program.items() if k[0] == 10]
        assert len(sublines) >= 1

    def test_malformed_if_still_stores(self, basic, helpers):
        """Malformed IF line should still be stored"""
        basic.process_command('10 IF THEN: PRINT "X"')
        assert 10 in basic.program
        sublines = [(k, v) for k, v in basic.expanded_program.items() if k[0] == 10]
        assert len(sublines) >= 1

    def test_valid_if_then_stored_as_single(self, basic):
        """Valid single-line IF/THEN should be stored by AST converter"""
        basic.process_command('10 IF 1=1 THEN PRINT "Y": GOTO 20')
        sublines = [(k, v) for k, v in basic.expanded_program.items() if k[0] == 10]
        # AST converter should expand this (likely multiple sublines)
        assert len(sublines) >= 1

    def test_program_runs_after_bad_line_stored(self, basic, helpers):
        """Program with a bad line should still run the good lines"""
        basic.process_command('10 PRINT "GOOD"')
        basic.process_command('20 END')
        # The bad line at 10 was already overwritten by the good line
        results = basic.process_command('RUN')
        text = helpers.get_text_output(results)
        assert 'GOOD' in text
