#!/usr/bin/env python3

"""
Comprehensive tests for Streaming Output Manager

Tests the centralized output management system with enhanced streaming capabilities,
output filtering, buffering, and formatting for different interface types.
"""

import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from test_base import BaseTestCase
from emulator.output_manager import (
    StreamingOutputManager, OutputMessage, OutputType, OutputPriority,
    TypeFilter, PriorityFilter, DebugFilter, LegacyOutputAdapter
)
from emulator.core import CoCoBasic


class OutputManagerTest(BaseTestCase):
    """Test cases for Streaming Output Manager functionality"""

    def setUp(self):
        """Set up test environment"""
        super().setUp()
        self.output_manager = StreamingOutputManager(debug_mode=True)

    def test_basic_functionality(self):
        """Test basic output manager functionality"""
        # Test creating and emitting a message
        message = self.output_manager.text("Hello, World!")
        
        self.assertEqual(message.type, OutputType.TEXT)
        self.assertEqual(message.content, "Hello, World!")
        self.assertEqual(message.priority, OutputPriority.NORMAL)
        self.assertTrue(message.timestamp > 0)

    def test_output_message_creation(self):
        """Test OutputMessage creation and conversion"""
        # Test manual message creation
        message = OutputMessage(
            type=OutputType.ERROR,
            content="Test error message",
            timestamp=time.time(),
            priority=OutputPriority.HIGH,
            source="test_module",
            line_number=42
        )
        
        self.assertEqual(message.type, OutputType.ERROR)
        self.assertEqual(message.content, "Test error message")
        self.assertEqual(message.priority, OutputPriority.HIGH)
        self.assertEqual(message.source, "test_module")
        self.assertEqual(message.line_number, 42)

    def test_message_to_dict_conversion(self):
        """Test converting messages to dictionary format"""
        message = OutputMessage(
            type=OutputType.TEXT,
            content="Test message",
            timestamp=time.time(),
            source="test",
            line_number=10
        )
        
        msg_dict = message.to_dict()
        self.assertEqual(msg_dict['type'], 'text')
        self.assertEqual(msg_dict['text'], 'Test message')
        self.assertEqual(msg_dict['source'], 'test')
        self.assertEqual(msg_dict['line'], 10)
        self.assertTrue('timestamp' in msg_dict)

    def test_message_to_legacy_format(self):
        """Test converting messages to legacy format"""
        # Test text message
        text_msg = OutputMessage(OutputType.TEXT, "Hello", time.time())
        legacy = text_msg.to_legacy_format()
        self.assertEqual(legacy['type'], 'text')
        self.assertEqual(legacy['text'], 'Hello')
        
        # Test error message
        error_msg = OutputMessage(OutputType.ERROR, "Error occurred", time.time())
        legacy = error_msg.to_legacy_format()
        self.assertEqual(legacy['type'], 'error')
        self.assertEqual(legacy['message'], 'Error occurred')
        
        # Test clear screen
        clear_msg = OutputMessage(OutputType.CLEAR_SCREEN, None, time.time())
        legacy = clear_msg.to_legacy_format()
        self.assertEqual(legacy['type'], 'clear_screen')

    def test_subscriber_management(self):
        """Test subscriber management functionality"""
        received_messages = []
        
        def test_subscriber(message):
            received_messages.append(message)
        
        # Add subscriber
        self.output_manager.add_subscriber(test_subscriber)
        
        # Emit a message
        self.output_manager.text("Test message")
        
        # Check subscriber received it
        self.assertEqual(len(received_messages), 1)
        self.assertEqual(received_messages[0].content, "Test message")
        
        # Remove subscriber
        self.output_manager.remove_subscriber(test_subscriber)
        
        # Emit another message
        self.output_manager.text("Second message")
        
        # Should still be only 1 message
        self.assertEqual(len(received_messages), 1)

    def test_multiple_subscribers(self):
        """Test multiple subscribers receiving messages"""
        subscriber1_messages = []
        subscriber2_messages = []
        
        def subscriber1(message):
            subscriber1_messages.append(message.content)
        
        def subscriber2(message):
            subscriber2_messages.append(message.content)
        
        # Add both subscribers
        self.output_manager.add_subscriber(subscriber1)
        self.output_manager.add_subscriber(subscriber2)
        
        # Emit messages
        self.output_manager.text("Message 1")
        self.output_manager.error("Error 1")
        
        # Both should receive both messages
        self.assertEqual(len(subscriber1_messages), 2)
        self.assertEqual(len(subscriber2_messages), 2)
        self.assertEqual(subscriber1_messages[0], "Message 1")
        self.assertEqual(subscriber2_messages[1], "Error 1")

    def test_type_filtering(self):
        """Test filtering messages by type"""
        # Create filter that only allows errors and warnings
        type_filter = TypeFilter([OutputType.ERROR, OutputType.WARNING])
        self.output_manager.add_filter(type_filter)
        
        received_messages = []
        self.output_manager.add_subscriber(lambda msg: received_messages.append(msg))
        
        # Emit different types of messages
        self.output_manager.text("Should be filtered")
        self.output_manager.error("Should pass")
        self.output_manager.warning("Should pass")
        self.output_manager.debug("Should be filtered")
        
        # Only error and warning should pass
        self.assertEqual(len(received_messages), 2)
        self.assertEqual(received_messages[0].type, OutputType.ERROR)
        self.assertEqual(received_messages[1].type, OutputType.WARNING)

    def test_priority_filtering(self):
        """Test filtering messages by priority"""
        # Create filter that only allows high priority messages
        priority_filter = PriorityFilter(OutputPriority.HIGH)
        self.output_manager.add_filter(priority_filter)
        
        received_messages = []
        self.output_manager.add_subscriber(lambda msg: received_messages.append(msg))
        
        # Emit messages with different priorities
        self.output_manager.emit(OutputType.TEXT, "Low priority", OutputPriority.LOW)
        self.output_manager.emit(OutputType.TEXT, "Normal priority", OutputPriority.NORMAL)
        self.output_manager.emit(OutputType.TEXT, "High priority", OutputPriority.HIGH)
        self.output_manager.emit(OutputType.TEXT, "Critical priority", OutputPriority.CRITICAL)
        
        # Only high and critical should pass
        self.assertEqual(len(received_messages), 2)
        self.assertEqual(received_messages[0].priority, OutputPriority.HIGH)
        self.assertEqual(received_messages[1].priority, OutputPriority.CRITICAL)

    def test_debug_filtering(self):
        """Test debug message filtering"""
        # Test with debug mode off
        no_debug_manager = StreamingOutputManager(debug_mode=False)
        received_messages = []
        no_debug_manager.add_subscriber(lambda msg: received_messages.append(msg))
        
        no_debug_manager.text("Normal message")
        no_debug_manager.debug("Debug message")
        
        # Only normal message should pass
        self.assertEqual(len(received_messages), 1)
        self.assertEqual(received_messages[0].type, OutputType.TEXT)
        
        # Test with debug mode on
        debug_manager = StreamingOutputManager(debug_mode=True)
        debug_messages = []
        debug_manager.add_subscriber(lambda msg: debug_messages.append(msg))
        
        debug_manager.text("Normal message")
        debug_manager.debug("Debug message")
        
        # Both should pass
        self.assertEqual(len(debug_messages), 2)

    def test_message_buffering(self):
        """Test message buffering functionality"""
        # Emit several messages
        for i in range(5):
            self.output_manager.text(f"Message {i}")
        
        # Check buffer contains messages
        buffer = self.output_manager.buffer
        self.assertEqual(len(buffer), 5)
        
        # Check messages are in order
        for i in range(5):
            self.assertEqual(buffer[i].content, f"Message {i}")
        
        # Test buffer size limit
        original_limit = self.output_manager.max_buffer_size
        self.output_manager.max_buffer_size = 3
        
        # Add more messages
        for i in range(5, 10):
            self.output_manager.text(f"Message {i}")
        
        # Buffer should only contain last 3 messages
        self.assertEqual(len(self.output_manager.buffer), 3)
        self.assertEqual(self.output_manager.buffer[-1].content, "Message 9")
        
        # Restore original limit
        self.output_manager.max_buffer_size = original_limit

    def test_message_retrieval_methods(self):
        """Test various message retrieval methods"""
        # Emit different types of messages
        self.output_manager.text("Text 1")
        self.output_manager.error("Error 1")
        self.output_manager.text("Text 2")
        start_time = time.time()
        time.sleep(0.001)  # Small delay
        self.output_manager.warning("Warning 1")
        
        # Test get_recent_messages
        recent = self.output_manager.get_recent_messages(3)
        self.assertEqual(len(recent), 3)
        self.assertEqual(recent[-1].content, "Warning 1")
        
        # Test get_messages_by_type
        text_messages = self.output_manager.get_messages_by_type(OutputType.TEXT)
        self.assertEqual(len(text_messages), 2)
        self.assertEqual(text_messages[0].content, "Text 1")
        self.assertEqual(text_messages[1].content, "Text 2")
        
        # Test get_messages_since
        recent_messages = self.output_manager.get_messages_since(start_time)
        self.assertEqual(len(recent_messages), 1)
        self.assertEqual(recent_messages[0].content, "Warning 1")

    def test_convenience_methods(self):
        """Test convenience methods for common message types"""
        # Test text method
        text_msg = self.output_manager.text("Hello")
        self.assertEqual(text_msg.type, OutputType.TEXT)
        self.assertEqual(text_msg.content, "Hello")
        
        # Test error method
        error_msg = self.output_manager.error("Error occurred")
        self.assertEqual(error_msg.type, OutputType.ERROR)
        self.assertEqual(error_msg.priority, OutputPriority.HIGH)
        
        # Test warning method
        warning_msg = self.output_manager.warning("Warning message")
        self.assertEqual(warning_msg.type, OutputType.WARNING)
        self.assertEqual(warning_msg.priority, OutputPriority.NORMAL)
        
        # Test debug method
        debug_msg = self.output_manager.debug("Debug info")
        self.assertEqual(debug_msg.type, OutputType.DEBUG)
        self.assertEqual(debug_msg.priority, OutputPriority.LOW)
        
        # Test clear_screen method
        clear_msg = self.output_manager.clear_screen()
        self.assertEqual(clear_msg.type, OutputType.CLEAR_SCREEN)
        
        # Test program_start/end methods
        start_msg = self.output_manager.program_start({"name": "test.bas"})
        self.assertEqual(start_msg.type, OutputType.PROGRAM_START)
        self.assertEqual(start_msg.priority, OutputPriority.HIGH)
        
        end_msg = self.output_manager.program_end({"status": "completed"})
        self.assertEqual(end_msg.type, OutputType.PROGRAM_END)

    def test_statistics_tracking(self):
        """Test statistics tracking functionality"""
        # Initial stats
        stats = self.output_manager.get_statistics()
        initial_sent = stats['messages_sent']
        initial_filtered = stats['messages_filtered']
        
        # Add a filter that blocks text messages
        text_filter = TypeFilter([OutputType.ERROR])
        self.output_manager.add_filter(text_filter)
        
        # Emit messages
        self.output_manager.text("Filtered message")
        self.output_manager.error("Passed message")
        
        # Check updated stats
        new_stats = self.output_manager.get_statistics()
        self.assertEqual(new_stats['messages_sent'], initial_sent + 1)  # Only error passed
        self.assertEqual(new_stats['messages_filtered'], initial_filtered + 1)  # Text was filtered
        self.assertEqual(new_stats['buffer_size'], len(self.output_manager.buffer))

    def test_legacy_output_adapter(self):
        """Test legacy output adapter functionality"""
        adapter = LegacyOutputAdapter(self.output_manager)
        
        received_legacy = []
        
        def legacy_callback(output):
            received_legacy.extend(output)
        
        # Set legacy callback
        adapter.set_output_callback(legacy_callback)
        
        # Emit messages through new system
        self.output_manager.text("Hello")
        self.output_manager.error("Error")
        
        # Should receive legacy format
        self.assertEqual(len(received_legacy), 2)
        self.assertEqual(received_legacy[0]['type'], 'text')
        self.assertEqual(received_legacy[0]['text'], 'Hello')
        self.assertEqual(received_legacy[1]['type'], 'error')
        self.assertEqual(received_legacy[1]['message'], 'Error')

    def test_legacy_emit_output_compatibility(self):
        """Test legacy emit_output method compatibility"""
        adapter = LegacyOutputAdapter(self.output_manager)
        
        # Test emitting legacy format messages
        legacy_output = [
            {'type': 'text', 'text': 'Hello World'},
            {'type': 'error', 'message': 'Something went wrong'},
            {'type': 'clear_screen'}
        ]
        
        result = adapter.emit_output(legacy_output)
        self.assertEqual(result, legacy_output)  # Should return original
        
        # Check messages were added to buffer
        buffer = self.output_manager.buffer
        self.assertTrue(len(buffer) >= 3)
        
        # Check last few messages match what we emitted
        recent = buffer[-3:]
        self.assertEqual(recent[0].content, 'Hello World')
        self.assertEqual(recent[1].content, 'Something went wrong')
        self.assertEqual(recent[2].type, OutputType.CLEAR_SCREEN)

    def test_integration_with_coco_basic(self):
        """Test integration with CoCoBasic emulator"""
        # Test that CoCoBasic has output manager
        self.assertTrue(hasattr(self.basic, 'output_manager'))
        self.assertTrue(hasattr(self.basic, 'legacy_adapter'))
        
        # Enable debug mode for this test so debug messages aren't filtered
        self.basic.output_manager.debug_mode = True
        # Update the debug filter to match
        for filter_obj in self.basic.output_manager.filters:
            if hasattr(filter_obj, 'debug_mode'):
                filter_obj.debug_mode = True
        
        # Test new output methods
        self.basic.emit_text("Test text")
        self.basic.emit_error("Test error")
        self.basic.emit_debug("Test debug")
        
        # Check messages were buffered
        buffer = self.basic.output_manager.buffer
        self.assertTrue(len(buffer) >= 3)

    def test_message_streaming(self):
        """Test message streaming functionality"""
        # Add some messages
        self.output_manager.text("Message 1")
        self.output_manager.error("Error 1")
        start_time = time.time()
        time.sleep(0.001)
        self.output_manager.text("Message 2")
        
        # Test streaming all messages
        all_messages = list(self.output_manager.stream_messages())
        self.assertTrue(len(all_messages) >= 3)
        
        # Test streaming since timestamp
        recent_messages = list(self.output_manager.stream_messages(start_time))
        self.assertEqual(len(recent_messages), 1)
        self.assertEqual(recent_messages[0].content, "Message 2")

    def test_to_legacy_format_conversion(self):
        """Test conversion of message buffer to legacy format"""
        # Add various message types
        self.output_manager.text("Text message")
        self.output_manager.error("Error message")
        self.output_manager.clear_screen()
        
        # Convert to legacy format
        legacy_messages = self.output_manager.to_legacy_format()
        
        self.assertTrue(len(legacy_messages) >= 3)
        
        # Check last three messages
        recent = legacy_messages[-3:]
        self.assertEqual(recent[0]['type'], 'text')
        self.assertEqual(recent[0]['text'], 'Text message')
        self.assertEqual(recent[1]['type'], 'error')
        self.assertEqual(recent[1]['message'], 'Error message')
        self.assertEqual(recent[2]['type'], 'clear_screen')

    def test_filter_combinations(self):
        """Test combining multiple filters"""
        # Add both type and priority filters
        type_filter = TypeFilter([OutputType.TEXT, OutputType.ERROR])
        priority_filter = PriorityFilter(OutputPriority.NORMAL)
        
        self.output_manager.add_filter(type_filter)
        self.output_manager.add_filter(priority_filter)
        
        received = []
        self.output_manager.add_subscriber(lambda msg: received.append(msg))
        
        # Emit various messages
        self.output_manager.emit(OutputType.TEXT, "Low text", OutputPriority.LOW)      # Filtered by priority
        self.output_manager.emit(OutputType.TEXT, "Normal text", OutputPriority.NORMAL) # Should pass
        self.output_manager.emit(OutputType.ERROR, "High error", OutputPriority.HIGH)   # Should pass
        self.output_manager.emit(OutputType.DEBUG, "Normal debug", OutputPriority.NORMAL) # Filtered by type
        
        # Should only receive text and error messages with normal+ priority
        self.assertEqual(len(received), 2)
        self.assertEqual(received[0].content, "Normal text")
        self.assertEqual(received[1].content, "High error")

    def test_buffer_clearing(self):
        """Test buffer clearing functionality"""
        # Add some messages
        self.output_manager.text("Message 1")
        self.output_manager.text("Message 2")
        
        # Verify buffer has messages
        self.assertTrue(len(self.output_manager.buffer) >= 2)
        
        # Clear buffer
        self.output_manager.clear_buffer()
        
        # Verify buffer is empty
        self.assertEqual(len(self.output_manager.buffer), 0)

    def test_subscriber_error_handling(self):
        """Test that subscriber errors don't break the output system"""
        def good_subscriber(message):
            pass  # Works fine
        
        def bad_subscriber(message):
            raise Exception("Subscriber error!")
        
        # Add both subscribers
        self.output_manager.add_subscriber(good_subscriber)
        self.output_manager.add_subscriber(bad_subscriber)
        
        # Emit message - should not raise exception despite bad subscriber
        try:
            self.output_manager.text("Test message")
            # If we get here, the error was handled properly
            self.assertTrue(True)
        except Exception:
            self.assertTrue(False, "Subscriber error should not propagate")

    def test_metadata_in_messages(self):
        """Test message metadata functionality"""
        metadata = {
            'command': 'PRINT',
            'execution_time': 0.001,
            'memory_usage': 1024
        }
        
        message = self.output_manager.emit(
            OutputType.TEXT,
            "Hello with metadata",
            source="test_module",
            line_number=42,
            metadata=metadata
        )
        
        self.assertEqual(message.metadata, metadata)
        
        # Test metadata in dictionary conversion
        msg_dict = message.to_dict()
        self.assertEqual(msg_dict['command'], 'PRINT')
        self.assertEqual(msg_dict['execution_time'], 0.001)
        self.assertEqual(msg_dict['memory_usage'], 1024)

    def test_output_types_enum(self):
        """Test all output types are properly supported"""
        test_cases = [
            (OutputType.TEXT, "text"),
            (OutputType.ERROR, "error"),
            (OutputType.GRAPHICS, "graphics"),
            (OutputType.SOUND, "sound"),
            (OutputType.CLEAR_SCREEN, "clear_screen"),
            (OutputType.PROMPT, "prompt"),
            (OutputType.DEBUG, "debug"),
            (OutputType.WARNING, "warning")
        ]
        
        for output_type, expected_value in test_cases:
            self.assertEqual(output_type.value, expected_value)
            
            # Test each type can be emitted
            message = self.output_manager.emit(output_type, f"Test {expected_value}")
            self.assertEqual(message.type, output_type)

    def test_source_and_line_tracking(self):
        """Test source module and line number tracking"""
        # Test with source and line number
        message = self.output_manager.text("Test", source="test_module", line_number=100)
        
        self.assertEqual(message.source, "test_module")
        self.assertEqual(message.line_number, 100)
        
        # Test in dictionary format
        msg_dict = message.to_dict()
        self.assertEqual(msg_dict['source'], 'test_module')
        self.assertEqual(msg_dict['line'], 100)


if __name__ == '__main__':
    test = OutputManagerTest("Output Manager Tests")
    results = test.run_all_tests()
    from test_base import print_test_results
    print_test_results(results, verbose=True)