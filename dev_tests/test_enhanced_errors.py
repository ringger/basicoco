#!/usr/bin/env python3

"""
Test script to demonstrate enhanced error reporting with line numbers and context.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from emulator.core import CoCoBasic

def test_enhanced_errors():
    """Test the enhanced error reporting system"""
    basic = CoCoBasic()
    
    print("Testing Enhanced Error Reporting")
    print("=" * 50)
    
    # Test 1: Undefined variable
    print("\n1. Testing undefined variable error:")
    try:
        result = basic.execute_command('PRINT UNDEFINED_VAR')
        print(f"Result: {result}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 2: Undefined function
    print("\n2. Testing undefined function error:")
    try:
        result = basic.execute_command('PRINT BADFUNCTION(5)')
        print(f"Result: {result}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 3: Undimensioned array
    print("\n3. Testing undimensioned array error:")
    try:
        result = basic.execute_command('PRINT UNDIM_ARRAY(5)')
        print(f"Result: {result}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 4: Type mismatch in array index
    print("\n4. Testing type mismatch in array index:")
    try:
        basic.execute_command('DIM TEST_ARRAY(10)')
        result = basic.execute_command('PRINT TEST_ARRAY("NOT_A_NUMBER")')
        print(f"Result: {result}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 5: Function with wrong argument count
    print("\n5. Testing function with wrong argument count:")
    try:
        result = basic.execute_command('PRINT LEFT$("HELLO")')  # Missing second argument
        print(f"Result: {result}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 6: Test in program context with line numbers
    print("\n6. Testing errors in program context:")
    program = [
        '10 A = 5',
        '20 B = UNDEFINED_VAR',  # This should show line 20
        '30 PRINT A + B'
    ]
    
    for line in program:
        basic.execute_command(line)
    
    try:
        result = basic.execute_command('RUN')
        print(f"Program result: {result}")
    except Exception as e:
        print(f"Program exception: {e}")

if __name__ == '__main__':
    test_enhanced_errors()