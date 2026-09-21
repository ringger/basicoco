"""Error paths and small branches the audit changed that no test reached
(#81 coverage pass; found with tools/diff_coverage.py)."""

import pytest


def errors(helpers, result):
    return '\n'.join(helpers.get_error_messages(result))


def run(basic, helpers, lines):
    return helpers.execute_program(basic, lines)


# -- expressions and the tokenizer -------------------------------------------

def test_string_subtraction_is_a_type_mismatch(basic, helpers):
    result = basic.process_command('PRINT "A"-"B"')
    assert "TYPE MISMATCH: - doesn't work on strings" in errors(helpers, result)


def test_question_mark_is_print(basic, helpers):
    assert helpers.get_text_output(basic.process_command('?1+1')) == [' 2 ']


def test_apostrophe_comment_after_a_statement(basic, helpers):
    assert not helpers.get_error_messages(basic.process_command("X=5 ' set X"))
    assert basic.variables['X'] == 5


@pytest.mark.parametrize('command, char', [('PRINT &G', '&'), ('PRINT 1 @', '@')])
def test_unknown_characters_are_syntax_errors(basic, helpers, command, char):
    assert f"Unexpected character '{char}'" in errors(helpers, basic.process_command(command))


def test_randomize_with_a_bad_seed(basic, helpers):
    result = basic.process_command('RANDOMIZE 1/0')
    assert 'Invalid RANDOMIZE seed: Division by zero' in errors(helpers, result)


# -- IF conversion -----------------------------------------------------------

def test_else_with_a_line_number_expression_jumps(basic, helpers):
    result = run(basic, helpers, ['10 IF 0 THEN 30 ELSE 10+10',
                                  '20 PRINT "TWENTY": END',
                                  '30 PRINT "THIRTY"'])
    assert helpers.get_text_output(result) == ['TWENTY']


def test_then_body_that_assigns_an_array_element(basic, helpers):
    basic.process_command('IF 1 THEN X(1)=2')
    assert helpers.get_text_output(basic.process_command('PRINT X(1)')) == [' 2 ']


def test_then_body_that_assigns_a_string_containing_equals(basic, helpers):
    basic.process_command('IF 1 THEN A$="X=Y"')
    assert basic.variables['A$'] == 'X=Y'


def test_empty_then_branch_runs_the_else(basic, helpers):
    assert helpers.get_text_output(basic.process_command('IF 0 THEN ELSE PRINT 2')) == [' 2 ']
    assert helpers.get_text_output(basic.process_command('IF 1 THEN ELSE PRINT 2')) == []


def test_else_rem_is_a_comment_not_a_jump(basic, helpers):
    result = run(basic, helpers, ['10 IF 0 THEN 30 ELSE REM NOTHING', '20 PRINT "NEXT"', '30 END'])
    assert helpers.get_text_output(result) == ['NEXT']


# -- arrays ------------------------------------------------------------------

@pytest.mark.parametrize('command', ['A("X")=5', 'PRINT A("X")', 'X=A(1,"X")'])
def test_string_array_subscript_is_a_type_mismatch(basic, helpers, command):
    """#95: used to say "invalid literal for int() with base 10: 'X'"."""
    message = errors(helpers, basic.process_command(command))
    assert 'TYPE MISMATCH: array subscripts must be numbers' in message
    assert 'int()' not in message


def test_string_subscript_in_input_is_a_type_mismatch(basic, helpers):
    result = helpers.execute_program(basic, ['10 INPUT A("X")'])
    assert 'TYPE MISMATCH: array subscripts must be numbers' in errors(helpers, result)


def test_string_array_dimension_is_refused(basic, helpers):
    result = basic.process_command('DIM A("X")')
    assert 'Invalid array dimension expression: TYPE MISMATCH' in errors(helpers, result)


# -- control flow ------------------------------------------------------------

def test_next_without_for_at_the_prompt(basic, helpers):
    assert 'NEXT WITHOUT FOR' in errors(helpers, basic.process_command('NEXT'))


def test_resume_to_an_unknown_target(basic, helpers):
    result = run(basic, helpers, ['10 ON ERROR GOTO 30', '20 X=1/0', '25 END',
                                  '30 PRINT "HANDLER"', '40 RESUME ZZ'])
    assert helpers.get_text_output(result) == ['HANDLER']
    assert 'UNDEFINED LINE 0' in errors(helpers, result)


# -- program editing ---------------------------------------------------------

def test_delete_a_range(basic, helpers):
    helpers.load_program(basic, ['10 PRINT 1', '20 PRINT 2', '30 PRINT 3'])
    assert helpers.get_text_output(basic.process_command('DELETE 10-20')) == ['DELETED 2 LINE(S)']
    assert sorted(basic.program) == [30]


def test_renum_refuses_to_reorder_lines(basic, helpers):
    helpers.load_program(basic, ['10 PRINT 1', '20 PRINT 2', '30 PRINT 3'])
    # Renumbering from line 20 to start at 5 would move 20 and 30 before 10
    result = basic.process_command('RENUM 5,20,1')
    assert 'RENUM WOULD REORDER PROGRAM LINES' in errors(helpers, result)
    assert sorted(basic.program) == [10, 20, 30]


# -- files -------------------------------------------------------------------

class TestFileErrors:
    @pytest.fixture(autouse=True)
    def _sandbox(self, temp_programs_dir):
        self.programs_dir = temp_programs_dir

    def test_print_hash_expression_error(self, basic, helpers):
        basic.process_command('OPEN "O", #1, "T"')
        result = basic.process_command('PRINT #1, 1/0')
        basic.process_command('CLOSE #1')
        assert 'Error evaluating PRINT# expression: Division by zero' in errors(helpers, result)

    def test_eof_of_a_bad_file_number(self, basic, helpers):
        result = basic.process_command('PRINT EOF(99)')
        assert 'FILE NUMBER ERROR: file number must be 1-15' in errors(helpers, result)

    @pytest.mark.parametrize('command', ['LOAD', 'MERGE', 'CHAIN'])
    def test_program_commands_stay_in_the_sandbox(self, basic, helpers, command):
        result = basic.process_command(f'{command} "../x"')
        assert f'{command}: PATH OUTSIDE PROGRAMS DIRECTORY' in errors(helpers, result)

    def test_cd_dot_stays_at_the_top(self, basic, helpers):
        result = basic.process_command('CD "."')
        assert helpers.get_text_output(result) == ['CHANGED FROM PROGRAMS/', 'TO PROGRAMS/']
        assert basic.file_manager.subdir == ''

    def test_chain_to_a_missing_line(self, basic, helpers):
        helpers.load_program(basic, ['10 PRINT "IN NEXT"'])
        basic.process_command('SAVE "NEXTP"')
        result = run(basic, helpers, ['10 CHAIN "NEXTP",999'])
        assert 'UNDEFINED LINE 999' in errors(helpers, result)
        assert helpers.get_text_output(result) == []

    def test_chain_to_a_missing_line_is_not_trapped(self, basic, helpers):
        """#116: the chained program never started, so there's nothing to
        RESUME, and the old handler's line means nothing in it."""
        helpers.load_program(basic, ['10 PRINT "IN NEXT"', '100 PRINT "HANDLER IN NEXTP"'])
        basic.process_command('SAVE "NEXTP"')
        result = run(basic, helpers, ['10 ON ERROR GOTO 100', '20 CHAIN "NEXTP",999',
                                      '100 PRINT "OLD HANDLER": END'])
        assert 'UNDEFINED LINE 999' in errors(helpers, result)
        assert helpers.get_text_output(result) == []


@pytest.mark.xfail(reason='#123: RUN ignores its line number', strict=True)
def test_run_to_a_missing_line(basic, helpers):
    """#116: RUN n clears ON ERROR first, so this always stops."""
    helpers.load_program(basic, ['10 ON ERROR GOTO 20', '20 PRINT "H"'])
    result = basic.process_command('RUN 999')
    assert 'UNDEFINED LINE 999' in errors(helpers, result)
    assert helpers.get_text_output(result) == []


# -- graphics ----------------------------------------------------------------

@pytest.mark.parametrize('command', [
    'LINE (A,)-(1,1),PSET',        # bad first pair
    'LINE (0,0)-(1,,PSET',         # bad second pair
])
def test_line_with_a_malformed_coordinate(basic, helpers, command):
    basic.process_command('PMODE 4,1')
    result = basic.process_command(command)
    message = errors(helpers, result)
    # #95: suggests LINE's own syntax, not the single-point LINE(x,y)
    assert 'Correct syntax: LINE(x1,y1)-(x2,y2)' in message, message
    assert 'LINE(x,y)' not in message
    assert not helpers.get_graphics_output(result)


def test_a_point_command_still_suggests_one_point(basic, helpers):
    basic.process_command('PMODE 4,1')
    assert 'Correct syntax: PSET(x,y)' in errors(helpers, basic.process_command('PSET (1,)'))


@pytest.mark.parametrize('command, shown', [
    ('IF 1 THEN "A"', 'Unrecognized command: "A"'),
    ('"A"', 'Unrecognized command: "A"'),
    ('X=5 "A"', 'Unexpected "A"'),
])
def test_syntax_errors_show_strings_with_their_quotes(basic, helpers, command, shown):
    assert shown in errors(helpers, basic.process_command(command))


def test_line_with_trailing_text(basic, helpers):
    basic.process_command('PMODE 4,1')
    result = basic.process_command('LINE (0,0)-(1,1)X')
    assert 'Unexpected text after LINE coordinates: X' in errors(helpers, result)


def test_screen_needs_a_mode(basic, helpers):
    assert 'SCREEN takes a mode' in errors(helpers, basic.process_command('SCREEN'))
    assert 'SCREEN takes a mode' in errors(helpers, basic.process_command('SCREEN 1,1,1'))


def test_screen_mode_out_of_range(basic, helpers):
    result = basic.process_command('SCREEN 3,1')
    assert 'ILLEGAL FUNCTION CALL: SCREEN mode 3 is not supported' in errors(helpers, result)
