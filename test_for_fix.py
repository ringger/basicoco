#!/usr/bin/env python3

"""
Test the FOR loop fix specifically
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import CoCoBasic

def test_for_loop_fix():
    basic = CoCoBasic()
    
    print("Testing FOR loop parsing fix:")
    print("=" * 40)
    
    # Test 1: Simple FOR with colon (the problem case)
    print("\n1. Testing: FOR I=1 TO 5:")
    try:
        result = basic.execute_command('FOR I=1 TO 5:')
        print(f"   Result: {result}")
        print(f"   Variables: {basic.variables}")
        print(f"   FOR stack: {basic.for_stack}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 2: Simple FOR without colon
    print("\n2. Testing: FOR I=1 TO 3")
    try:
        basic.for_stack.clear()  # Clear previous
        result = basic.execute_command('FOR I=1 TO 3')
        print(f"   Result: {result}")
        print(f"   Variables: {basic.variables}")
        print(f"   FOR stack: {basic.for_stack}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 3: Multi-statement line (the real problem)
    print("\n3. Testing program with multi-statement FOR:")
    try:
        basic.execute_command('CLEAR')
        
        # Add the problematic line
        line_num, code = basic.parse_line('10 FOR I=1 TO 3: PRINT I: NEXT I')
        if line_num is not None:
            basic.program[line_num] = code
            print(f"   Added to program: {line_num} {code}")
        
        # Try to run it
        print("   Running program...")
        result = basic.execute_command('RUN')
        print(f"   RUN result: {result}")
        
    except Exception as e:
        print(f"   ERROR: {e}")
    
    print("\n" + "=" * 40)

if __name__ == '__main__':
    test_for_loop_fix()