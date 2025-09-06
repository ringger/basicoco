#!/usr/bin/env python3

"""
Test DATA/READ/RESTORE commands
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import CoCoBasic

def test_data_commands():
    basic = CoCoBasic()
    
    print("Testing DATA/READ/RESTORE commands:")
    print("=" * 40)
    
    try:
        basic.execute_command('NEW')
        
        # Create a test program with DATA statements
        program_lines = [
            '10 DATA 100, 200, "HELLO", 3.14',
            '20 DATA "WORLD", 500',
            '30 READ A, B, C$, D',
            '40 PRINT "A="; A; "B="; B; "C$="; C$; "D="; D',
            '50 READ E$, F',
            '60 PRINT "E$="; E$; "F="; F',
            '70 RESTORE',
            '80 READ X',
            '90 PRINT "After RESTORE, X="; X',
        ]
        
        # Add all program lines
        for line in program_lines:
            line_num, code = basic.parse_line(line)
            if line_num is not None:
                basic.program[line_num] = code
                basic.expand_line_to_sublines(line_num, code)
        
        print("Program:")
        result = basic.execute_command('LIST')
        for item in result:
            if item.get('type') == 'text':
                print(f"  {item['text']}")
        
        print("\nRunning program:")
        print("=" * 40)
        
        result = basic.execute_command('RUN')
        
        for item in result:
            if item.get('type') == 'text':
                print(item['text'])
            elif item.get('type') == 'error':
                print(f"ERROR: {item['message']}")
        
        print(f"\nData statements collected: {basic.data_statements}")
        print(f"Data pointer after execution: {basic.data_pointer}")
        print(f"Final variables: {basic.variables}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_data_commands()