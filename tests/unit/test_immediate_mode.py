"""Immediate-mode behaviour (task #19): control structures and jumps typed
at the prompt run alongside the stored program, not in place of it."""

import pytest


def show(helpers, result):
    return helpers.get_text_output(result), helpers.get_error_messages(result)


def test_goto_runs_program_from_line(basic, helpers):
    basic.process_command('10 PRINT "START"')
    basic.process_command('100 PRINT "AT 100"')
    assert show(helpers, basic.process_command('GOTO 100')) == (['AT 100'], [])


def test_goto_keeps_variables(basic, helpers):
    basic.process_command('100 PRINT A')
    texts, errors = show(helpers, basic.process_command('A=7: GOTO 100'))
    assert errors == [] and ' '.join(texts).split() == ['7']


def test_if_then_goto_into_program(basic, helpers):
    basic.process_command('100 PRINT "AT 100"')
    assert show(helpers, basic.process_command('X=1: IF X=1 THEN GOTO 100')) == (['AT 100'], [])


def test_gosub_returns_to_prompt(basic, helpers):
    basic.process_command('10 PRINT "MAIN SHOULD NOT RUN"')
    basic.process_command('500 PRINT "IN SUB": RETURN')
    assert show(helpers, basic.process_command('GOSUB 500')) == (['IN SUB'], [])


def test_input_inside_immediate_loop_resumes(basic, helpers):
    result = basic.process_command('FOR I=1 TO 2: INPUT A: T=T+A: NEXT: PRINT T')
    for value in ('5', '6'):
        assert any(r.get('type') == 'input_request' for r in result), result
        basic.store_input_value(basic.input_variables[0], value)
        basic.clear_input_state()
        result = basic.continue_program_execution()
    assert show(helpers, result) == ([' 11 '], [])


def test_temporary_line_is_never_listed_or_left_behind(basic, helpers):
    basic.process_command('10 PRINT 1')
    basic.process_command('FOR I=1 TO 2: X=X+I: NEXT')
    assert list(basic.program) == [10]
    assert -1 not in basic.data_values
    basic.process_command('FOR I=1 TO 1: INPUT A: NEXT')  # pending INPUT
    assert helpers.get_text_output(basic.process_command('LIST')) == ['10 PRINT 1']


def test_immediate_stop_does_not_arm_cont(basic, helpers):
    assert helpers.get_text_output(basic.process_command('STOP')) == ['BREAK']
    assert helpers.get_error_messages(basic.process_command('CONT'))


def test_immediate_pause_after_program_input_does_not_arm_continuation(basic, helpers):
    # #25: PAUSE used a stale program_counter (left by an earlier INPUT) to
    # decide it was inside a program, and armed a pause continuation.
    basic.process_command('10 INPUT A')
    basic.process_command('20 END')
    basic.process_command('RUN')
    basic.store_input_value(basic.input_variables[0], '1')
    basic.clear_input_state()
    basic.continue_program_execution()
    result = basic.process_command('PAUSE 0')
    assert any(r.get('type') == 'pause' for r in result)
    assert not basic.waiting_for_pause_continuation


def test_immediate_loops_do_not_duplicate_data(basic, helpers):
    basic.process_command('10 DATA 1,2')
    basic.process_command('FOR I=1 TO 1: X=1: NEXT')
    basic.process_command('FOR I=1 TO 1: X=1: NEXT')
    assert len(basic.data_statements) == 2


@pytest.mark.parametrize('condition, message', [
    ('1/0', 'Division by zero'),                 # #93: used to escape as ZeroDivisionError
    ('9^999', 'OVERFLOW'),
    ('X=', 'Error in IF condition'),
])
def test_block_if_whose_condition_fails_is_a_basic_error(basic, helpers, condition, message):
    result = basic.process_command(f'IF {condition} THEN')
    assert message in '\n'.join(helpers.get_error_messages(result)), result
    assert basic.if_stack == []
    assert helpers.get_text_output(basic.process_command('PRINT "OK"')) == ['OK']
