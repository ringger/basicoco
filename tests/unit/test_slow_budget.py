"""The slow-test budget check (#91, tests/plugins/slow_budget.py)."""

import slow_budget

pytest_plugins = ['pytester']

SAMPLE_TESTS = """
    import time
    import pytest

    def test_quick():
        pass

    def test_sluggish():
        time.sleep(0.15)

    @pytest.mark.slow
    def test_marked_slow():
        time.sleep(0.15)
"""


def run_sample(pytester, monkeypatch, budget):
    # Checked as if untraced, so this also holds in a coverage run
    monkeypatch.setattr(slow_budget, '_measuring', lambda: False)
    pytester.makeini(f"""
        [pytest]
        slow_test_budget = {budget}
        markers =
            slow: slow test
    """)
    pytester.makepyfile(SAMPLE_TESTS)
    # pytest-playwright's soft-assertion hook can't nest inside this run
    return pytester.runpytest('-p', 'slow_budget', '-p', 'no:playwright')


def test_an_unmarked_test_over_budget_is_flagged(pytester, monkeypatch):
    result = run_sample(pytester, monkeypatch, 0.05)
    result.assert_outcomes(passed=3, warnings=1)
    result.stdout.fnmatch_lines(['*test_sluggish took *s (budget 0.05s)*mark it @pytest.mark.slow*'])
    assert 'test_marked_slow took' not in result.stdout.str()
    assert 'test_quick took' not in result.stdout.str()


def test_a_zero_budget_turns_the_check_off(pytester, monkeypatch):
    run_sample(pytester, monkeypatch, 0).assert_outcomes(passed=3, warnings=0)
