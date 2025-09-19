"""
Pytest configuration and fixtures for TRS-80 Color Computer BASIC Emulator tests.

This file provides common fixtures and configuration that will be available
to all test files automatically.
"""

import pytest
import sys
import os
from typing import Dict, List, Any

# Add project root to Python path
sys.path.insert(0, os.path.dirname(__file__))

from emulator.core import CoCoBasic


@pytest.fixture
def basic():
    """
    Provide a fresh CoCoBasic instance for each test.

    This fixture automatically creates a new emulator instance and cleans
    up after each test to ensure test isolation.
    """
    emulator = CoCoBasic()
    emulator.process_command('NEW')  # Clear any existing state
    yield emulator
    # Cleanup happens automatically when the fixture goes out of scope


@pytest.fixture
def basic_with_program(basic):
    """
    Provide a CoCoBasic instance with a simple test program loaded.

    Useful for tests that need a basic program structure.
    """
    program_lines = [
        '10 PRINT "HELLO"',
        '20 A = 5',
        '30 PRINT A',
        '40 END'
    ]

    for line in program_lines:
        basic.process_command(line)

    return basic


@pytest.fixture
def graphics_basic(basic):
    """
    Provide a CoCoBasic instance with graphics mode initialized.

    Useful for graphics-related tests.
    """
    basic.process_command('PMODE 4,1')
    basic.process_command('PCLS')
    return basic


# Helper functions available to all tests
class TestHelpers:
    """Collection of helper methods for tests"""

    @staticmethod
    def get_text_output(results: List[Dict[str, Any]]) -> List[str]:
        """Extract text output from command results"""
        return [item['text'] for item in results if item.get('type') == 'text']

    @staticmethod
    def get_error_messages(results: List[Dict[str, Any]]) -> List[str]:
        """Extract error messages from command results"""
        return [item['message'] for item in results if item.get('type') == 'error']

    @staticmethod
    def get_graphics_output(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract graphics output from command results"""
        graphics_types = {'pmode', 'pset', 'preset', 'line', 'circle', 'draw', 'pcls',
                         'set_pmode', 'clear_graphics', 'turtle_graphics', 'paint'}
        return [item for item in results if item.get('type') in graphics_types]

    @staticmethod
    def assert_variable_equals(basic: CoCoBasic, var_name: str, expected_value: Any):
        """Assert that a variable has the expected value"""
        actual_value = basic.variables.get(var_name.upper())
        assert actual_value == expected_value, f"Variable {var_name}: expected {expected_value}, got {actual_value}"

    @staticmethod
    def assert_array_element_equals(basic: CoCoBasic, array_name: str, indices: List[int], expected_value: Any):
        """Assert that an array element has the expected value"""
        array_name = array_name.upper()
        if array_name in basic.arrays:
            try:
                actual_value = basic.arrays[array_name]
                for index in indices:
                    actual_value = actual_value[index]
                assert actual_value == expected_value, f"Array {array_name}[{indices}]: expected {expected_value}, got {actual_value}"
            except (IndexError, KeyError):
                pytest.fail(f"Array element {array_name}[{indices}] does not exist")
        else:
            pytest.fail(f"Array {array_name} does not exist")

    @staticmethod
    def assert_error_output(basic: CoCoBasic, command: str, expected_error: str = None):
        """Assert that a command produces an error"""
        result = basic.process_command(command)

        if not result or result[0].get('type') != 'error':
            pytest.fail(f"Expected error from command '{command}', got: {result}")

        if expected_error is not None:
            actual_error = result[0].get('message', '')
            if expected_error not in actual_error:
                pytest.fail(f"Expected error containing '{expected_error}', got '{actual_error}'")

    @staticmethod
    def load_program(basic: CoCoBasic, program_lines: List[str]):
        """Load a program from a list of line strings"""
        basic.process_command('NEW')
        for line in program_lines:
            basic.process_command(line)

    @staticmethod
    def execute_program(basic: CoCoBasic, program_lines: List[str]) -> List[Dict[str, Any]]:
        """Load and run a program, returning the execution results"""
        TestHelpers.load_program(basic, program_lines)
        return basic.process_command('RUN')


@pytest.fixture
def helpers():
    """Provide the TestHelpers class to tests"""
    return TestHelpers


# Pytest hooks and configuration
def pytest_configure(config):
    """Configure pytest with custom settings"""
    # Register custom markers
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line("markers", "integration: Integration tests for component interactions")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Tests that take longer than 1 second")
    config.addinivalue_line("markers", "graphics: Tests that involve graphics operations")
    config.addinivalue_line("markers", "io: Tests that involve input/output operations")
    config.addinivalue_line("markers", "cli: Tests that involve CLI interactions")
    config.addinivalue_line("markers", "websocket: Tests that involve WebSocket functionality")
    config.addinivalue_line("markers", "regression: Regression tests for specific bugs")


def pytest_collection_modifyitems(config, items):
    """Modify test items during collection"""
    # Add markers based on test file paths
    for item in items:
        # Add unit marker to tests in tests/unit/
        if "tests/unit/" in str(item.fspath):
            item.add_marker(pytest.mark.unit)

        # Add integration marker to tests in tests/integration/
        elif "tests/integration/" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Add e2e marker to tests in tests/integration/e2e/
        if "tests/integration/e2e/" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)

        # Add cli marker to tests in tests/integration/cli/
        if "tests/integration/cli/" in str(item.fspath):
            item.add_marker(pytest.mark.cli)

        # Add markers based on test names
        if "graphics" in item.name.lower():
            item.add_marker(pytest.mark.graphics)

        if "input" in item.name.lower() or "output" in item.name.lower():
            item.add_marker(pytest.mark.io)

        if "websocket" in item.name.lower():
            item.add_marker(pytest.mark.websocket)


@pytest.fixture(scope="session")
def test_data_dir():
    """Provide path to test data directory"""
    return os.path.join(os.path.dirname(__file__), "tests", "data")


# Performance fixtures
@pytest.fixture
def benchmark_basic(basic):
    """
    Provide a basic instance for performance benchmarking.

    Can be used with pytest-benchmark if installed.
    """
    return basic