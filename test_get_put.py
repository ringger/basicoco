#!/usr/bin/env python3

"""
Test GET/PUT commands for advanced graphics operations
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import CoCoBasic

def test_get_put():
    basic = CoCoBasic()
    
    print("Testing GET/PUT commands:")
    print("=" * 40)
    
    try:
        basic.execute_command('NEW')
        
        # Test GET/PUT in text mode (should fail)
        print("Testing GET in text mode (should fail):")
        result = basic.execute_command('GET (0,0)-(10,10), A')
        if result and result[0].get('type') == 'error':
            print(f"GET in text mode: {result[0]['message']}")
        else:
            print("GET in text mode: Unexpected result")
        
        # Switch to graphics mode
        print("\nSwitching to graphics mode:")
        result = basic.execute_command('PMODE 1,1')
        print(f"PMODE 1,1: {result[0]['type'] if result else 'OK'}")
        
        result = basic.execute_command('SCREEN 1,1')
        print(f"SCREEN 1,1: {result[0]['type'] if result else 'OK'}")
        
        # Now test GET command
        print("\nTesting GET command in graphics mode:")
        result = basic.execute_command('GET (10,10)-(20,15), SPRITE')
        if result:
            if result[0].get('type') == 'get':
                print(f"GET (10,10)-(20,15), SPRITE: Success - stored to array {result[0]['array']}")
            elif result[0].get('type') == 'error':
                print(f"GET command error: {result[0]['message']}")
            else:
                print(f"GET command result: {result}")
        else:
            print("GET command: No result")
        
        # Test PUT command
        print("\nTesting PUT command:")
        result = basic.execute_command('PUT (50,20), SPRITE')
        if result:
            if result[0].get('type') == 'put':
                print(f"PUT (50,20), SPRITE: Success - action {result[0]['action']}")
            elif result[0].get('type') == 'error':
                print(f"PUT command error: {result[0]['message']}")
            else:
                print(f"PUT command result: {result}")
        else:
            print("PUT command: No result")
        
        # Test PUT with action
        print("\nTesting PUT with XOR action:")
        result = basic.execute_command('PUT (60,25), SPRITE, XOR')
        if result:
            if result[0].get('type') == 'put':
                print(f"PUT (60,25), SPRITE, XOR: Success - action {result[0]['action']}")
            elif result[0].get('type') == 'error':
                print(f"PUT XOR command error: {result[0]['message']}")
            else:
                print(f"PUT XOR command result: {result}")
        else:
            print("PUT XOR command: No result")
        
        # Test PUT with undimensioned array
        print("\nTesting PUT with undimensioned array:")
        result = basic.execute_command('PUT (10,10), NONEXISTENT')
        if result and result[0].get('type') == 'error':
            print(f"PUT with undimensioned array: {result[0]['message']}")
        else:
            print("PUT with undimensioned array: Unexpected result")
        
        # Test in a program
        print("\nTesting in a program:")
        program_lines = [
            '10 PMODE 2,1: SCREEN 1,1',
            '20 PSET (10,10): PSET (11,10): PSET (12,10)',
            '30 PSET (10,11): PSET (11,11): PSET (12,11)',
            '40 PRINT "Drawing original sprite..."',
            '50 GET (10,10)-(12,11), BLOCK',
            '60 PRINT "Sprite captured with GET"',
            '70 PUT (20,20), BLOCK',
            '80 PRINT "Sprite displayed at (20,20) with PUT"',
            '90 PUT (30,30), BLOCK, XOR',
            '100 PRINT "Sprite displayed at (30,30) with XOR"',
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
            elif item.get('type') in ['get', 'put']:
                print(f"Graphics operation: {item['type'].upper()} at {item}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_get_put()