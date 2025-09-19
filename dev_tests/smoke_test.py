#!/usr/bin/env python3

"""
Smoke Test Suite for TRS-80 Color Computer BASIC Emulator

This script performs comprehensive smoke testing to verify that core emulator
functionality is working correctly. Ideal for:
- Post-deployment verification
- Development regression testing  
- Quick functionality validation
- Pre-commit testing workflow

Usage: python smoke_test.py [--quick]
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from emulator.core import CoCoBasic

def format_result(result):
    """Format test results for better readability"""
    if not result:
        return "No output"
    
    output = []
    for item in result:
        if item.get('type') == 'text':
            output.append(f"Text: '{item['text']}'")
        elif item.get('type') == 'pmode':
            output.append(f"Graphics mode {item['mode']}, page {item['page']}")
        elif item.get('type') == 'pset':
            color_info = f", color {item['color']}" if item.get('color') is not None else ""
            output.append(f"Pixel at ({item['x']}, {item['y']}){color_info}")
        elif item.get('type') == 'error':
            output.append(f"❌ ERROR: {item['message']}")
        elif item.get('type') == 'input_request':
            output.append(f"Input request: '{item['prompt']}' for {item['variable']}")
        else:
            # Handle other types gracefully
            output.append(str(item))
    
    return " | ".join(output) if output else str(result)

def comprehensive_smoke_test():
    """Run comprehensive smoke tests with enhanced output"""
    basic = CoCoBasic()
    
    # Test cases: (command, description)
    tests = [
        # Basic I/O
        ('PRINT "HELLO WORLD"', "Basic text output"),
        ('PRINT 42', "Numeric output"),
        
        # Variables
        ('A = 5', "Numeric variable assignment"),
        ('PRINT A', "Numeric variable access"), 
        ('B$ = "TEST"', "String variable assignment"),
        ('PRINT B$', "String variable access"),
        
        # Mathematical expressions
        ('PRINT 5 + 3 * 2', "Mathematical expression"),
        ('PRINT SQR(16)', "Built-in function"),
        
        # Graphics
        ('PMODE 4,1', "Graphics mode setup"),
        ('PSET(10,20)', "Pixel plotting"),
        ('PSET(50,30),2', "Pixel with color"),
        
        # Arrays
        ('DIM A(10)', "Array declaration"),
        ('A(5) = 42', "Array element assignment"),
        ('PRINT A(5)', "Array element access"),
        ('DIM B$(3)', "String array declaration"),
        ('B$(1) = "ARRAY"', "String array assignment"),
        ('PRINT B$(1)', "String array access"),
        
        # String functions
        ('PRINT LEN("HELLO")', "String length function"),
        ('PRINT LEFT$("HELLO",3)', "String substring function"),
        
        # Control flow setup (single statements)
        ('FOR I = 1 TO 3', "FOR loop start"),
        ('PRINT I', "Loop variable access"),
        ('NEXT I', "FOR loop end"),
    ]
    
    print("💨 TRS-80 Color Computer BASIC Emulator - Comprehensive Smoke Test")
    print("=" * 75)
    print(f"{'Test Description':<30} | {'Command':<20} | {'Result'}")
    print("-" * 75)
    
    passed = 0
    total = len(tests)
    
    for command, description in tests:
        try:
            result = basic.process_command(command)
            formatted = format_result(result)
            
            # Check if it's an error
            has_error = any(item.get('type') == 'error' for item in result) if result else False
            status_icon = "❌" if has_error else "✅"
            
            print(f"{status_icon} {description:<27} | {command:<20} | {formatted}")
            
            if not has_error:
                passed += 1
                
        except Exception as e:
            print(f"❌ {description:<27} | {command:<20} | EXCEPTION: {str(e)}")
    
    print("=" * 75)
    print(f"📊 Test Summary: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All smoke tests PASSED! Emulator is working correctly.")
    else:
        print("⚠️  Some smoke tests FAILED. Check emulator functionality.")
    
    return passed == total

def quick_smoke_test():
    """Minimal smoke test for rapid verification"""
    basic = CoCoBasic()
    
    tests = [
        'PRINT "OK"',
        'A = 10: PRINT A',  
        'PMODE 4,1',
        'DIM B(5): B(2) = 99: PRINT B(2)'
    ]
    
    print("⚡ Quick Smoke Test Mode")
    for i, test in enumerate(tests, 1):
        result = basic.process_command(test)
        has_error = any(item.get('type') == 'error' for item in result) if result else False
        status = "❌" if has_error else "✅"
        print(f"{status} Smoke Test {i}: {test}")
    
    print("⚡ Quick smoke test complete!")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='TRS-80 BASIC Emulator Smoke Test Suite')
    parser.add_argument('--quick', '-q', action='store_true', 
                       help='Run quick smoke test mode (4 essential tests, faster)')
    
    args = parser.parse_args()
    
    if args.quick:
        quick_smoke_test()
    else:
        comprehensive_smoke_test()