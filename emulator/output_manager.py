"""
StreamingOutputManager for TRS-80 Color Computer BASIC Emulator

Provides centralized output management with structured messages,
filtering, and legacy compatibility.
"""

from typing import Any, Dict, List, Optional, Callable, Union
from enum import Enum
from dataclasses import dataclass
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
    source: Optional[str] = None
    line_number: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_legacy_format(self) -> Dict[str, Any]:
        """Convert to legacy dict format for backward compatibility"""
        if self.type == OutputType.TEXT:
            return {'type': 'text', 'text': str(self.content)}
        elif self.type == OutputType.ERROR:
            return {'type': 'error', 'message': str(self.content)}
        elif self.type == OutputType.CLEAR_SCREEN:
            return {'type': 'clear_screen'}
        elif self.type == OutputType.GRAPHICS:
            return {'type': 'graphics', 'content': self.content}
        else:
            result = {'type': self.type.value, 'content': self.content}
            if self.source:
                result['source'] = self.source
            return result


class OutputFilter:
    """Base class for output filters"""

    def should_include(self, message: OutputMessage) -> bool:
        return True

    def transform(self, message: OutputMessage) -> OutputMessage:
        return message


class DebugFilter(OutputFilter):
    """Filter that removes debug messages when not in debug mode"""

    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode

    def should_include(self, message: OutputMessage) -> bool:
        if message.type == OutputType.DEBUG and not self.debug_mode:
            return False
        return True


class StreamingOutputManager:
    """Centralized output management with structured messages and filtering."""

    def __init__(self, debug_mode: bool = False):
        self.subscribers: List[Callable] = []
        self.filters: List[OutputFilter] = []
        self.buffer: List[OutputMessage] = []
        self._max_buffer_size = 1000
        self.debug_mode = debug_mode
        self.messages_sent = 0
        self.messages_filtered = 0
        self.filters.append(DebugFilter(debug_mode))

    def add_subscriber(self, callback: Callable[[OutputMessage], None]):
        """Add a callback that receives all output messages"""
        if callback not in self.subscribers:
            self.subscribers.append(callback)

    def remove_subscriber(self, callback: Callable):
        """Remove a subscriber callback"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)

    def emit(self, output_type: OutputType, content: Any,
             priority: OutputPriority = OutputPriority.NORMAL,
             source: Optional[str] = None,
             line_number: Optional[int] = None,
             metadata: Optional[Dict[str, Any]] = None) -> OutputMessage:
        """Emit a structured output message."""
        message = OutputMessage(
            type=output_type, content=content, timestamp=time.time(),
            priority=priority, source=source, line_number=line_number,
            metadata=metadata
        )

        for filter_obj in self.filters:
            if not filter_obj.should_include(message):
                self.messages_filtered += 1
                return message
            message = filter_obj.transform(message)

        self.buffer.append(message)
        if len(self.buffer) > self._max_buffer_size:
            self.buffer.pop(0)

        for subscriber in self.subscribers:
            try:
                subscriber(message)
            except Exception:
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

    def debug(self, message: str, source: Optional[str] = None,
              line_number: Optional[int] = None) -> OutputMessage:
        """Emit a debug message"""
        return self.emit(OutputType.DEBUG, message, OutputPriority.LOW,
                        source=source, line_number=line_number)


class LegacyOutputAdapter:
    """Adapter providing old-style emit_output interface on top of StreamingOutputManager."""

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
            self.legacy_callback([message.to_legacy_format()])

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
                self.output_manager.emit(OutputType.CLEAR_SCREEN, None)
            elif output_type == 'graphics':
                self.output_manager.emit(OutputType.GRAPHICS, item.get('content'))
            else:
                self.output_manager.emit(OutputType.TEXT, str(item))
        return output
