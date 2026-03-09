"""Tests for iteration safety limits, hard cap, and auto-yield."""

import pytest


class TestSafetyLimits:
    """Test iteration safety and hard cap behavior."""

    def test_safety_on_stops_infinite_loop(self, basic, helpers):
        """Safety ON should stop programs exceeding max_iterations."""
        basic.max_iterations = 100
        helpers.load_program(basic, [
            '10 GOTO 10',
        ])
        result = basic.process_command('RUN')
        errors = helpers.get_error_messages(result)
        assert any('TOO MANY ITERATIONS' in e for e in errors)

    def test_safety_off_allows_more_iterations(self, basic, helpers):
        """Safety OFF should allow programs past the soft limit."""
        basic.max_iterations = 10
        basic.safety_enabled = False
        basic.max_absolute_iterations = 1000
        helpers.load_program(basic, [
            '10 X = X + 1',
            '20 IF X < 50 THEN GOTO 10',
            '30 PRINT X',
        ])
        result = basic.process_command('RUN')
        text = helpers.get_text_output(result)
        assert any('50' in t for t in text)

    def test_hard_cap_stops_even_with_safety_off(self, basic, helpers):
        """Hard cap should stop programs even when safety is disabled."""
        basic.safety_enabled = False
        basic.max_absolute_iterations = 100
        helpers.load_program(basic, [
            '10 GOTO 10',
        ])
        result = basic.process_command('RUN')
        errors = helpers.get_error_messages(result)
        assert any('ABSOLUTE ITERATION LIMIT' in e for e in errors)

    def test_safety_command_on(self, basic):
        """SAFETY ON should enable iteration limits."""
        basic.safety_enabled = False
        result = basic.process_command('SAFETY ON')
        assert basic.safety_enabled is True

    def test_safety_command_off(self, basic):
        """SAFETY OFF should disable iteration limits and show hard cap warning."""
        result = basic.process_command('SAFETY OFF')
        assert basic.safety_enabled is False
        text = [item['text'] for item in result if item.get('type') == 'text']
        assert any('HARD CAP' in t for t in text)

    def test_safety_command_status(self, basic):
        """SAFETY with no args should show current status."""
        result = basic.process_command('SAFETY')
        text = [item['text'] for item in result if item.get('type') == 'text']
        assert any('ON' in t for t in text)

    def test_iteration_count_resets_on_run(self, basic, helpers):
        """iteration_count should reset when RUN starts."""
        basic.iteration_count = 999
        helpers.load_program(basic, [
            '10 PRINT "HELLO"',
        ])
        basic.process_command('RUN')
        # After a short program, count should be small (not 999+)
        assert basic.iteration_count < 10


class TestAutoYield:
    """Test auto-yield for graphics-heavy programs."""

    def test_auto_yield_on_pcls_after_graphics(self, basic, helpers):
        """PCLS after graphics output should trigger auto-yield."""
        basic.safety_enabled = False
        helpers.load_program(basic, [
            '10 PMODE 4',
            '20 SCREEN 1',
            '30 LINE (0,0)-(10,10),1',
            '40 PCLS',
            '50 PRINT "FRAME2"',
        ])
        result = basic.process_command('RUN')
        pauses = [item for item in result if item.get('type') == 'pause']
        assert len(pauses) >= 1
        assert pauses[0]['duration'] == 0.05
        # PRINT should NOT be in the first batch
        assert not any('FRAME2' in item.get('text', '') for item in result)

    def test_no_auto_yield_on_first_pcls(self, basic, helpers):
        """First PCLS (before any graphics) should not trigger auto-yield."""
        helpers.load_program(basic, [
            '10 PMODE 4',
            '20 SCREEN 1',
            '30 PCLS',
            '40 LINE (0,0)-(10,10),1',
            '50 PRINT "DONE"',
        ])
        result = basic.process_command('RUN')
        text = helpers.get_text_output(result)
        assert any('DONE' in t for t in text)

    def test_auto_yield_does_not_trigger_without_graphics(self, basic, helpers):
        """Non-graphics programs should not auto-yield."""
        helpers.load_program(basic, [
            '10 FOR I=1 TO 500',
            '20 X = I * 2',
            '30 NEXT I',
        ])
        result = basic.process_command('RUN')
        pauses = [item for item in result if item.get('type') == 'pause']
        assert len(pauses) == 0

    def test_auto_yield_continues_execution(self, basic, helpers):
        """After auto-yield, continue_program_execution should resume."""
        basic.safety_enabled = False
        helpers.load_program(basic, [
            '10 PMODE 4',
            '20 SCREEN 1',
            '30 LINE (0,0)-(10,10),1',
            '40 PCLS',
            '50 PRINT "DONE"',
        ])
        result = basic.process_command('RUN')
        assert basic.waiting_for_pause_continuation
        result2 = basic.continue_program_execution()
        text = helpers.get_text_output(result2)
        assert any('DONE' in t for t in text)
