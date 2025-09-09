#!/usr/bin/env python3
"""Test to see if old function code paths are still used"""

from emulator.core import CoCoBasic

# Create a test to see if the old code paths are actually used
class DebugBasic(CoCoBasic):
    def substitute_basic_functions(self, expr):
        print(f'OLD substitute_basic_functions called with: {expr}')
        return super().substitute_basic_functions(expr)
        
    def evaluate_single_function(self, expr):
        print(f'OLD evaluate_single_function called with: {expr}')
        return super().evaluate_single_function(expr)

debug_basic = DebugBasic()

print("Testing to see if old function code paths are still used...")
print("=" * 60)

# Test some expressions to see if old code paths are hit
print('Testing: 2 + 3')
result = debug_basic.evaluate_expression('2 + 3')
print(f'Result: {result}')
print()

print('Testing: LEFT$("HELLO", 3)')
result = debug_basic.evaluate_expression('LEFT$("HELLO", 3)')
print(f'Result: {result}')
print()

print('Testing nested: LEN(LEFT$("HELLO", 3))')
result = debug_basic.evaluate_expression('LEN(LEFT$("HELLO", 3))')
print(f'Result: {result}')
print()

print('Testing variable with function: X = 5, then ABS(X)')
debug_basic.variables['X'] = -5
result = debug_basic.evaluate_expression('ABS(X)')
print(f'Result: {result}')
print()

print("=" * 60)
print("If no 'OLD' messages appear above, the old code paths are not used!")