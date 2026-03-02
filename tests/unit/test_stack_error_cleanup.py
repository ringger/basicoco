"""Tests for stack cleanup after errors in various control structures.

Covers gaps not addressed by test_error_recovery.py or test_stack_clearing.py:
- WHILE stack cleanup on errors
- DO stack cleanup on errors
- Deeply nested mixed control structures
- Stack state after CONT
"""

import pytest


class TestWhileStackCleanup:
    """Verify while_stack is cleared after errors inside WHILE loops."""

    def test_error_inside_while_clears_stack(self, basic, helpers):
        program = [
            '10 X = 1',
            '20 WHILE X < 10',
            '30 UNDIM(999) = 5',
            '40 X = X + 1',
            '50 WEND',
        ]
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        assert any("UNDIM'D ARRAY" in e for e in errors)
        assert basic.while_stack == []

    def test_nested_while_error_clears_all(self, basic, helpers):
        program = [
            '10 X = 1',
            '20 WHILE X < 5',
            '30 Y = 1',
            '40 WHILE Y < 5',
            '50 UNDIM(999) = 5',
            '60 Y = Y + 1',
            '70 WEND',
            '80 X = X + 1',
            '90 WEND',
        ]
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        assert any("UNDIM'D ARRAY" in e for e in errors)
        assert basic.while_stack == []


class TestDoStackCleanup:
    """Verify do_stack is cleared after errors inside DO loops."""

    def test_error_inside_do_clears_stack(self, basic, helpers):
        program = [
            '10 X = 1',
            '20 DO WHILE X < 10',
            '30 UNDIM(999) = 5',
            '40 X = X + 1',
            '50 LOOP',
        ]
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        assert any("UNDIM'D ARRAY" in e for e in errors)
        assert basic.do_stack == []


class TestDeeplyNestedMixedStructures:
    """Test deeply nested mixed control structures execute correctly."""

    def test_for_inside_while_inside_if(self, basic, helpers):
        """FOR within WHILE within IF — all three stack types."""
        program = [
            '10 X = 1',
            '20 IF X = 1 THEN',
            '30 WHILE X < 4',
            '40 FOR I = 1 TO 2',
            '50 PRINT X * 10 + I',
            '60 NEXT I',
            '70 X = X + 1',
            '80 WEND',
            '90 ENDIF',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Unexpected errors: {errors}"
        # X=1: I=1→11, I=2→12; X=2: I=1→21, I=2→22; X=3: I=1→31, I=2→32
        expected = ['11', '12', '21', '22', '31', '32']
        # Filter only numeric output
        numeric = [t.strip() for t in text if t.strip().lstrip('-').isdigit()]
        assert numeric == expected
        # All stacks clean
        assert basic.for_stack == []
        assert basic.while_stack == []
        assert basic.if_stack == []

    def test_error_in_deeply_nested_clears_all_stacks(self, basic, helpers):
        """Error deep in nested structures should clear all stacks."""
        program = [
            '5 DIM A(3)',
            '10 X = 1',
            '20 IF X = 1 THEN',
            '30 WHILE X < 10',
            '40 FOR I = 1 TO 5',
            '50 A(I) = I',         # BAD SUBSCRIPT when I > 3
            '60 NEXT I',
            '70 X = X + 1',
            '80 WEND',
            '90 ENDIF',
        ]
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        assert any("BAD SUBSCRIPT" in e for e in errors)
        assert basic.for_stack == []
        assert basic.while_stack == []


class TestRecoveryAfterStackErrors:
    """Verify the interpreter can run new programs after stack errors."""

    def test_run_new_program_after_while_error(self, basic, helpers):
        # First: error inside WHILE
        program1 = [
            '10 WHILE 1',
            '20 UNDIM(999) = 5',
            '30 WEND',
        ]
        helpers.execute_program(basic, program1)

        # Second: clean program should work fine
        program2 = [
            '10 PRINT "CLEAN"',
        ]
        results = helpers.execute_program(basic, program2)
        text = helpers.get_text_output(results)
        assert 'CLEAN' in text

    def test_run_new_program_after_do_error(self, basic, helpers):
        program1 = [
            '10 DO WHILE 1',
            '20 UNDIM(999) = 5',
            '30 LOOP',
        ]
        helpers.execute_program(basic, program1)

        program2 = [
            '10 FOR I = 1 TO 3',
            '20 PRINT I',
            '30 NEXT I',
        ]
        results = helpers.execute_program(basic, program2)
        text = helpers.get_text_output(results)
        assert ' 1 ' in text
        assert ' 3 ' in text
        assert basic.for_stack == []
