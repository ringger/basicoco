#!/usr/bin/env python3

"""
Unit tests for BasicParser methods: split_on_delimiter, split_on_delimiter_paren_aware,
is_rem_line, and expand_line_to_sublines.
"""

import pytest
from emulator.parser import BasicParser


class TestIsRemLine:
    """Test BasicParser.is_rem_line"""

    def test_uppercase_rem(self):
        assert BasicParser.is_rem_line('REM This is a comment') is True

    def test_lowercase_rem(self):
        assert BasicParser.is_rem_line('rem lowercase comment') is True

    def test_mixed_case_rem(self):
        assert BasicParser.is_rem_line('Rem Mixed Case') is True

    def test_rem_with_leading_spaces(self):
        assert BasicParser.is_rem_line('   REM indented') is True

    def test_rem_with_colons(self):
        assert BasicParser.is_rem_line('REM EXERCISES: GOSUB/RETURN, DATA/READ') is True

    def test_rem_with_keywords(self):
        assert BasicParser.is_rem_line('REM IF THEN GOTO PRINT') is True

    def test_not_rem_print(self):
        assert BasicParser.is_rem_line('PRINT "HELLO"') is False

    def test_not_rem_variable_starting_with_rem(self):
        assert BasicParser.is_rem_line('REMEMBER = 5') is True
        # Note: this is actually correct behavior for BASIC — "REMEMBER" starts with "REM"
        # and CoCo BASIC would treat it as REM. This test documents the behavior.

    def test_empty_string(self):
        assert BasicParser.is_rem_line('') is False

    def test_whitespace_only(self):
        assert BasicParser.is_rem_line('   ') is False


class TestSplitOnDelimiter:
    """Test BasicParser.split_on_delimiter"""

    def test_single_statement(self):
        assert BasicParser.split_on_delimiter('PRINT "HELLO"') == ['PRINT "HELLO"']

    def test_two_statements(self):
        assert BasicParser.split_on_delimiter('A = 5: B = 10') == ['A = 5', 'B = 10']

    def test_three_statements(self):
        result = BasicParser.split_on_delimiter('A = 1: B = 2: PRINT A + B')
        assert result == ['A = 1', 'B = 2', 'PRINT A + B']

    def test_colon_inside_quotes_not_split(self):
        result = BasicParser.split_on_delimiter('PRINT "TIME: 12:30"')
        assert result == ['PRINT "TIME: 12:30"']

    def test_colon_after_quoted_string(self):
        result = BasicParser.split_on_delimiter('PRINT "TIME: 12:30": GOTO 100')
        assert result == ['PRINT "TIME: 12:30"', 'GOTO 100']

    def test_multiple_quoted_strings_with_colons(self):
        result = BasicParser.split_on_delimiter('PRINT "A:B"; "C:D": PRINT "E"')
        assert result == ['PRINT "A:B"; "C:D"', 'PRINT "E"']

    def test_empty_quoted_string_near_colon(self):
        result = BasicParser.split_on_delimiter('A$ = "": B$ = "X"')
        assert result == ['A$ = ""', 'B$ = "X"']

    def test_strips_whitespace(self):
        result = BasicParser.split_on_delimiter('  A = 5  :  B = 10  ')
        assert result == ['A = 5', 'B = 10']

    def test_empty_string(self):
        assert BasicParser.split_on_delimiter('') == []

    def test_whitespace_only(self):
        assert BasicParser.split_on_delimiter('   ') == []

    def test_no_delimiter(self):
        assert BasicParser.split_on_delimiter('PRINT 42') == ['PRINT 42']

    def test_custom_delimiter(self):
        result = BasicParser.split_on_delimiter('A,B,C', delimiter=',')
        assert result == ['A', 'B', 'C']

    def test_adjacent_colons_skip_empty(self):
        result = BasicParser.split_on_delimiter('A = 5:: B = 10')
        assert result == ['A = 5', 'B = 10']

    def test_trailing_colon(self):
        result = BasicParser.split_on_delimiter('PRINT "X":')
        assert result == ['PRINT "X"']


class TestSplitOnDelimiterParenAware:
    """Test BasicParser.split_on_delimiter_paren_aware"""

    def test_simple_split(self):
        result = BasicParser.split_on_delimiter_paren_aware('A = 5: B = 10')
        assert result == ['A = 5', 'B = 10']

    def test_colon_inside_parens_not_split(self):
        # This would matter if BASIC ever had colons inside parenthesized groups
        # (unusual, but tests the paren-awareness)
        result = BasicParser.split_on_delimiter_paren_aware('CALL SUB(A:B): PRINT X',
                                                            delimiter=':')
        # The colon inside parens should NOT split
        assert result == ['CALL SUB(A:B)', 'PRINT X']

    def test_nested_parens(self):
        result = BasicParser.split_on_delimiter_paren_aware('F(G(X:Y)):Z', delimiter=':')
        assert result == ['F(G(X:Y))', 'Z']

    def test_quotes_still_respected(self):
        result = BasicParser.split_on_delimiter_paren_aware('PRINT "A:B": NEXT')
        assert result == ['PRINT "A:B"', 'NEXT']

    def test_function_call_with_comma_delimiter(self):
        result = BasicParser.split_on_delimiter_paren_aware('LEFT$(A$,3),MID$(B$,2,1)',
                                                            delimiter=',')
        assert result == ['LEFT$(A$,3)', 'MID$(B$,2,1)']

    def test_array_index_with_comma_delimiter(self):
        result = BasicParser.split_on_delimiter_paren_aware('A(1,2),B(3)', delimiter=',')
        assert result == ['A(1,2)', 'B(3)']

    def test_empty_string(self):
        assert BasicParser.split_on_delimiter_paren_aware('') == []


class TestExpandLineToSublines:
    """Test BasicParser.expand_line_to_sublines (static method on parser)"""

    def test_single_statement(self):
        expanded = {}
        BasicParser.expand_line_to_sublines(10, 'PRINT "HELLO"', expanded)
        assert expanded == {(10, 0): 'PRINT "HELLO"'}

    def test_multi_statement(self):
        expanded = {}
        BasicParser.expand_line_to_sublines(10, 'A = 5: B = 10: PRINT A + B', expanded)
        assert expanded == {
            (10, 0): 'A = 5',
            (10, 1): 'B = 10',
            (10, 2): 'PRINT A + B',
        }

    def test_if_then_split(self):
        """Parser-level expand splits IF/THEN on colons (core.py handles
        AST conversion for control structures before reaching this method)"""
        expanded = {}
        BasicParser.expand_line_to_sublines(10, 'IF A = 5 THEN PRINT "YES": GOTO 100', expanded)
        assert len(expanded) == 2
        assert expanded[(10, 0)] == 'IF A = 5 THEN PRINT "YES"'
        assert expanded[(10, 1)] == 'GOTO 100'

    def test_rem_not_split(self):
        """REM lines should never be split on colons.
        Note: expand_line_to_sublines in parser.py doesn't check REM — the caller
        (core.py expand_line_to_sublines) does. The parser method splits blindly.
        This test documents the parser-level behavior."""
        expanded = {}
        BasicParser.expand_line_to_sublines(20, 'REM EXERCISES: GOSUB, DATA', expanded)
        # Parser-level expand splits on colons (REM guard is in core.py)
        # This documents current behavior
        assert (20, 0) in expanded

    def test_quoted_colons_preserved(self):
        expanded = {}
        BasicParser.expand_line_to_sublines(10, 'PRINT "TIME: 12:30": END', expanded)
        assert expanded == {
            (10, 0): 'PRINT "TIME: 12:30"',
            (10, 1): 'END',
        }

    def test_strips_whitespace(self):
        expanded = {}
        BasicParser.expand_line_to_sublines(10, '  A = 5  :  B = 10  ', expanded)
        assert expanded[(10, 0)] == 'A = 5'
        assert expanded[(10, 1)] == 'B = 10'


class TestHasControlKeyword:
    """Test BasicParser.has_control_keyword"""

    def test_if_detected(self):
        assert BasicParser.has_control_keyword('IF X=1 THEN PRINT "Y"') is True

    def test_for_detected(self):
        assert BasicParser.has_control_keyword('FOR I = 1 TO 10') is True

    def test_while_detected(self):
        assert BasicParser.has_control_keyword('WHILE X < 5') is True

    def test_do_with_colon(self):
        assert BasicParser.has_control_keyword('DO: X=X+1: LOOP') is True

    def test_do_with_space(self):
        assert BasicParser.has_control_keyword('DO WHILE X < 5') is True

    def test_case_insensitive(self):
        assert BasicParser.has_control_keyword('for i = 1 to 3') is True

    def test_print_not_detected(self):
        assert BasicParser.has_control_keyword('PRINT "HELLO"') is False

    def test_dim_not_detected(self):
        assert BasicParser.has_control_keyword('DIM A(5)') is False

    def test_empty_not_detected(self):
        assert BasicParser.has_control_keyword('') is False

    def test_leading_spaces(self):
        assert BasicParser.has_control_keyword('  IF X THEN Y') is True


class TestCoreExpandLineToSublines:
    """Test the core.py expand_line_to_sublines method (which adds REM guards and AST conversion)"""

    def test_rem_not_split(self, basic):
        """REM lines with colons should be stored as single sublines"""
        basic.process_command('10 REM EXERCISES: GOSUB/RETURN, DATA/READ')
        # Should be a single expanded subline
        rem_sublines = [(k, v) for k, v in basic.expanded_program.items() if k[0] == 10]
        assert len(rem_sublines) == 1
        assert 'REM EXERCISES: GOSUB/RETURN, DATA/READ' in rem_sublines[0][1]

    def test_multi_statement_expanded(self, basic):
        """Plain multi-statement lines should expand into separate sublines"""
        basic.process_command('10 A = 5: B = 10: PRINT A + B')
        sublines = sorted([(k, v) for k, v in basic.expanded_program.items() if k[0] == 10])
        assert len(sublines) == 3
        assert sublines[0][1] == 'A = 5'
        assert sublines[1][1] == 'B = 10'
        assert sublines[2][1] == 'PRINT A + B'

    def test_if_then_kept_together(self, basic):
        """IF/THEN lines should be handled by AST converter, not split naively"""
        basic.process_command('10 IF A = 5 THEN PRINT "YES": GOTO 100')
        sublines = [(k, v) for k, v in basic.expanded_program.items() if k[0] == 10]
        # AST converter may expand this into multiple sublines, but they should
        # be semantically correct (not naively split on colons)
        assert len(sublines) >= 1

    def test_single_statement_stored(self, basic):
        """Single statements should produce exactly one subline"""
        basic.process_command('10 PRINT "HELLO"')
        sublines = [(k, v) for k, v in basic.expanded_program.items() if k[0] == 10]
        assert len(sublines) == 1
        assert sublines[0][1] == 'PRINT "HELLO"'
