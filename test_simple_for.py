#!/usr/bin/env python3

"""
Test simple FOR/NEXT loop separately 
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import CoCoBasic

def test_simple_for():
    basic = CoCoBasic()
    
    print("Testing simple FOR/NEXT loop:")
    print("=" * 30)
    
    try:
        basic.execute_command('CLEAR')
        
        # Add separate lines (not multi-statement)
        line_num, code = basic.parse_line('10 FOR I=1 TO 2')
        basic.program[line_num] = code
        
        line_num, code = basic.parse_line('20 PRINT I')  
        basic.program[line_num] = code
        
        line_num, code = basic.parse_line('30 NEXT I')
        basic.program[line_num] = code
        
        print("Program:")
        result = basic.execute_command('LIST')
        for item in result:
            print(f"  {item['text']}")
        
        print("\nRunning with timeout protection...")
        # Add a counter to prevent infinite loops
        basic.loop_counter = 0
        result = basic.execute_command('RUN')
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == '__main__':
    test_simple_for()