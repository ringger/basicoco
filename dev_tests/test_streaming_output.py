#!/usr/bin/env python3

"""
Test script to demonstrate the enhanced StreamingOutputManager capabilities.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from emulator.core import CoCoBasic
from emulator.output_manager import OutputType, OutputPriority, TypeFilter, PriorityFilter

def test_streaming_output():
    """Test the StreamingOutputManager functionality"""
    print("Testing Enhanced StreamingOutputManager")
    print("=" * 50)
    
    # Test 1: Basic output functionality
    print("\n1. Testing basic output functionality:")
    basic = CoCoBasic(debug_mode=True)
    
    # Send various types of output
    basic.emit_text("Hello, World!", source="test")
    basic.emit_error("Test error message", source="test")
    basic.emit_debug("Debug information", source="test")
    
    # Test 2: Message buffering and retrieval
    print("\n2. Testing message buffering:")
    recent_messages = basic.output_manager.get_recent_messages(5)
    print(f"Recent messages in buffer: {len(recent_messages)}")
    
    for i, msg in enumerate(recent_messages):
        print(f"  {i+1}. [{msg.type.value}] {msg.content} (from: {msg.source})")
    
    # Test 3: Filtering functionality
    print("\n3. Testing output filtering:")
    
    # Add a type filter to only show errors
    error_filter = TypeFilter([OutputType.ERROR, OutputType.WARNING])
    basic.output_manager.add_filter(error_filter)
    
    print("Added error filter - now only errors and warnings will be shown")
    basic.emit_text("This text should be filtered out")
    basic.emit_error("This error should be shown")
    basic.emit_text("This text should also be filtered out") 
    
    # Check filtered messages
    error_messages = basic.output_manager.get_messages_by_type(OutputType.ERROR)
    print(f"Error messages in buffer: {len(error_messages)}")
    
    # Test 4: Legacy compatibility
    print("\n4. Testing legacy compatibility:")
    
    # Remove filter for this test
    basic.output_manager.remove_filter(error_filter)
    
    def legacy_callback(output):
        print(f"Legacy callback received: {output}")
    
    # Set up legacy callback
    basic.legacy_adapter.set_output_callback(legacy_callback)
    
    # Emit using legacy format
    basic.emit_output([{'type': 'text', 'text': 'Legacy format message'}])
    basic.emit_output({'type': 'error', 'message': 'Legacy error message'})
    
    # Test 5: Statistics and monitoring
    print("\n5. Testing statistics and monitoring:")
    stats = basic.output_manager.get_statistics()
    print(f"Output statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test 6: Program context
    print("\n6. Testing program context tracking:")
    basic.current_line = 100
    basic.emit_text("Message from line 100", source="program")
    basic.emit_error("Error from line 100", source="program")
    
    # Show messages with line numbers
    recent_with_lines = [msg for msg in basic.output_manager.get_recent_messages(10) 
                        if msg.line_number is not None]
    print(f"Messages with line numbers: {len(recent_with_lines)}")
    for msg in recent_with_lines:
        print(f"  Line {msg.line_number}: [{msg.type.value}] {msg.content}")

def test_streaming_with_real_commands():
    """Test streaming output with real BASIC commands"""
    print("\n" + "="*50)
    print("Testing StreamingOutputManager with real BASIC commands")
    print("="*50)
    
    # Create a callback to monitor real-time output
    output_log = []
    
    def monitor_callback(message):
        output_log.append(f"[{message.type.value}] {message.content}")
    
    basic = CoCoBasic(debug_mode=True)
    basic.output_manager.add_subscriber(monitor_callback)
    
    # Execute some commands
    print("\nExecuting BASIC commands...")
    
    # These should generate output through the new system
    commands = [
        'A = 5',
        'PRINT A',
        'PRINT "HELLO WORLD"',
        'HELP PRINT',
        'LIST'  # This will show empty program
    ]
    
    for cmd in commands:
        print(f"\nExecuting: {cmd}")
        result = basic.execute_command(cmd)
        
    print(f"\nMonitored output log ({len(output_log)} messages):")
    for i, entry in enumerate(output_log):
        print(f"  {i+1}. {entry}")

if __name__ == '__main__':
    test_streaming_output()
    test_streaming_with_real_commands()