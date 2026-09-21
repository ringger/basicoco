"""Keep the default test run fast (#91): warn about any test not marked
`slow` whose call phase takes longer than the budget, the `slow_test_budget`
ini value in seconds (0 turns the check off).

The check is skipped while coverage or a debugger is tracing, since tracing
makes every test several times slower.
"""

import sys

import pytest


def pytest_addoption(parser):
    parser.addini('slow_test_budget',
                  'Seconds a test not marked slow may take before it is flagged (0: no check)',
                  default='1.0')


def _measuring():
    """True while coverage or a debugger traces the run."""
    if sys.gettrace() is not None:
        return True
    coverage = sys.modules.get('coverage')
    return bool(coverage and coverage.Coverage.current())


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    report = yield
    budget = float(item.config.getini('slow_test_budget'))
    if (call.when == 'call' and budget > 0 and report.duration > budget
            and item.get_closest_marker('slow') is None and not _measuring()):
        item.warn(pytest.PytestWarning(
            f'{item.nodeid} took {report.duration:.1f}s (budget {budget:g}s): '
            'mark it @pytest.mark.slow or make it faster'))
    return report
