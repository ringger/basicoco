#!/usr/bin/env python3
"""
Debug what execute_command returns vs run_program directly
"""

import sys
sys.path.append('/home/ringger/trs80')
from emulator.core import CoCoBasic

def debug_callback(output):
    print(f"CALLBACK: {output}")

def test_execute_vs_run():
    print("🔍 === EXECUTE_COMMAND vs RUN_PROGRAM TEST === 🔍")
    
    emulator = CoCoBasic(output_callback=debug_callback)
    
    print("\n1. Setting up program...")
    emulator.program[10] = 'PRINT "HELLO FROM PROGRAM"'
    emulator.expand_line_to_sublines(10, 'PRINT "HELLO FROM PROGRAM"')
    
    print("\n2. Calling run_program() directly...")
    result1 = emulator.run_program()
    print(f"run_program() returned: {result1}")
    
    print("\n3. Calling execute_command('RUN')...")
    result2 = emulator.execute_command('RUN')
    print(f"execute_command('RUN') returned: {result2}")
    
    print("\n4. Testing simple command...")
    result3 = emulator.execute_command('PRINT "IMMEDIATE"')
    print(f"execute_command('PRINT') returned: {result3}")

if __name__ == '__main__':
    test_execute_vs_run()