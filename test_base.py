#!/usr/bin/env python3

"""
Base test framework for TRS-80 Color Computer BASIC emulator tests.
Provides common setup, teardown, assertion methods, and utilities.
"""

import sys
import os
import traceback
from typing import List, Dict, Any, Optional, Union
from abc import ABC, abstractmethod

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

from app import CoCoBasic


class TestResult:
    """Represents the result of a single test case"""
    def __init__(self, name: str, passed: bool, message: str = "", error: Optional[Exception] = None):
        self.name = name
        self.passed = passed
        self.message = message
        self.error = error
        self.traceback = None
        if error:
            self.traceback = traceback.format_exc()


class TestSuite:
    """Collection of test results and statistics"""
    def __init__(self, name: str):
        self.name = name
        self.results: List[TestResult] = []
        self.setup_error: Optional[Exception] = None
        self.teardown_error: Optional[Exception] = None

    def add_result(self, result: TestResult):
        self.results.append(result)

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def total_count(self) -> int:
        return len(self.results)

    @property
    def success_rate(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.passed_count / self.total_count


class BaseTestCase(ABC):
    """
    Base class for all TRS-80 BASIC emulator tests.
    
    Provides common setup/teardown, assertion methods, and utilities
    for testing the CoCoBasic interpreter.
    """

    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        self.basic: Optional[CoCoBasic] = None
        self.test_suite = TestSuite(self.name)

    def setUp(self):
        """Set up test fixture - create fresh CoCoBasic instance"""
        try:
            self.basic = CoCoBasic()
            self.basic.execute_command('NEW')  # Clear any existing state
        except Exception as e:
            self.test_suite.setup_error = e
            raise

    def tearDown(self):
        """Clean up after test"""
        try:
            if self.basic:
                self.basic = None
        except Exception as e:
            self.test_suite.teardown_error = e

    def run_test_method(self, method_name: str) -> TestResult:
        """Run a single test method and return the result"""
        try:
            method = getattr(self, method_name)
            method()
            return TestResult(method_name, True, "Test passed")
        except AssertionError as e:
            return TestResult(method_name, False, str(e), e)
        except Exception as e:
            return TestResult(method_name, False, f"Unexpected error: {str(e)}", e)

    def run_all_tests(self) -> TestSuite:
        """Discover and run all test methods (methods starting with 'test_')"""
        try:
            self.setUp()
        except Exception as e:
            # If setup fails, return early with setup error
            return self.test_suite

        test_methods = [method for method in dir(self) 
                       if method.startswith('test_') and callable(getattr(self, method))]
        
        for method_name in sorted(test_methods):
            result = self.run_test_method(method_name)
            self.test_suite.add_result(result)

        try:
            self.tearDown()
        except Exception as e:
            # Teardown error is recorded but doesn't fail the tests
            pass

        return self.test_suite

    # Assertion methods for different types of results
    def assert_command_result(self, command: str, expected_type: str = None, 
                            expected_text: str = None, expected_count: int = None):
        """Assert that a command produces expected results"""
        if not self.basic:
            raise AssertionError("CoCoBasic instance not initialized")
        
        result = self.basic.execute_command(command)
        
        if expected_count is not None:
            if len(result) != expected_count:
                raise AssertionError(f"Expected {expected_count} result items, got {len(result)}")
        
        if expected_type is not None or expected_text is not None:
            if not result:
                raise AssertionError(f"Command '{command}' returned no results")
            
            item = result[0]
            
            if expected_type is not None and item.get('type') != expected_type:
                raise AssertionError(f"Expected type '{expected_type}', got '{item.get('type')}'")
            
            if expected_text is not None and item.get('text') != expected_text:
                raise AssertionError(f"Expected text '{expected_text}', got '{item.get('text')}'")

    def assert_text_output(self, command: str, expected_text: str):
        """Assert that a command produces specific text output"""
        self.assert_command_result(command, expected_type='text', expected_text=expected_text)

    def assert_error_output(self, command: str, expected_error: str = None):
        """Assert that a command produces an error"""
        if not self.basic:
            raise AssertionError("CoCoBasic instance not initialized")
        
        result = self.basic.execute_command(command)
        
        if not result or result[0].get('type') != 'error':
            raise AssertionError(f"Expected error from command '{command}', got: {result}")
        
        if expected_error is not None:
            actual_error = result[0].get('message', '')
            if expected_error not in actual_error:
                raise AssertionError(f"Expected error containing '{expected_error}', got '{actual_error}'")

    def assert_graphics_output(self, command: str, expected_graphics_type: str = None):
        """Assert that a command produces graphics output"""
        if not self.basic:
            raise AssertionError("CoCoBasic instance not initialized")
        
        result = self.basic.execute_command(command)
        
        graphics_types = ['pmode', 'pset', 'preset', 'line', 'circle', 'draw', 'pcls', 
                         'set_pmode', 'clear_graphics', 'turtle_graphics', 'paint']
        has_graphics = any(item.get('type') in graphics_types for item in result)
        
        if not has_graphics:
            raise AssertionError(f"Expected graphics output from command '{command}', got: {result}")
        
        if expected_graphics_type is not None:
            has_expected_type = any(item.get('type') == expected_graphics_type for item in result)
            if not has_expected_type:
                raise AssertionError(f"Expected graphics type '{expected_graphics_type}' from command '{command}'")

    def assert_variable_equals(self, variable_name: str, expected_value: Union[int, float, str]):
        """Assert that a variable has the expected value"""
        if not self.basic:
            raise AssertionError("CoCoBasic instance not initialized")
        
        actual_value = self.basic.variables.get(variable_name)
        
        if actual_value != expected_value:
            raise AssertionError(f"Variable '{variable_name}': expected {expected_value}, got {actual_value}")

    def assert_program_lines(self, expected_line_count: int):
        """Assert that the program has the expected number of lines"""
        if not self.basic:
            raise AssertionError("CoCoBasic instance not initialized")
        
        actual_count = len(self.basic.program)
        
        if actual_count != expected_line_count:
            raise AssertionError(f"Expected {expected_line_count} program lines, got {actual_count}")

    def assertTrue(self, condition, message: str = None):
        """Assert that condition is true"""
        if not condition:
            raise AssertionError(message or f"Expected True, got {condition}")

    def assertFalse(self, condition, message: str = None):
        """Assert that condition is false"""
        if condition:
            raise AssertionError(message or f"Expected False, got {condition}")

    def assertEqual(self, first, second, message: str = None):
        """Assert that two values are equal"""
        if first != second:
            raise AssertionError(message or f"Expected {second}, got {first}")

    def assertNotEqual(self, first, second, message: str = None):
        """Assert that two values are not equal"""
        if first == second:
            raise AssertionError(message or f"Expected values to be different, both are {first}")

    def assertIn(self, item, container, message: str = None):
        """Assert that item is in container"""
        if item not in container:
            raise AssertionError(message or f"Expected {item} to be in {container}")

    def assertNotIn(self, item, container, message: str = None):
        """Assert that item is not in container"""
        if item in container:
            raise AssertionError(message or f"Expected {item} not to be in {container}")

    # Helper methods for common test operations
    def load_program(self, program_lines: List[str]):
        """Load a program from a list of line strings"""
        if not self.basic:
            raise AssertionError("CoCoBasic instance not initialized")
        
        for line in program_lines:
            line_num, code = self.basic.parse_line(line)
            if line_num is not None:
                self.basic.program[line_num] = code
                self.basic.expand_line_to_sublines(line_num, code)

    def execute_program(self, program_lines: List[str]) -> List[Dict[str, Any]]:
        """Load and run a program, returning the execution results"""
        self.load_program(program_lines)
        return self.basic.execute_command('RUN')

    def get_text_output(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract text output from command results"""
        return [item['text'] for item in results if item.get('type') == 'text']

    def get_error_messages(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract error messages from command results"""
        return [item['message'] for item in results if item.get('type') == 'error']

    def simulate_input(self, input_value: str):
        """Simulate user input for INPUT commands"""
        if not self.basic:
            raise AssertionError("CoCoBasic instance not initialized")
        
        # This would be used in conjunction with INPUT command testing
        # Implementation depends on how INPUT is handled in the emulator
        pass

    def mock_graphics_output(self):
        """Mock graphics output for headless testing"""
        # This could disable actual graphics operations for testing
        # Implementation would depend on the graphics system
        pass

    @abstractmethod
    def test_basic_functionality(self):
        """Every test class must implement this basic test"""
        pass


class BasicCommandTest(BaseTestCase):
    """Base class for testing individual BASIC commands"""
    
    def __init__(self, command_name: str):
        super().__init__(f"{command_name}_test")
        self.command_name = command_name

    def test_basic_functionality(self):
        """Basic test that the command exists and can be parsed"""
        # This is a placeholder - individual command tests should override
        pass


class IntegrationTest(BaseTestCase):
    """Base class for integration tests that test multiple commands together"""
    
    def test_basic_functionality(self):
        """Basic integration test"""
        # Test that basic operations work together
        self.assert_text_output('PRINT "HELLO"', 'HELLO')
        self.basic.execute_command('A = 5')
        self.assert_variable_equals('A', 5)
        self.assert_text_output('PRINT A', '5')


def print_test_results(test_suite: TestSuite, verbose: bool = False):
    """Print formatted test results"""
    print(f"\n{'='*60}")
    print(f"Test Suite: {test_suite.name}")
    print(f"{'='*60}")
    
    if test_suite.setup_error:
        print(f"❌ SETUP ERROR: {test_suite.setup_error}")
        return

    print(f"Tests run: {test_suite.total_count}")
    print(f"Passed: {test_suite.passed_count} ✅")
    print(f"Failed: {test_suite.failed_count} ❌")
    print(f"Success rate: {test_suite.success_rate:.1%}")
    
    if verbose or test_suite.failed_count > 0:
        print(f"\n{'Detailed Results':<40} {'Status'}")
        print(f"{'-'*50}")
        
        for result in test_suite.results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"{result.name:<40} {status}")
            
            if not result.passed:
                print(f"    Message: {result.message}")
                if verbose and result.traceback:
                    print(f"    Traceback: {result.traceback}")
    
    if test_suite.teardown_error:
        print(f"\n⚠️  TEARDOWN ERROR: {test_suite.teardown_error}")

    print(f"{'='*60}")


if __name__ == '__main__':
    # Demo of the base test framework
    class DemoTest(BaseTestCase):
        def test_basic_functionality(self):
            self.assert_text_output('PRINT "TEST"', 'TEST')
        
        def test_variables(self):
            self.basic.execute_command('X = 42')
            self.assert_variable_equals('X', 42)
            self.assert_text_output('PRINT X', '42')
        
        def test_program_loading(self):
            program = [
                '10 PRINT "HELLO"',
                '20 PRINT "WORLD"'
            ]
            self.load_program(program)
            self.assert_program_lines(2)

    # Run the demo test
    demo = DemoTest("Demo Test")
    results = demo.run_all_tests()
    print_test_results(results, verbose=True)