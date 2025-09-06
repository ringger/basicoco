#!/usr/bin/env python3

"""
Test ON GOTO/GOSUB commands
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import CoCoBasic

def test_on_commands():
    basic = CoCoBasic()
    
    print("Testing ON GOTO/GOSUB commands:")
    print("=" * 40)
    
    try:
        basic.execute_command('NEW')
        
        # Create a test program with ON GOTO/GOSUB
        program_lines = [
            '10 FOR I = 1 TO 4',
            '20 PRINT "I ="; I',
            '30 ON I GOTO 100, 200, 300, 400',
            '40 PRINT "This should not print"',
            '50 NEXT I',
            '60 END',
            '100 PRINT "  Branch 1": GOTO 50',
            '200 PRINT "  Branch 2": GOTO 50', 
            '300 PRINT "  Branch 3": GOTO 50',
            '400 PRINT "  Branch 4": GOTO 50',
        ]
        
        # Add all program lines
        for line in program_lines:
            line_num, code = basic.parse_line(line)
            if line_num is not None:
                basic.program[line_num] = code
                basic.expand_line_to_sublines(line_num, code)
        
        print("Program (ON GOTO test):")
        result = basic.execute_command('LIST')
        for item in result:
            if item.get('type') == 'text':
                print(f"  {item['text']}")
        
        print("\nRunning ON GOTO program:")
        print("=" * 40)
        
        result = basic.execute_command('RUN')
        
        for item in result:
            if item.get('type') == 'text':
                print(item['text'])
            elif item.get('type') == 'error':
                print(f"ERROR: {item['message']}")
        
        print("\n" + "=" * 40)
        print("Testing ON GOSUB:")
        print("=" * 40)
        
        # Test ON GOSUB
        basic.execute_command('NEW')
        
        program_lines2 = [
            '10 FOR I = 1 TO 3',
            '20 PRINT "Calling subroutine"; I',
            '30 ON I GOSUB 100, 200, 300',
            '40 PRINT "Back from subroutine"',
            '50 NEXT I',
            '60 END',
            '100 PRINT "  In subroutine 1": RETURN',
            '200 PRINT "  In subroutine 2": RETURN',
            '300 PRINT "  In subroutine 3": RETURN',
        ]
        
        # Add all program lines
        for line in program_lines2:
            line_num, code = basic.parse_line(line)
            if line_num is not None:
                basic.program[line_num] = code
                basic.expand_line_to_sublines(line_num, code)
        
        print("Program (ON GOSUB test):")
        result = basic.execute_command('LIST')
        for item in result:
            if item.get('type') == 'text':
                print(f"  {item['text']}")
        
        print("\nRunning ON GOSUB program:")
        result = basic.execute_command('RUN')
        
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
    test_on_commands()