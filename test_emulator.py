#!/usr/bin/env python3

"""
Simple test script for the TRS-80 Color Computer BASIC emulator
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import CoCoBasic

def test_basic_commands():
    print("Testing TRS-80 Color Computer BASIC Emulator")
    print("=" * 50)
    
    basic = CoCoBasic()
    
    # Test 1: Simple PRINT
    print("\n1. Testing PRINT command:")
    result = basic.execute_command('PRINT "HELLO WORLD"')
    print(f"Output: {result}")
    
    # Test 2: Variable assignment and PRINT
    print("\n2. Testing variables:")
    basic.execute_command('A = 42')
    result = basic.execute_command('PRINT A')
    print(f"Output: {result}")
    
    # Test 3: Simple program
    print("\n3. Testing simple program:")
    line_num, code = basic.parse_line('10 PRINT "LINE 10"')
    if line_num is not None:
        basic.program[line_num] = code
    line_num, code = basic.parse_line('20 PRINT "LINE 20"')
    if line_num is not None:
        basic.program[line_num] = code
    result = basic.execute_command('LIST')
    print("Program listing:")
    for item in result:
        if item['type'] == 'text':
            print(f"  {item['text']}")
    
    # Test 4: Run program
    print("\n4. Running program:")
    result = basic.execute_command('RUN')
    for item in result:
        if item['type'] == 'text':
            print(f"  {item['text']}")
    
    # Test 5: FOR/NEXT loop
    print("\n5. Testing FOR/NEXT loop:")
    basic.execute_command('CLEAR')
    line_num, code = basic.parse_line('10 FOR I=1 TO 3')
    if line_num is not None:
        basic.program[line_num] = code
    line_num, code = basic.parse_line('20 PRINT I')
    if line_num is not None:
        basic.program[line_num] = code
    line_num, code = basic.parse_line('30 NEXT I')
    if line_num is not None:
        basic.program[line_num] = code
    result = basic.execute_command('RUN')
    for item in result:
        if item['type'] == 'text':
            print(f"  {item['text']}")
    
    # Test 6: Graphics commands
    print("\n6. Testing graphics commands:")
    basic.execute_command('CLEAR')
    result = basic.execute_command('PMODE 4,1')
    print(f"PMODE result: {result}")
    result = basic.execute_command('PSET(100,100)')
    print(f"PSET result: {result}")
    result = basic.execute_command('LINE(0,0)-(255,191)')
    print(f"LINE result: {result}")
    result = basic.execute_command('CIRCLE(128,96),50')
    print(f"CIRCLE result: {result}")
    
    # Test 7: Sound command
    print("\n7. Testing SOUND command:")
    result = basic.execute_command('SOUND 1000,30')
    print(f"SOUND result: {result}")
    
    print("\n" + "=" * 50)
    print("All tests completed!")

if __name__ == '__main__':
    test_basic_commands()