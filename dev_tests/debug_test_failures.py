#!/usr/bin/env python3
"""Debug specific test failures"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from emulator.core import CoCoBasic

# Test 1: Graphics - DRAW command with variables
print("Test 1: DRAW command with variables")
basic = CoCoBasic()
basic.variables['X'] = 10
result = basic.execute_command('DRAW "R" + STR$(X)')
print(f"  DRAW command result: {result}")
print()

# Test 2: INKEY$ comparison  
print("Test 2: INKEY$ in expressions")
basic = CoCoBasic()
basic.keyboard_buffer = ['A']
# First get INKEY$ value
val = basic.evaluate_expression('INKEY$')
print(f"  INKEY$ returned: {repr(val)}")
print(f"  Buffer after: {basic.keyboard_buffer}")
print()

# Test 3: Variable assignment edge cases
print("Test 3: Complex variable expressions")
basic = CoCoBasic()
basic.variables['A'] = 5
basic.variables['B'] = 3
result = basic.execute_command('LET C = A * B + 2')
print(f"  LET C = A * B + 2 result: {result}")
print(f"  C = {basic.variables.get('C')}")
print()

# Test 4: Cross-command - likely FOR loop with functions
print("Test 4: FOR loop with function")
basic = CoCoBasic()
program = """
10 FOR I = 1 TO LEN("TEST")
20 PRINT I
30 NEXT I
"""
for line in program.strip().split('\n'):
    basic.execute_command(line)

result = basic.execute_command('RUN')
print(f"  FOR loop result has {len(result)} items")
for item in result:
    if item.get('type') == 'text':
        print(f"    Output: {item.get('text')}")
print()

# Test 5: Edge case that might be failing
print("Test 5: Expression evaluation edge cases")
basic = CoCoBasic()
try:
    # This might be calling old methods
    basic.variables['S$'] = "HELLO"
    result = basic.evaluate_expression('LEN(S$)')
    print(f"  LEN(S$) = {result}")
except Exception as e:
    print(f"  ERROR: {e}")