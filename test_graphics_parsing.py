#!/usr/bin/env python3

"""
Test graphics coordinate parsing before fixing
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import CoCoBasic

def test_graphics_parsing():
    basic = CoCoBasic()
    
    print("Testing graphics coordinate parsing:")
    print("=" * 40)
    
    # Test PSET
    print("\n1. Testing: PSET(128,96)")
    try:
        result = basic.execute_command('PSET(128,96)')
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test LINE
    print("\n2. Testing: LINE(0,0)-(255,191)")
    try:
        result = basic.execute_command('LINE(0,0)-(255,191)')
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test CIRCLE
    print("\n3. Testing: CIRCLE(128,96),50")
    try:
        result = basic.execute_command('CIRCLE(128,96),50')
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    print("\n" + "=" * 40)

if __name__ == '__main__':
    test_graphics_parsing()