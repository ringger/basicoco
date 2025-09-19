#!/usr/bin/env python3
"""
Test the emulator directly to see if output callbacks work
"""

import sys
sys.path.append('/home/ringger/trs80')
from emulator.core import CoCoBasic

def debug_output_callback(output):
    print(f"DEBUG: Output callback called with: {output}")

def test_direct_emulator():
    print("🔍 === DIRECT EMULATOR TEST === 🔍")
    
    # Create emulator with debug callback
    emulator = CoCoBasic(output_callback=debug_output_callback, debug_mode=True)
    
    print("\n1. Testing simple PRINT statement...")
    result = emulator.process_command('10 PRINT "HELLO WORLD"')
    print(f"execute_command result: {result}")
    
    print("\n2. Testing RUN command...")
    result = emulator.process_command('RUN')
    print(f"RUN result: {result}")
    
    print("\n3. Testing manual program execution...")
    emulator.program[10] = 'PRINT "HELLO WORLD"'
    emulator.expand_line_to_sublines(10, 'PRINT "HELLO WORLD"')
    result = emulator.run_program()
    print(f"run_program result: {result}")

if __name__ == '__main__':
    test_direct_emulator()