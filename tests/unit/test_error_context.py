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
        assert error.message == "SYNTAX ERROR: Missing semicolon"
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

    def test_file_error_always_has_suggestions(self, basic, helpers):
        """#13: every file error carries at least two suggestions."""
        error = self.error_manager.file_error("DISK FULL", "x.bas", "save", line=5)
        assert len(error.suggestions) >= 2

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


def _first_error(helpers, result):
    errors = helpers.get_error_messages(result)
    assert errors, result
    return errors[0]


class TestErrorLineAttribution:
    """#13: errors name the program line they happened on exactly once;
    immediate-mode errors name no line; wrapped errors keep one suggestion
    block and their real category."""

    @pytest.mark.parametrize('code,phrase', [
        ('X = 1 +', 'SYNTAX ERROR'), ('X=Q(20)', 'BAD SUBSCRIPT'),
        ('PRINT 1/0', 'Division by zero'), ('PRINT LEN(5)', 'TYPE MISMATCH'),
    ])
    def test_program_error_names_its_line_once(self, basic, helpers, code, phrase):
        helpers.load_program(basic, ['10 PRINT 1', f'40 {code}'])
        message = _first_error(helpers, helpers.run_to_completion(basic))
        first = message.splitlines()[0]
        assert phrase in first
        assert first.endswith('at line 40'), first
        assert first.count(' at line ') == 1
        assert message.count('Suggestions:') == 1

    @pytest.mark.parametrize('code', ['X = 1 +', 'X=Q(20)', 'PRINT 1/0', 'PMODE 9', 'GOTO 999'])
    def test_immediate_error_names_no_line(self, basic, helpers, code):
        first = _first_error(helpers, basic.process_command(code)).splitlines()[0]
        assert ' at line ' not in first, first

    def test_runtime_error_is_not_labelled_syntax_error(self, basic, helpers):
        first = _first_error(helpers, basic.process_command('X=Q(20)')).splitlines()[0]
        assert first == 'BAD SUBSCRIPT'

    def test_wrapped_error_keeps_inner_suggestions(self, basic, helpers):
        message = _first_error(helpers, basic.process_command('PRINT LEN(5)'))
        assert 'LEN(STR$(N))' in message

    def test_every_error_has_two_suggestions(self, basic, helpers):
        for code in ['PRINT EOF(3)', 'PRINT MID$("A")', 'PRINT INSTR(1)', 'X=Q(20)',
                     'PMODE 9', 'PRINT LEN(5)', 'OPEN "Q", #1, "X"']:
            message = _first_error(helpers, basic.process_command(code))
            count = sum(1 for l in message.splitlines() if l.startswith('  - '))
            assert count >= 2, (code, message)
