#!/usr/bin/env python3

"""
Test script to demonstrate the enhanced command registry with HELP functionality.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from emulator.core import CoCoBasic

def test_help_system():
    """Test the new HELP command and plugin architecture"""
    basic = CoCoBasic()
    
    print("Testing Enhanced Command Registry with HELP System")
    print("=" * 60)
    
    # Test 1: General help
    print("\n1. Testing general help:")
    result = basic.execute_command('HELP')
    for item in result:
        if item.get('type') == 'text':
            print(item['text'])
    
    # Test 2: Help for specific command
    print("\n2. Testing help for specific command (PRINT):")
    result = basic.execute_command('HELP PRINT')
    for item in result:
        if item.get('type') == 'text':
            print(item['text'])
    
    # Test 3: Help for control flow command
    print("\n3. Testing help for control flow command (FOR):")
    result = basic.execute_command('HELP FOR')
    for item in result:
        if item.get('type') == 'text':
            print(item['text'])
    
    # Test 4: Help for unknown command
    print("\n4. Testing help for unknown command:")
    result = basic.execute_command('HELP UNKNOWN')
    for item in result:
        if item.get('type') == 'text':
            print(item['text'])
    
    # Test 5: Test command registry functionality
    print("\n5. Testing command registry functionality:")
    registry = basic.command_registry
    
    print(f"Total registered commands: {len(registry.list_commands())}")
    print(f"Categories: {', '.join(registry.get_all_categories())}")
    
    for category in ['control', 'graphics', 'system']:
        commands = registry.get_commands_by_category(category)
        print(f"{category.title()} commands: {', '.join(commands[:5])}{'...' if len(commands) > 5 else ''}")

if __name__ == '__main__':
    test_help_system()