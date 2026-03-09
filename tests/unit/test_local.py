"""Tests for LOCAL variable save/restore in GOSUB/RETURN."""

import pytest


class TestLocal:
    """LOCAL saves variables on entry, RETURN restores them."""

    def test_local_restores_on_return(self, basic, helpers):
        """LOCAL variable is restored after RETURN."""
        results = helpers.execute_program(basic, [
            '10 X=42',
            '20 GOSUB 100',
            '30 PRINT X',
            '40 END',
            '100 LOCAL X',
            '110 X=99',
            '120 RETURN',
        ])
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        texts = helpers.get_text_output(results)
        assert any('42' in t for t in texts), f"X should be 42 after RETURN, got: {texts}"

    def test_local_multiple_vars(self, basic, helpers):
        """LOCAL saves and restores multiple variables."""
        results = helpers.execute_program(basic, [
            '10 A=1: B=2: C=3',
            '20 GOSUB 100',
            '30 PRINT A;B;C',
            '40 END',
            '100 LOCAL A, B, C',
            '110 A=10: B=20: C=30',
            '120 RETURN',
        ])
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        texts = helpers.get_text_output(results)
        # Should print 1 2 3, not 10 20 30
        output = ' '.join(texts)
        assert '1' in output and '2' in output and '3' in output

    def test_local_string_variable(self, basic, helpers):
        """LOCAL works with string variables."""
        results = helpers.execute_program(basic, [
            '10 N$="HELLO"',
            '20 GOSUB 100',
            '30 PRINT N$',
            '40 END',
            '100 LOCAL N$',
            '110 N$="GOODBYE"',
            '120 RETURN',
        ])
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        texts = helpers.get_text_output(results)
        assert any('HELLO' in t for t in texts)

    def test_local_nested_gosub(self, basic, helpers):
        """LOCAL works correctly with nested GOSUB calls."""
        results = helpers.execute_program(basic, [
            '10 X=1',
            '20 GOSUB 100',
            '30 PRINT "FINAL";X',
            '40 END',
            '100 LOCAL X',
            '110 X=2',
            '120 GOSUB 200',
            '130 PRINT "MID";X',
            '140 RETURN',
            '200 LOCAL X',
            '210 X=3',
            '220 PRINT "INNER";X',
            '230 RETURN',
        ])
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        texts = helpers.get_text_output(results)
        output = ' '.join(texts)
        assert 'INNER 3' in output or 'INNER3' in output
        assert 'MID 2' in output or 'MID2' in output
        assert 'FINAL 1' in output or 'FINAL1' in output

    def test_local_without_gosub_errors(self, basic, helpers):
        """LOCAL outside GOSUB gives error."""
        results = helpers.execute_program(basic, [
            '10 LOCAL X',
            '20 END',
        ])
        errors = helpers.get_error_messages(results)
        assert any('LOCAL WITHOUT GOSUB' in e for e in errors)

    def test_local_undefined_var(self, basic, helpers):
        """LOCAL with undefined variable removes it on RETURN."""
        results = helpers.execute_program(basic, [
            '10 GOSUB 100',
            '20 PRINT Q',
            '30 END',
            '100 LOCAL Q',
            '110 Q=999',
            '120 RETURN',
        ])
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        texts = helpers.get_text_output(results)
        # Q was undefined before LOCAL, should be 0 (default) after RETURN
        assert any('0' in t for t in texts)

    def test_local_loop_var_isolation(self, basic, helpers):
        """LOCAL protects caller's loop variable from subroutine."""
        results = helpers.execute_program(basic, [
            '10 FOR I=1 TO 3',
            '20 GOSUB 100',
            '30 NEXT I',
            '40 PRINT "DONE"',
            '50 END',
            '100 LOCAL I',
            '110 FOR I=1 TO 5',
            '120 NEXT I',
            '130 RETURN',
        ])
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        texts = helpers.get_text_output(results)
        assert any('DONE' in t for t in texts)

    def test_local_no_args_errors(self, basic, helpers):
        """LOCAL without variable names gives error."""
        results = helpers.execute_program(basic, [
            '10 GOSUB 100',
            '20 END',
            '100 LOCAL',
            '110 RETURN',
        ])
        errors = helpers.get_error_messages(results)
        assert any('variable names' in e.lower() for e in errors)

    def test_local_in_direct_mode_errors(self, basic):
        """LOCAL in direct mode (no GOSUB active) gives error."""
        result = basic.process_command('LOCAL X')
        errors = [item['message'] for item in result if item.get('type') == 'error']
        assert any('LOCAL WITHOUT GOSUB' in e for e in errors)

    def test_local_with_on_gosub(self, basic, helpers):
        """LOCAL works correctly when called via ON...GOSUB."""
        results = helpers.execute_program(basic, [
            '10 X=42',
            '20 C=1',
            '30 ON C GOSUB 100',
            '40 PRINT X',
            '50 END',
            '100 LOCAL X',
            '110 X=99',
            '120 RETURN',
        ])
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        texts = helpers.get_text_output(results)
        assert any('42' in t for t in texts), f"X should be 42 after RETURN, got: {texts}"


class TestLocalWithIfReturn:
    """Test LOCAL + GOSUB + IF THEN GOSUB: RETURN patterns.

    These isolate the DoMoves/DoTurn bug where:
    - Outer sub has LOCAL + FOR loop + GOSUB to inner sub
    - Inner sub has IF cond THEN GOSUB worker: RETURN
    - The RETURN in the IF-expanded block may exit wrong GOSUB level
    """

    def test_if_then_gosub_return(self, basic, helpers):
        """IF cond THEN GOSUB sub: RETURN — basic pattern."""
        results = helpers.execute_program(basic, [
            '10 X=0',
            '20 GOSUB 100',
            '30 PRINT "X=";X',
            '40 END',
            '100 REM OUTER',
            '110 IF 1=1 THEN GOSUB 200: RETURN',
            '120 RETURN',
            '200 X=99',
            '210 RETURN',
        ])
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        texts = helpers.get_text_output(results)
        output = ' '.join(texts)
        assert '99' in output, f"X should be 99: {texts}"

    def test_if_then_gosub_return_false(self, basic, helpers):
        """IF false THEN GOSUB: RETURN — should fall through."""
        results = helpers.execute_program(basic, [
            '10 X=0',
            '20 GOSUB 100',
            '30 PRINT "X=";X',
            '40 END',
            '100 REM OUTER',
            '110 IF 1=0 THEN GOSUB 200: RETURN',
            '120 X=50',
            '130 RETURN',
            '200 X=99',
            '210 RETURN',
        ])
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        texts = helpers.get_text_output(results)
        output = ' '.join(texts)
        assert '50' in output, f"X should be 50: {texts}"

    def test_for_loop_with_if_gosub_return(self, basic, helpers):
        """FOR loop calling sub with IF THEN GOSUB: RETURN.
        This is the DoMoves/DoTurn pattern."""
        results = helpers.execute_program(basic, [
            '10 X=0',
            '20 GOSUB 100',
            '30 PRINT "X=";X',
            '40 END',
            '100 REM OUTER (LIKE DoMoves)',
            '110 FOR I=1 TO 3',
            '120   GOSUB 200',
            '130 NEXT I',
            '140 RETURN',
            '200 REM INNER (LIKE DoTurn)',
            '210 IF 1=1 THEN GOSUB 300: RETURN',
            '220 RETURN',
            '300 REM WORKER (LIKE Permute)',
            '310 X=X+1',
            '320 RETURN',
        ])
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        texts = helpers.get_text_output(results)
        output = ' '.join(texts)
        assert '3' in output, f"X should be 3 (called 3 times): {texts}"

    def test_local_for_loop_with_if_gosub_return(self, basic, helpers):
        """LOCAL + FOR loop + IF THEN GOSUB: RETURN.
        Exact DoMoves pattern with LOCAL variables."""
        results = helpers.execute_program(basic, [
            '10 X=0',
            '20 GOSUB 100',
            '30 PRINT "X=";X',
            '40 END',
            '100 REM OUTER (LIKE DoMoves)',
            '110 LOCAL I',
            '120 FOR I=1 TO 3',
            '130   GOSUB 200',
            '140 NEXT I',
            '150 RETURN',
            '200 REM INNER (LIKE DoTurn)',
            '210 IF 1=1 THEN GOSUB 300: RETURN',
            '220 RETURN',
            '300 REM WORKER (LIKE Permute)',
            '310 X=X+1',
            '320 RETURN',
        ])
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        texts = helpers.get_text_output(results)
        output = ' '.join(texts)
        assert '3' in output, f"X should be 3 (called 3 times): {texts}"

    def test_local_for_loop_if_gosub_return_with_string(self, basic, helpers):
        """Full DoMoves simulation: LOCAL string + FOR + IF GOSUB: RETURN."""
        results = helpers.execute_program(basic, [
            '10 X=0: MS$="ABC"',
            '20 GOSUB 100',
            '30 PRINT "X=";X',
            '40 END',
            '100 REM DoMoves sim',
            '110 LOCAL MI, MC$',
            '120 FOR MI=1 TO LEN(MS$)',
            '130   MC$=MID$(MS$,MI,1)',
            '140   GOSUB 200',
            '150 NEXT MI',
            '160 RETURN',
            '200 REM DoTurn sim',
            '210 IF 1=1 THEN GOSUB 300: RETURN',
            '220 RETURN',
            '300 REM Permute sim',
            '310 X=X+1',
            '320 RETURN',
        ])
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        texts = helpers.get_text_output(results)
        output = ' '.join(texts)
        assert '3' in output, f"X should be 3 (3 chars processed): {texts}"

    def test_if_variable_then_gosub_return(self, basic, helpers):
        """IF var=0 THEN GOSUB: RETURN — matching AN=0 pattern."""
        results = helpers.execute_program(basic, [
            '10 AN=0: X=0',
            '20 FOR I=1 TO 3',
            '30   GOSUB 100',
            '40 NEXT I',
            '50 PRINT "X=";X',
            '60 END',
            '100 REM DoTurn',
            '110 IF AN=0 THEN GOSUB 200: RETURN',
            '120 REM animated path',
            '130 GOSUB 200',
            '140 RETURN',
            '200 REM Permute',
            '210 X=X+1',
            '220 RETURN',
        ])
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        texts = helpers.get_text_output(results)
        output = ' '.join(texts)
        assert '3' in output, f"X should be 3: {texts}"
