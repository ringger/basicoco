"""Tests for PRIVATE variable scope in GOSUB/RETURN."""

import pytest


class TestPrivate:
    """PRIVATE saves variables, initializes them, and restores on RETURN."""

    def test_private_initializes_and_restores(self, basic, helpers):
        """PRIVATE variable starts at 0, caller's value restored on RETURN."""
        results = helpers.execute_program(basic, [
            '10 X=42',
            '20 GOSUB 100',
            '30 PRINT X',
            '40 END',
            '100 PRIVATE X',
            '110 PRINT X',
            '120 X=99',
            '130 RETURN',
        ])
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        texts = helpers.get_text_output(results)
        # Line 110 prints 0 (initialized), line 30 prints 42 (restored)
        assert texts[0].strip() == '0', f"PRIVATE should init to 0, got: {texts[0]}"
        assert texts[1].strip() == '42', f"Should restore to 42, got: {texts[1]}"

    def test_private_string_initializes_empty(self, basic, helpers):
        """PRIVATE string variable starts as "", restored on RETURN."""
        results = helpers.execute_program(basic, [
            '10 N$="HELLO"',
            '20 GOSUB 100',
            '30 PRINT N$',
            '40 END',
            '100 PRIVATE N$',
            '110 PRINT LEN(N$)',
            '120 N$="GOODBYE"',
            '130 RETURN',
        ])
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        texts = helpers.get_text_output(results)
        # Line 110 prints 0 (empty string length), line 30 prints HELLO
        assert texts[0].strip() == '0', f"PRIVATE string should be empty, got len: {texts[0]}"
        assert 'HELLO' in texts[1], f"Should restore to HELLO, got: {texts[1]}"

    def test_private_multiple_variables(self, basic, helpers):
        """PRIVATE initializes multiple variables to defaults."""
        results = helpers.execute_program(basic, [
            '10 A=1: B=2: C=3',
            '20 GOSUB 100',
            '30 PRINT A;B;C',
            '40 END',
            '100 PRIVATE A, B, C',
            '110 PRINT A;B;C',
            '120 RETURN',
        ])
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        texts = helpers.get_text_output(results)
        # Line 110: all zeros; line 30: restored to 1 2 3
        output_sub = texts[0]
        assert '1' not in output_sub, f"PRIVATE vars should be 0: {output_sub}"
        output_caller = texts[1]
        assert '1' in output_caller and '2' in output_caller and '3' in output_caller

    def test_private_nested_gosub(self, basic, helpers):
        """PRIVATE works correctly with nested GOSUB calls."""
        results = helpers.execute_program(basic, [
            '10 X=1',
            '20 GOSUB 100',
            '30 PRINT "FINAL";X',
            '40 END',
            '100 PRIVATE X',
            '110 X=2',
            '120 GOSUB 200',
            '130 PRINT "MID";X',
            '140 RETURN',
            '200 PRIVATE X',
            '210 PRINT "INNER";X',
            '220 X=3',
            '230 RETURN',
        ])
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        texts = helpers.get_text_output(results)
        output = ' '.join(texts)
        # Inner: X starts at 0 (PRIVATE), Mid: X is 2 (set before inner call), Final: X is 1 (restored)
        assert 'INNER 0' in output or 'INNER0' in output
        assert 'MID 2' in output or 'MID2' in output
        assert 'FINAL 1' in output or 'FINAL1' in output

    def test_private_without_gosub_errors(self, basic, helpers):
        """PRIVATE outside GOSUB gives error."""
        results = helpers.execute_program(basic, [
            '10 PRIVATE X',
            '20 END',
        ])
        errors = helpers.get_error_messages(results)
        assert any('PRIVATE WITHOUT GOSUB' in e for e in errors)

    def test_private_no_args_errors(self, basic, helpers):
        """PRIVATE with no variable names gives error."""
        results = helpers.execute_program(basic, [
            '10 GOSUB 100',
            '20 END',
            '100 PRIVATE',
            '110 RETURN',
        ])
        errors = helpers.get_error_messages(results)
        assert any('variable names' in e.lower() for e in errors)

    def test_private_undefined_var(self, basic, helpers):
        """PRIVATE on undefined var starts at 0, removed on RETURN."""
        results = helpers.execute_program(basic, [
            '10 GOSUB 100',
            '20 PRINT Q',
            '30 END',
            '100 PRIVATE Q',
            '110 PRINT Q',
            '120 Q=999',
            '130 RETURN',
        ])
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        texts = helpers.get_text_output(results)
        # Line 110: Q is 0 (PRIVATE init), line 20: Q is 0 (removed, default)
        assert texts[0].strip() == '0', f"PRIVATE should init to 0, got: {texts[0]}"
        assert texts[1].strip() == '0', f"Q should be removed after RETURN, got: {texts[1]}"

    def test_mixed_local_and_private(self, basic, helpers):
        """LOCAL and PRIVATE in same subroutine both work correctly."""
        results = helpers.execute_program(basic, [
            '10 A=10: B=20',
            '20 GOSUB 100',
            '30 PRINT A;B',
            '40 END',
            '100 LOCAL A',
            '110 PRIVATE B',
            '120 PRINT A;B',
            '130 A=99: B=99',
            '140 RETURN',
        ])
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        texts = helpers.get_text_output(results)
        # Line 120: A=10 (LOCAL inherits), B=0 (PRIVATE inits)
        # Line 30: A=10, B=20 (both restored)
        sub_output = texts[0]
        assert '10' in sub_output, f"LOCAL A should inherit 10: {sub_output}"
        assert '0' in sub_output, f"PRIVATE B should be 0: {sub_output}"
        caller_output = texts[1]
        assert '10' in caller_output and '20' in caller_output

    def test_private_with_on_gosub(self, basic, helpers):
        """PRIVATE works with ON...GOSUB."""
        results = helpers.execute_program(basic, [
            '10 X=42',
            '20 C=1',
            '30 ON C GOSUB 100',
            '40 PRINT X',
            '50 END',
            '100 PRIVATE X',
            '110 PRINT X',
            '120 X=99',
            '130 RETURN',
        ])
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        texts = helpers.get_text_output(results)
        assert texts[0].strip() == '0', f"PRIVATE should init to 0: {texts[0]}"
        assert texts[1].strip() == '42', f"Should restore to 42: {texts[1]}"
