#!/usr/bin/env python3

"""
Test additional string functions CHR$, ASC, STR$, VAL
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import CoCoBasic

def test_string_functions():
    basic = CoCoBasic()
    
    print("Testing additional string functions:")
    print("=" * 40)
    
    try:
        basic.execute_command('NEW')
        
        # Test CHR$ function
        print("Testing CHR$ function:")
        result = basic.execute_command('PRINT CHR$(65)')
        print(f'CHR$(65): {result[0]["text"] if result and "text" in result[0] else "ERROR"}')
        
        result = basic.execute_command('PRINT CHR$(72); CHR$(69); CHR$(76); CHR$(76); CHR$(79)')
        print(f'CHR$(72,69,76,76,79): {result[0]["text"] if result and "text" in result[0] else "ERROR"}')
        
        # Test ASC function
        print("\nTesting ASC function:")
        result = basic.execute_command('PRINT ASC("A")')
        print(f'ASC("A"): {result[0]["text"] if result and "text" in result[0] else "ERROR"}')
        
        result = basic.execute_command('PRINT ASC("HELLO")')
        print(f'ASC("HELLO"): {result[0]["text"] if result and "text" in result[0] else "ERROR"}')
        
        # Test STR$ function
        print("\nTesting STR$ function:")
        result = basic.execute_command('PRINT STR$(123)')
        print(f'STR$(123): "{result[0]["text"]}" if result and "text" in result[0] else "ERROR"')
        
        result = basic.execute_command('PRINT STR$(-456)')
        print(f'STR$(-456): "{result[0]["text"]}" if result and "text" in result[0] else "ERROR"')
        
        result = basic.execute_command('PRINT STR$(3.14)')
        print(f'STR$(3.14): "{result[0]["text"]}" if result and "text" in result[0] else "ERROR"')
        
        # Test VAL function
        print("\nTesting VAL function:")
        result = basic.execute_command('PRINT VAL("123")')
        print(f'VAL("123"): {result[0]["text"] if result and "text" in result[0] else "ERROR"}')
        
        result = basic.execute_command('PRINT VAL("3.14159")')
        print(f'VAL("3.14159"): {result[0]["text"] if result and "text" in result[0] else "ERROR"}')
        
        result = basic.execute_command('PRINT VAL("ABC")')
        print(f'VAL("ABC"): {result[0]["text"] if result and "text" in result[0] else "ERROR"}')
        
        # Test combined usage
        print("\nTesting combined usage:")
        basic.variables['N'] = 72
        result = basic.execute_command('PRINT CHR$(N)')
        print(f'CHR$(N) where N=72: {result[0]["text"] if result and "text" in result[0] else "ERROR"}')
        
        basic.variables['S$'] = "123.45"
        result = basic.execute_command('PRINT VAL(S$)')
        print(f'VAL(S$) where S$="123.45": {result[0]["text"] if result and "text" in result[0] else "ERROR"}')
        
        # Test in a program
        print("\nTesting in a program:")
        program_lines = [
            '10 S$ = "COLOR COMPUTER"',
            '20 FOR I = 1 TO LEN(S$)',
            '30 C$ = MID$(S$, I, 1)',
            '40 PRINT C$; " = "; ASC(C$)',
            '50 NEXT I',
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
    test_string_functions()