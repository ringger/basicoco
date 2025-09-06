#!/usr/bin/env python3

"""
Test DRAW command for Logo-style turtle graphics
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import CoCoBasic

def test_draw():
    basic = CoCoBasic()
    
    print("Testing DRAW command:")
    print("=" * 40)
    
    try:
        basic.execute_command('NEW')
        
        # Test DRAW in text mode (should fail)
        print("Testing DRAW in text mode (should fail):")
        result = basic.execute_command('DRAW "U10"')
        if result and result[0].get('type') == 'error':
            print(f"DRAW in text mode: {result[0]['message']}")
        else:
            print("DRAW in text mode: Unexpected result")
        
        # Switch to graphics mode
        print("\nSwitching to graphics mode:")
        result = basic.execute_command('PMODE 2,1')
        print(f"PMODE 2,1: {result[0]['type'] if result else 'OK'}")
        
        result = basic.execute_command('SCREEN 1,1')
        print(f"SCREEN 1,1: {result[0]['type'] if result else 'OK'}")
        
        # Test basic DRAW commands
        print(f"\nInitial turtle position: ({basic.turtle_x}, {basic.turtle_y})")
        
        print("\nTesting basic DRAW commands:")
        
        # Draw up 10 units
        result = basic.execute_command('DRAW "U10"')
        if result:
            print(f"DRAW \"U10\": {len(result)} line(s) drawn")
            for item in result:
                if item.get('type') == 'line':
                    print(f"  Line from ({item['x1']}, {item['y1']}) to ({item['x2']}, {item['y2']})")
            print(f"  New turtle position: ({basic.turtle_x}, {basic.turtle_y})")
        
        # Draw right 15 units
        result = basic.execute_command('DRAW "R15"')
        if result:
            print(f"DRAW \"R15\": {len(result)} line(s) drawn")
            for item in result:
                if item.get('type') == 'line':
                    print(f"  Line from ({item['x1']}, {item['y1']}) to ({item['x2']}, {item['y2']})")
            print(f"  New turtle position: ({basic.turtle_x}, {basic.turtle_y})")
        
        # Draw down 10 units
        result = basic.execute_command('DRAW "D10"')
        if result:
            print(f"DRAW \"D10\": {len(result)} line(s) drawn")
            for item in result:
                if item.get('type') == 'line':
                    print(f"  Line from ({item['x1']}, {item['y1']}) to ({item['x2']}, {item['y2']})")
            print(f"  New turtle position: ({basic.turtle_x}, {basic.turtle_y})")
        
        # Draw left 15 units to complete rectangle
        result = basic.execute_command('DRAW "L15"')
        if result:
            print(f"DRAW \"L15\": {len(result)} line(s) drawn")
            for item in result:
                if item.get('type') == 'line':
                    print(f"  Line from ({item['x1']}, {item['y1']}) to ({item['x2']}, {item['y2']})")
            print(f"  New turtle position: ({basic.turtle_x}, {basic.turtle_y})")
        
        # Test diagonal commands
        print("\nTesting diagonal commands:")
        result = basic.execute_command('DRAW "E5F5G5H5"')
        if result:
            print(f"DRAW \"E5F5G5H5\": {len(result)} line(s) drawn")
            for i, item in enumerate(result):
                if item.get('type') == 'line':
                    directions = ['NE', 'SE', 'SW', 'NW']
                    print(f"  {directions[i]} line from ({item['x1']}, {item['y1']}) to ({item['x2']}, {item['y2']})")
            print(f"  Final turtle position: ({basic.turtle_x}, {basic.turtle_y})")
        
        # Test multiple commands in one string
        print("\nTesting multiple commands in one string:")
        basic.turtle_x = 50  # Reset position
        basic.turtle_y = 50
        print(f"Reset turtle position: ({basic.turtle_x}, {basic.turtle_y})")
        
        result = basic.execute_command('DRAW "U10R10D10L10"')
        if result:
            print(f"DRAW \"U10R10D10L10\": {len(result)} line(s) drawn (should be 4)")
            for i, item in enumerate(result):
                if item.get('type') == 'line':
                    directions = ['Up', 'Right', 'Down', 'Left']
                    print(f"  {directions[i]}: ({item['x1']}, {item['y1']}) to ({item['x2']}, {item['y2']})")
            print(f"  Final turtle position: ({basic.turtle_x}, {basic.turtle_y})")
        
        # Test with variables
        print("\nTesting with variables:")
        basic.variables['D$'] = "R20D20L20U20"
        result = basic.execute_command('DRAW D$')
        if result:
            print(f"DRAW D$: {len(result)} line(s) drawn")
            print(f"  Drew square with variable D$ = \"R20D20L20U20\"")
            print(f"  Final turtle position: ({basic.turtle_x}, {basic.turtle_y})")
        
        # Test in a program
        print("\nTesting in a program:")
        program_lines = [
            '10 PMODE 3,1: SCREEN 1,1',
            '20 PRINT "Drawing a house with DRAW..."',
            '30 REM Draw house base',
            '40 DRAW "U20R30D20L30"',
            '50 REM Draw roof',
            '60 DRAW "U10E15F15D10"',
            '70 REM Draw door',
            '80 DRAW "BU5BR10"',  # Move to door position (blank moves)',
            '90 DRAW "D10R5U10L5"',
            '100 PRINT "House complete!"',
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
        
        # Reset turtle for program
        basic.turtle_x = 64
        basic.turtle_y = 96
        print(f"\nReset turtle position for program: ({basic.turtle_x}, {basic.turtle_y})")
        
        print("\nRunning program:")
        result = basic.execute_command('RUN')
        
        line_count = 0
        for item in result:
            if item.get('type') == 'text':
                print(item['text'])
            elif item.get('type') == 'line':
                line_count += 1
            elif item.get('type') == 'error':
                print(f"ERROR: {item['message']}")
        
        print(f"\nProgram drew {line_count} lines total")
        print(f"Final turtle position: ({basic.turtle_x}, {basic.turtle_y})")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_draw()