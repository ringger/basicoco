#!/usr/bin/env python3

"""
Test the INPUT command
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import CoCoBasic

def test_input_command():
    basic = CoCoBasic()
    
    print("Testing INPUT command:")
    print("=" * 30)
    
    try:
        basic.execute_command('CLEAR')
        
        # Test simple INPUT command
        print("Test 1: Simple INPUT X")
        result = basic.execute_command('INPUT X')
        print(f"Result: {result}")
        
        # Test INPUT with prompt
        print("\nTest 2: INPUT with prompt")
        result = basic.execute_command('INPUT "ENTER YOUR NAME"; N$')
        print(f"Result: {result}")
        
        # Test INPUT in a program
        print("\nTest 3: INPUT in a program")
        
        # Add program lines
        line_num, code = basic.parse_line('10 INPUT "WHAT IS YOUR AGE"; A')
        basic.program[line_num] = code
        basic.expand_line_to_sublines(line_num, code)
        
        line_num, code = basic.parse_line('20 PRINT "YOU ARE"; A; "YEARS OLD"')
        basic.program[line_num] = code
        basic.expand_line_to_sublines(line_num, code)
        
        print("Program:")
        result = basic.execute_command('LIST')
        for item in result:
            if item.get('type') == 'text':
                print(f"  {item['text']}")
        
        print("\nRunning program (will need user input):")
        result = basic.execute_command('RUN')
        
        print("Output:")
        for item in result:
            if item.get('type') == 'text':
                print(f"  TEXT: {item['text']}")
            elif item.get('type') == 'input_request':
                print(f"  INPUT REQUEST: prompt='{item['prompt']}', variable='{item['variable']}'")
                
                # Simulate user input
                print("  Simulating user input: '25'")
                basic.variables[item['variable']] = 25
                basic.waiting_for_input = False
                
                # Continue execution
                if hasattr(basic, 'continue_program_execution'):
                    continue_result = basic.continue_program_execution()
                    print("  Continuing execution:")
                    for cont_item in continue_result:
                        if cont_item.get('type') == 'text':
                            print(f"    TEXT: {cont_item['text']}")
            elif item.get('type') == 'error':
                print(f"  ERROR: {item['message']}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_input_command()