#!/usr/bin/env python3

"""
Tests for GOSUB + IF THEN on the same line.

Regression tests for the bug where `GOSUB Sub: IF cond THEN A=1: B=2`
split into 3 sublines, causing B=2 to execute unconditionally.
The fix detects mid-line IF/THEN and routes it through AST conversion.
"""

import pytest


class TestGosubIfSameLine:
    """Test that GOSUB + IF THEN on the same line splits correctly."""

    def test_gosub_if_then_true_branch(self, basic, helpers):
        """GOSUB Sub: IF 1=1 THEN A=1: B=2 — both assignments should execute."""
        basic.process_command('10 GOSUB 100: IF 1=1 THEN A=1: B=2')
        basic.process_command('20 END')
        basic.process_command('100 RETURN')
        results = basic.process_command('RUN')
        helpers.assert_variable_equals(basic, 'A', 1)
        helpers.assert_variable_equals(basic, 'B', 2)

    def test_gosub_if_then_false_branch(self, basic, helpers):
        """GOSUB Sub: IF 1=0 THEN A=1: B=2 — neither assignment should execute."""
        basic.process_command('10 GOSUB 100: IF 1=0 THEN A=1: B=2')
        basic.process_command('20 END')
        basic.process_command('100 RETURN')
        results = basic.process_command('RUN')
        assert basic.variables.get('A') is None
        assert basic.variables.get('B') is None

    def test_gosub_if_then_else(self, basic, helpers):
        """GOSUB Sub: IF 1=0 THEN A=1 ELSE A=2 — ELSE branch should execute."""
        basic.process_command('10 GOSUB 100: IF 1=0 THEN A=1 ELSE A=2')
        basic.process_command('20 END')
        basic.process_command('100 RETURN')
        results = basic.process_command('RUN')
        helpers.assert_variable_equals(basic, 'A', 2)

    def test_gosub_if_then_else_multi_stmt(self, basic, helpers):
        """GOSUB Sub: IF 1=0 THEN A=1: B=2 ELSE A=3: B=4 — ELSE body executes."""
        basic.process_command('10 GOSUB 100: IF 1=0 THEN A=1: B=2 ELSE A=3: B=4')
        basic.process_command('20 END')
        basic.process_command('100 RETURN')
        results = basic.process_command('RUN')
        helpers.assert_variable_equals(basic, 'A', 3)
        helpers.assert_variable_equals(basic, 'B', 4)

    def test_multiple_stmts_before_if(self, basic, helpers):
        """A=5: GOSUB Sub: IF 1=0 THEN A=1 — A should remain 5."""
        basic.process_command('10 A=5: GOSUB 100: IF 1=0 THEN A=1')
        basic.process_command('20 END')
        basic.process_command('100 RETURN')
        results = basic.process_command('RUN')
        helpers.assert_variable_equals(basic, 'A', 5)

    def test_print_before_if(self, basic, helpers):
        """PRINT "HI": IF 1=0 THEN A=1: B=2 — neither A nor B should be set."""
        basic.process_command('10 PRINT "HI": IF 1=0 THEN A=1: B=2')
        basic.process_command('20 END')
        results = basic.process_command('RUN')
        text = helpers.get_text_output(results)
        assert any('HI' in t for t in text)
        assert basic.variables.get('A') is None
        assert basic.variables.get('B') is None

    def test_subline_count_gosub_if(self, basic):
        """Verify subline structure: GOSUB + IF THEN body should use AST conversion."""
        basic.process_command('10 GOSUB 100: IF 1=1 THEN A=1: B=2')
        sublines = [(k, v) for k, v in basic.expanded_program.items() if k[0] == 10]
        # Should have: GOSUB 100, IF 1=1 THEN, A=1, B=2, ENDIF
        # (not just 3 flat sublines)
        assert len(sublines) >= 4, f"Expected >= 4 sublines, got {len(sublines)}: {sublines}"

    def test_no_if_still_splits_normally(self, basic, helpers):
        """GOSUB Sub: A=1: B=2 (no IF) — should still split on all colons."""
        basic.process_command('10 GOSUB 100: A=1: B=2')
        basic.process_command('20 END')
        basic.process_command('100 RETURN')
        results = basic.process_command('RUN')
        helpers.assert_variable_equals(basic, 'A', 1)
        helpers.assert_variable_equals(basic, 'B', 2)
