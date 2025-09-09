"""
Error Context System for TRS-80 Color Computer BASIC Emulator

This module provides structured error handling with enhanced context information,
including line numbers, column positions, and source code context for better debugging.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


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
        """Format error message with optional context"""
        if include_context and self.context:
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
        self.execution_stack: List[SourceContext] = []
    
    def set_context(self, line: int, source: Optional[str] = None, 
                   filename: Optional[str] = None, function: Optional[str] = None):
        """Set current execution context"""
        self.current_line = line
        self.current_source = source
        self.current_filename = filename
        self.current_function = function
    
    def push_context(self, line: int, source: Optional[str] = None, 
                    filename: Optional[str] = None, function: Optional[str] = None):
        """Push context onto execution stack (for nested calls)"""
        context = SourceContext(
            line_number=line,
            source_line=source,
            filename=filename,
            function_name=function
        )
        self.execution_stack.append(context)
        self.set_context(line, source, filename, function)
    
    def pop_context(self):
        """Pop context from execution stack"""
        if self.execution_stack:
            self.execution_stack.pop()
            if self.execution_stack:
                last_context = self.execution_stack[-1]
                self.set_context(
                    last_context.line_number,
                    last_context.source_line,
                    last_context.filename,
                    last_context.function_name
                )
            else:
                self.current_line = None
                self.current_source = None
                self.current_filename = None
                self.current_function = None
    
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
        """Create a syntax error with context"""
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
                  line: Optional[int] = None) -> BasicError:
        """Create a type mismatch error"""
        context = self.create_context(line)
        details = f"Expected {expected_type}, got {actual_type}"
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
                        line: Optional[int] = None) -> BasicError:
        """Create an arithmetic error"""
        context = self.create_context(line)
        details = f"Operation: {operation}"
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
        
        return BasicError(
            message=message,
            category=ErrorCategory.FILE,
            severity=ErrorSeverity.ERROR,
            context=context,
            details=details,
            suggestions=suggestions,
            error_code="FILE_ERROR"
        )
    
    def warning(self, message: str, line: Optional[int] = None,
               suggestions: Optional[List[str]] = None) -> BasicError:
        """Create a warning message"""
        context = self.create_context(line)
        return BasicError(
            message=message,
            category=ErrorCategory.SYNTAX,  # Most warnings are syntax-related
            severity=ErrorSeverity.WARNING,
            context=context,
            suggestions=suggestions,
            error_code="WARNING"
        )
    
    def get_stack_trace(self) -> List[str]:
        """Get current execution stack trace"""
        trace = []
        for i, context in enumerate(reversed(self.execution_stack)):
            prefix = "  " * i
            trace.append(f"{prefix}at {context}")
        return trace


# Global error context manager instance
error_context = ErrorContextManager()


def create_legacy_error(message: str) -> Dict[str, Any]:
    """Create legacy-format error for backward compatibility"""
    return {'type': 'error', 'message': message}


def convert_error_to_legacy(error: BasicError) -> Dict[str, Any]:
    """Convert structured error to legacy format"""
    return create_legacy_error(error.message)


def enhance_error_message(message: str, line: Optional[int] = None) -> str:
    """Enhance a simple error message with context"""
    if line is not None:
        return f"{message} at line {line}"
    return message


# Common error creation functions for backward compatibility
def syntax_error(message: str, line: Optional[int] = None) -> Dict[str, Any]:
    """Create a syntax error in legacy format"""
    enhanced_message = enhance_error_message(f"SYNTAX ERROR: {message}", line)
    return create_legacy_error(enhanced_message)


def runtime_error(message: str, line: Optional[int] = None) -> Dict[str, Any]:
    """Create a runtime error in legacy format"""
    enhanced_message = enhance_error_message(message, line)
    return create_legacy_error(enhanced_message)


def file_error(message: str, filename: str, line: Optional[int] = None) -> Dict[str, Any]:
    """Create a file error in legacy format"""
    enhanced_message = enhance_error_message(f"{message}: {filename}", line)
    return create_legacy_error(enhanced_message)