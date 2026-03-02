"""Tests for RND argument semantics (CoCo BASIC)."""

import pytest


class TestRndPositive:
    """RND(n) with n > 0 returns a new random number each time."""

    def test_returns_float_between_0_and_1(self, basic):
        result = basic.evaluate_expression('RND(1)')
        assert isinstance(result, float)
        assert 0 < result < 1

    def test_successive_calls_differ(self, basic):
        """Multiple RND(1) calls should (almost certainly) differ."""
        values = [basic.evaluate_expression('RND(1)') for _ in range(10)]
        assert len(set(values)) > 1


class TestRndZero:
    """RND(0) returns the last random number."""

    def test_rnd_zero_repeats_last(self, basic):
        val = basic.evaluate_expression('RND(1)')
        repeat = basic.evaluate_expression('RND(0)')
        assert repeat == val

    def test_rnd_zero_repeats_multiple_times(self, basic):
        basic.evaluate_expression('RND(1)')
        a = basic.evaluate_expression('RND(0)')
        b = basic.evaluate_expression('RND(0)')
        assert a == b

    def test_rnd_zero_before_any_rnd(self, basic):
        """RND(0) before any RND call returns 0.0 (initial last_rnd)."""
        result = basic.evaluate_expression('RND(0)')
        assert result == 0.0

    def test_rnd_zero_updates_after_new_rnd(self, basic):
        first = basic.evaluate_expression('RND(1)')
        basic.evaluate_expression('RND(0)')  # should be first
        second = basic.evaluate_expression('RND(5)')
        repeat = basic.evaluate_expression('RND(0)')
        assert repeat == second


class TestRndNegative:
    """RND(-n) reseeds the generator for deterministic sequences."""

    def test_negative_reseeds(self, basic):
        """Same negative seed produces same sequence."""
        basic.evaluate_expression('RND(-42)')
        a = basic.evaluate_expression('RND(1)')
        basic.evaluate_expression('RND(-42)')
        b = basic.evaluate_expression('RND(1)')
        assert a == b

    def test_different_negative_seeds_differ(self, basic):
        basic.evaluate_expression('RND(-100)')
        a = basic.evaluate_expression('RND(1)')
        basic.evaluate_expression('RND(-200)')
        b = basic.evaluate_expression('RND(1)')
        assert a != b

    def test_negative_seed_returns_value(self, basic):
        """RND(-n) itself returns a random number (not just reseeding)."""
        result = basic.evaluate_expression('RND(-7)')
        assert isinstance(result, float)
        assert 0 < result < 1

    def test_negative_seed_updates_last_rnd(self, basic):
        val = basic.evaluate_expression('RND(-42)')
        repeat = basic.evaluate_expression('RND(0)')
        assert repeat == val


class TestRndWithRandomize:
    """RANDOMIZE and RND interact correctly."""

    def test_randomize_then_rnd(self, basic):
        """RANDOMIZE sets seed, RND produces deterministic sequence."""
        basic.process_command('RANDOMIZE 99')
        a = basic.evaluate_expression('RND(1)')
        basic.process_command('RANDOMIZE 99')
        b = basic.evaluate_expression('RND(1)')
        assert a == b

    def test_rnd_in_program(self, basic, helpers):
        """RND works in a running program."""
        result = helpers.execute_program(basic, [
            '10 RANDOMIZE 42',
            '20 PRINT RND(1)',
        ])
        output = helpers.get_text_output(result)
        assert len(output) == 1
        val = float(output[0].strip())
        assert 0 < val < 1
