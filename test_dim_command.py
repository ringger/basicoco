#!/usr/bin/env python3

"""
Test DIM command for array declarations
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import CoCoBasic

def test_dim_command():
    basic = CoCoBasic()
    
    print("Testing DIM command:")
    print("=" * 40)
    
    try:
        basic.execute_command('NEW')
        
        # Test simple 1D numeric array
        print("Testing 1D numeric array:")
        result = basic.execute_command('DIM A(10)')
        print(f'DIM A(10): {"OK" if not result else "ERROR - " + str(result)}')
        
        # Test setting and getting array elements
        result = basic.execute_command('A(5) = 42')
        print(f'A(5) = 42: {result[0]["text"] if result and "text" in result[0] else "ERROR"}')
        
        result = basic.execute_command('PRINT A(5)')
        print(f'PRINT A(5): {result[0]["text"] if result and "text" in result[0] else "ERROR"}')
        
        # Test 1D string array
        print("\nTesting 1D string array:")
        result = basic.execute_command('DIM B$(5)')
        print(f'DIM B$(5): {"OK" if not result else "ERROR - " + str(result)}')
        
        result = basic.execute_command('B$(3) = "HELLO"')
        print(f'B$(3) = "HELLO": {result[0]["text"] if result and "text" in result[0] else "ERROR"}')
        
        result = basic.execute_command('PRINT B$(3)')
        print(f'PRINT B$(3): {result[0]["text"] if result and "text" in result[0] else "ERROR"}')
        
        # Test 2D array
        print("\nTesting 2D array:")
        result = basic.execute_command('DIM C(3,4)')
        print(f'DIM C(3,4): {"OK" if not result else "ERROR - " + str(result)}')
        
        result = basic.execute_command('C(2,3) = 99')
        print(f'C(2,3) = 99: {result[0]["text"] if result and "text" in result[0] else "ERROR"}')
        
        result = basic.execute_command('PRINT C(2,3)')
        print(f'PRINT C(2,3): {result[0]["text"] if result and "text" in result[0] else "ERROR"}')
        
        # Test multiple arrays in one DIM statement
        print("\nTesting multiple arrays in one DIM:")
        result = basic.execute_command('DIM X(5), Y$(3), Z(2,2)')
        print(f'DIM X(5), Y$(3), Z(2,2): {"OK" if not result else "ERROR - " + str(result)}')
        
        # Test array bounds checking
        print("\nTesting array bounds:")
        result = basic.execute_command('A(15) = 10')
        print(f'A(15) = 10 (should fail): {result[0]["message"] if result and "message" in result[0] else "NO ERROR - BAD"}')
        
        # Test accessing undimensioned array
        print("\nTesting undimensioned array:")
        result = basic.execute_command('PRINT D(5)')
        print(f'PRINT D(5) (should fail): {result[0]["message"] if result and "message" in result[0] else "NO ERROR - BAD"}')
        
        # Test in a program
        print("\nTesting in a program:")
        program_lines = [
            '10 DIM NUMS(5), NAMES$(3)',
            '20 FOR I = 0 TO 4',
            '30 NUMS(I) = I * 10',
            '40 NEXT I',
            '50 NAMES$(0) = "FIRST"',
            '60 NAMES$(1) = "SECOND"',
            '70 NAMES$(2) = "THIRD"',
            '80 FOR I = 0 TO 4',
            '90 PRINT "NUMS("; I; ") = "; NUMS(I)',
            '100 NEXT I',
            '110 FOR I = 0 TO 2',
            '120 PRINT "NAMES$("; I; ") = "; NAMES$(I)',
            '130 NEXT I',
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
        
        print("\nRunning program:")
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
    test_dim_command()