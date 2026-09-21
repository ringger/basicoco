"""
Error Context System for TRS-80 Color Computer BASIC Emulator

This module provides structured error handling with enhanced context information,
including line numbers, column positions, and source code context for better debugging.
"""

import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

# Python exceptions that evaluating BASIC code can raise and that must be
# reported as BASIC runtime errors (never allowed to escape the interpreter).
BASIC_RUNTIME_ERRORS = (ValueError, IndexError, KeyError, AttributeError,
                        TypeError, ZeroDivisionError, OverflowError)


class ErrorSeverity(Enum):
    """Error severity levels"""
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


class ErrorCategory(Enum):
    """Categories of errors for better organization"""
    SYNTAX = "syntax"
    RUNTIME = "runtime"
    TYPE = "type"
    REFERENCE = "reference"
    ARITHMETIC = "arithmetic"
    FILE = "file"
    MEMORY = "memory"
    SYSTEM = "system"


@dataclass
class SourceContext:
    """Source code context for error reporting"""
    line_number: int
    column: Optional[int] = None
    length: Optional[int] = None
    source_line: Optional[str] = None
    filename: Optional[str] = None
    function_name: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation for error messages"""
        location = f"line {self.line_number}"
        if self.column is not None:
            location += f", column {self.column}"
        if self.filename:
            location += f" in {self.filename}"
        return location


@dataclass
class BasicError:
    """Structured error with rich context information"""
    message: str
    category: ErrorCategory
    severity: ErrorSeverity = ErrorSeverity.ERROR
    context: Optional[SourceContext] = None
    details: Optional[str] = None
    suggestions: Optional[List[str]] = None
    error_code: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for output"""
        result = {
            'type': 'error',
            'message': self.message,
            'category': self.category.value,
            'severity': self.severity.value
        }
        
        if self.context:
            result['line'] = self.context.line_number
            if self.context.column is not None:
                result['column'] = self.context.column
            if self.context.source_line:
                result['source'] = self.context.source_line
            if self.context.filename:
                result['filename'] = self.context.filename
        
        if self.details:
            result['details'] = self.details
        
        if self.suggestions:
            result['suggestions'] = self.suggestions
            
        if self.error_code:
            result['code'] = self.error_code
        
        return result
    
    def format_message(self, include_context: bool = True) -> str:
        """Format error message with optional context.

        Immediate-mode errors (line 0, or the temporary line -1) carry no
        location, as on the CoCo; a message that already names its line
        (a wrapped inner error) isn't given a second one.
        """
        if (include_context and self.context and self.context.line_number > 0
                and ' at line ' not in self.message):
            return f"{self.message} at {self.context}"
        return self.message
    
    def format_detailed(self) -> str:
        """Format detailed error message with suggestions"""
        lines = [self.format_message()]
        
        if self.details:
            lines.append(f"Details: {self.details}")
        
        if self.context and self.context.source_line:
            lines.append(f"Source: {self.context.source_line}")
            if self.context.column is not None and self.context.length:
                # Add pointer to error location
                pointer = " " * (self.context.column - 1) + "^" * max(1, self.context.length)
                lines.append(f"        {pointer}")
        
        if self.suggestions:
            lines.append("Suggestions:")
            for suggestion in self.suggestions:
                lines.append(f"  - {suggestion}")
        
        return "\n".join(lines)


class ErrorContextManager:
    """
    Manager for error context and structured error reporting.
    
    Provides facilities for creating rich error messages with source context,
    tracking execution state, and formatting errors for different output modes.
    """
    
    def __init__(self):
        self.current_line: Optional[int] = None
        self.current_source: Optional[str] = None
        self.current_filename: Optional[str] = None
        self.current_function: Optional[str] = None

    def set_context(self, line: int, source: Optional[str] = None, 
                   filename: Optional[str] = None, function: Optional[str] = None):
        """Set current execution context"""
        self.current_line = line
        self.current_source = source
        self.current_filename = filename
        self.current_function = function

    def create_context(self, line: Optional[int] = None, column: Optional[int] = None,
                      length: Optional[int] = None, source: Optional[str] = None) -> SourceContext:
        """Create source context from current state or provided parameters"""
        return SourceContext(
            line_number=line or self.current_line or 0,
            column=column,
            length=length,
            source_line=source or self.current_source,
            filename=self.current_filename,
            function_name=self.current_function
        )
    
    def syntax_error(self, message: str, line: Optional[int] = None,
                    column: Optional[int] = None, length: Optional[int] = None,
                    suggestions: Optional[List[str]] = None) -> BasicError:
        """Create a syntax error with context. Auto-prefixes 'SYNTAX ERROR:' if not present."""
        if not message.startswith('SYNTAX ERROR'):
            message = f'SYNTAX ERROR: {message}'
        context = self.create_context(line, column, length)
        return BasicError(
            message=message,
            category=ErrorCategory.SYNTAX,
            severity=ErrorSeverity.ERROR,
            context=context,
            suggestions=suggestions,
            error_code="SYNTAX"
        )
    
    def runtime_error(self, message: str, line: Optional[int] = None,
                     details: Optional[str] = None,
                     suggestions: Optional[List[str]] = None) -> BasicError:
        """Create a runtime error with context"""
        context = self.create_context(line)
        return BasicError(
            message=message,
            category=ErrorCategory.RUNTIME,
            severity=ErrorSeverity.ERROR,
            context=context,
            details=details,
            suggestions=suggestions,
            error_code="RUNTIME"
        )
    
    def type_error(self, message: str, expected_type: str, actual_type: str,
                  line: Optional[int] = None, suggestions: Optional[List[str]] = None) -> BasicError:
        """Create a type mismatch error"""
        context = self.create_context(line)
        details = f"Expected {expected_type}, got {actual_type}"
        
        if suggestions is None:
            suggestions = [f"Ensure the value is of type {expected_type}"]
        
        return BasicError(
            message=message,
            category=ErrorCategory.TYPE,
            severity=ErrorSeverity.ERROR,
            context=context,
            details=details,
            suggestions=suggestions,
            error_code="TYPE_MISMATCH"
        )
    
    def reference_error(self, name: str, error_type: str = "UNDEFINED",
                       line: Optional[int] = None,
                       suggestions: Optional[List[str]] = None) -> BasicError:
        """Create a reference error (undefined variable, function, etc.)"""
        context = self.create_context(line)
        message = f"{error_type}: {name}"
        
        if not suggestions:
            if error_type == "UNDEFINED VARIABLE":
                suggestions = [
                    f"Define the variable first: LET {name} = value",
                    "Check for typos in the variable name"
                ]
            elif error_type == "UNDEFINED FUNCTION":
                suggestions = [
                    "Check the function name spelling",
                    "Ensure the function is supported in this BASIC dialect"
                ]
            elif error_type == "UNDEFINED LINE":
                suggestions = [
                    "Check that the line number exists in the program",
                    "Use LIST to see available line numbers"
                ]
        
        return BasicError(
            message=message,
            category=ErrorCategory.REFERENCE,
            severity=ErrorSeverity.ERROR,
            context=context,
            suggestions=suggestions,
            error_code=error_type.replace(" ", "_")
        )
    
    def arithmetic_error(self, message: str, operation: str,
                        line: Optional[int] = None, suggestions: Optional[List[str]] = None) -> BasicError:
        """Create an arithmetic error"""
        context = self.create_context(line)
        details = f"Operation: {operation}"
        
        if suggestions is None:
            suggestions = []
            
            if "division by zero" in message.lower():
                suggestions.append("Check that the divisor is not zero")
                suggestions.append("Use conditional logic to handle zero divisors")
            elif "overflow" in message.lower():
                suggestions.append("Use smaller numbers to avoid overflow")
                suggestions.append("Break the calculation into smaller steps")
        
        return BasicError(
            message=message,
            category=ErrorCategory.ARITHMETIC,
            severity=ErrorSeverity.ERROR,
            context=context,
            details=details,
            suggestions=suggestions,
            error_code="ARITHMETIC"
        )
    
    def file_error(self, message: str, filename: str, operation: str,
                  line: Optional[int] = None) -> BasicError:
        """Create a file operation error"""
        context = self.create_context(line)
        details = f"File: {filename}, Operation: {operation}"
        suggestions = []
        
        if "not found" in message.lower():
            suggestions.append("Check that the file exists in the expected location")
            suggestions.append("Verify the filename spelling and extension")
        elif "permission" in message.lower():
            suggestions.append("Check file permissions")
            suggestions.append("Ensure the file is not locked by another program")
        else:
            suggestions.append("Use DIR to list the available files")
            suggestions.append('Filenames are plain names inside programs/, e.g. "MYPROG"')

        return BasicError(
            message=message,
            category=ErrorCategory.FILE,
            severity=ErrorSeverity.ERROR,
            context=context,
            details=details,
            suggestions=suggestions,
            error_code="FILE_ERROR"
        )

    def wrapped_error(self, prefix: str, exc: Exception, line: Optional[int] = None,
                      suggestions: Optional[List[str]] = None) -> BasicError:
        """A runtime error that wraps another error's text, e.g.
        "Error in PSET: TYPE MISMATCH ...".

        The inner text may be a full formatted error (message, Details,
        Suggestions). Only its first line goes into the message, with any
        trailing "at line N" dropped (the wrapper adds the current line), and
        its own suggestions win over the generic *suggestions*.
        """
        text_lines = str(exc).splitlines() or ['']
        head = re.sub(r' at line -?\d+.*$', '', text_lines[0])
        inner = [l.strip()[2:] for l in text_lines[1:] if l.strip().startswith('- ')]
        return self.runtime_error(f"{prefix}{head}", line,
                                  suggestions=inner or suggestions)


# ── Response builder helpers ──────────────────────────────────────────
# Use these instead of hand-building response dicts.

def error_response(error: 'BasicError') -> List[Dict[str, Any]]:
    """Build a standard error response list from a BasicError."""
    return [{'type': 'error', 'message': error.format_detailed()}]


def text_response(text: str, source: Optional[str] = None) -> List[Dict[str, Any]]:
    """Build a standard text response list (for returning from execute_* methods)."""
    return [text_message(text, source=source)]


def text_message(text: str, source: Optional[str] = None, inline: bool = False) -> Dict[str, Any]:
    """Build a single text message dict (for appending to output lists)."""
    result = {'type': 'text', 'text': text}
    if source:
        result['source'] = source
    if inline:
        result['inline'] = True
    return result


def error_message(message: str) -> Dict[str, Any]:
    """Build a single error message dict (for appending to output lists)."""
    return {'type': 'error', 'message': message}