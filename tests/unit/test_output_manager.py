#!/usr/bin/env python3

"""
Tests for Streaming Output Manager

Tests the centralized output management system including structured messages,
debug filtering, buffering, subscriber management, and legacy compatibility.
"""

import sys
import os
import time
import pytest
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from emulator.output_manager import (
    StreamingOutputManager, OutputMessage, OutputType, OutputPriority,
    DebugFilter, LegacyOutputAdapter
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
        message = output_manager.text("Hello, World!")

        assert message.type == OutputType.TEXT
        assert message.content == "Hello, World!"
        assert message.priority == OutputPriority.NORMAL
        assert message.timestamp > 0

    def test_output_message_creation(self, basic, helpers):
        """Test OutputMessage creation"""
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

        # Test graphics
        gfx_msg = OutputMessage(OutputType.GRAPHICS, {'data': 'test'}, time.time())
        legacy = gfx_msg.to_legacy_format()
        assert legacy['type'] == 'graphics'
        assert legacy['content'] == {'data': 'test'}

        # Test fallback type includes source
        other_msg = OutputMessage(OutputType.SOUND, "beep", time.time(), source="test")
        legacy = other_msg.to_legacy_format()
        assert legacy['type'] == 'sound'
        assert legacy['source'] == 'test'

    def test_subscriber_management(self, basic, helpers, output_manager):
        """Test subscriber management functionality"""
        received_messages = []

        def test_subscriber(message):
            received_messages.append(message)

        output_manager.add_subscriber(test_subscriber)
        output_manager.text("Test message")
        assert len(received_messages) == 1
        assert received_messages[0].content == "Test message"

        output_manager.remove_subscriber(test_subscriber)
        output_manager.text("Second message")
        assert len(received_messages) == 1

    def test_duplicate_subscriber_ignored(self, basic, helpers, output_manager):
        """Adding the same subscriber twice should not duplicate it."""
        received = []
        def sub(msg):
            received.append(msg)

        output_manager.add_subscriber(sub)
        output_manager.add_subscriber(sub)
        output_manager.text("Test")
        assert len(received) == 1

    def test_multiple_subscribers(self, basic, helpers, output_manager):
        """Test multiple subscribers receiving messages"""
        subscriber1_messages = []
        subscriber2_messages = []

        def subscriber1(message):
            subscriber1_messages.append(message.content)

        def subscriber2(message):
            subscriber2_messages.append(message.content)

        output_manager.add_subscriber(subscriber1)
        output_manager.add_subscriber(subscriber2)

        output_manager.text("Message 1")
        output_manager.error("Error 1")

        assert len(subscriber1_messages) == 2
        assert len(subscriber2_messages) == 2
        assert subscriber1_messages[0] == "Message 1"
        assert subscriber2_messages[1] == "Error 1"

    def test_debug_filtering(self, basic, helpers):
        """Test debug message filtering"""
        # With debug mode off
        no_debug_manager = StreamingOutputManager(debug_mode=False)
        received_messages = []
        no_debug_manager.add_subscriber(lambda msg: received_messages.append(msg))

        no_debug_manager.text("Normal message")
        no_debug_manager.debug("Debug message")

        assert len(received_messages) == 1
        assert received_messages[0].type == OutputType.TEXT

        # With debug mode on
        debug_manager = StreamingOutputManager(debug_mode=True)
        debug_messages = []
        debug_manager.add_subscriber(lambda msg: debug_messages.append(msg))

        debug_manager.text("Normal message")
        debug_manager.debug("Debug message")

        assert len(debug_messages) == 2

    def test_message_buffering(self, basic, helpers, output_manager):
        """Test message buffering functionality"""
        for i in range(5):
            output_manager.text(f"Message {i}")

        buffer = output_manager.buffer
        assert len(buffer) == 5
        for i in range(5):
            assert buffer[i].content == f"Message {i}"

    def test_buffer_size_limit(self, basic, helpers):
        """Test that buffer respects max size limit."""
        manager = StreamingOutputManager(debug_mode=True)
        manager._max_buffer_size = 3

        for i in range(5):
            manager.text(f"Message {i}")

        assert len(manager.buffer) == 3
        assert manager.buffer[-1].content == "Message 4"
        assert manager.buffer[0].content == "Message 2"

    def test_convenience_methods(self, basic, helpers, output_manager):
        """Test convenience methods for common message types"""
        text_msg = output_manager.text("Hello")
        assert text_msg.type == OutputType.TEXT
        assert text_msg.content == "Hello"

        error_msg = output_manager.error("Error occurred")
        assert error_msg.type == OutputType.ERROR
        assert error_msg.priority == OutputPriority.HIGH

        debug_msg = output_manager.debug("Debug info")
        assert debug_msg.type == OutputType.DEBUG
        assert debug_msg.priority == OutputPriority.LOW

    def test_messages_sent_counter(self, basic, helpers, output_manager):
        """Test that messages_sent counter increments correctly."""
        assert output_manager.messages_sent == 0
        output_manager.text("One")
        output_manager.error("Two")
        assert output_manager.messages_sent == 2

    def test_messages_filtered_counter(self, basic, helpers):
        """Test that messages_filtered counter increments for filtered messages."""
        manager = StreamingOutputManager(debug_mode=False)
        assert manager.messages_filtered == 0
        manager.debug("Filtered out")
        assert manager.messages_filtered == 1
        manager.text("Not filtered")
        assert manager.messages_filtered == 1

    def test_legacy_output_adapter(self, basic, helpers, output_manager):
        """Test legacy output adapter functionality"""
        adapter = LegacyOutputAdapter(output_manager)
        received_legacy = []

        def legacy_callback(output):
            received_legacy.extend(output)

        adapter.set_output_callback(legacy_callback)

        output_manager.text("Hello")
        output_manager.error("Error")

        assert len(received_legacy) == 2
        assert received_legacy[0]['type'] == 'text'
        assert received_legacy[0]['text'] == 'Hello'
        assert received_legacy[1]['type'] == 'error'
        assert received_legacy[1]['message'] == 'Error'

    def test_legacy_adapter_callback_replacement(self, basic, helpers, output_manager):
        """Replacing the legacy callback should unsubscribe the old one."""
        adapter = LegacyOutputAdapter(output_manager)
        first = []
        second = []

        adapter.set_output_callback(lambda out: first.extend(out))
        output_manager.text("A")
        assert len(first) == 1

        adapter.set_output_callback(lambda out: second.extend(out))
        output_manager.text("B")
        # First callback should not receive "B"
        assert len(first) == 1
        assert len(second) == 1

    def test_legacy_emit_output_compatibility(self, basic, helpers, output_manager):
        """Test legacy emit_output method compatibility"""
        adapter = LegacyOutputAdapter(output_manager)

        legacy_output = [
            {'type': 'text', 'text': 'Hello World'},
            {'type': 'error', 'message': 'Something went wrong'},
            {'type': 'clear_screen'}
        ]

        result = adapter.emit_output(legacy_output)
        assert result == legacy_output

        buffer = output_manager.buffer
        assert len(buffer) >= 3
        recent = buffer[-3:]
        assert recent[0].content == 'Hello World'
        assert recent[1].content == 'Something went wrong'
        assert recent[2].type == OutputType.CLEAR_SCREEN

    def test_legacy_emit_output_single_dict(self, basic, helpers, output_manager):
        """emit_output should accept a single dict (not just a list)."""
        adapter = LegacyOutputAdapter(output_manager)
        result = adapter.emit_output({'type': 'text', 'text': 'Single'})
        assert result == [{'type': 'text', 'text': 'Single'}]
        assert output_manager.buffer[-1].content == 'Single'

    def test_integration_with_coco_basic(self, basic, helpers):
        """Test integration with CoCoBasic emulator"""
        assert hasattr(basic, 'output_manager')
        assert hasattr(basic, 'legacy_adapter')

        # Enable debug mode so debug messages aren't filtered
        basic.output_manager.debug_mode = True
        for filter_obj in basic.output_manager.filters:
            if hasattr(filter_obj, 'debug_mode'):
                filter_obj.debug_mode = True

        basic.emit_text("Test text")
        basic.emit_error("Test error")
        basic.emit_debug("Test debug")

        buffer = basic.output_manager.buffer
        assert len(buffer) >= 3

    def test_subscriber_error_handling(self, basic, helpers, output_manager):
        """Test that subscriber errors don't break the output system"""
        def bad_subscriber(message):
            raise Exception("Subscriber error!")

        output_manager.add_subscriber(bad_subscriber)

        # Should not raise despite bad subscriber
        output_manager.text("Test message")
        assert output_manager.messages_sent == 1

    def test_metadata_in_messages(self, basic, helpers, output_manager):
        """Test message metadata functionality"""
        metadata = {'command': 'PRINT', 'execution_time': 0.001}

        message = output_manager.emit(
            OutputType.TEXT, "Hello with metadata",
            source="test_module", line_number=42, metadata=metadata
        )

        assert message.metadata == metadata
        assert message.metadata['command'] == 'PRINT'

    def test_output_types_enum(self, basic, helpers, output_manager):
        """Test all output types are properly supported"""
        test_cases = [
            (OutputType.TEXT, "text"),
            (OutputType.ERROR, "error"),
            (OutputType.GRAPHICS, "graphics"),
            (OutputType.SOUND, "sound"),
            (OutputType.CLEAR_SCREEN, "clear_screen"),
            (OutputType.PROMPT, "prompt"),
            (OutputType.DEBUG, "debug"),
            (OutputType.WARNING, "warning"),
        ]

        for output_type, expected_value in test_cases:
            assert output_type.value == expected_value
            message = output_manager.emit(output_type, f"Test {expected_value}")
            assert message.type == output_type

    def test_source_and_line_tracking(self, basic, helpers, output_manager):
        """Test source module and line number tracking"""
        message = output_manager.text("Test", source="test_module", line_number=100)

        assert message.source == "test_module"
        assert message.line_number == 100
