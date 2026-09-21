"""Unit tests for single-line control-structure expansion (ast_converter.py).

expand_statements() turns one stored line into sublines, keeping each
statement's source text verbatim and expanding one-line IFs into blocks.
"""

import pytest

from emulator.ast_converter import (
    expand_statements, parse_and_convert_single_line, _split_else,
    _find_else_outside_quotes, starts_control_structure,
)

COMMANDS = frozenset({'PRINT', 'GOTO', 'GOSUB', 'CLS', 'SOUND', 'PSET', 'END',
                      'NEXT', 'FOR', 'IF', 'RETURN', 'LOCATE'})


def expand(code):
    return expand_statements(code, COMMANDS)


class TestPlainLines:
    def test_single_statement(self):
        assert expand('PRINT "HI"') == ['PRINT "HI"']

    def test_colon_split_keeps_source_text(self):
        assert expand('X=10-(5-2): PRINT X') == ['X=10-(5-2)', 'PRINT X']

    def test_colon_inside_string_not_split(self):
        assert expand('PRINT "A:B": X=1') == ['PRINT "A:B"', 'X=1']

    def test_rem_ends_line(self):
        assert expand('A=1: REM X: Y') == ['A=1', 'REM X: Y']

    def test_empty(self):
        assert expand('') == []


class TestIfExpansion:
    def test_multi_statement_body(self):
        assert expand('IF A=1 THEN PRINT "ONE": B=2') == \
            ['IF A=1 THEN', 'PRINT "ONE"', 'B=2', 'ENDIF']

    def test_else_branch(self):
        assert expand('IF X>5 THEN PRINT "BIG": ELSE PRINT "SMALL"') == \
            ['IF X>5 THEN', 'PRINT "BIG"', 'ELSE', 'PRINT "SMALL"', 'ENDIF']

    def test_crunched_then_after_string(self):
        assert expand('IF A$="X"THEN PRINT "1": PRINT "2"') == \
            ['IF A$="X" THEN', 'PRINT "1"', 'PRINT "2"', 'ENDIF']

    def test_crunched_then_after_number(self):
        assert expand('IF A=0THEN PRINT "X": PRINT "Y"')[0] == 'IF A=0 THEN'

    def test_then_inside_string_is_not_keyword(self):
        assert expand('IF A$="THEN" THEN PRINT "Z": X=1')[0] == 'IF A$="THEN" THEN'

    def test_else_inside_string_is_not_keyword(self):
        lines = expand('IF A THEN PRINT " ELSE ": X=1')
        assert 'ELSE' not in lines

    def test_else_inside_rem_is_not_keyword(self):
        lines = expand('IF A THEN PRINT 1: REM ELSE PRINT 2')
        assert 'ELSE' not in lines

    def test_rem_colon_in_body(self):
        assert expand('IF 1 THEN PRINT "A": REM X: PRINT "B"') == \
            ['IF 1 THEN', 'PRINT "A"', 'REM X: PRINT "B"', 'ENDIF']

    def test_mid_line_if_takes_rest_of_line(self):
        assert expand('GOSUB 100: IF C THEN A=1: B=2') == \
            ['GOSUB 100', 'IF C THEN', 'A=1', 'B=2', 'ENDIF']

    def test_bare_block_if_is_left_alone(self):
        assert expand('IF A=1 THEN') == ['IF A=1 THEN']

    def test_assignment_starting_with_if_letters_is_not_if(self):
        assert expand('IFLAG=1: PRINT IFLAG') == ['IFLAG=1', 'PRINT IFLAG']


class TestElseBinding:
    def test_else_binds_to_inner_if(self):
        assert expand('IF A THEN IF B THEN PRINT 1 ELSE PRINT 2') == \
            ['IF A THEN', 'IF B THEN', 'PRINT 1', 'ELSE', 'PRINT 2', 'ENDIF', 'ENDIF']

    def test_else_chain(self):
        lines = expand('IF A THEN PRINT 1 ELSE IF B THEN PRINT 2 ELSE PRINT 3')
        assert lines[:4] == ['IF A THEN', 'PRINT 1', 'ELSE', 'IF B THEN']

    def test_split_else_helper(self):
        assert _split_else('PRINT 1 ELSE PRINT 2') == ('PRINT 1', 'PRINT 2')
        assert _split_else('IF B THEN X ELSE Y') == ('IF B THEN X ELSE Y', None)
        assert _find_else_outside_quotes('PRINT " ELSE "') == -1


class TestImplicitGoto:
    @pytest.mark.parametrize('code,expected', [
        ('IF X=5 THEN 100', ['IF X=5 THEN GOTO 100']),
        ('IF X=5 GOTO 100', ['IF X=5 THEN GOTO 100']),
        ('IF X=5 THEN 100 ELSE 200', ['IF X=5 THEN GOTO 100 ELSE GOTO 200']),
        ('IF A=5 THEN A*B', ['IF A=5 THEN GOTO A*B']),
        ('IF A THEN Fin', ['IF A THEN GOTO Fin']),
    ])
    def test_jump_forms_stay_single_line(self, code, expected):
        assert expand(code) == expected

    @pytest.mark.parametrize('body', ['CLS', 'SOUND F, 1', 'PSET(10,10)', 'X=1', 'PRINT 1'])
    def test_statements_are_not_goto_targets(self, body):
        assert expand(f'IF A THEN {body}') == ['IF A THEN', body, 'ENDIF']


class TestLoops:
    def test_for_line_is_plain_split(self):
        assert expand('FOR I=1 TO 3: PRINT I: NEXT I: PRINT "DONE"') == \
            ['FOR I=1 TO 3', 'PRINT I', 'NEXT I', 'PRINT "DONE"']

    def test_nested_for_on_one_line(self):
        assert expand('FOR I=1 TO 2: FOR J=1 TO 2: PRINT I;J: NEXT J: NEXT I') == \
            ['FOR I=1 TO 2', 'FOR J=1 TO 2', 'PRINT I;J', 'NEXT J', 'NEXT I']

    def test_if_inside_one_line_loop_covers_only_its_statement(self):
        """BasiCoCo convention: the loop's NEXT is not swallowed by the IF."""
        assert expand('FOR J=1 TO 3: IF J=2 THEN PRINT "TWO": NEXT J') == \
            ['FOR J=1 TO 3', 'IF J=2 THEN', 'PRINT "TWO"', 'ENDIF', 'NEXT J']

    def test_open_for_without_next_lets_if_take_rest(self):
        assert expand('FOR J=1 TO 3: IF J=2 THEN PRINT "A": PRINT "B"') == \
            ['FOR J=1 TO 3', 'IF J=2 THEN', 'PRINT "A"', 'PRINT "B"', 'ENDIF']


class TestPublicEntryPoint:
    def test_non_control_returns_none(self):
        assert parse_and_convert_single_line('PRINT "HELLO"') is None
        assert parse_and_convert_single_line('') is None

    def test_loop_without_colon_returns_none(self):
        assert parse_and_convert_single_line('FOR I=1 TO 3') is None

    def test_starts_control_structure(self):
        assert starts_control_structure('DO')
        assert starts_control_structure('DO WHILE X')
        assert starts_control_structure('IF A THEN')
        assert not starts_control_structure('DOG=1')
        assert not starts_control_structure('IFLAG=1')

    # Cases ported from the removed StatementSplitter.has_control_keyword tests
    @pytest.mark.parametrize('code,expected', [
        ('IF X=1 THEN PRINT "Y"', True), ('FOR I = 1 TO 10', True),
        ('WHILE X < 5', True), ('DO: X=X+1: LOOP', True), ('DO WHILE X < 5', True),
        ('for i = 1 to 3', True), ('  IF X THEN Y', True),
        ('PRINT "HELLO"', False), ('DIM A(5)', False), ('', False),
    ])
    def test_control_structure_detection(self, code, expected):
        assert bool(starts_control_structure(code)) is expected
