#!/usr/bin/env python3

"""
Unit tests for core.py commands and utilities.

Tests execute_stop, execute_cont, execute_new, execute_next,
eval_int, check_reserved_name, and clear_interpreter_state.
"""

import pytest


class TestRunArguments:
    """#123: RUN used to ignore its argument and always start at the top."""

    PROGRAM = ['10 X=1: PRINT "TEN"', '20 PRINT "TWENTY";X', '30 Tail:', '40 PRINT "FORTY"']

    def test_run_from_a_line_clears_variables(self, basic, helpers):
        helpers.load_program(basic, self.PROGRAM)
        basic.process_command('X=9')
        assert helpers.get_text_output(basic.process_command('RUN 20')) == ['TWENTY 0 ', 'FORTY']

    def test_run_from_a_label(self, basic, helpers):
        helpers.load_program(basic, self.PROGRAM)
        assert helpers.get_text_output(basic.process_command('RUN Tail')) == ['FORTY']

    def test_run_loads_and_runs_a_file(self, basic, helpers, temp_programs_dir):
        helpers.load_program(basic, ['10 PRINT "FROM FILE"'])
        basic.process_command('SAVE "OTHER"')
        helpers.load_program(basic, ['10 PRINT "OLD"'])
        result = basic.process_command('RUN "OTHER"')
        assert helpers.get_text_output(result)[-1] == 'FROM FILE'
        assert basic.program == {10: 'PRINT "FROM FILE"'}

    def test_run_a_missing_file(self, basic, helpers, temp_programs_dir):
        helpers.load_program(basic, ['10 PRINT "OLD"'])
        errors = helpers.get_error_messages(basic.process_command('RUN "NOPE"'))
        assert errors and 'NOPE' in errors[0]
        assert basic.program == {10: 'PRINT "OLD"'}


class TestExecuteStop:
    """Test STOP command"""

    def test_stop_halts_execution(self, basic, helpers):
        """STOP halts program and reports BREAK"""
        result = helpers.execute_program(basic, [
            '10 PRINT "BEFORE"',
            '20 STOP',
            '30 PRINT "AFTER"',
        ])
        texts = helpers.get_text_output(result)
        assert 'BEFORE' in texts
        assert any('BREAK' in t for t in texts)
        assert 'AFTER' not in texts

    def test_stop_preserves_variables(self, basic, helpers):
        """STOP preserves variable state for CONT"""
        helpers.execute_program(basic, [
            '10 X = 42',
            '20 STOP',
            '30 PRINT X',
        ])
        assert basic.variables['X'] == 42

    def test_stop_records_position(self, basic, helpers):
        """STOP records stopped position for CONT"""
        helpers.execute_program(basic, [
            '10 PRINT "A"',
            '20 STOP',
            '30 PRINT "B"',
        ])
        assert basic.stopped_position is not None


class TestExecuteCont:
    """Test CONT command"""

    def test_cont_resumes_after_stop(self, basic, helpers):
        """CONT resumes execution after STOP"""
        helpers.execute_program(basic, [
            '10 PRINT "BEFORE"',
            '20 STOP',
            '30 PRINT "AFTER"',
            '40 END',
        ])
        result = basic.process_command('CONT')
        texts = helpers.get_text_output(result)
        assert 'AFTER' in texts

    def test_cont_without_stop_errors(self, basic, helpers):
        """CONT without prior STOP produces error"""
        result = basic.process_command('CONT')
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0


class TestExecuteNew:
    """Test NEW command"""

    def test_new_clears_program(self, basic, helpers):
        """NEW clears stored program"""
        basic.process_command('10 PRINT "HELLO"')
        basic.process_command('NEW')
        assert len(basic.program) == 0

    def test_new_clears_variables(self, basic, helpers):
        """NEW clears all variables"""
        basic.process_command('X = 42')
        basic.process_command('NEW')
        assert 'X' not in basic.variables

    def test_new_clears_arrays(self, basic, helpers):
        """NEW clears dimensioned arrays"""
        basic.process_command('DIM A(10)')
        basic.process_command('NEW')
        assert len(basic.arrays) == 0

    def test_new_returns_ready(self, basic, helpers):
        """NEW outputs READY message"""
        result = basic.process_command('NEW')
        texts = helpers.get_text_output(result)
        assert any('READY' in t for t in texts)


class TestExecuteNext:
    """Test NEXT command (registry side of FOR/NEXT)"""

    def test_next_without_for_errors(self, basic, helpers):
        """NEXT without matching FOR produces error"""
        result = basic.process_command('NEXT I')
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0

    def test_for_next_loop_executes(self, basic, helpers):
        """FOR/NEXT loop executes correct number of iterations"""
        result = helpers.execute_program(basic, [
            '10 S = 0',
            '20 FOR I = 1 TO 5',
            '30 S = S + I',
            '40 NEXT I',
            '50 PRINT S',
        ])
        texts = helpers.get_text_output(result)
        assert any('15' in t for t in texts)

    def test_for_next_with_step(self, basic, helpers):
        """FOR/NEXT with STEP works correctly"""
        result = helpers.execute_program(basic, [
            '10 S = 0',
            '20 FOR I = 0 TO 10 STEP 2',
            '30 S = S + 1',
            '40 NEXT I',
            '50 PRINT S',
        ])
        texts = helpers.get_text_output(result)
        assert any('6' in t for t in texts)


class TestEvalInt:
    """Test eval_int utility method"""

    def test_eval_int_with_literal(self, basic):
        """eval_int converts literal integer string"""
        assert basic.eval_int('42') == 42

    def test_eval_int_with_float(self, basic):
        """eval_int truncates float to integer"""
        assert basic.eval_int('3.7') == 3

    def test_eval_int_with_expression(self, basic):
        """eval_int evaluates expression and converts"""
        basic.variables['X'] = 10
        assert basic.eval_int('X + 5') == 15

    def test_eval_int_with_negative(self, basic):
        """eval_int handles negative values"""
        assert basic.eval_int('-3') == -3


class TestCheckReservedName:
    """Test check_reserved_name guard"""

    def test_reserved_name_rejected(self, basic, helpers):
        """Assignment to reserved function name produces error"""
        result = basic.process_command('LEN = 5')
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0

    def test_non_reserved_name_allowed(self, basic, helpers):
        """Assignment to regular variable name succeeds"""
        result = basic.process_command('X = 5')
        errors = helpers.get_error_messages(result)
        assert errors == []
        assert basic.variables['X'] == 5

    def test_dim_reserved_name_rejected(self, basic, helpers):
        """DIM with reserved function name produces error"""
        result = basic.process_command('DIM ABS(10)')
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0


class TestClearInterpreterState:
    """Test clear_interpreter_state method"""

    def test_clears_variables(self, basic):
        """State clear removes all variables"""
        basic.variables['X'] = 42
        basic.clear_interpreter_state()
        assert 'X' not in basic.variables

    def test_clears_arrays(self, basic):
        """State clear removes all arrays"""
        basic.process_command('DIM A(10)')
        basic.clear_interpreter_state()
        assert len(basic.arrays) == 0

    def test_resets_graphics_mode(self, basic):
        """State clear turns graphics off (no PMODE; PMODE 0 is a real mode)"""
        basic.graphics_mode = 4
        basic.clear_interpreter_state()
        assert basic.graphics_mode is None

    def test_resets_drawing_state(self, basic):
        """State clear resets turtle position and draw color"""
        basic.turtle_x = 200
        basic.turtle_y = 150
        basic.current_draw_color = 3
        basic.screen_mode = 2
        basic.clear_interpreter_state()
        assert basic.turtle_x == 128   # centre of the 256x192 screen (#101)
        assert basic.turtle_y == 96
        assert basic.current_draw_color == 1
        assert basic.screen_mode == 1

    def test_resets_pixel_buffer(self, basic):
        """State clear empties the pixel buffer"""
        basic.graphics.pixel_buffer[(10, 10)] = 1
        basic.clear_interpreter_state()
        assert len(basic.graphics.pixel_buffer) == 0

    def test_resets_error_state(self, basic):
        """State clear resets ON ERROR GOTO state"""
        basic.on_error_goto_line = 100
        basic.error_number = 5
        basic.in_error_handler = True
        basic.clear_interpreter_state()
        assert basic.on_error_goto_line is None
        assert basic.error_number == 0
        assert basic.in_error_handler is False

    def test_clears_program_when_requested(self, basic):
        """State clear with clear_program=True removes program"""
        basic.process_command('10 PRINT "HI"')
        basic.clear_interpreter_state(clear_program=True)
        assert len(basic.program) == 0

    def test_preserves_program_when_requested(self, basic):
        """State clear with clear_program=False keeps program"""
        basic.process_command('10 PRINT "HI"')
        basic.clear_interpreter_state(clear_program=False)
        assert len(basic.program) == 1


class TestClearCommand:
    """CLEAR [n]: erase variables and arrays (n, the string space, is accepted
    and ignored); the program stays."""

    @pytest.mark.parametrize('command', ['CLEAR', 'CLEAR 1000', 'CLEAR 200*5'])
    def test_clears_variables_and_arrays_keeps_program(self, basic, helpers, command):
        basic.process_command('10 PRINT "HI"')
        basic.process_command('A = 5: B$ = "X": DIM C(3)')
        result = basic.process_command(command)
        assert helpers.get_error_messages(result) == []
        assert basic.variables == {} and basic.arrays == {}
        assert list(basic.program) == [10]

    def test_clear_in_program_prints_nothing(self, basic, helpers):
        helpers.load_program(basic, ['10 A = 1', '20 CLEAR 500', '30 PRINT A'])
        results = helpers.run_to_completion(basic)
        assert helpers.get_error_messages(results) == []
        assert ' '.join(helpers.get_text_output(results)).split() == ['0']

    def test_non_numeric_argument_is_error(self, basic, helpers):
        errors = helpers.get_error_messages(basic.process_command('CLEAR "A"'))
        assert errors
