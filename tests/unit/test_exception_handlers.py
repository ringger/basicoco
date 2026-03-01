#!/usr/bin/env python3

"""
Tests for narrowed exception handlers in core.py.

Verifies that specific exception types (ValueError, TypeError, etc.)
are properly caught where broad 'except Exception' was narrowed.
Each test triggers the specific error path and verifies graceful handling.
"""

import pytest


class TestIfThenExceptionHandling:
    """Test the IF/THEN handler catches ValueError/TypeError for non-numeric THEN parts"""

    def test_if_then_with_string_target(self, basic, helpers):
        """IF 1=1 THEN with a non-numeric, non-keyword THEN part should be treated as statement"""
        # This triggers the (ValueError, TypeError) handler in IF/THEN
        # when trying int(evaluate_expression(then_part)) fails
        basic.process_command('X = 5')
        result = basic.process_command('IF 1=1 THEN X = 10')
        assert basic.variables.get('X') == 10

    def test_if_then_with_goto_number(self, basic, helpers):
        """IF 1=1 THEN 100 should be treated as GOTO 100"""
        program = [
            '10 IF 1=1 THEN 30',
            '20 PRINT "SKIPPED"',
            '30 PRINT "TARGET"',
        ]
        results = helpers.execute_program(basic, program)
        output = helpers.get_text_output(results)
        assert any('TARGET' in t for t in output)
        assert not any('SKIPPED' in t for t in output)

    def test_if_false_then_no_execution(self, basic, helpers):
        """IF 0=1 THEN should not execute"""
        basic.process_command('X = 5')
        basic.process_command('IF 0=1 THEN X = 10')
        assert basic.variables.get('X') == 5

    def test_if_then_with_expression_target(self, basic, helpers):
        """IF with expression that evaluates to line number"""
        program = [
            '10 L = 30',
            '20 IF 1=1 THEN L',
            '30 PRINT "FOUND"',
        ]
        # Should not crash - either treats L as GOTO or as statement
        results = helpers.execute_program(basic, program)


class TestGotoExceptionHandling:
    """Test GOTO handler catches TypeError/KeyError after ValueError"""

    def test_goto_valid_line(self, basic, helpers):
        """GOTO with valid line number should work"""
        program = [
            '10 GOTO 30',
            '20 PRINT "SKIPPED"',
            '30 PRINT "REACHED"',
        ]
        results = helpers.execute_program(basic, program)
        output = helpers.get_text_output(results)
        assert any('REACHED' in t for t in output)
        assert not any('SKIPPED' in t for t in output)

    def test_goto_invalid_expression(self, basic, helpers):
        """GOTO with invalid expression should produce error, not crash"""
        result = basic.process_command('GOTO "ABC"')
        # Should produce an error result, not an unhandled exception
        assert any(item.get('type') == 'error' for item in result)

    def test_goto_empty_args(self, basic, helpers):
        """GOTO with no args should produce error"""
        result = basic.process_command('GOTO')
        assert any(item.get('type') == 'error' for item in result)


class TestGosubExceptionHandling:
    """Test GOSUB handler catches TypeError/KeyError after ValueError"""

    def test_gosub_valid_subroutine(self, basic, helpers):
        """GOSUB to valid subroutine should work"""
        program = [
            '10 GOSUB 30',
            '20 END',
            '30 PRINT "SUB"',
            '40 RETURN',
        ]
        results = helpers.execute_program(basic, program)
        output = helpers.get_text_output(results)
        assert any('SUB' in t for t in output)

    def test_gosub_invalid_expression(self, basic, helpers):
        """GOSUB with invalid expression should produce error"""
        result = basic.process_command('GOSUB "ABC"')
        assert any(item.get('type') == 'error' for item in result)


class TestOnGotoExceptionHandling:
    """Test ON GOTO/GOSUB handlers catch ValueError/TypeError"""

    def test_on_goto_valid(self, basic, helpers):
        """ON X GOTO with valid index should jump correctly"""
        program = [
            '10 X = 2',
            '20 ON X GOTO 50, 60, 70',
            '30 PRINT "FELL THROUGH"',
            '40 END',
            '50 PRINT "ONE"',
            '55 END',
            '60 PRINT "TWO"',
            '65 END',
            '70 PRINT "THREE"',
            '75 END',
        ]
        results = helpers.execute_program(basic, program)
        output = helpers.get_text_output(results)
        assert any('TWO' in t for t in output)

    def test_on_goto_string_expression(self, basic, helpers):
        """ON with string expression should produce error"""
        basic.process_command('A$ = "HELLO"')
        result = basic.process_command('ON A$ GOTO 100, 200')
        # Should produce error about expression needing to be numeric
        assert any(item.get('type') == 'error' for item in result)

    def test_on_goto_out_of_range(self, basic, helpers):
        """ON with out-of-range index should not crash"""
        program = [
            '10 X = 5',
            '20 ON X GOTO 50, 60',
            '30 PRINT "FELL THROUGH"',
            '40 END',
            '50 PRINT "ONE"',
            '55 END',
            '60 PRINT "TWO"',
            '65 END',
        ]
        # Index 5 is out of range for 2 targets - should fall through or error, not crash
        results = helpers.execute_program(basic, program)


class TestSoundExceptionHandling:
    """Test SOUND handler catches TypeError after ValueError"""

    def test_sound_valid(self, basic, helpers):
        """SOUND with valid parameters should work"""
        result = basic.process_command('SOUND 440, 100')
        # Should produce a sound result, not an error
        assert not any(item.get('type') == 'error' for item in result)

    def test_sound_string_params(self, basic, helpers):
        """SOUND with string parameters should produce error"""
        basic.process_command('A$ = "HELLO"')
        result = basic.process_command('SOUND A$, 100')
        assert any(item.get('type') == 'error' for item in result)


class TestPauseExceptionHandling:
    """Test PAUSE handler catches ValueError/TypeError"""

    def test_pause_valid(self, basic, helpers):
        """PAUSE with valid duration should work"""
        result = basic.process_command('PAUSE 0.1')
        assert not any(item.get('type') == 'error' for item in result)

    def test_pause_no_args(self, basic, helpers):
        """PAUSE with no args should use default"""
        result = basic.process_command('PAUSE')
        assert not any(item.get('type') == 'error' for item in result)

    def test_pause_string_arg(self, basic, helpers):
        """PAUSE with string arg should produce error"""
        basic.process_command('A$ = "HELLO"')
        result = basic.process_command('PAUSE A$')
        assert any(item.get('type') == 'error' for item in result)


class TestArrayExceptionHandling:
    """Test array assignment handler catches IndexError/TypeError/KeyError"""

    def test_array_valid_assignment(self, basic, helpers):
        """Valid array assignment should work"""
        basic.process_command('DIM A(10)')
        result = basic.process_command('A(5) = 42')
        assert not any(item.get('type') == 'error' for item in result)

    def test_array_out_of_bounds(self, basic, helpers):
        """Array out of bounds should produce error"""
        basic.process_command('DIM A(5)')
        result = basic.process_command('A(10) = 42')
        assert any(item.get('type') == 'error' for item in result)

    def test_array_negative_index(self, basic, helpers):
        """Array negative index should produce error"""
        basic.process_command('DIM A(5)')
        result = basic.process_command('A(-1) = 42')
        assert any(item.get('type') == 'error' for item in result)


class TestDeleteExceptionHandling:
    """Test DELETE handler catches TypeError/KeyError after ValueError"""

    def test_delete_valid_line(self, basic, helpers):
        """DELETE with valid line should work"""
        basic.process_command('10 PRINT "HELLO"')
        result = basic.process_command('DELETE 10')
        # Should not crash
        assert not any(item.get('type') == 'error' for item in result)

    def test_delete_nonexistent_line(self, basic, helpers):
        """DELETE with nonexistent line should handle gracefully"""
        result = basic.process_command('DELETE 9999')
        # Should not crash - either error or "not found" message
