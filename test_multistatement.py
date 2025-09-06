#!/usr/bin/env python3

"""
Test multi-statement support before fixing
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import CoCoBasic

def test_multistatement():
    basic = CoCoBasic()
    
    print("Testing multi-statement support:")
    print("=" * 40)
    
    # Test the problem case
    print("\n1. Testing program with: 10 FOR I=1 TO 3: PRINT I: NEXT I")
    try:
        basic.execute_command('CLEAR')
        
        line_num, code = basic.parse_line('10 FOR I=1 TO 3: PRINT I: NEXT I')
        if line_num is not None:
            basic.program[line_num] = code
            print(f"   Stored in program: {line_num} -> '{code}'")
        
        # List to see what's stored
        result = basic.execute_command('LIST')
        print(f"   LIST result: {result}")
        
        # Try to run
        print("   Running program...")
        result = basic.execute_command('RUN')
        print(f"   RUN result: {result}")
        
    except Exception as e:
        print(f"   ERROR: {e}")
    
    print("\n" + "=" * 40)

if __name__ == '__main__':
    test_multistatement()