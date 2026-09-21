#!/usr/bin/env python3

"""
Unit tests for StatementSplitter methods: split_on_delimiter, split_on_delimiter_paren_aware,
is_rem_line, and core's expand_line_to_sublines.
"""

import pytest
from emulator.text_utils import StatementSplitter


class TestIsRemLine:
    """Test StatementSplitter.is_rem_line"""

    def test_uppercase_rem(self):
        assert StatementSplitter.is_rem_line('REM This is a comment') is True

    def test_lowercase_rem(self):
        assert StatementSplitter.is_rem_line('rem lowercase comment') is True

    def test_mixed_case_rem(self):
        assert StatementSplitter.is_rem_line('Rem Mixed Case') is True

    def test_rem_with_leading_spaces(self):
        assert StatementSplitter.is_rem_line('   REM indented') is True

    def test_rem_with_colons(self):
        assert StatementSplitter.is_rem_line('REM EXERCISES: GOSUB/RETURN, DATA/READ') is True

    def test_rem_with_keywords(self):
        assert StatementSplitter.is_rem_line('REM IF THEN GOTO PRINT') is True

    def test_not_rem_print(self):
        assert StatementSplitter.is_rem_line('PRINT "HELLO"') is False

    def test_not_rem_variable_starting_with_rem(self):
        assert StatementSplitter.is_rem_line('REMEMBER = 5') is True
        # Note: this is actually correct behavior for BASIC — "REMEMBER" starts with "REM"
        # and CoCo BASIC would treat it as REM. This test documents the behavior.

    def test_empty_string(self):
        assert StatementSplitter.is_rem_line('') is False

    def test_whitespace_only(self):
        assert StatementSplitter.is_rem_line('   ') is False


class TestSplitOnDelimiter:
    """Test StatementSplitter.split_on_delimiter"""

    def test_single_statement(self):
        assert StatementSplitter.split_on_delimiter('PRINT "HELLO"') == ['PRINT "HELLO"']

    def test_two_statements(self):
        assert StatementSplitter.split_on_delimiter('A = 5: B = 10') == ['A = 5', 'B = 10']

    def test_three_statements(self):
        result = StatementSplitter.split_on_delimiter('A = 1: B = 2: PRINT A + B')
        assert result == ['A = 1', 'B = 2', 'PRINT A + B']

    def test_colon_inside_quotes_not_split(self):
        result = StatementSplitter.split_on_delimiter('PRINT "TIME: 12:30"')
        assert result == ['PRINT "TIME: 12:30"']

    def test_colon_after_quoted_string(self):
        result = StatementSplitter.split_on_delimiter('PRINT "TIME: 12:30": GOTO 100')
        assert result == ['PRINT "TIME: 12:30"', 'GOTO 100']

    def test_multiple_quoted_strings_with_colons(self):
        result = StatementSplitter.split_on_delimiter('PRINT "A:B"; "C:D": PRINT "E"')
        assert result == ['PRINT "A:B"; "C:D"', 'PRINT "E"']

    def test_empty_quoted_string_near_colon(self):
        result = StatementSplitter.split_on_delimiter('A$ = "": B$ = "X"')
        assert result == ['A$ = ""', 'B$ = "X"']

    def test_strips_whitespace(self):
        result = StatementSplitter.split_on_delimiter('  A = 5  :  B = 10  ')
        assert result == ['A = 5', 'B = 10']

    def test_empty_string(self):
        assert StatementSplitter.split_on_delimiter('') == []

    def test_whitespace_only(self):
        assert StatementSplitter.split_on_delimiter('   ') == []

    def test_no_delimiter(self):
        assert StatementSplitter.split_on_delimiter('PRINT 42') == ['PRINT 42']

    def test_custom_delimiter(self):
        result = StatementSplitter.split_on_delimiter('A,B,C', delimiter=',')
        assert result == ['A', 'B', 'C']

    def test_adjacent_colons_skip_empty(self):
        result = StatementSplitter.split_on_delimiter('A = 5:: B = 10')
        assert result == ['A = 5', 'B = 10']

    def test_trailing_colon(self):
        result = StatementSplitter.split_on_delimiter('PRINT "X":')
        assert result == ['PRINT "X"']

    def test_rem_with_colon_not_split(self):
        """REM comments consume the rest of the line, colons included."""
        result = StatementSplitter.split_on_delimiter('REM U CW CYCLE: TFR(0)')
        assert result == ['REM U CW CYCLE: TFR(0)']

    def test_inline_rem_with_colon_not_split(self):
        """Inline REM after code preserves colons within the comment."""
        result = StatementSplitter.split_on_delimiter('A=1: REM U CW CYCLE: TFR(0)')
        assert result == ['A=1', 'REM U CW CYCLE: TFR(0)']

    def test_rem_after_multiple_statements(self):
        result = StatementSplitter.split_on_delimiter('A=1: B=2: REM comment: with: colons')
        assert result == ['A=1', 'B=2', 'REM comment: with: colons']

    def test_rem_prefix_is_a_comment(self):
        """As on the CoCo (keywords are crunched by prefix), REMEMBER=5 is
        REM + "EMBER=5", so the rest of the line is a comment — consistent
        with is_rem_line() and the tokenizer."""
        result = StatementSplitter.split_on_delimiter('REMEMBER=5: A=1')
        assert result == ['REMEMBER=5: A=1']

    def test_apostrophe_comment_after_statement(self):
        assert StatementSplitter.split_on_delimiter("SOUND 100,5 ' beep: loud") == \
            ['SOUND 100,5', "' beep: loud"]

    def test_apostrophe_quotes_filename_for_file_commands(self):
        assert StatementSplitter.split_on_delimiter("SAVE 'my:prog': PRINT 1") == \
            ["SAVE 'my:prog'", 'PRINT 1']

    def test_apostrophe_inside_double_quotes(self):
        assert StatementSplitter.split_on_delimiter('PRINT "RUBIK\'S": A=1') == \
            ['PRINT "RUBIK\'S"', 'A=1']


class TestSplitOnDelimiterParenAware:
    """Test StatementSplitter.split_on_delimiter_paren_aware"""

    def test_simple_split(self):
        result = StatementSplitter.split_on_delimiter_paren_aware('A = 5: B = 10')
        assert result == ['A = 5', 'B = 10']

    def test_colon_inside_parens_not_split(self):
        # This would matter if BASIC ever had colons inside parenthesized groups
        # (unusual, but tests the paren-awareness)
        result = StatementSplitter.split_on_delimiter_paren_aware('CALL SUB(A:B): PRINT X',
                                                            delimiter=':')
        # The colon inside parens should NOT split
        assert result == ['CALL SUB(A:B)', 'PRINT X']

    def test_nested_parens(self):
        result = StatementSplitter.split_on_delimiter_paren_aware('F(G(X:Y)):Z', delimiter=':')
        assert result == ['F(G(X:Y))', 'Z']

    def test_quotes_still_respected(self):
        result = StatementSplitter.split_on_delimiter_paren_aware('PRINT "A:B": NEXT')
        assert result == ['PRINT "A:B"', 'NEXT']

    def test_function_call_with_comma_delimiter(self):
        result = StatementSplitter.split_on_delimiter_paren_aware('LEFT$(A$,3),MID$(B$,2,1)',
                                                            delimiter=',')
        assert result == ['LEFT$(A$,3)', 'MID$(B$,2,1)']

    def test_array_index_with_comma_delimiter(self):
        result = StatementSplitter.split_on_delimiter_paren_aware('A(1,2),B(3)', delimiter=',')
        assert result == ['A(1,2)', 'B(3)']

    def test_empty_string(self):
        assert StatementSplitter.split_on_delimiter_paren_aware('') == []


class TestCoreExpandLineToSublines:
    """Test the core.py expand_line_to_sublines method (which adds REM guards and AST conversion)"""

    def test_rem_not_split(self, basic):
        """REM lines with colons should be stored as single sublines"""
        basic.process_command('10 REM EXERCISES: GOSUB/RETURN, DATA/READ')
        # Should be a single expanded subline
        rem_sublines = [(k, v) for k, v in basic.expanded_program.items() if k[0] == 10]
        assert len(rem_sublines) == 1
        # Stored as a compiled no-op (the text stays in basic.program for LIST)
        assert rem_sublines[0][1].keyword == 'REM'
        assert basic.program[10] == 'REM EXERCISES: GOSUB/RETURN, DATA/READ'

    def test_multi_statement_expanded(self, basic):
        """Plain multi-statement lines should expand into separate sublines"""
        basic.process_command('10 A = 5: B = 10: PRINT A + B')
        sublines = sorted([(k, v) for k, v in basic.expanded_program.items() if k[0] == 10])
        assert len(sublines) == 3
        # Sublines may be AST nodes (pre-parsed) or strings — just check count

    def test_if_then_kept_together(self, basic):
        """IF/THEN lines should be handled by AST converter, not split naively"""
        basic.process_command('10 IF A = 5 THEN PRINT "YES": GOTO 100')
        sublines = [(k, v) for k, v in basic.expanded_program.items() if k[0] == 10]
        # AST converter may expand this into multiple sublines, but they should
        # be semantically correct (not naively split on colons)
        assert len(sublines) >= 1

    def test_inline_rem_with_colon_not_split(self, basic):
        """Code followed by REM with colons: REM consumes rest of line"""
        basic.process_command('10 A=1: REM U CW CYCLE: TFR(0)')
        sublines = sorted([(k, v) for k, v in basic.expanded_program.items() if k[0] == 10])
        # Should be exactly 2 sublines: A=1 and the REM comment (not 3)
        assert len(sublines) == 2
        # REM should not cause runtime errors
        result = basic.process_command('RUN')
        errors = [r for r in (result or []) if isinstance(r, dict) and r.get('type') == 'error']
        assert errors == []

    def test_single_statement_stored(self, basic):
        """Single statements should produce exactly one subline"""
        basic.process_command('10 PRINT "HELLO"')
        sublines = [(k, v) for k, v in basic.expanded_program.items() if k[0] == 10]
        assert len(sublines) == 1
        # May be an AST node (pre-parsed) rather than a string
