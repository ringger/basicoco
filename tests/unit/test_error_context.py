#!/usr/bin/env python3

"""
Comprehensive tests for Error Context System

Tests the structured error reporting system that provides enhanced error messages
with line numbers, context information, and helpful suggestions.
"""

import pytest
from emulator.error_context import (
    ErrorContextManager, BasicError, SourceContext, 
    ErrorSeverity, ErrorCategory,
    create_legacy_error, convert_error_to_legacy,
    syntax_error, runtime_error, file_error
)
from emulator.core import CoCoBasic


class TestErrorContext:
    """Test cases for Error Context System functionality"""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test environment"""
        self.error_manager = ErrorContextManager()

    def test_basic_functionality(self, basic, helpers):
        """Test basic error context functionality"""
        # Test creating a simple syntax error
        error = self.error_manager.syntax_error("Missing semicolon", line=10)
        assert error.message == "Missing semicolon"
        assert error.category == ErrorCategory.SYNTAX
        assert error.context.line_number == 10

    def test_source_context_creation(self, basic, helpers):
        """Test SourceContext creation and formatting"""
        context = SourceContext(
            line_number=25,
            column=15,
            length=5,
            source_line="PRINT A + B",
            filename="test.bas",
            function_name="main"
        )
        
        assert context.line_number == 25
        assert context.column == 15
        assert context.length == 5
        assert context.source_line == "PRINT A + B"
        assert context.filename == "test.bas"
        assert context.function_name == "main"
        
        # Test string representation
        context_str = str(context)
        assert "line 25" in context_str
        assert "column 15" in context_str
        assert "test.bas" in context_str

    def test_basic_error_creation(self, basic, helpers):
        """Test BasicError creation and formatting"""
        context = SourceContext(line_number=10, source_line="LET A = B + C")
        error = BasicError(
            message="Undefined variable",
            category=ErrorCategory.REFERENCE,
            severity=ErrorSeverity.ERROR,
            context=context,
            details="Variable 'C' has not been defined",
            suggestions=["Define C first: LET C = value", "Check spelling of variable name"],
            error_code="UNDEFINED_VAR"
        )
        
        assert error.message == "Undefined variable"
        assert error.category == ErrorCategory.REFERENCE
        assert error.severity == ErrorSeverity.ERROR
        assert error.context.line_number == 10
        assert len(error.suggestions) == 2
        assert error.error_code == "UNDEFINED_VAR"

    def test_error_to_dict_conversion(self, basic, helpers):
        """Test converting errors to dictionary format"""
        context = SourceContext(line_number=5, column=10, source_line="GOTO 100")
        error = BasicError(
            message="Undefined line",
            category=ErrorCategory.REFERENCE,
            context=context,
            suggestions=["Add line 100 to your program"]
        )
        
        error_dict = error.to_dict()
        assert error_dict['type'] == 'error'
        assert error_dict['message'] == 'Undefined line'
        assert error_dict['category'] == 'reference'
        assert error_dict['line'] == 5
        assert error_dict['column'] == 10
        assert error_dict['source'] == 'GOTO 100'
        assert len(error_dict['suggestions']) == 1

    def test_error_formatting(self, basic, helpers):
        """Test error message formatting"""
        context = SourceContext(line_number=15, column=8, source_line="PRINT A B")
        error = BasicError(
            message="Syntax error",
            category=ErrorCategory.SYNTAX,
            context=context,
            details="Missing comma between arguments"
        )
        
        # Test basic formatting
        formatted = error.format_message()
        assert "Syntax error" in formatted
        assert "line 15" in formatted
        
        # Test detailed formatting
        detailed = error.format_detailed()
        assert "Syntax error" in detailed
        assert "PRINT A B" in detailed
        assert "Missing comma" in detailed

    def test_context_manager_functionality(self, basic, helpers):
        """Test ErrorContextManager state management"""
        # Test setting context
        self.error_manager.set_context(42, "TEST LINE", "test.bas", "test_function")
        assert self.error_manager.current_line == 42
        assert self.error_manager.current_source == "TEST LINE"
        assert self.error_manager.current_filename == "test.bas"
        assert self.error_manager.current_function == "test_function"
        
        # Test context stack - push_context creates a new context
        self.error_manager.push_context(50, "NESTED LINE", "nested.bas")
        assert self.error_manager.current_line == 50
        assert len(self.error_manager.execution_stack) == 1
        
        # After popping, there's no previous context to restore to
        # so current values become None
        self.error_manager.pop_context()
        assert self.error_manager.current_line == None
        assert len(self.error_manager.execution_stack) == 0

    def test_syntax_error_creation(self, basic, helpers):
        """Test syntax error creation with context"""
        self.error_manager.set_context(25, "PRINT A + +", "program.bas")
        
        error = self.error_manager.syntax_error(
            "Invalid operator sequence",
            column=10,
            length=3,
            suggestions=["Remove extra operator", "Check expression syntax"]
        )
        
        assert error.category == ErrorCategory.SYNTAX
        assert error.context.line_number == 25
        assert error.context.column == 10
        assert error.context.length == 3
        assert len(error.suggestions) == 2
        assert error.error_code == "SYNTAX"

    def test_runtime_error_creation(self, basic, helpers):
        """Test runtime error creation"""
        error = self.error_manager.runtime_error(
            "Division by zero",
            line=100,
            details="Attempted to divide by zero in expression",
            suggestions=["Check that divisor is not zero", "Use conditional logic"]
        )
        
        assert error.category == ErrorCategory.RUNTIME
        assert error.context.line_number == 100
        assert error.details == "Attempted to divide by zero in expression"

    def test_type_error_creation(self, basic, helpers):
        """Test type mismatch error creation"""
        error = self.error_manager.type_error(
            "Type mismatch in assignment",
            "string",
            "number",
            line=75
        )
        
        assert error.category == ErrorCategory.TYPE
        assert error.context.line_number == 75
        assert "Expected string, got number" in error.details
        assert error.error_code == "TYPE_MISMATCH"

    def test_reference_error_creation(self, basic, helpers):
        """Test reference error creation"""
        error = self.error_manager.reference_error(
            "UNDEFINED_VAR",
            "UNDEFINED VARIABLE",
            line=30
        )
        
        assert error.category == ErrorCategory.REFERENCE
        assert error.message == "UNDEFINED VARIABLE: UNDEFINED_VAR"
        assert error.context.line_number == 30
        assert len(error.suggestions) > 0

    def test_arithmetic_error_creation(self, basic, helpers):
        """Test arithmetic error creation"""
        error = self.error_manager.arithmetic_error(
            "Division by zero",
            "10 / 0",
            line=60
        )
        
        assert error.category == ErrorCategory.ARITHMETIC
        assert "10 / 0" in error.details
        assert any("divisor" in suggestion for suggestion in error.suggestions)

    def test_file_error_creation(self, basic, helpers):
        """Test file operation error creation"""
        error = self.error_manager.file_error(
            "File not found",
            "missing.bas",
            "load",
            line=5
        )
        
        assert error.category == ErrorCategory.FILE
        assert "missing.bas" in error.details
        assert "load" in error.details
        assert any("exists" in suggestion for suggestion in error.suggestions)

    def test_warning_creation(self, basic, helpers):
        """Test warning message creation"""
        warning = self.error_manager.warning(
            "Variable not used",
            line=20,
            suggestions=["Remove unused variable", "Use variable in calculation"]
        )
        
        assert warning.severity == ErrorSeverity.WARNING
        assert warning.category == ErrorCategory.SYNTAX
        assert warning.error_code == "WARNING"

    def test_stack_trace_generation(self, basic, helpers):
        """Test execution stack trace generation"""
        # Build a call stack
        self.error_manager.push_context(10, "GOSUB 100", "main.bas", "main")
        self.error_manager.push_context(100, "GOSUB 200", "main.bas", "subroutine1") 
        self.error_manager.push_context(200, "LET A = B + C", "main.bas", "subroutine2")
        
        stack_trace = self.error_manager.get_stack_trace()
        assert len(stack_trace) == 3
        
        # Check that most recent call is first
        assert "line 200" in stack_trace[0]
        assert "line 100" in stack_trace[1]
        assert "line 10" in stack_trace[2]

    def test_legacy_compatibility_functions(self, basic, helpers):
        """Test legacy compatibility functions"""
        # Test create_legacy_error
        legacy = create_legacy_error("Test error message")
        assert legacy['type'] == 'error'
        assert legacy['message'] == 'Test error message'
        
        # Test convert_error_to_legacy
        error = BasicError("Structured error", ErrorCategory.SYNTAX)
        legacy = convert_error_to_legacy(error)
        assert legacy['type'] == 'error'
        assert legacy['message'] == 'Structured error'
        
        # Test standalone error functions
        syntax_err = syntax_error("Bad syntax", 10)
        assert syntax_err['type'] == 'error'
        assert "SYNTAX ERROR" in syntax_err['message']
        assert "line 10" in syntax_err['message']
        
        runtime_err = runtime_error("Runtime problem", 25)
        assert "line 25" in runtime_err['message']
        
        file_err = file_error("File issue", "test.bas", 15)
        assert "test.bas" in file_err['message']

    def test_integration_with_expression_evaluator(self, basic, helpers):
        """Test integration with expression evaluator error reporting"""
        # This tests that the enhanced error system works with the expression evaluator
        try:
            # This should trigger enhanced error reporting
            result = basic.evaluate_expression("", line=42)
        except ValueError as e:
            error_msg = str(e)
            assert "line 42" in error_msg  # Should include line number
            assert "Empty expression" in error_msg

    def test_multiple_error_contexts(self, basic, helpers):
        """Test handling multiple error contexts"""
        errors = []
        
        # Create errors with different contexts
        self.error_manager.set_context(10, "LINE 10", "file1.bas")
        errors.append(self.error_manager.syntax_error("Error 1"))
        
        self.error_manager.set_context(20, "LINE 20", "file2.bas")
        errors.append(self.error_manager.runtime_error("Error 2"))
        
        self.error_manager.set_context(30, "LINE 30", "file3.bas")
        errors.append(self.error_manager.type_error("Error 3", "string", "number"))
        
        # Verify each error has correct context
        assert errors[0].context.line_number == 10
        assert errors[1].context.line_number == 20
        assert errors[2].context.line_number == 30
        
        # Verify different error types
        assert errors[0].category == ErrorCategory.SYNTAX
        assert errors[1].category == ErrorCategory.RUNTIME
        assert errors[2].category == ErrorCategory.TYPE

    def test_error_message_enhancement(self, basic, helpers):
        """Test error message enhancement functions"""
        from emulator.error_context import enhance_error_message
        
        # Test basic enhancement
        enhanced = enhance_error_message("Basic error")
        assert enhanced == "Basic error"
        
        # Test with line number
        enhanced = enhance_error_message("Basic error", 42)
        assert enhanced == "Basic error at line 42"

    def test_context_preservation_across_calls(self, basic, helpers):
        """Test that context is preserved across multiple operations"""
        # Set initial context
        self.error_manager.set_context(100, "MAIN LINE", "program.bas", "main")
        
        # Create multiple errors - they should all inherit the context
        error1 = self.error_manager.syntax_error("First error")
        error2 = self.error_manager.runtime_error("Second error")
        
        assert error1.context.line_number == 100
        assert error2.context.line_number == 100
        assert error1.context.source_line == "MAIN LINE"
        assert error2.context.source_line == "MAIN LINE"

    def test_error_suggestions_quality(self, basic, helpers):
        """Test that error suggestions are helpful and relevant"""
        # Test undefined variable suggestions
        error = self.error_manager.reference_error("MYVAR", "UNDEFINED VARIABLE")
        suggestions = error.suggestions
        assert any("LET MYVAR" in suggestion for suggestion in suggestions)
        assert any("typo" in suggestion.lower() for suggestion in suggestions)
        
        # Test division by zero suggestions  
        error = self.error_manager.arithmetic_error("Division by zero", "A / 0")
        suggestions = error.suggestions
        assert any("divisor" in suggestion.lower() for suggestion in suggestions)
        assert any("conditional" in suggestion.lower() for suggestion in suggestions)
