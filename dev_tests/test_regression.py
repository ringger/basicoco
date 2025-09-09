#!/usr/bin/env python3
"""Test for regression issues after refactoring"""

from emulator.core import CoCoBasic
import sys

basic = CoCoBasic()

# Run a simple test
test_failures = []

# Test that we haven't broken something crucial
try:
    # Test DIM command for arrays
    result = basic.execute_command('DIM A(10)')
    print("DIM A(10):", result)
    
    result = basic.execute_command('LET A(5) = 42')
    print("LET A(5) = 42:", result)
    
    val = basic.evaluate_expression('A(5)')
    print(f"A(5) = {val}")
    if val != 42:
        test_failures.append(f'Array access failed: expected 42, got {val}')
except Exception as e:
    test_failures.append(f'Array test failed: {e}')

# Test function detection vs array detection
try:
    result = basic.execute_command('DIM B(5)')
    result = basic.execute_command('LET B(3) = 7')
    val = basic.evaluate_expression('B(3)')
    print(f"B(3) = {val}")
    if val != 7:
        test_failures.append(f'Array B access failed: expected 7, got {val}')
except Exception as e:
    test_failures.append(f'Array B test failed: {e}')

# Test that LEFT$ is not treated as an array
try:
    val = basic.evaluate_expression('LEFT$("TEST", 2)')
    print(f'LEFT$("TEST", 2) = {val}')
    if val != 'TE':
        test_failures.append(f'LEFT$ function failed: expected TE, got {val}')
except Exception as e:
    test_failures.append(f'LEFT$ test failed: {e}')

# Test INKEY$ special function
try:
    basic.keyboard_buffer = ['X']
    val = basic.evaluate_expression('INKEY$')
    print(f'INKEY$ = {val}')
    if val != 'X':
        test_failures.append(f'INKEY$ failed: expected X, got {val}')
except Exception as e:
    test_failures.append(f'INKEY$ test failed: {e}')

# Test evaluate_single_function if it's still called
try:
    # This might be an issue - evaluate_single_function might still be needed
    result = basic.evaluate_single_function('LEFT$("HELLO", 3)')
    print(f'evaluate_single_function test = {result}')
except AttributeError:
    print("evaluate_single_function method no longer exists (expected)")
except Exception as e:
    test_failures.append(f'evaluate_single_function test failed: {e}')

if test_failures:
    print('\nTest failures found:')
    for failure in test_failures:
        print(f'  - {failure}')
    sys.exit(1)
else:
    print('\n✅ All regression tests passed!')