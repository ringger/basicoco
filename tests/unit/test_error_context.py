#!/usr/bin/env python3

"""
Comprehensive tests for Error Context System

Tests the structured error reporting system that provides enhanced error messages
with line numbers, context information, and helpful suggestions.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from test_base import BaseTestCase
from emulator.error_context import (
    ErrorContextManager, BasicError, SourceContext, 
    ErrorSeverity, ErrorCategory,
    create_legacy_error, convert_error_to_legacy,
    syntax_error, runtime_error, file_error
)
from emulator.core import CoCoBasic


class ErrorContextTest(BaseTestCase):
    """Test cases for Error Context System functionality"""

    def setUp(self):
        """Set up test environment"""
        super().setUp()
        self.error_manager = ErrorContextManager()

    def test_basic_functionality(self):
        """Test basic error context functionality"""
        # Test creating a simple syntax error
        error = self.error_manager.syntax_error("Missing semicolon", line=10)
        self.assertEqual(error.message, "Missing semicolon")
        self.assertEqual(error.category, ErrorCategory.SYNTAX)
        self.assertEqual(error.context.line_number, 10)

    def test_source_context_creation(self):
        """Test SourceContext creation and formatting"""
        context = SourceContext(
            line_number=25,
            column=15,
            length=5,
            source_line="PRINT A + B",
            filename="test.bas",
            function_name="main"
        )
        
        self.assertEqual(context.line_number, 25)
        self.assertEqual(context.column, 15)
        self.assertEqual(context.length, 5)
        self.assertEqual(context.source_line, "PRINT A + B")
        self.assertEqual(context.filename, "test.bas")
        self.assertEqual(context.function_name, "main")
        
        # Test string representation
        context_str = str(context)
        self.assertIn("line 25", context_str)
        self.assertIn("column 15", context_str)
        self.assertIn("test.bas", context_str)

    def test_basic_error_creation(self):
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
        
        self.assertEqual(error.message, "Undefined variable")
        self.assertEqual(error.category, ErrorCategory.REFERENCE)
        self.assertEqual(error.severity, ErrorSeverity.ERROR)
        self.assertEqual(error.context.line_number, 10)
        self.assertEqual(len(error.suggestions), 2)
        self.assertEqual(error.error_code, "UNDEFINED_VAR")

    def test_error_to_dict_conversion(self):
        """Test converting errors to dictionary format"""
        context = SourceContext(line_number=5, column=10, source_line="GOTO 100")
        error = BasicError(
            message="Undefined line",
            category=ErrorCategory.REFERENCE,
            context=context,
            suggestions=["Add line 100 to your program"]
        )
        
        error_dict = error.to_dict()
        self.assertEqual(error_dict['type'], 'error')
        self.assertEqual(error_dict['message'], 'Undefined line')
        self.assertEqual(error_dict['category'], 'reference')
        self.assertEqual(error_dict['line'], 5)
        self.assertEqual(error_dict['column'], 10)
        self.assertEqual(error_dict['source'], 'GOTO 100')
        self.assertEqual(len(error_dict['suggestions']), 1)

    def test_error_formatting(self):
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
        self.assertIn("Syntax error", formatted)
        self.assertIn("line 15", formatted)
        
        # Test detailed formatting
        detailed = error.format_detailed()
        self.assertIn("Syntax error", detailed)
        self.assertIn("PRINT A B", detailed)
        self.assertIn("Missing comma", detailed)

    def test_context_manager_functionality(self):
        """Test ErrorContextManager state management"""
        # Test setting context
        self.error_manager.set_context(42, "TEST LINE", "test.bas", "test_function")
        self.assertEqual(self.error_manager.current_line, 42)
        self.assertEqual(self.error_manager.current_source, "TEST LINE")
        self.assertEqual(self.error_manager.current_filename, "test.bas")
        self.assertEqual(self.error_manager.current_function, "test_function")
        
        # Test context stack - push_context creates a new context
        self.error_manager.push_context(50, "NESTED LINE", "nested.bas")
        self.assertEqual(self.error_manager.current_line, 50)
        self.assertEqual(len(self.error_manager.execution_stack), 1)
        
        # After popping, there's no previous context to restore to
        # so current values become None
        self.error_manager.pop_context()
        self.assertEqual(self.error_manager.current_line, None)
        self.assertEqual(len(self.error_manager.execution_stack), 0)

    def test_syntax_error_creation(self):
        """Test syntax error creation with context"""
        self.error_manager.set_context(25, "PRINT A + +", "program.bas")
        
        error = self.error_manager.syntax_error(
            "Invalid operator sequence",
            column=10,
            length=3,
            suggestions=["Remove extra operator", "Check expression syntax"]
        )
        
        self.assertEqual(error.category, ErrorCategory.SYNTAX)
        self.assertEqual(error.context.line_number, 25)
        self.assertEqual(error.context.column, 10)
        self.assertEqual(error.context.length, 3)
        self.assertEqual(len(error.suggestions), 2)
        self.assertEqual(error.error_code, "SYNTAX")

    def test_runtime_error_creation(self):
        """Test runtime error creation"""
        error = self.error_manager.runtime_error(
            "Division by zero",
            line=100,
            details="Attempted to divide by zero in expression",
            suggestions=["Check that divisor is not zero", "Use conditional logic"]
        )
        
        self.assertEqual(error.category, ErrorCategory.RUNTIME)
        self.assertEqual(error.context.line_number, 100)
        self.assertEqual(error.details, "Attempted to divide by zero in expression")

    def test_type_error_creation(self):
        """Test type mismatch error creation"""
        error = self.error_manager.type_error(
            "Type mismatch in assignment",
            "string",
            "number",
            line=75
        )
        
        self.assertEqual(error.category, ErrorCategory.TYPE)
        self.assertEqual(error.context.line_number, 75)
        self.assertIn("Expected string, got number", error.details)
        self.assertEqual(error.error_code, "TYPE_MISMATCH")

    def test_reference_error_creation(self):
        """Test reference error creation"""
        error = self.error_manager.reference_error(
            "UNDEFINED_VAR",
            "UNDEFINED VARIABLE",
            line=30
        )
        
        self.assertEqual(error.category, ErrorCategory.REFERENCE)
        self.assertEqual(error.message, "UNDEFINED VARIABLE: UNDEFINED_VAR")
        self.assertEqual(error.context.line_number, 30)
        self.assertTrue(len(error.suggestions) > 0)

    def test_arithmetic_error_creation(self):
        """Test arithmetic error creation"""
        error = self.error_manager.arithmetic_error(
            "Division by zero",
            "10 / 0",
            line=60
        )
        
        self.assertEqual(error.category, ErrorCategory.ARITHMETIC)
        self.assertIn("10 / 0", error.details)
        self.assertTrue(any("divisor" in suggestion for suggestion in error.suggestions))

    def test_file_error_creation(self):
        """Test file operation error creation"""
        error = self.error_manager.file_error(
            "File not found",
            "missing.bas",
            "load",
            line=5
        )
        
        self.assertEqual(error.category, ErrorCategory.FILE)
        self.assertIn("missing.bas", error.details)
        self.assertIn("load", error.details)
        self.assertTrue(any("exists" in suggestion for suggestion in error.suggestions))

    def test_warning_creation(self):
        """Test warning message creation"""
        warning = self.error_manager.warning(
            "Variable not used",
            line=20,
            suggestions=["Remove unused variable", "Use variable in calculation"]
        )
        
        self.assertEqual(warning.severity, ErrorSeverity.WARNING)
        self.assertEqual(warning.category, ErrorCategory.SYNTAX)
        self.assertEqual(warning.error_code, "WARNING")

    def test_stack_trace_generation(self):
        """Test execution stack trace generation"""
        # Build a call stack
        self.error_manager.push_context(10, "GOSUB 100", "main.bas", "main")
        self.error_manager.push_context(100, "GOSUB 200", "main.bas", "subroutine1") 
        self.error_manager.push_context(200, "LET A = B + C", "main.bas", "subroutine2")
        
        stack_trace = self.error_manager.get_stack_trace()
        self.assertEqual(len(stack_trace), 3)
        
        # Check that most recent call is first
        self.assertIn("line 200", stack_trace[0])
        self.assertIn("line 100", stack_trace[1])
        self.assertIn("line 10", stack_trace[2])

    def test_legacy_compatibility_functions(self):
        """Test legacy compatibility functions"""
        # Test create_legacy_error
        legacy = create_legacy_error("Test error message")
        self.assertEqual(legacy['type'], 'error')
        self.assertEqual(legacy['message'], 'Test error message')
        
        # Test convert_error_to_legacy
        error = BasicError("Structured error", ErrorCategory.SYNTAX)
        legacy = convert_error_to_legacy(error)
        self.assertEqual(legacy['type'], 'error')
        self.assertEqual(legacy['message'], 'Structured error')
        
        # Test standalone error functions
        syntax_err = syntax_error("Bad syntax", 10)
        self.assertEqual(syntax_err['type'], 'error')
        self.assertIn("SYNTAX ERROR", syntax_err['message'])
        self.assertIn("line 10", syntax_err['message'])
        
        runtime_err = runtime_error("Runtime problem", 25)
        self.assertIn("line 25", runtime_err['message'])
        
        file_err = file_error("File issue", "test.bas", 15)
        self.assertIn("test.bas", file_err['message'])

    def test_integration_with_expression_evaluator(self):
        """Test integration with expression evaluator error reporting"""
        # This tests that the enhanced error system works with the expression evaluator
        try:
            # This should trigger enhanced error reporting
            result = self.basic.expression_evaluator.evaluate("", line=42)
        except ValueError as e:
            error_msg = str(e)
            self.assertIn("line 42", error_msg)  # Should include line number
            self.assertIn("Empty expression", error_msg)

    def test_multiple_error_contexts(self):
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
        self.assertEqual(errors[0].context.line_number, 10)
        self.assertEqual(errors[1].context.line_number, 20)
        self.assertEqual(errors[2].context.line_number, 30)
        
        # Verify different error types
        self.assertEqual(errors[0].category, ErrorCategory.SYNTAX)
        self.assertEqual(errors[1].category, ErrorCategory.RUNTIME)
        self.assertEqual(errors[2].category, ErrorCategory.TYPE)

    def test_error_message_enhancement(self):
        """Test error message enhancement functions"""
        from emulator.error_context import enhance_error_message
        
        # Test basic enhancement
        enhanced = enhance_error_message("Basic error")
        self.assertEqual(enhanced, "Basic error")
        
        # Test with line number
        enhanced = enhance_error_message("Basic error", 42)
        self.assertEqual(enhanced, "Basic error at line 42")

    def test_context_preservation_across_calls(self):
        """Test that context is preserved across multiple operations"""
        # Set initial context
        self.error_manager.set_context(100, "MAIN LINE", "program.bas", "main")
        
        # Create multiple errors - they should all inherit the context
        error1 = self.error_manager.syntax_error("First error")
        error2 = self.error_manager.runtime_error("Second error")
        
        self.assertEqual(error1.context.line_number, 100)
        self.assertEqual(error2.context.line_number, 100)
        self.assertEqual(error1.context.source_line, "MAIN LINE")
        self.assertEqual(error2.context.source_line, "MAIN LINE")

    def test_error_suggestions_quality(self):
        """Test that error suggestions are helpful and relevant"""
        # Test undefined variable suggestions
        error = self.error_manager.reference_error("MYVAR", "UNDEFINED VARIABLE")
        suggestions = error.suggestions
        self.assertTrue(any("LET MYVAR" in suggestion for suggestion in suggestions))
        self.assertTrue(any("typo" in suggestion.lower() for suggestion in suggestions))
        
        # Test division by zero suggestions  
        error = self.error_manager.arithmetic_error("Division by zero", "A / 0")
        suggestions = error.suggestions
        self.assertTrue(any("divisor" in suggestion.lower() for suggestion in suggestions))
        self.assertTrue(any("conditional" in suggestion.lower() for suggestion in suggestions))


if __name__ == '__main__':
    test = ErrorContextTest("Error Context Tests")
    results = test.run_all_tests()
    from test_base import print_test_results
    print_test_results(results, verbose=True)