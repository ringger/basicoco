"""
Expression Evaluation module for TRS-80 Color Computer BASIC Emulator

This module provides AST-based expression evaluation that handles:
- Mathematical expressions with proper operator precedence
- String expressions and concatenation  
- Function calls (both nested and simple)
- Variable and array reference resolution
- Type conversions and coercion
- Enhanced error reporting with line/column information

Uses Abstract Syntax Tree parsing for robust expression handling.
"""

from typing import Any, Dict, List, Optional
from .functions import register_all_functions
from .ast_parser import ASTParser, ASTEvaluator
from .error_context import ErrorContextManager


class ExpressionEvaluator:
    """
    AST-based expression evaluator for BASIC expressions.
    
    Uses Abstract Syntax Tree parsing to handle all expression evaluation including:
    - Nested functions with proper precedence
    - Complex mathematical operations with operator precedence
    - String operations and concatenation
    - Variable and array reference resolution
    - Enhanced error reporting with source location context
    """
    
    def __init__(self, emulator):
        """Initialize evaluator with reference to main emulator for variable access"""
        self.emulator = emulator
        self.function_registry = FunctionRegistry()
        register_all_functions(self.function_registry)
        
        # Initialize AST parser for expression evaluation
        self.ast_parser = ASTParser()
        self.ast_evaluator = ASTEvaluator(emulator)
        
        # Initialize error context manager
        self.error_context = ErrorContextManager()
    
    def evaluate(self, expr: str, line: int = 1) -> Any:
        """
        Main entry point for expression evaluation.
        
        Args:
            expr: The expression string to evaluate
            line: Source line number for error reporting (optional)
            
        Returns:
            The evaluated result (number, string, or boolean)
            
        Raises:
            ValueError: If the expression is invalid
        """
        expr = expr.strip()
        if not expr:
            error = self.error_context.syntax_error("Empty expression", line)
            raise ValueError(error.format_message())
        
        # Set error context for this evaluation
        self.error_context.set_context(line, expr)
        
        try:
            # Use AST parser for all expression evaluation
            ast_node = self.ast_parser.parse_expression(expr, line)
            return self.ast_evaluator.visit(ast_node)
            
        except ValueError as e:
            # Re-raise with enhanced context if not already enhanced
            if "at line" not in str(e):
                error = self.error_context.runtime_error(str(e), line)
                raise ValueError(error.format_message()) from e
            raise
    
    
    def parse_statement(self, stmt: str, line: int = 1) -> Any:
        """
        Parse a BASIC statement into an AST (for future use).
        
        This method prepares the foundation for advanced language features
        like multi-line IF/THEN/ELSE structures.
        """
        return self.ast_parser.parse_statement(stmt, line)
    
    
    def _evaluate_array_access(self, array_name: str, indices_str: str) -> Any:
        """Evaluate array element access"""
        if array_name not in self.emulator.arrays:
            error = self.error_context.reference_error(
                array_name, 
                "UNDIM'D ARRAY",
                suggestions=[
                    f"Declare the array first: DIM {array_name}(size)",
                    "Check the array name spelling"
                ]
            )
            raise ValueError(error.format_message())
        
        # Parse and evaluate indices
        indices = []
        try:
            for idx in indices_str.split(','):
                indices.append(int(self.evaluate(idx.strip())))
        except ValueError as e:
            error = self.error_context.type_error(
                "Invalid array index",
                "integer",
                "non-numeric expression"
            )
            raise ValueError(error.format_message()) from e
        
        # Get array element using VariableManager
        value, error_msg = self.emulator.variable_manager.get_array_element(array_name, indices)
        if error_msg:
            error = self.error_context.runtime_error(
                error_msg,
                suggestions=["Check that array indices are within bounds"]
            )
            raise ValueError(error.format_message())
        
        return value
    
    
    


class FunctionRegistry:
    """Registry for BASIC functions with extensible registration system"""
    
    def __init__(self):
        self.functions: Dict[str, callable] = {}
    
    def register(self, name: str, handler: callable):
        """Register a function handler"""
        self.functions[name.upper()] = handler
    
    def get_handler(self, name: str) -> Optional[callable]:
        """Get handler for a function"""
        return self.functions.get(name.upper())
    
    def list_functions(self) -> List[str]:
        """List all registered function names"""
        return sorted(self.functions.keys())
    
    def is_function(self, name: str) -> bool:
        """Check if a name is a registered function"""
        return name.upper() in self.functions