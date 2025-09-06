#!/usr/bin/env python3

"""
Test the FOR/NEXT infinite loop fix
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import CoCoBasic

def test_for_fix():
    basic = CoCoBasic()
    
    print("Testing FOR/NEXT loop fix:")
    print("=" * 30)
    
    try:
        basic.execute_command('CLEAR')
        
        # Add simple FOR loop program
        line_num, code = basic.parse_line('10 FOR I=1 TO 3')
        basic.program[line_num] = code
        
        line_num, code = basic.parse_line('20 PRINT I')  
        basic.program[line_num] = code
        
        line_num, code = basic.parse_line('30 NEXT I')
        basic.program[line_num] = code
        
        print("Program:")
        result = basic.execute_command('LIST')
        for item in result:
            if item.get('type') == 'text':
                print(f"  {item['text']}")
        
        print("\nRunning program (should print 1, 2, 3):")
        result = basic.execute_command('RUN')
        
        print("Output:")
        for item in result:
            if item.get('type') == 'text':
                print(f"  {item['text']}")
            elif item.get('type') == 'error':
                print(f"  ERROR: {item['message']}")
        
        print(f"\nFinal variable I value: {basic.variables.get('I', 'undefined')}")
        print(f"Iteration count: {basic.iteration_count}")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == '__main__':
    test_for_fix()