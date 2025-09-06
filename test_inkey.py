#!/usr/bin/env python3

"""
Test INKEY$ function for non-blocking keyboard input
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import CoCoBasic

def test_inkey():
    basic = CoCoBasic()
    
    print("Testing INKEY$ function:")
    print("=" * 40)
    
    try:
        basic.execute_command('NEW')
        
        # Test INKEY$ with empty buffer
        print("Testing INKEY$ with empty buffer:")
        result = basic.execute_command('PRINT INKEY$')
        print(f'PRINT INKEY$ (empty buffer): "{result[0]["text"] if result and "text" in result[0] else "ERROR"}"')
        
        # Add some keys to the buffer manually
        print("\nAdding keys to buffer manually:")
        basic.add_key_to_buffer('A')
        basic.add_key_to_buffer('B') 
        basic.add_key_to_buffer('C')
        print("Added keys: A, B, C")
        
        # Test retrieving keys one by one
        print("\nRetrieving keys with INKEY$:")
        for i in range(4):  # Try one extra to test empty buffer
            result = basic.execute_command('PRINT INKEY$')
            key = result[0]["text"] if result and "text" in result[0] else "ERROR"
            print(f'INKEY$ call {i+1}: "{key}"')
        
        # Test in a program that checks for keypress
        print("\nTesting in a program:")
        program_lines = [
            '10 PRINT "Press any key (or wait 5 loops for timeout)..."',
            '20 FOR I = 1 TO 5',
            '30 K$ = INKEY$',
            '40 IF K$ <> "" THEN PRINT "You pressed: "; K$: GOTO 60',
            '50 PRINT "Loop "; I; " - no key pressed"',
            '55 NEXT I',
            '60 PRINT "Done!"',
        ]
        
        # Add all program lines
        for line in program_lines:
            line_num, code = basic.parse_line(line)
            if line_num is not None:
                basic.program[line_num] = code
                basic.expand_line_to_sublines(line_num, code)
        
        print("\nProgram:")
        result = basic.execute_command('LIST')
        for item in result:
            if item.get('type') == 'text':
                print(f"  {item['text']}")
        
        print("\nRunning program with pre-loaded key 'X':")
        # Pre-load a key
        basic.add_key_to_buffer('X')
        
        result = basic.execute_command('RUN')
        
        for item in result:
            if item.get('type') == 'text':
                print(item['text'])
            elif item.get('type') == 'error':
                print(f"ERROR: {item['message']}")
        
        # Test with function call syntax INKEY$()
        print("\nTesting INKEY$() syntax:")
        basic.add_key_to_buffer('Y')
        result = basic.execute_command('PRINT INKEY$()')
        key = result[0]["text"] if result and "text" in result[0] else "ERROR"
        print(f'PRINT INKEY$(): "{key}"')
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_inkey()