#!/usr/bin/env python3

"""
Test CONT command
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import CoCoBasic

def test_cont_command():
    basic = CoCoBasic()
    
    print("Testing CONT command:")
    print("=" * 40)
    
    try:
        basic.execute_command('NEW')
        
        # Create a test program with STOP
        program_lines = [
            '10 PRINT "LINE 10"',
            '20 PRINT "LINE 20"',
            '30 STOP',
            '40 PRINT "LINE 40"',
            '50 PRINT "LINE 50"',
            '60 END',
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
        
        print("\nRunning program (should stop at line 30):")
        print("=" * 40)
        
        result = basic.execute_command('RUN')
        
        for item in result:
            if item.get('type') == 'text':
                print(item['text'])
            elif item.get('type') == 'error':
                print(f"ERROR: {item['message']}")
        
        print(f"\nStopped position: {basic.stopped_position}")
        
        print("\nContinuing with CONT:")
        print("=" * 40)
        
        result = basic.execute_command('CONT')
        
        for item in result:
            if item.get('type') == 'text':
                print(item['text'])
            elif item.get('type') == 'error':
                print(f"ERROR: {item['message']}")
        
        print("\nTesting CONT without previous STOP:")
        basic.execute_command('NEW')
        result = basic.execute_command('CONT')
        
        for item in result:
            if item.get('type') == 'text':
                print(item['text'])
            elif item.get('type') == 'error':
                print(f"ERROR: {item['message']}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_cont_command()