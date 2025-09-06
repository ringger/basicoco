#!/usr/bin/env python3

"""
Simple test script for basic functionality
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import CoCoBasic

def simple_test():
    basic = CoCoBasic()
    
    # Test PRINT
    result = basic.execute_command('PRINT "HELLO"')
    print(f"PRINT: {result}")
    
    # Test variable
    basic.execute_command('A = 5')
    result = basic.execute_command('PRINT A')
    print(f"Variable: {result}")
    
    # Test PMODE
    result = basic.execute_command('PMODE 4,1')
    print(f"PMODE: {result}")
    
    # Test PSET
    result = basic.execute_command('PSET(10,20)')
    print(f"PSET: {result}")

if __name__ == '__main__':
    simple_test()