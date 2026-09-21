"""Regression tests for interpreter-core bugs found in the Sept 2026 audit.

Each test names its task number. Covers program storage, the execution loop,
loop skipping/NEXT semantics, GOSUB/RETURN, STOP/CONT, labels and RENUM.
"""

import pytest


def run(basic, helpers, lines, max_frames=1000):
    helpers.load_program(basic, lines)
    results = helpers.run_to_completion(basic, max_frames=max_frames)
    return helpers.get_text_output(results), helpers.get_error_messages(results)


def words(texts):
    """All whitespace-separated tokens of the text output, in order."""
    return ' '.join(texts).split()


class TestLineReentry:
    """#14: re-typing a program line must fully replace the old one."""

    def test_shorter_retyped_line_drops_old_statements(self, basic, helpers):
        basic.process_command('NEW')
        basic.process_command('10 A=1:B=2:PRINT "OLD"')
        basic.process_command('10 A=1')
        basic.process_command('20 PRINT "END"')
        texts = helpers.get_text_output(basic.process_command('RUN'))
        assert 'OLD' not in ' '.join(texts)
        assert 'END' in ' '.join(texts)

    def test_retyped_data_line_does_not_duplicate_values(self, basic, helpers):
        basic.process_command('NEW')
        basic.process_command('10 DATA 1,2')
        basic.process_command('10 DATA 1,2')
        basic.process_command('20 READ A,B,C')
        errors = helpers.get_error_messages(basic.process_command('RUN'))
        assert any('OUT OF DATA' in e.upper() for e in errors), errors

    def test_deleted_data_line_values_are_gone(self, basic, helpers):
        basic.process_command('NEW')
        basic.process_command('10 DATA 7')
        basic.process_command('10')
        basic.process_command('20 READ A')
        errors = helpers.get_error_messages(basic.process_command('RUN'))
        assert any('OUT OF DATA' in e.upper() for e in errors), errors


class TestErrorsInCompiledStatements:
    """#15: runtime errors in pre-compiled commands must be BASIC errors."""

    @pytest.mark.parametrize('lines', [
        ['10 X=0', '20 WHILE 1/X', '30 WEND'],
        ['10 X=0', '20 IF 1/X THEN', '30 PRINT "IN"', '40 ENDIF'],
        ['10 X=0', '20 DO', '30 LOOP UNTIL 1/X'],
    ], ids=['while', 'multiline-if', 'loop-until'])
    def test_division_by_zero_is_reported_not_raised(self, basic, helpers, lines):
        texts, errors = run(basic, helpers, lines)
        assert any('DIVISION BY ZERO' in e.upper() or '/0' in e for e in errors), errors
        assert not basic.running

    def test_on_error_traps_error_in_while_condition(self, basic, helpers):
        texts, errors = run(basic, helpers, [
            '10 ON ERROR GOTO 100',
            '20 X=0',
            '30 WHILE 1/X',
            '40 WEND',
            '50 END',
            '100 PRINT "TRAPPED"',
            '110 END',
        ])
        assert errors == []
        assert 'TRAPPED' in texts[-1]


class TestIterationCounter:
    """#16: the runaway-program guard must not accumulate across resumes."""

    def test_input_loop_survives_many_turns(self, basic, helpers):
        helpers.load_program(basic, [
            '10 INPUT A',
            '20 FOR K=1 TO 1000: NEXT K',
            '30 GOTO 10',
        ])
        result = basic.process_command('RUN')
        for turn in range(80):  # 80 turns x ~2000 statements > 50,000 limit
            assert any(r.get('type') == 'input_request' for r in result), result
            basic.store_input_value({'name': 'A', 'array': False}, str(turn))
            result = basic.continue_program_execution()
            errors = helpers.get_error_messages(result)
            assert errors == [], f'turn {turn}: {errors}'


class TestReturnOnLastLine:
    """#17: RETURN to a GOSUB on the last line must end the program."""

    def test_gosub_on_last_line_returns_and_ends(self, basic, helpers):
        texts, errors = run(basic, helpers, [
            '10 GOTO 50',
            '20 PRINT "SUB"',
            '30 RETURN',
            '50 GOSUB 20',
        ])
        assert errors == []
        assert sum('SUB' in t for t in texts) == 1, texts


class TestLoopSkipping:
    """#18: zero-trip loops and EXIT FOR must respect nesting and case."""

    def test_zero_trip_for_with_nested_unnamed_next(self, basic, helpers):
        texts, errors = run(basic, helpers, [
            '10 FOR I=1 TO 0',
            '20 FOR J=1 TO 2',
            '30 PRINT "INNER"',
            '40 NEXT',
            '50 NEXT',
            '60 PRINT "DONE"',
        ])
        assert errors == []
        assert texts == ['DONE'] or words(texts) == ['DONE'], texts

    def test_zero_trip_while_with_nested_while(self, basic, helpers):
        texts, errors = run(basic, helpers, [
            '10 WHILE 0',
            '20 WHILE 0',
            '30 WEND',
            '40 PRINT "BAD"',
            '50 WEND',
            '60 PRINT "DONE"',
        ])
        assert errors == []
        assert words(texts) == ['DONE'], texts

    def test_zero_trip_do_while_with_nested_do(self, basic, helpers):
        texts, errors = run(basic, helpers, [
            '10 DO WHILE 0',
            '20 DO WHILE 0',
            '30 LOOP',
            '40 PRINT "BAD"',
            '50 LOOP',
            '60 PRINT "DONE"',
        ])
        assert errors == []
        assert words(texts) == ['DONE'], texts

    def test_exit_for_skips_past_inner_unnamed_next(self, basic, helpers):
        texts, errors = run(basic, helpers, [
            '10 FOR I=1 TO 3',
            '20 EXIT FOR',
            '30 FOR J=1 TO 2',
            '40 NEXT',
            '50 NEXT I',
            '60 PRINT "DONE"',
        ])
        assert errors == []
        assert words(texts) == ['DONE'], texts

    def test_zero_trip_for_lowercase_next_variable(self, basic, helpers):
        texts, errors = run(basic, helpers, [
            '10 for i=1 to 0',
            '20 print "BAD"',
            '30 next i',
            '40 print "DONE"',
        ])
        assert errors == []
        assert words(texts) == ['DONE'], texts


class TestNextVariableList:
    """#18: NEXT J,I closes both loops; NEXT I unwinds stale inner frames."""

    def test_next_with_two_variables(self, basic, helpers):
        texts, errors = run(basic, helpers, [
            '10 FOR I=1 TO 2',
            '20 FOR J=1 TO 2',
            '30 PRINT I;J',
            '40 NEXT J,I',
            '50 PRINT "END"',
        ])
        assert errors == []
        assert words(texts) == ['1', '1', '1', '2', '2', '1', '2', '2', 'END'], texts
        assert basic.for_stack == []

    def test_next_outer_variable_unwinds_abandoned_inner_loop(self, basic, helpers):
        texts, errors = run(basic, helpers, [
            '10 FOR I=1 TO 2',
            '20 FOR J=1 TO 5',
            '30 IF J=2 THEN GOTO 50',
            '40 NEXT J',
            '50 NEXT I',
            '60 PRINT I;J',
        ])
        assert errors == []
        assert words(texts) == ['3', '2'], texts


class TestForFrameReuse:
    """#43: re-executing FOR for an active variable must replace its frame."""

    def test_goto_back_to_for_does_not_leak_frames(self, basic, helpers):
        texts, errors = run(basic, helpers, [
            '10 C=0',
            '20 FOR I=1 TO 3',
            '30 C=C+1: IF C<5 THEN GOTO 20',
            '40 NEXT I',
        ])
        assert errors == []
        assert basic.for_stack == []


class TestContinue:
    """#20: CONT works after each of several STOPs."""

    def test_cont_after_second_stop(self, basic, helpers):
        helpers.load_program(basic, [
            '10 PRINT "A"', '20 STOP', '30 PRINT "B"', '40 STOP', '50 PRINT "C"',
        ])
        basic.process_command('RUN')
        first = basic.process_command('CONT')
        second = basic.process_command('CONT')
        assert helpers.get_error_messages(first) == []
        assert helpers.get_error_messages(second) == []
        assert 'C' in ' '.join(helpers.get_text_output(second))


class TestLabels:
    """#21: deleting a label line unregisters the label."""

    def test_deleted_label_is_undefined(self, basic, helpers):
        basic.process_command('NEW')
        basic.process_command('10 GOTO FOO')
        basic.process_command('20 FOO:')
        basic.process_command('30 PRINT "HI"')
        basic.process_command('20')
        assert 'FOO' not in basic.labels


class TestRenum:
    """#21: RENUM must keep DATA, ELSE targets and RESTORE targets consistent."""

    def test_renum_does_not_duplicate_data(self, basic, helpers):
        basic.process_command('NEW')
        basic.process_command('10 DATA 1,2')
        basic.process_command('20 READ A,B,C')
        basic.process_command('RENUM 100,10')
        errors = helpers.get_error_messages(basic.process_command('RUN'))
        assert any('OUT OF DATA' in e.upper() for e in errors), errors

    def test_renum_updates_else_target(self, basic, helpers):
        basic.process_command('NEW')
        basic.process_command('10 IF 0 THEN 30 ELSE 40')
        basic.process_command('30 PRINT "THEN"')
        basic.process_command('35 END')
        basic.process_command('40 PRINT "ELSE"')
        basic.process_command('RENUM 100,10')
        results = basic.process_command('RUN')
        assert helpers.get_error_messages(results) == []
        assert 'ELSE' in ' '.join(helpers.get_text_output(results))

    def test_renum_updates_restore_target(self, basic, helpers):
        basic.process_command('NEW')
        basic.process_command('10 DATA 1')
        basic.process_command('20 DATA 2')
        basic.process_command('30 RESTORE 20: READ A: PRINT A')
        basic.process_command('RENUM 100,10')
        results = basic.process_command('RUN')
        assert helpers.get_error_messages(results) == []
        assert words(helpers.get_text_output(results)) == ['2']


class TestConditions:
    """#23: a malformed condition is a syntax error, not silently false."""

    def test_malformed_loop_until_condition_is_an_error(self, basic, helpers):
        texts, errors = run(basic, helpers, ['10 DO', '20 LOOP UNTIL X='])
        assert errors, 'expected a syntax error'
        assert not any('ITERATION' in e.upper() for e in errors), errors


class TestErrorHandling:
    """#24: RESUME accepts labels; missing handler lines don't wedge state."""

    def test_resume_to_label(self, basic, helpers):
        texts, errors = run(basic, helpers, [
            '10 ON ERROR GOTO 100',
            '20 X=1/0',
            '30 END',
            '40 Fin:',
            '50 PRINT "RESUMED"',
            '60 END',
            '100 RESUME Fin',
        ])
        assert errors == []
        assert 'RESUMED' in ' '.join(texts)

    def test_missing_handler_line_does_not_leave_handler_flag(self, basic, helpers):
        texts, errors = run(basic, helpers, ['10 ON ERROR GOTO 900', '20 X=1/0'])
        assert errors
        assert basic.in_error_handler is False

    def test_print_hash_with_extra_spaces_writes_to_file(self, basic, helpers, temp_programs_dir):
        texts, errors = run(basic, helpers, [
            '10 OPEN "O",#1,"SPACED.TXT"',
            '20 PRINT     #1,"Z"',
            '30 CLOSE #1',
        ])
        assert errors == []
        assert 'Z' not in ' '.join(texts)


@pytest.mark.parametrize('program, message', [
    (['10 PRINT 1/0'], 'Division by zero'),
    (['10 GOTO 10'], 'TOO MANY ITERATIONS'),
])
def test_runtime_errors_are_output_not_warnings(basic, helpers, caplog, program, message):
    """#98: a BASIC runtime error is program output; logging it at WARNING
    made the CLI (no logging configured) print it a second time."""
    with caplog.at_level('WARNING'):
        texts, errors = run(basic, helpers, program)
    assert len(errors) == 1 and message in errors[0]
    assert caplog.records == []
