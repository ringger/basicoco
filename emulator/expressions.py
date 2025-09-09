"""
Expression Evaluation module for TRS-80 Color Computer BASIC Emulator

This module provides a dedicated expression evaluator that handles:
- Mathematical expressions with proper operator precedence
- String expressions and concatenation
- Function calls (both nested and simple)
- Variable and array reference resolution
- Type conversions and coercion

This replaces the monolithic expression evaluation previously embedded in core.py
"""

import re
from typing import Any, Dict, List, Optional, Tuple, Union
from .functions import register_all_functions
from .ast_parser import ASTParser, ASTEvaluator, SourceLocation
from .error_context import ErrorContextManager, ErrorCategory


class ExpressionEvaluator:
    """
    Dedicated expression evaluator for BASIC expressions.
    
    Handles all expression evaluation including nested functions,
    complex mathematical operations, string operations, and variable resolution.
    """
    
    def __init__(self, emulator):
        """Initialize evaluator with reference to main emulator for variable access"""
        self.emulator = emulator
        self.function_registry = FunctionRegistry()
        register_all_functions(self.function_registry)
        
        # Initialize AST parser for advanced expression parsing
        self.ast_parser = ASTParser()
        self.ast_evaluator = ASTEvaluator(emulator)
        self.use_ast_parser = False  # Feature flag - can be enabled later
        
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
            # Use AST parser if enabled (for advanced features)
            if self.use_ast_parser:
                try:
                    ast_node = self.ast_parser.parse_expression(expr, line)
                    return self.ast_evaluator.visit(ast_node)
                except Exception as e:
                    # Fall back to legacy parser if AST parsing fails
                    pass
            
            # First check if it's a simple literal or variable
            result = self._try_simple_evaluation(expr)
            if result is not None:
                return result
            
            # Check if entire expression is a single function call
            result = self._try_function_call(expr)
            if result is not None:
                return result
            
            # Complex expression - parse and evaluate
            return self._evaluate_complex_expression(expr)
            
        except ValueError as e:
            # Re-raise with enhanced context if not already enhanced
            if "at line" not in str(e):
                error = self.error_context.runtime_error(str(e), line)
                raise ValueError(error.format_message()) from e
            raise
    
    def enable_ast_parsing(self, enabled: bool = True):
        """
        Enable or disable AST-based parsing for advanced features.
        
        AST parsing provides:
        - Better error messages with line/column information
        - Support for complex nested expressions
        - Foundation for advanced language features
        """
        self.use_ast_parser = enabled
    
    def parse_statement(self, stmt: str, line: int = 1) -> Any:
        """
        Parse a BASIC statement into an AST (for future use).
        
        This method prepares the foundation for advanced language features
        like multi-line IF/THEN/ELSE structures.
        """
        if not self.use_ast_parser:
            raise ValueError("AST parsing not enabled")
        
        return self.ast_parser.parse_statement(stmt, line)
    
    def _try_simple_evaluation(self, expr: str) -> Optional[Any]:
        """Try to evaluate as a simple literal or variable"""
        # String literal
        if expr.startswith('"') and expr.endswith('"') and expr.count('"') == 2:
            return expr[1:-1]
        
        # Numeric literal
        try:
            if '.' in expr or 'E' in expr.upper():
                return float(expr)
            else:
                return int(expr)
        except ValueError:
            pass
        
        # Simple variable reference (case insensitive)
        if re.match(r'^[A-Za-z]\w*\$?$', expr):
            var_name = expr.upper()
            if var_name in self.emulator.variables:
                return self.emulator.variables[var_name]
        
        # Simple array reference (but not a function call)
        array_match = re.match(r'^([A-Za-z]\w*\$?)\(([^)]+)\)$', expr)
        if array_match:
            array_name = array_match.group(1).upper()
            # Check if it's a function name, not an array
            if not self.function_registry.is_function(array_name):
                return self._evaluate_array_access(array_name, array_match.group(2))
        
        return None
    
    def _try_function_call(self, expr: str) -> Optional[Any]:
        """Try to evaluate as a function call"""
        # Check each registered function
        for func_name in self.function_registry.list_functions():
            if expr.upper().startswith(func_name + '('):
                # Check if the entire expression is consumed by this function call
                args_str = self._extract_function_args(expr, func_name)
                if args_str is not None:
                    # Verify that the function call consumes the entire expression
                    expected_end = len(func_name) + 1 + len(args_str) + 1  # func_name + ( + args + )
                    if expected_end == len(expr):
                        return self._evaluate_function(func_name, expr)
        
        # Special case for INKEY$ (with or without parentheses)
        if expr.upper() == 'INKEY$' or re.match(r'INKEY\$\(\s*\)$', expr, re.IGNORECASE):
            return self._evaluate_inkey()
        
        return None
    
    def _evaluate_complex_expression(self, expr: str) -> Any:
        """Evaluate a complex expression with operators and function calls"""
        # First, substitute all function calls with their results
        expr = self._substitute_functions(expr)
        
        # Then substitute array accesses
        expr = self._substitute_arrays(expr)
        
        # Substitute variables
        expr = self._substitute_variables(expr)
        
        # Replace BASIC operators with Python equivalents
        expr = expr.replace('<>', '!=')
        
        # Evaluate the final expression
        try:
            return eval(expr)
        except ZeroDivisionError:
            # BASIC behavior for division by zero - return infinity but warn
            return float('inf')
        except Exception as e:
            error = self.error_context.runtime_error(
                "Invalid expression",
                details=str(e),
                suggestions=[
                    "Check for syntax errors in the expression",
                    "Verify all variables are defined",
                    "Ensure proper use of operators and parentheses"
                ]
            )
            raise ValueError(error.format_message()) from e
    
    def _substitute_functions(self, expr: str) -> str:
        """Replace all function calls in expression with their evaluated results"""
        changed = True
        while changed:
            changed = False
            
            for func_name in self.function_registry.list_functions():
                # Search case-insensitively
                pattern = func_name + '('
                pos = 0
                
                while True:
                    # Case-insensitive search
                    upper_expr = expr.upper()
                    pos = upper_expr.find(pattern.upper(), pos)
                    if pos == -1:
                        break
                    
                    # Find matching closing parenthesis
                    paren_count = 0
                    start_pos = pos + len(pattern) - 1  # Position of opening parenthesis
                    end_pos = -1
                    
                    for i in range(start_pos, len(expr)):
                        if expr[i] == '(':
                            paren_count += 1
                        elif expr[i] == ')':
                            paren_count -= 1
                            if paren_count == 0:
                                end_pos = i
                                break
                    
                    if end_pos != -1:
                        func_call = expr[pos:end_pos + 1]
                        try:
                            result = self._evaluate_function(func_name, func_call)
                            
                            # Format result for substitution
                            if isinstance(result, str):
                                replacement = '"' + result.replace('"', '\\"') + '"'
                            else:
                                replacement = str(result)
                            
                            expr = expr[:pos] + replacement + expr[end_pos + 1:]
                            changed = True
                            break  # Exit inner loop and restart from beginning with modified expression
                        except:
                            pos += len(pattern)
                    else:
                        break
        
        return expr
    
    def _substitute_arrays(self, expr: str) -> str:
        """Replace array accesses with their values"""
        def replace_array(match):
            array_name = match.group(1).upper()
            indices_str = match.group(2)
            
            try:
                value = self._evaluate_array_access(array_name, indices_str)
                if isinstance(value, str):
                    return '"' + value.replace('"', '\\"') + '"'
                else:
                    return str(value)
            except Exception as e:
                raise ValueError(str(e))
        
        return re.sub(r'([A-Za-z]\w*\$?)\(([^)]+)\)', replace_array, expr)
    
    def _substitute_variables(self, expr: str) -> str:
        """Replace variable references with their values"""
        for var_name, value in self.emulator.variables.items():
            # Create appropriate regex pattern for the variable
            if var_name.endswith('$'):
                pattern = r'\b' + re.escape(var_name) + r'(?![A-Za-z0-9_$])'
            else:
                pattern = r'\b' + re.escape(var_name) + r'\b'
            
            if re.search(pattern, expr, re.IGNORECASE):
                if isinstance(value, str):
                    replacement = '"' + value.replace('"', '\\"') + '"'
                else:
                    replacement = str(value)
                expr = re.sub(pattern, replacement, expr, flags=re.IGNORECASE)
        
        return expr
    
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
    
    def _evaluate_function(self, func_name: str, expr: str) -> Any:
        """Evaluate a function call"""
        handler = self.function_registry.get_handler(func_name)
        if not handler:
            error = self.error_context.reference_error(
                func_name,
                "UNDEFINED FUNCTION",
                suggestions=[
                    "Check the function name spelling",
                    "Ensure the function is supported in this BASIC dialect",
                    f"Available functions: {', '.join(self.function_registry.list_functions()[:10])}"
                ]
            )
            raise ValueError(error.format_message())
        
        # Extract arguments
        args_str = self._extract_function_args(expr, func_name)
        if args_str is None:
            error = self.error_context.syntax_error(
                f"Invalid {func_name} function call",
                suggestions=[
                    f"Correct syntax: {func_name}(arguments)",
                    "Check for missing or mismatched parentheses"
                ]
            )
            raise ValueError(error.format_message())
        
        # Parse arguments
        try:
            args = self._parse_function_args(args_str)
            
            # Call handler with evaluated arguments
            return handler(self, args)
        except Exception as e:
            error = self.error_context.runtime_error(
                f"Error in {func_name} function",
                details=str(e),
                suggestions=[
                    "Check function arguments are of correct type",
                    "Verify argument count matches function requirements"
                ]
            )
            raise ValueError(error.format_message()) from e
    
    def _extract_function_args(self, expr: str, func_name: str) -> Optional[str]:
        """Extract the arguments string from a function call"""
        prefix = f"{func_name}("
        if not expr.upper().startswith(prefix.upper()):
            return None
        
        # Find matching closing parenthesis
        paren_count = 0
        start_pos = len(prefix) - 1
        
        for i in range(start_pos, len(expr)):
            if expr[i] == '(':
                paren_count += 1
            elif expr[i] == ')':
                paren_count -= 1
                if paren_count == 0:
                    return expr[len(prefix):i].strip()
        
        return None
    
    def _parse_function_args(self, args_str: str) -> List[str]:
        """Parse comma-separated function arguments respecting parentheses"""
        if not args_str.strip():
            return []
        
        args = []
        current_arg = ""
        paren_count = 0
        in_quotes = False
        
        for char in args_str:
            if char == '"' and not in_quotes:
                in_quotes = True
                current_arg += char
            elif char == '"' and in_quotes:
                in_quotes = False
                current_arg += char
            elif char == ',' and paren_count == 0 and not in_quotes:
                args.append(current_arg.strip())
                current_arg = ""
            else:
                if char == '(' and not in_quotes:
                    paren_count += 1
                elif char == ')' and not in_quotes:
                    paren_count -= 1
                current_arg += char
        
        if current_arg.strip():
            args.append(current_arg.strip())
        
        return args
    
    def _evaluate_inkey(self) -> str:
        """Evaluate INKEY$ function"""
        if self.emulator.keyboard_buffer:
            return self.emulator.keyboard_buffer.pop(0)
        return ""
    


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