#!/usr/bin/env python3

"""
Comprehensive tests for Streaming Output Manager

Tests the centralized output management system with enhanced streaming capabilities,
output filtering, buffering, and formatting for different interface types.
"""

import sys
import os
import time
import pytest
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from test_base import BaseTestCase
from emulator.output_manager import (
    StreamingOutputManager, OutputMessage, OutputType, OutputPriority,
    TypeFilter, PriorityFilter, DebugFilter, LegacyOutputAdapter
)
from emulator.core import CoCoBasic


class TestOutputManager:
    """Test cases for Streaming Output Manager functionality"""

    @pytest.fixture
    def output_manager(self):
        """Fixture to provide output manager for tests"""
        return StreamingOutputManager(debug_mode=True)

    def test_basic_functionality(self, basic, helpers, output_manager):
        """Test basic output manager functionality"""
        # Test creating and emitting a message
        message = self.output_manager.text("Hello, World!")
        
        assert message.type == OutputType.TEXT
        assert message.content == "Hello, World!"
        assert message.priority == OutputPriority.NORMAL
        assert message.timestamp > 0

    def test_output_message_creation(self, basic, helpers):
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
        
        assert message.type == OutputType.ERROR
        assert message.content == "Test error message"
        assert message.priority == OutputPriority.HIGH
        assert message.source == "test_module"
        assert message.line_number == 42

    def test_message_to_dict_conversion(self, basic, helpers):
        """Test converting messages to dictionary format"""
        message = OutputMessage(
            type=OutputType.TEXT,
            content="Test message",
            timestamp=time.time(),
            source="test",
            line_number=10
        )
        
        msg_dict = message.to_dict()
        assert msg_dict['type'] == 'text'
        assert msg_dict['text'] == 'Test message'
        assert msg_dict['source'] == 'test'
        assert msg_dict['line'] == 10
        assert 'timestamp' in msg_dict

    def test_message_to_legacy_format(self, basic, helpers):
        """Test converting messages to legacy format"""
        # Test text message
        text_msg = OutputMessage(OutputType.TEXT, "Hello", time.time())
        legacy = text_msg.to_legacy_format()
        assert legacy['type'] == 'text'
        assert legacy['text'] == 'Hello'
        
        # Test error message
        error_msg = OutputMessage(OutputType.ERROR, "Error occurred", time.time())
        legacy = error_msg.to_legacy_format()
        assert legacy['type'] == 'error'
        assert legacy['message'] == 'Error occurred'
        
        # Test clear screen
        clear_msg = OutputMessage(OutputType.CLEAR_SCREEN, None, time.time())
        legacy = clear_msg.to_legacy_format()
        assert legacy['type'] == 'clear_screen'

    def test_subscriber_management(self, basic, helpers):
        """Test subscriber management functionality"""
        received_messages = []
        
        def test_subscriber(message):
            received_messages.append(message)
        
        # Add subscriber
        self.output_manager.add_subscriber(test_subscriber)
        
        # Emit a message
        self.output_manager.text("Test message")
        
        # Check subscriber received it
        assert len(received_messages) == 1
        assert received_messages[0].content == "Test message"
        
        # Remove subscriber
        self.output_manager.remove_subscriber(test_subscriber)
        
        # Emit another message
        self.output_manager.text("Second message")
        
        # Should still be only 1 message
        assert len(received_messages) == 1

    def test_multiple_subscribers(self, basic, helpers):
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
        assert len(subscriber1_messages) == 2
        assert len(subscriber2_messages) == 2
        assert subscriber1_messages[0] == "Message 1"
        assert subscriber2_messages[1] == "Error 1"

    def test_type_filtering(self, basic, helpers):
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
        assert len(received_messages) == 2
        assert received_messages[0].type == OutputType.ERROR
        assert received_messages[1].type == OutputType.WARNING

    def test_priority_filtering(self, basic, helpers):
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
        assert len(received_messages) == 2
        assert received_messages[0].priority == OutputPriority.HIGH
        assert received_messages[1].priority == OutputPriority.CRITICAL

    def test_debug_filtering(self, basic, helpers):
        """Test debug message filtering"""
        # Test with debug mode off
        no_debug_manager = StreamingOutputManager(debug_mode=False)
        received_messages = []
        no_debug_manager.add_subscriber(lambda msg: received_messages.append(msg))
        
        no_debug_manager.text("Normal message")
        no_debug_manager.debug("Debug message")
        
        # Only normal message should pass
        assert len(received_messages) == 1
        assert received_messages[0].type == OutputType.TEXT
        
        # Test with debug mode on
        debug_manager = StreamingOutputManager(debug_mode=True)
        debug_messages = []
        debug_manager.add_subscriber(lambda msg: debug_messages.append(msg))
        
        debug_manager.text("Normal message")
        debug_manager.debug("Debug message")
        
        # Both should pass
        assert len(debug_messages) == 2

    def test_message_buffering(self, basic, helpers):
        """Test message buffering functionality"""
        # Emit several messages
        for i in range(5):
            self.output_manager.text(f"Message {i}")
        
        # Check buffer contains messages
        buffer = self.output_manager.buffer
        assert len(buffer) == 5
        
        # Check messages are in order
        for i in range(5):
            assert buffer[i].content == f"Message {i}"
        
        # Test buffer size limit
        original_limit = self.output_manager.max_buffer_size
        self.output_manager.max_buffer_size = 3
        
        # Add more messages
        for i in range(5, 10):
            self.output_manager.text(f"Message {i}")
        
        # Buffer should only contain last 3 messages
        assert len(self.output_manager.buffer) == 3
        assert self.output_manager.buffer[-1].content == "Message 9"
        
        # Restore original limit
        self.output_manager.max_buffer_size = original_limit

    def test_message_retrieval_methods(self, basic, helpers):
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
        assert len(recent) == 3
        assert recent[-1].content == "Warning 1"
        
        # Test get_messages_by_type
        text_messages = self.output_manager.get_messages_by_type(OutputType.TEXT)
        assert len(text_messages) == 2
        assert text_messages[0].content == "Text 1"
        assert text_messages[1].content == "Text 2"
        
        # Test get_messages_since
        recent_messages = self.output_manager.get_messages_since(start_time)
        assert len(recent_messages) == 1
        assert recent_messages[0].content == "Warning 1"

    def test_convenience_methods(self, basic, helpers):
        """Test convenience methods for common message types"""
        # Test text method
        text_msg = self.output_manager.text("Hello")
        assert text_msg.type == OutputType.TEXT
        assert text_msg.content == "Hello"
        
        # Test error method
        error_msg = self.output_manager.error("Error occurred")
        assert error_msg.type == OutputType.ERROR
        assert error_msg.priority == OutputPriority.HIGH
        
        # Test warning method
        warning_msg = self.output_manager.warning("Warning message")
        assert warning_msg.type == OutputType.WARNING
        assert warning_msg.priority == OutputPriority.NORMAL
        
        # Test debug method
        debug_msg = self.output_manager.debug("Debug info")
        assert debug_msg.type == OutputType.DEBUG
        assert debug_msg.priority == OutputPriority.LOW
        
        # Test clear_screen method
        clear_msg = self.output_manager.clear_screen()
        assert clear_msg.type == OutputType.CLEAR_SCREEN
        
        # Test program_start/end methods
        start_msg = self.output_manager.program_start({"name": "test.bas"})
        assert start_msg.type == OutputType.PROGRAM_START
        assert start_msg.priority == OutputPriority.HIGH
        
        end_msg = self.output_manager.program_end({"status": "completed"})
        assert end_msg.type == OutputType.PROGRAM_END

    def test_statistics_tracking(self, basic, helpers):
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
        assert new_stats['messages_sent'] == initial_sent + 1  # Only error passed
        assert new_stats['messages_filtered'] == initial_filtered + 1  # Text was filtered
        assert new_stats['buffer_size'] == len(self.output_manager.buffer)

    def test_legacy_output_adapter(self, basic, helpers):
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
        assert len(received_legacy) == 2
        assert received_legacy[0]['type'] == 'text'
        assert received_legacy[0]['text'] == 'Hello'
        assert received_legacy[1]['type'] == 'error'
        assert received_legacy[1]['message'] == 'Error'

    def test_legacy_emit_output_compatibility(self, basic, helpers):
        """Test legacy emit_output method compatibility"""
        adapter = LegacyOutputAdapter(self.output_manager)
        
        # Test emitting legacy format messages
        legacy_output = [
            {'type': 'text', 'text': 'Hello World'},
            {'type': 'error', 'message': 'Something went wrong'},
            {'type': 'clear_screen'}
        ]
        
        result = adapter.emit_output(legacy_output)
        assert result == legacy_output  # Should return original
        
        # Check messages were added to buffer
        buffer = self.output_manager.buffer
        assert len(buffer >= 3)
        
        # Check last few messages match what we emitted
        recent = buffer[-3:]
        assert recent[0].content == 'Hello World'
        assert recent[1].content == 'Something went wrong'
        assert recent[2].type == OutputType.CLEAR_SCREEN

    def test_integration_with_coco_basic(self, basic, helpers):
        """Test integration with CoCoBasic emulator"""
        # Test that CoCoBasic has output manager
        assert hasattr(basic, 'output_manager')
        assert hasattr(basic, 'legacy_adapter')
        
        # Enable debug mode for this test so debug messages aren't filtered
        basic.output_manager.debug_mode = True
        # Update the debug filter to match
        for filter_obj in basic.output_manager.filters:
            if hasattr(filter_obj, 'debug_mode'):
                filter_obj.debug_mode = True
        
        # Test new output methods
        basic.emit_text("Test text")
        basic.emit_error("Test error")
        basic.emit_debug("Test debug")
        
        # Check messages were buffered
        buffer = basic.output_manager.buffer
        assert len(buffer >= 3)

    def test_message_streaming(self, basic, helpers):
        """Test message streaming functionality"""
        # Add some messages
        self.output_manager.text("Message 1")
        self.output_manager.error("Error 1")
        start_time = time.time()
        time.sleep(0.001)
        self.output_manager.text("Message 2")
        
        # Test streaming all messages
        all_messages = list(self.output_manager.stream_messages())
        assert len(all_messages >= 3)
        
        # Test streaming since timestamp
        recent_messages = list(self.output_manager.stream_messages(start_time))
        assert len(recent_messages) == 1
        assert recent_messages[0].content == "Message 2"

    def test_to_legacy_format_conversion(self, basic, helpers):
        """Test conversion of message buffer to legacy format"""
        # Add various message types
        self.output_manager.text("Text message")
        self.output_manager.error("Error message")
        self.output_manager.clear_screen()
        
        # Convert to legacy format
        legacy_messages = self.output_manager.to_legacy_format()
        
        assert len(legacy_messages >= 3)
        
        # Check last three messages
        recent = legacy_messages[-3:]
        assert recent[0]['type'] == 'text'
        assert recent[0]['text'] == 'Text message'
        assert recent[1]['type'] == 'error'
        assert recent[1]['message'] == 'Error message'
        assert recent[2]['type'] == 'clear_screen'

    def test_filter_combinations(self, basic, helpers):
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
        assert len(received) == 2
        assert received[0].content == "Normal text"
        assert received[1].content == "High error"

    def test_buffer_clearing(self, basic, helpers):
        """Test buffer clearing functionality"""
        # Add some messages
        self.output_manager.text("Message 1")
        self.output_manager.text("Message 2")
        
        # Verify buffer has messages
        assert len(self.output_manager.buffer >= 2)
        
        # Clear buffer
        self.output_manager.clear_buffer()
        
        # Verify buffer is empty
        assert len(self.output_manager.buffer) == 0

    def test_subscriber_error_handling(self, basic, helpers):
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
            assert True
        except Exception:
            assert False, "Subscriber error should not propagate"

    def test_metadata_in_messages(self, basic, helpers):
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
        
        assert message.metadata == metadata
        
        # Test metadata in dictionary conversion
        msg_dict = message.to_dict()
        assert msg_dict['command'] == 'PRINT'
        assert msg_dict['execution_time'] == 0.001
        assert msg_dict['memory_usage'] == 1024

    def test_output_types_enum(self, basic, helpers):
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
            assert output_type.value == expected_value
            
            # Test each type can be emitted
            message = self.output_manager.emit(output_type, f"Test {expected_value}")
            assert message.type == output_type

    def test_source_and_line_tracking(self, basic, helpers):
        """Test source module and line number tracking"""
        # Test with source and line number
        message = self.output_manager.text("Test", source="test_module", line_number=100)
        
        assert message.source == "test_module"
        assert message.line_number == 100
        
        # Test in dictionary format
        msg_dict = message.to_dict()
        assert msg_dict['source'] == 'test_module'
        assert msg_dict['line'] == 100
