#!/usr/bin/env python3

"""
Test the complete BASIC implementation with a comprehensive program
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import CoCoBasic

def test_complete_basic():
    basic = CoCoBasic()
    
    print("Testing Complete TRS-80 Color Computer BASIC Implementation:")
    print("=" * 60)
    
    try:
        basic.execute_command('NEW')
        
        # Create a comprehensive test program
        program_lines = [
            '10 REM *** COMPREHENSIVE BASIC TEST PROGRAM ***',
            '20 PRINT "COLOR COMPUTER BASIC TEST"',
            '30 PRINT "======================="',
            '40 PRINT',
            '50 REM Test variables and math',
            '60 A = 5: B = 3.14: C$ = "HELLO"',
            '70 PRINT "A ="; A; "B ="; B; "C$ ="; C$',
            '80 PRINT "A + B ="; A + B',
            '90 PRINT "ABS(-7) ="; ABS(-7)',
            '100 PRINT "SQR(16) ="; SQR(16)',
            '110 PRINT "INT(3.7) ="; INT(3.7)',
            '120 PRINT',
            '130 REM Test string functions',
            '140 S$ = "COLOR COMPUTER"',
            '150 PRINT "S$ ="; S$',
            '160 PRINT "LEN(S$) ="; LEN(S$)',
            '170 PRINT "LEFT$(S$,5) ="; LEFT$(S$,5)',
            '180 PRINT "RIGHT$(S$,8) ="; RIGHT$(S$,8)',
            '190 PRINT "MID$(S$,7,3) ="; MID$(S$,7,3)',
            '200 PRINT',
            '210 REM Test FOR/NEXT loop',
            '220 PRINT "FOR loop test:"',
            '230 FOR I = 1 TO 3',
            '240 PRINT "I ="; I',
            '250 NEXT I',
            '260 PRINT',
            '270 REM Test IF/THEN',
            '280 X = 10',
            '290 IF X > 5 THEN PRINT "X is greater than 5"',
            '300 IF X < 5 THEN PRINT "X is less than 5"',
            '310 PRINT',
            '320 REM Test GOSUB/RETURN',
            '330 PRINT "Calling subroutine..."',
            '340 GOSUB 400',
            '350 PRINT "Back from subroutine"',
            '360 END',
            '400 REM Subroutine',
            '410 PRINT "  In subroutine"',
            '420 RETURN',
        ]
        
        # Add all program lines
        for line in program_lines:
            line_num, code = basic.parse_line(line)
            if line_num is not None:
                basic.program[line_num] = code
                basic.expand_line_to_sublines(line_num, code)
        
        print("Program loaded:")
        result = basic.execute_command('LIST')
        for item in result:
            if item.get('type') == 'text':
                print(f"  {item['text']}")
        
        print("\n" + "=" * 60)
        print("Running comprehensive test program:")
        print("=" * 60)
        
        result = basic.execute_command('RUN')
        
        for item in result:
            if item.get('type') == 'text':
                print(item['text'])
            elif item.get('type') == 'error':
                print(f"ERROR: {item['message']}")
            elif item.get('type') == 'input_request':
                print(f"INPUT REQUEST: {item['prompt']} (variable: {item['variable']})")
        
        print("\n" + "=" * 60)
        print("Test completed successfully!")
        
        # Show final state
        print(f"Final variables: {dict(list(basic.variables.items())[:10])}")  # Show first 10
        print(f"Program had {len(basic.program)} lines")
        print(f"Expanded to {len(basic.expanded_program)} sub-lines")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_complete_basic()