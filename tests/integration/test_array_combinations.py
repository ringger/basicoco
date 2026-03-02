"""
Tests for array variables used in combination with other language features.

These tests verify that array elements work correctly as expressions in
contexts beyond basic assignment and PRINT — loops, conditions, nested
access, string functions, and self-modification patterns.
"""

import pytest


class TestNestedArrayAccess:
    """Using an array element as the index into another array."""

    def test_array_element_as_index(self, basic, helpers):
        program = [
            '10 DIM A(5), B(5)',
            '20 A(0) = 3',
            '30 B(3) = 99',
            '40 PRINT B(A(0))',
            '50 END',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert ' 99 ' in text

    def test_nested_array_index_in_assignment(self, basic, helpers):
        program = [
            '10 DIM IDX(3), V(5)',
            '20 IDX(1) = 4',
            '30 V(IDX(1)) = 77',
            '40 PRINT V(4)',
            '50 END',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert ' 77 ' in text

    def test_nested_array_chain(self, basic, helpers):
        """A(B(C(0))) — three levels of indirection."""
        program = [
            '10 DIM A(5), B(5), C(5)',
            '20 C(0) = 2',
            '30 B(2) = 4',
            '40 A(4) = 55',
            '50 PRINT A(B(C(0)))',
            '60 END',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert ' 55 ' in text

    def test_same_array_nested(self, basic, helpers):
        """A(A(0)) — array used as its own index."""
        program = [
            '10 DIM A(5)',
            '20 A(0) = 3',
            '30 A(3) = 42',
            '40 PRINT A(A(0))',
            '50 END',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert ' 42 ' in text


class TestArraysInWhileDoConditions:
    """Array elements used in WHILE and DO loop conditions."""

    def test_while_condition_with_array(self, basic, helpers):
        """WHILE loop condition that reads from an array element."""
        program = [
            '10 DIM A(5)',
            '20 A(0) = 1',
            '30 I = 0',
            '40 WHILE A(I) < 100',
            '50   I = I + 1',
            '60   A(I) = A(I - 1) * 3',
            '70 WEND',
            '80 PRINT "STOPPED AT"; A(I)',
            '90 END',
        ]
        # A(0)=1, A(1)=3, A(2)=9, A(3)=27, A(4)=81, A(5)=243 → stops
        results = helpers.execute_program(basic, program)
        text = ' '.join(helpers.get_text_output(results))
        assert '243' in text

    def test_do_loop_while_with_array(self, basic, helpers):
        program = [
            '10 DIM S(3)',
            '20 I = 0',
            '30 DO',
            '40   S(I) = I * 10',
            '50   I = I + 1',
            '60 LOOP WHILE I <= 2',
            '70 PRINT S(0); S(1); S(2)',
            '80 END',
        ]
        results = helpers.execute_program(basic, program)
        text = ' '.join(helpers.get_text_output(results))
        assert '0' in text
        assert '10' in text
        assert '20' in text

    def test_while_comparing_two_array_elements(self, basic, helpers):
        program = [
            '10 DIM A(5)',
            '20 A(0) = 1',
            '30 A(1) = 100',
            '40 WHILE A(0) < A(1)',
            '50   A(0) = A(0) * 2',
            '60 WEND',
            '70 PRINT A(0)',
            '80 END',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert ' 128 ' in text


class TestArraysInOnGotoGosub:
    """Array elements used in ON...GOTO and ON...GOSUB."""

    def test_on_goto_with_array_value(self, basic, helpers):
        program = [
            '10 DIM A(3)',
            '20 A(1) = 2',
            '30 ON A(1) GOTO 100, 200, 300',
            '40 PRINT "FELL THROUGH"',
            '50 END',
            '100 PRINT "FIRST"',
            '110 END',
            '200 PRINT "SECOND"',
            '210 END',
            '300 PRINT "THIRD"',
            '310 END',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert 'SECOND' in text
        assert 'FIRST' not in text
        assert 'THIRD' not in text

    def test_on_gosub_with_array_value(self, basic, helpers):
        program = [
            '10 DIM A(3)',
            '20 A(0) = 3',
            '30 ON A(0) GOSUB 100, 200, 300',
            '40 PRINT "BACK"',
            '50 END',
            '100 PRINT "SUB1"',
            '110 RETURN',
            '200 PRINT "SUB2"',
            '210 RETURN',
            '300 PRINT "SUB3"',
            '310 RETURN',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert 'SUB3' in text
        assert 'BACK' in text
        assert 'SUB1' not in text

    def test_on_goto_with_array_expression(self, basic, helpers):
        program = [
            '10 DIM A(3)',
            '20 A(2) = 10',
            '30 ON A(2) / 10 GOTO 100, 200',
            '40 PRINT "FELL THROUGH"',
            '50 END',
            '100 PRINT "FIRST"',
            '110 END',
            '200 PRINT "SECOND"',
            '210 END',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert 'FIRST' in text


class TestArraySelfModification:
    """Patterns where array elements are read and written in the same statement or loop."""

    def test_increment_array_element(self, basic, helpers):
        program = [
            '10 DIM A(5)',
            '20 A(3) = 10',
            '30 A(3) = A(3) + 1',
            '40 PRINT A(3)',
            '50 END',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert ' 11 ' in text

    def test_accumulate_in_loop(self, basic, helpers):
        program = [
            '10 DIM A(5)',
            '20 A(0) = 1',
            '30 FOR I = 1 TO 5',
            '40   A(I) = A(I - 1) * 2',
            '50 NEXT I',
            '60 PRINT A(5)',
            '70 END',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert ' 32 ' in text

    def test_swap_two_elements(self, basic, helpers):
        program = [
            '10 DIM A(5)',
            '20 A(1) = 10',
            '30 A(2) = 20',
            '40 T = A(1)',
            '50 A(1) = A(2)',
            '60 A(2) = T',
            '70 PRINT A(1); A(2)',
            '80 END',
        ]
        results = helpers.execute_program(basic, program)
        text = ' '.join(helpers.get_text_output(results))
        assert '20' in text
        assert '10' in text

    def test_running_sum_in_array(self, basic, helpers):
        program = [
            '10 DIM SUM(5)',
            '20 SUM(0) = 0',
            '30 FOR I = 1 TO 5',
            '40   SUM(I) = SUM(I - 1) + I',
            '50 NEXT I',
            '60 PRINT SUM(5)',
            '70 END',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert ' 15 ' in text


class TestStringArraysWithFunctions:
    """String array elements used with string functions."""

    def test_mid_with_string_array(self, basic, helpers):
        program = [
            '10 DIM N$(3)',
            '20 N$(1) = "HELLO WORLD"',
            '30 PRINT MID$(N$(1), 7, 5)',
            '40 END',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert 'WORLD' in text

    def test_left_right_with_string_array(self, basic, helpers):
        program = [
            '10 DIM W$(3)',
            '20 W$(0) = "ABCDEF"',
            '30 PRINT LEFT$(W$(0), 3)',
            '40 PRINT RIGHT$(W$(0), 3)',
            '50 END',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert 'ABC' in text
        assert 'DEF' in text

    def test_len_with_string_array(self, basic, helpers):
        program = [
            '10 DIM S$(3)',
            '20 S$(0) = "HI"',
            '30 S$(1) = "HELLO"',
            '40 S$(2) = "GREETINGS"',
            '50 FOR I = 0 TO 2',
            '60   PRINT LEN(S$(I))',
            '70 NEXT I',
            '80 END',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert ' 2 ' in text
        assert ' 5 ' in text
        assert ' 9 ' in text

    def test_string_array_concatenation(self, basic, helpers):
        program = [
            '10 DIM A$(3), B$(3)',
            '20 A$(1) = "HELLO"',
            '30 B$(1) = " WORLD"',
            '40 C$ = A$(1) + B$(1)',
            '50 PRINT C$',
            '60 END',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert 'HELLO WORLD' in text

    def test_asc_chr_with_string_array(self, basic, helpers):
        program = [
            '10 DIM C$(3)',
            '20 C$(0) = "A"',
            '30 PRINT ASC(C$(0))',
            '40 PRINT CHR$(ASC(C$(0)) + 1)',
            '50 END',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert ' 65 ' in text
        assert 'B' in text

    def test_val_str_with_arrays(self, basic, helpers):
        program = [
            '10 DIM S$(3), N(3)',
            '20 S$(0) = "42"',
            '30 N(0) = VAL(S$(0))',
            '40 PRINT N(0) + 8',
            '50 PRINT STR$(N(0))',
            '60 END',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert ' 50 ' in text


class TestArraysInIfConditions:
    """Array elements in complex IF conditions."""

    def test_if_comparing_two_array_elements(self, basic, helpers):
        program = [
            '10 DIM A(3)',
            '20 A(1) = 5',
            '30 A(2) = 10',
            '40 IF A(1) < A(2) THEN PRINT "CORRECT"',
            '50 END',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert 'CORRECT' in text

    def test_if_with_and_on_arrays(self, basic, helpers):
        """AND with array elements in program mode (multi-line IF expansion)."""
        program = [
            '10 DIM A(5)',
            '20 A(1) = 5',
            '30 A(2) = 10',
            '40 A(3) = 15',
            '50 IF A(1) < A(2) AND A(2) < A(3) THEN PRINT "SORTED"',
            '60 END',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert 'SORTED' in text

    def test_if_with_or_on_arrays(self, basic, helpers):
        """OR with array elements in program mode (multi-line IF expansion)."""
        program = [
            '10 DIM A(5)',
            '20 A(1) = 5',
            '30 A(2) = 10',
            '40 A(3) = 15',
            '50 IF A(1) > A(2) OR A(3) > 100 THEN PRINT "BAD"',
            '60 PRINT "DONE"',
            '70 END',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert 'BAD' not in text
        assert 'DONE' in text

    def test_if_else_with_array_condition(self, basic, helpers):
        program = [
            '10 DIM SCORE(3)',
            '20 SCORE(0) = 85',
            '30 IF SCORE(0) >= 90 THEN',
            '40   PRINT "A"',
            '50 ELSE',
            '60   PRINT "B"',
            '70 ENDIF',
            '80 END',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert 'B' in text
        assert 'A' not in text


class TestMultiDimensionalArrays:
    """Multi-dimensional arrays in various contexts."""

    def test_2d_array_in_nested_loops(self, basic, helpers):
        program = [
            '10 DIM M(3, 3)',
            '20 FOR R = 0 TO 2',
            '30   FOR C = 0 TO 2',
            '40     M(R, C) = R * 3 + C',
            '50   NEXT C',
            '60 NEXT R',
            '70 PRINT M(1, 2)',
            '80 PRINT M(2, 1)',
            '90 END',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert ' 5 ' in text   # 1*3 + 2
        assert ' 7 ' in text   # 2*3 + 1

    def test_2d_array_with_variable_indices(self, basic, helpers):
        program = [
            '10 DIM GRID(5, 5)',
            '20 R = 2',
            '30 C = 3',
            '40 GRID(R, C) = 99',
            '50 PRINT GRID(2, 3)',
            '60 END',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert ' 99 ' in text

    def test_2d_string_array(self, basic, helpers):
        program = [
            '10 DIM T$(2, 2)',
            '20 T$(0, 0) = "X"',
            '30 T$(1, 1) = "O"',
            '40 PRINT T$(0, 0); T$(1, 1)',
            '50 END',
        ]
        results = helpers.execute_program(basic, program)
        text = ' '.join(helpers.get_text_output(results))
        assert 'X' in text
        assert 'O' in text
