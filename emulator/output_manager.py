"""
StreamingOutputManager for TRS-80 Color Computer BASIC Emulator

This module provides centralized output management with enhanced streaming capabilities,
output filtering, buffering, and formatting for different interface types.
"""

from typing import Any, Dict, List, Optional, Callable, Union, Iterator
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import time


class OutputType(Enum):
    """Types of output that can be generated"""
    TEXT = "text"
    ERROR = "error"
    GRAPHICS = "graphics"
    SOUND = "sound"
    CLEAR_SCREEN = "clear_screen"
    SET_CURSOR = "set_cursor"
    PROMPT = "prompt"
    INPUT_REQUEST = "input_request"
    PROGRAM_START = "program_start"
    PROGRAM_END = "program_end"
    DEBUG = "debug"
    WARNING = "warning"


class OutputPriority(Enum):
    """Priority levels for output messages"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class OutputMessage:
    """Structured output message with metadata"""
    type: OutputType
    content: Any
    timestamp: float
    priority: OutputPriority = OutputPriority.NORMAL
    source: Optional[str] = None  # Source module/command that generated this
    line_number: Optional[int] = None  # Program line number if applicable
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for compatibility"""
        result = {
            'type': self.type.value,
            'timestamp': self.timestamp,
            'priority': self.priority.value
        }
        
        # Handle different content types
        if self.type == OutputType.TEXT:
            result['text'] = str(self.content)
        elif self.type == OutputType.ERROR:
            result['message'] = str(self.content)
        else:
            result['content'] = self.content
        
        # Add optional fields
        if self.source:
            result['source'] = self.source
        if self.line_number is not None:
            result['line'] = self.line_number
        if self.metadata:
            result.update(self.metadata)
        
        return result
    
    def to_legacy_format(self) -> Dict[str, Any]:
        """Convert to legacy format for backward compatibility"""
        if self.type == OutputType.TEXT:
            return {'type': 'text', 'text': str(self.content)}
        elif self.type == OutputType.ERROR:
            return {'type': 'error', 'message': str(self.content)}
        elif self.type == OutputType.CLEAR_SCREEN:
            return {'type': 'clear_screen'}
        elif self.type == OutputType.GRAPHICS:
            return {'type': 'graphics', 'content': self.content}
        else:
            return self.to_dict()


class OutputFilter:
    """Base class for output filters"""
    
    def should_include(self, message: OutputMessage) -> bool:
        """Return True if message should be included in output"""
        return True
    
    def transform(self, message: OutputMessage) -> OutputMessage:
        """Transform message before output"""
        return message


class TypeFilter(OutputFilter):
    """Filter messages by output type"""
    
    def __init__(self, allowed_types: List[OutputType]):
        self.allowed_types = set(allowed_types)
    
    def should_include(self, message: OutputMessage) -> bool:
        return message.type in self.allowed_types


class PriorityFilter(OutputFilter):
    """Filter messages by priority level"""
    
    def __init__(self, min_priority: OutputPriority):
        self.min_priority = min_priority
    
    def should_include(self, message: OutputMessage) -> bool:
        return message.priority.value >= self.min_priority.value


class DebugFilter(OutputFilter):
    """Filter that removes debug messages in production mode"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
    
    def should_include(self, message: OutputMessage) -> bool:
        if message.type == OutputType.DEBUG and not self.debug_mode:
            return False
        return True


class StreamingOutputManager:
    """
    Centralized output management system with streaming capabilities.
    
    Provides:
    - Structured output messages with metadata
    - Real-time streaming to multiple subscribers
    - Output filtering and transformation
    - Buffering for batch processing
    - Different output formats for different interfaces
    """
    
    def __init__(self, debug_mode: bool = False):
        self.subscribers: List[Callable] = []
        self.filters: List[OutputFilter] = []
        self.buffer: List[OutputMessage] = []
        self._max_buffer_size = 1000
        self.debug_mode = debug_mode
        
        # Statistics
        self.messages_sent = 0
        self.messages_filtered = 0
        
        # Add default filters
        self.add_filter(DebugFilter(debug_mode))
    
    @property
    def max_buffer_size(self) -> int:
        """Get the maximum buffer size"""
        return self._max_buffer_size
    
    @max_buffer_size.setter
    def max_buffer_size(self, value: int):
        """Set the maximum buffer size and trim buffer if needed"""
        self._max_buffer_size = value
        # Trim buffer to new size if needed
        while len(self.buffer) > self._max_buffer_size:
            self.buffer.pop(0)
    
    def add_subscriber(self, callback: Callable[[OutputMessage], None]):
        """Add a callback function that will receive all output messages"""
        if callback not in self.subscribers:
            self.subscribers.append(callback)
    
    def remove_subscriber(self, callback: Callable):
        """Remove a subscriber callback"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    def add_filter(self, filter_obj: OutputFilter):
        """Add an output filter"""
        self.filters.append(filter_obj)
    
    def remove_filter(self, filter_obj: OutputFilter):
        """Remove an output filter"""
        if filter_obj in self.filters:
            self.filters.remove(filter_obj)
    
    def emit(self, output_type: OutputType, content: Any, 
             priority: OutputPriority = OutputPriority.NORMAL,
             source: Optional[str] = None,
             line_number: Optional[int] = None,
             metadata: Optional[Dict[str, Any]] = None) -> OutputMessage:
        """
        Emit an output message.
        
        Args:
            output_type: Type of output message
            content: The actual content/data
            priority: Priority level of the message
            source: Source module/command that generated this
            line_number: Program line number if applicable
            metadata: Additional metadata
            
        Returns:
            The created OutputMessage
        """
        message = OutputMessage(
            type=output_type,
            content=content,
            timestamp=time.time(),
            priority=priority,
            source=source,
            line_number=line_number,
            metadata=metadata
        )
        
        # Apply filters
        for filter_obj in self.filters:
            if not filter_obj.should_include(message):
                self.messages_filtered += 1
                return message
            message = filter_obj.transform(message)
        
        # Add to buffer
        self.buffer.append(message)
        if len(self.buffer) > self._max_buffer_size:
            self.buffer.pop(0)  # Remove oldest message
        
        # Send to subscribers
        for subscriber in self.subscribers:
            try:
                subscriber(message)
            except Exception:
                # Don't let subscriber errors break the output system
                pass
        
        self.messages_sent += 1
        return message
    
    def text(self, text: str, source: Optional[str] = None, 
             line_number: Optional[int] = None) -> OutputMessage:
        """Emit a text message"""
        return self.emit(OutputType.TEXT, text, source=source, line_number=line_number)
    
    def error(self, message: str, source: Optional[str] = None,
              line_number: Optional[int] = None) -> OutputMessage:
        """Emit an error message"""
        return self.emit(OutputType.ERROR, message, OutputPriority.HIGH, 
                        source=source, line_number=line_number)
    
    def warning(self, message: str, source: Optional[str] = None,
                line_number: Optional[int] = None) -> OutputMessage:
        """Emit a warning message"""
        return self.emit(OutputType.WARNING, message, OutputPriority.NORMAL,
                        source=source, line_number=line_number)
    
    def debug(self, message: str, source: Optional[str] = None,
              line_number: Optional[int] = None) -> OutputMessage:
        """Emit a debug message"""
        return self.emit(OutputType.DEBUG, message, OutputPriority.LOW,
                        source=source, line_number=line_number)
    
    def clear_screen(self) -> OutputMessage:
        """Emit a clear screen command"""
        return self.emit(OutputType.CLEAR_SCREEN, None)
    
    def graphics(self, graphics_data: Any, source: Optional[str] = None) -> OutputMessage:
        """Emit graphics data"""
        return self.emit(OutputType.GRAPHICS, graphics_data, source=source)
    
    def sound(self, sound_data: Any, source: Optional[str] = None) -> OutputMessage:
        """Emit sound data"""
        return self.emit(OutputType.SOUND, sound_data, source=source)
    
    def program_start(self, program_info: Optional[Dict] = None) -> OutputMessage:
        """Signal that program execution is starting"""
        return self.emit(OutputType.PROGRAM_START, program_info, OutputPriority.HIGH)
    
    def program_end(self, program_info: Optional[Dict] = None) -> OutputMessage:
        """Signal that program execution has ended"""
        return self.emit(OutputType.PROGRAM_END, program_info, OutputPriority.HIGH)
    
    def get_recent_messages(self, count: int = 10) -> List[OutputMessage]:
        """Get the most recent messages from the buffer"""
        return self.buffer[-count:] if count <= len(self.buffer) else self.buffer[:]
    
    def get_messages_by_type(self, output_type: OutputType) -> List[OutputMessage]:
        """Get all messages of a specific type from the buffer"""
        return [msg for msg in self.buffer if msg.type == output_type]
    
    def get_messages_since(self, timestamp: float) -> List[OutputMessage]:
        """Get all messages since a specific timestamp"""
        return [msg for msg in self.buffer if msg.timestamp >= timestamp]
    
    def clear_buffer(self):
        """Clear the message buffer"""
        self.buffer.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get output statistics"""
        return {
            'messages_sent': self.messages_sent,
            'messages_filtered': self.messages_filtered,
            'buffer_size': len(self.buffer),
            'subscribers': len(self.subscribers),
            'filters': len(self.filters)
        }
    
    def to_legacy_format(self, messages: Optional[List[OutputMessage]] = None) -> List[Dict[str, Any]]:
        """
        Convert messages to legacy format for backward compatibility.
        
        Args:
            messages: List of messages to convert, or None for recent buffer
            
        Returns:
            List of legacy format dictionaries
        """
        if messages is None:
            messages = self.buffer
        
        return [msg.to_legacy_format() for msg in messages]
    
    def stream_messages(self, since_timestamp: Optional[float] = None) -> Iterator[OutputMessage]:
        """
        Stream messages from the buffer.
        
        Args:
            since_timestamp: Only return messages after this timestamp
            
        Yields:
            OutputMessage objects
        """
        for message in self.buffer:
            if since_timestamp is None or message.timestamp >= since_timestamp:
                yield message


class LegacyOutputAdapter:
    """
    Adapter to make StreamingOutputManager compatible with legacy code.
    
    Provides the old-style emit_output interface while using the new system.
    """
    
    def __init__(self, output_manager: StreamingOutputManager):
        self.output_manager = output_manager
        self.legacy_callback: Optional[Callable] = None
    
    def set_output_callback(self, callback: Optional[Callable]):
        """Set legacy output callback"""
        if self.legacy_callback:
            self.output_manager.remove_subscriber(self._legacy_subscriber)
        
        self.legacy_callback = callback
        if callback:
            self.output_manager.add_subscriber(self._legacy_subscriber)
    
    def _legacy_subscriber(self, message: OutputMessage):
        """Convert new messages to legacy format and call legacy callback"""
        if self.legacy_callback:
            legacy_data = [message.to_legacy_format()]
            self.legacy_callback(legacy_data)
    
    def emit_output(self, output: Union[List[Dict], Dict]):
        """Legacy emit_output interface"""
        if isinstance(output, dict):
            output = [output]
        
        for item in output:
            output_type = item.get('type', 'text')
            
            if output_type == 'text':
                self.output_manager.text(item.get('text', ''))
            elif output_type == 'error':
                self.output_manager.error(item.get('message', ''))
            elif output_type == 'clear_screen':
                self.output_manager.clear_screen()
            elif output_type == 'graphics':
                self.output_manager.graphics(item.get('content'))
            else:
                # For unknown types, emit as-is
                self.output_manager.emit(OutputType.TEXT, str(item))
        
        return output