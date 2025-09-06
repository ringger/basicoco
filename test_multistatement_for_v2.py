#!/usr/bin/env python3

"""
Test multi-statement FOR loop with new virtual sub-line system
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import CoCoBasic

def test_multistatement_for():
    basic = CoCoBasic()
    
    print("Testing multi-statement FOR loop with virtual sub-lines:")
    print("=" * 60)
    
    try:
        basic.execute_command('CLEAR')
        
        # Add the multi-statement FOR loop
        line_num, code = basic.parse_line('10 FOR I=1 TO 3: PRINT I: NEXT I')
        if line_num is not None:
            basic.program[line_num] = code
            basic.expand_line_to_sublines(line_num, code)
        
        print("Original program line:")
        result = basic.execute_command('LIST')
        for item in result:
            if item.get('type') == 'text':
                print(f"  {item['text']}")
        
        print("\\nExpanded sub-lines:")
        for (line_num, sub_index), statement in sorted(basic.expanded_program.items()):
            print(f"  {line_num}.{sub_index}: {statement}")
        
        print("\\nRunning program (should print 1, 2, 3):")
        result = basic.execute_command('RUN')
        
        print("Output:")
        for item in result:
            if item.get('type') == 'text':
                print(f"  {item['text']}")
            elif item.get('type') == 'error':
                print(f"  ERROR: {item['message']}")
        
        print(f"\\nFinal variable I: {basic.variables.get('I', 'undefined')}")
        print(f"Iteration count: {basic.iteration_count}")
        print(f"FOR stack: {basic.for_stack}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_multistatement_for()