"""Tests for TIMER pseudo-variable."""

import time

import pytest


class TestTimerRead:
    """Tests for reading the TIMER pseudo-variable."""

    def test_timer_returns_integer(self, basic, helpers):
        result = basic.process_command('PRINT TIMER')
        output = helpers.get_text_output(result)
        assert len(output) == 1
        assert int(output[0].strip()) >= 0

    def test_timer_increments(self, basic, helpers):
        result1 = basic.process_command('PRINT TIMER')
        t1 = int(helpers.get_text_output(result1)[0].strip())
        time.sleep(0.05)
        result2 = basic.process_command('PRINT TIMER')
        t2 = int(helpers.get_text_output(result2)[0].strip())
        assert t2 >= t1

    def test_timer_in_expression(self, basic, helpers):
        basic.process_command('T = TIMER')
        assert 'T' in basic.variables
        assert isinstance(basic.variables['T'], int)
        assert basic.variables['T'] >= 0

    def test_timer_in_comparison(self, basic, helpers):
        result = basic.process_command('IF TIMER >= 0 THEN PRINT "OK"')
        output = helpers.get_text_output(result)
        assert output == ['OK']


class TestTimerWrite:
    """Tests for setting the TIMER pseudo-variable."""

    def test_timer_reset_to_zero(self, basic, helpers):
        time.sleep(0.02)
        basic.process_command('TIMER = 0')
        result = basic.process_command('PRINT TIMER')
        t = int(helpers.get_text_output(result)[0].strip())
        # Should be close to 0 (within a few ticks)
        assert t < 10

    def test_timer_set_to_value(self, basic, helpers):
        basic.process_command('TIMER = 600')
        result = basic.process_command('PRINT TIMER')
        t = int(helpers.get_text_output(result)[0].strip())
        # Should be close to 600 (10 seconds worth of ticks)
        assert 598 <= t <= 610

    def test_timer_set_negative(self, basic, helpers):
        """Setting TIMER to negative is allowed (matches real CoCo)."""
        basic.process_command('TIMER = -60')
        result = basic.process_command('PRINT TIMER')
        t = int(helpers.get_text_output(result)[0].strip())
        assert t <= 0


class TestTimerInProgram:
    """Tests for TIMER within program execution."""

    def test_timer_in_program(self, basic, helpers):
        result = helpers.execute_program(basic, [
            '10 TIMER = 0',
            '20 T = TIMER',
            '30 PRINT T',
        ])
        output = helpers.get_text_output(result)
        assert len(output) == 1
        t = int(output[0].strip())
        assert t >= 0
        assert t < 60  # Should be well under 1 second

    def test_timer_reset_on_new(self, basic, helpers):
        time.sleep(0.02)
        basic.process_command('NEW')
        result = basic.process_command('PRINT TIMER')
        t = int(helpers.get_text_output(result)[0].strip())
        assert t < 10

    def test_timer_arithmetic(self, basic, helpers):
        basic.process_command('TIMER = 120')
        result = basic.process_command('PRINT TIMER / 60')
        output = helpers.get_text_output(result)
        val = float(output[0].strip())
        # Should be approximately 2.0 (120 ticks / 60 Hz)
        assert 1.9 <= val <= 2.2
