"""Tests for RND argument semantics (CoCo BASIC).

CoCo semantics:
  RND(n) where n >= 1: random integer from 1 to INT(n)
  RND(0): random fraction, 0 <= x < 1 (not a repeat, as in MS BASIC-80)
  RND(-n): reseed with n, then return a fraction (0 <= x < 1)
"""

import pytest


class TestRndPositiveInteger:
    """RND(n) with n >= 1 returns a random integer from 1 to n."""

    def test_rnd_1_always_returns_1(self, basic):
        """RND(1) always returns 1 (only possible integer from 1 to 1)."""
        for _ in range(10):
            result = basic.evaluate_expression('RND(1)')
            assert result == 1

    def test_rnd_6_returns_integer_1_to_6(self, basic):
        values = set()
        for _ in range(100):
            result = basic.evaluate_expression('RND(6)')
            assert isinstance(result, int)
            assert 1 <= result <= 6
            values.add(result)
        # Should hit most values in 100 trials
        assert len(values) >= 4

    def test_rnd_100_returns_integer_1_to_100(self, basic):
        values = set()
        for _ in range(200):
            result = basic.evaluate_expression('RND(100)')
            assert isinstance(result, int)
            assert 1 <= result <= 100
            values.add(result)
        assert len(values) >= 20

    def test_successive_calls_differ(self, basic):
        """Multiple RND(6) calls should produce different values."""
        values = [basic.evaluate_expression('RND(6)') for _ in range(20)]
        assert len(set(values)) > 1


class TestRndZero:
    """RND(0) returns a fresh random fraction (CoCo Color BASIC)."""

    def test_rnd_zero_is_a_fraction(self, basic):
        for _ in range(50):
            value = basic.evaluate_expression('RND(0)')
            assert isinstance(value, float)
            assert 0 <= value < 1

    def test_rnd_zero_does_not_repeat(self, basic):
        values = {basic.evaluate_expression('RND(0)') for _ in range(20)}
        assert len(values) > 1

    def test_rnd_zero_before_any_rnd_is_random(self, basic):
        assert 0 <= basic.evaluate_expression('RND(0)') < 1

    def test_rnd_zero_sequence_reproducible_after_reseed(self, basic):
        basic.evaluate_expression('RND(-5)')
        first = [basic.evaluate_expression('RND(0)') for _ in range(3)]
        basic.evaluate_expression('RND(-5)')
        second = [basic.evaluate_expression('RND(0)') for _ in range(3)]
        assert first == second


class TestRndNegative:
    """RND(-n) reseeds the generator and returns a float."""

    def test_negative_reseeds(self, basic):
        """Same negative seed produces same sequence."""
        basic.evaluate_expression('RND(-42)')
        a = basic.evaluate_expression('RND(6)')
        basic.evaluate_expression('RND(-42)')
        b = basic.evaluate_expression('RND(6)')
        assert a == b

    def test_different_negative_seeds_differ(self, basic):
        basic.evaluate_expression('RND(-100)')
        a = basic.evaluate_expression('RND(6)')
        basic.evaluate_expression('RND(-200)')
        b = basic.evaluate_expression('RND(6)')
        assert a != b

    def test_negative_seed_returns_float(self, basic):
        """RND(-n) itself returns a float (0 < x < 1)."""
        result = basic.evaluate_expression('RND(-7)')
        assert isinstance(result, float)
        assert 0 < result < 1

    def test_negative_seed_is_deterministic(self, basic):
        assert basic.evaluate_expression('RND(-42)') == basic.evaluate_expression('RND(-42)')


class TestRndWithRandomize:
    """RANDOMIZE and RND interact correctly."""

    def test_randomize_then_rnd(self, basic):
        """RANDOMIZE sets seed, RND produces deterministic sequence."""
        basic.process_command('RANDOMIZE 99')
        a = basic.evaluate_expression('RND(6)')
        basic.process_command('RANDOMIZE 99')
        b = basic.evaluate_expression('RND(6)')
        assert a == b

    def test_rnd_in_program(self, basic, helpers):
        """RND works in a running program."""
        result = helpers.execute_program(basic, [
            '10 RANDOMIZE 42',
            '20 PRINT RND(6)',
        ])
        output = helpers.get_text_output(result)
        assert len(output) == 1
        val = int(output[0].strip())
        assert 1 <= val <= 6
