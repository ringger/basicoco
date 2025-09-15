#!/usr/bin/env python3

"""
Unit Test Runner for TRS-80 Color Computer BASIC emulator.
Runs only unit tests located in tests/unit/ directory.
"""

import sys
import os
import importlib.util
import argparse
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

from test_base import BaseTestCase, TestSuite, TestResult, print_test_results


class UnitTestDiscovery:
    """Discovers unit test files in the tests/unit/ directory"""
    
    def __init__(self):
        self.test_directory = Path("tests/unit")
        self.discovered_tests: List[Dict[str, Any]] = []

    def discover_test_files(self, pattern: str = "test_*.py") -> List[Path]:
        """Find all unit test files matching the pattern"""
        if not self.test_directory.exists():
            return []
        return list(self.test_directory.glob(pattern))

    def load_test_module(self, file_path: Path):
        """Load a Python module from file path"""
        spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
                return module
            except Exception as e:
                print(f"⚠️  Failed to load {file_path}: {e}")
                return None
        return None

    def discover_test_classes(self, module) -> List[type]:
        """Find test classes in a module (classes inheriting from BaseTestCase)"""
        test_classes = []
        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, type) and 
                issubclass(obj, BaseTestCase) and 
                obj is not BaseTestCase):
                test_classes.append(obj)
        return test_classes

    def discover_test_functions(self, module) -> List[callable]:
        """Find standalone test functions (functions starting with 'test_')"""
        test_functions = []
        for name in dir(module):
            obj = getattr(module, name)
            if callable(obj) and name.startswith('test_') and not name.startswith('test_base'):
                test_functions.append(obj)
        return test_functions

    def discover_all_tests(self) -> List[Dict[str, Any]]:
        """Discover all unit tests"""
        self.discovered_tests = []
        
        test_files = self.discover_test_files()
        
        for file_path in test_files:
            module = self.load_test_module(file_path)
            if not module:
                continue

            # Look for test classes
            test_classes = self.discover_test_classes(module)
            for test_class in test_classes:
                self.discovered_tests.append({
                    'type': 'class',
                    'file': str(file_path),
                    'name': test_class.__name__,
                    'class': test_class,
                    'module': module
                })

            # Look for standalone test functions
            test_functions = self.discover_test_functions(module)
            for test_function in test_functions:
                self.discovered_tests.append({
                    'type': 'function',
                    'file': str(file_path),
                    'name': test_function.__name__,
                    'function': test_function,
                    'module': module
                })

        return self.discovered_tests


class UnitTestRunner:
    """Runs unit tests and collects results"""
    
    def __init__(self, verbose: bool = False, stop_on_failure: bool = False):
        self.verbose = verbose
        self.stop_on_failure = stop_on_failure
        self.all_results: List[TestSuite] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def run_test_class(self, test_class: type) -> TestSuite:
        """Run all test methods in a test class"""
        try:
            instance = test_class()
            return instance.run_all_tests()
        except Exception as e:
            # Create a failed test suite for classes that can't be instantiated
            suite = TestSuite(test_class.__name__)
            suite.setup_error = e
            return suite

    def run_test_function(self, test_function: callable, file_path: str) -> TestSuite:
        """Run a standalone test function"""
        function_name = test_function.__name__
        suite = TestSuite(f"{Path(file_path).stem}::{function_name}")
        
        try:
            test_function()
            suite.add_result(TestResult(function_name, True, "Function test passed"))
        except AssertionError as e:
            suite.add_result(TestResult(function_name, False, str(e), e))
        except Exception as e:
            suite.add_result(TestResult(function_name, False, f"Unexpected error: {str(e)}", e))
        
        return suite

    def run_discovered_tests(self, discovered_tests: List[Dict[str, Any]]) -> List[TestSuite]:
        """Run all discovered unit tests"""
        self.start_time = time.time()
        self.all_results = []
        
        total_tests = len(discovered_tests)
        print(f"Running {total_tests} unit test suites...")
        print("=" * 60)
        
        for i, test_info in enumerate(discovered_tests):
            file_name = Path(test_info['file']).name
            test_name = test_info['name']
            
            print(f"[{i+1}/{total_tests}] {file_name}::{test_name} ", end="")
            
            if test_info['type'] == 'class':
                suite = self.run_test_class(test_info['class'])
            else:  # function
                suite = self.run_test_function(test_info['function'], test_info['file'])
            
            self.all_results.append(suite)
            
            # Print immediate feedback
            if suite.setup_error:
                print("❌ SETUP FAILED")
            elif suite.failed_count > 0:
                print(f"❌ {suite.failed_count}/{suite.total_count} failed")
            else:
                print(f"✅ {suite.total_count} passed")
            
            if self.verbose:
                print_test_results(suite, verbose=False)
            
            if self.stop_on_failure and suite.failed_count > 0:
                print("Stopping on first failure...")
                break
        
        self.end_time = time.time()
        return self.all_results

    def print_summary(self):
        """Print overall test summary"""
        if not self.all_results:
            print("No unit tests were run.")
            return

        total_suites = len(self.all_results)
        total_tests = sum(suite.total_count for suite in self.all_results)
        total_passed = sum(suite.passed_count for suite in self.all_results)
        total_failed = sum(suite.failed_count for suite in self.all_results)
        setup_errors = sum(1 for suite in self.all_results if suite.setup_error)
        
        duration = self.end_time - self.start_time if self.start_time and self.end_time else 0
        
        print("\n" + "=" * 60)
        print("UNIT TEST SUMMARY")
        print("=" * 60)
        print(f"Test suites run: {total_suites}")
        print(f"Total tests: {total_tests}")
        print(f"Passed: {total_passed} ✅")
        print(f"Failed: {total_failed} ❌")
        if setup_errors > 0:
            print(f"Setup errors: {setup_errors} ⚠️")
        
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        print(f"Success rate: {success_rate:.1f}%")
        print(f"Duration: {duration:.2f}s")
        
        if total_failed > 0:
            print("\nFAILED UNIT TEST SUITES:")
            for suite in self.all_results:
                if suite.failed_count > 0:
                    print(f"  ❌ {suite.name}: {suite.failed_count}/{suite.total_count} failed")
        
        if setup_errors > 0:
            print("\nSETUP ERROR SUITES:")
            for suite in self.all_results:
                if suite.setup_error:
                    print(f"  ⚠️  {suite.name}: {suite.setup_error}")

    def get_exit_code(self) -> int:
        """Return appropriate exit code based on test results"""
        if not self.all_results:
            return 1  # No tests run
        
        total_failed = sum(suite.failed_count for suite in self.all_results)
        setup_errors = sum(1 for suite in self.all_results if suite.setup_error)
        
        return 0 if (total_failed == 0 and setup_errors == 0) else 1


def main():
    """Main entry point for the unit test runner"""
    parser = argparse.ArgumentParser(
        description="TRS-80 Color Computer BASIC Emulator Unit Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_unit_tests.py                    # Run all unit tests
  python run_unit_tests.py -v                 # Run with verbose output
  python run_unit_tests.py --stop-on-failure  # Stop on first failure
        """
    )
    
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Show detailed test results"
    )
    
    parser.add_argument(
        "--stop-on-failure", 
        action="store_true", 
        help="Stop running tests after the first failure"
    )
    
    args = parser.parse_args()
    
    print("TRS-80 Color Computer BASIC Emulator Unit Test Runner")
    print("=" * 60)
    
    # Discover unit tests
    discovery = UnitTestDiscovery()
    print("Discovering unit tests in tests/unit/...")
    
    discovered_tests = discovery.discover_all_tests()
    
    if not discovered_tests:
        print("❌ No unit tests found!")
        return 1
    
    print(f"Found {len(discovered_tests)} unit test suites")
    
    # Run tests
    runner = UnitTestRunner(verbose=args.verbose, stop_on_failure=args.stop_on_failure)
    runner.run_discovered_tests(discovered_tests)
    
    # Print summary
    runner.print_summary()
    
    return runner.get_exit_code()


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)