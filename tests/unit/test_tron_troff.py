"""Tests for TRON/TROFF trace mode."""

import pytest


class TestTron:
    """Tests for TRON — enable trace mode."""

    def test_tron_enables_trace(self, basic):
        basic.process_command('TRON')
        assert basic.trace_mode is True

    def test_troff_disables_trace(self, basic):
        basic.process_command('TRON')
        basic.process_command('TROFF')
        assert basic.trace_mode is False

    def test_trace_off_by_default(self, basic):
        assert basic.trace_mode is False

    def test_tron_in_direct_mode(self, basic, helpers):
        result = basic.process_command('TRON')
        errors = helpers.get_error_messages(result)
        assert len(errors) == 0


def _load_and_run_with_tron(basic, helpers, lines):
    """Load program, enable TRON, then RUN."""
    helpers.load_program(basic, lines)
    basic.process_command('TRON')
    return basic.process_command('RUN')


class TestTraceOutput:
    """Tests for trace output during program execution."""

    def test_trace_prints_line_numbers(self, basic, helpers):
        result = _load_and_run_with_tron(basic, helpers, [
            '10 PRINT "A"',
            '20 PRINT "B"',
        ])
        output = helpers.get_text_output(result)
        assert '[10]' in output
        assert 'A' in output
        assert '[20]' in output
        assert 'B' in output

    def test_trace_line_order(self, basic, helpers):
        result = _load_and_run_with_tron(basic, helpers, [
            '10 PRINT "HELLO"',
            '20 END',
        ])
        output = helpers.get_text_output(result)
        idx_10 = output.index('[10]')
        idx_hello = output.index('HELLO')
        idx_20 = output.index('[20]')
        assert idx_10 < idx_hello < idx_20

    def test_no_trace_without_tron(self, basic, helpers):
        result = helpers.execute_program(basic, [
            '10 PRINT "HELLO"',
            '20 PRINT "WORLD"',
        ])
        output = helpers.get_text_output(result)
        assert '[10]' not in output
        assert '[20]' not in output

    def test_trace_with_goto(self, basic, helpers):
        result = _load_and_run_with_tron(basic, helpers, [
            '10 GOTO 30',
            '20 PRINT "SKIP"',
            '30 PRINT "HERE"',
        ])
        output = helpers.get_text_output(result)
        assert '[10]' in output
        assert '[30]' in output
        assert '[20]' not in output
        assert 'SKIP' not in output

    def test_trace_with_for_loop(self, basic, helpers):
        result = _load_and_run_with_tron(basic, helpers, [
            '10 FOR I = 1 TO 2',
            '20 PRINT I',
            '30 NEXT I',
        ])
        output = helpers.get_text_output(result)
        # Line 10 should appear once, lines 20/30 twice each
        assert output.count('[10]') == 1
        assert output.count('[20]') == 2
        assert output.count('[30]') == 2

    def test_troff_in_program(self, basic, helpers):
        result = _load_and_run_with_tron(basic, helpers, [
            '10 PRINT "A"',
            '20 TROFF',
            '30 PRINT "B"',
        ])
        output = helpers.get_text_output(result)
        assert '[10]' in output
        assert '[20]' in output
        assert '[30]' not in output
        assert 'A' in output
        assert 'B' in output

    def test_tron_in_program(self, basic, helpers):
        result = helpers.execute_program(basic, [
            '10 PRINT "A"',
            '20 TRON',
            '30 PRINT "B"',
        ])
        output = helpers.get_text_output(result)
        assert '[10]' not in output
        assert '[30]' in output
        assert 'A' in output
        assert 'B' in output


class TestTraceReset:
    """Tests for trace mode reset behavior."""

    def test_new_resets_trace(self, basic):
        basic.process_command('TRON')
        basic.process_command('NEW')
        assert basic.trace_mode is False

    def test_run_preserves_trace(self, basic, helpers):
        """TRON persists across RUN (like real CoCo)."""
        helpers.load_program(basic, ['10 PRINT "X"'])
        basic.process_command('TRON')
        result = basic.process_command('RUN')
        output = helpers.get_text_output(result)
        assert '[10]' in output

    def test_trace_only_on_first_sub_statement(self, basic, helpers):
        """Multi-statement lines should only trace once per line."""
        result = _load_and_run_with_tron(basic, helpers, [
            '10 A = 1: B = 2: PRINT A + B',
        ])
        output = helpers.get_text_output(result)
        assert output.count('[10]') == 1
