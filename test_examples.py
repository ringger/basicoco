#!/usr/bin/env python3

"""
Test the examples to see which ones work
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import CoCoBasic

def test_all_examples():
    basic = CoCoBasic()
    
    examples = [
        ('PRINT "HELLO WORLD"', 'Simple text output'),
        ('A = 42', 'Variable assignment'),
        ('PRINT A', 'Print variable'),
        ('PMODE 4,1', 'Set graphics mode'),
        ('SCREEN 1,1', 'Set screen mode'),
        ('PSET(128,96)', 'Set pixel'),
        ('LINE(0,0)-(255,191)', 'Draw line'),
        ('CIRCLE(128,96),50', 'Draw circle'),
        ('PCLS', 'Clear graphics'),
        ('COLOR 4,0', 'Set colors'),
        ('SOUND 1000,30', 'Play sound'),
        ('CLS', 'Clear screen')
    ]
    
    print("Testing TRS-80 Color Computer Examples:")
    print("=" * 50)
    
    working = []
    broken = []
    
    for example, description in examples:
        print(f"\n{description}: {example}")
        try:
            result = basic.execute_command(example)
            if result and len(result) > 0 and result[0].get('type') != 'error':
                print(f"  ✅ WORKS: {result}")
                working.append(example)
            else:
                print(f"  ❌ ERROR: {result}")
                broken.append(example)
        except Exception as e:
            print(f"  ❌ EXCEPTION: {e}")
            broken.append(example)
    
    # Test a simple program
    print(f"\nTesting simple program:")
    try:
        basic.execute_command('CLEAR')
        
        # Add lines to program
        line_num, code = basic.parse_line('10 PRINT "LINE 10"')
        if line_num is not None:
            basic.program[line_num] = code
            
        line_num, code = basic.parse_line('20 PRINT "LINE 20"')
        if line_num is not None:
            basic.program[line_num] = code
        
        result = basic.execute_command('LIST')
        print(f"  LIST result: {result}")
        
        result = basic.execute_command('RUN')
        print(f"  RUN result: {result}")
        
        working.extend(['LIST', 'RUN'])
        
    except Exception as e:
        print(f"  ❌ Program test failed: {e}")
        broken.extend(['LIST', 'RUN'])
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"✅ Working commands ({len(working)}):")
    for cmd in working:
        print(f"  - {cmd}")
    
    if broken:
        print(f"\n❌ Broken commands ({len(broken)}):")
        for cmd in broken:
            print(f"  - {cmd}")

if __name__ == '__main__':
    test_all_examples()