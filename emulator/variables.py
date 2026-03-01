"""
Variables and Arrays module for TRS-80 Color Computer BASIC Emulator

This module contains all variable and array management functionality including
DIM command, array bounds checking, variable type handling, and storage.
Extracted from the main CoCoBasic class for better organization.
"""

import re


class VariableManager:
    """Handler for BASIC variable and array operations"""
    
    def __init__(self, emulator):
        """Initialize variable manager with reference to main emulator"""
        self.emulator = emulator
    
    def register_commands(self, registry):
        """Register variable and array commands with the command registry"""
        registry.register('DIM', self.execute_dim)
        registry.register('LET', self.execute_let)
    
    def execute_dim(self, args):
        """Execute DIM command to dimension arrays"""
        try:
            # DIM A(10), B$(5,10), C(20) - Parse comma-separated array declarations, respecting parentheses
            if not args:
                error = self.emulator.error_context.syntax_error(
                    "DIM command requires array declarations",
                    self.emulator.current_line,
                    suggestions=[
                        'Correct syntax: DIM array_name(size)',
                        'Example: DIM A(10), B$(5,10)',
                        'Specify at least one array to dimension'
                    ]
                )
                return [{'type': 'error', 'message': error.format_detailed()}]
            
            # Parse comma-separated array declarations, but be careful with parentheses
            array_defs = []
            current_def = ""
            paren_count = 0
            
            for char in args:
                current_def += char
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                elif char == ',' and paren_count == 0:
                    array_defs.append(current_def[:-1].strip())  # Exclude the comma
                    current_def = ""
            
            if current_def.strip():
                array_defs.append(current_def.strip())
            
            for array_def in array_defs:
                array_def = array_def.strip()
                
                # Parse array_name(dimensions)
                match = re.match(r'(\w+\$?)\(([^)]+)\)', array_def)
                if not match:
                    error = self.emulator.error_context.syntax_error(
                        f"Invalid array declaration syntax: {array_def}",
                        self.emulator.current_line,
                        suggestions=[
                            'Correct syntax: array_name(dimensions)',
                            'Example: DIM A(10), B$(5,10)',
                            'Array name must be followed by parentheses with dimensions'
                        ]
                    )
                    return [{'type': 'error', 'message': error.format_detailed()}]
                
                array_name = match.group(1).upper()
                dimensions_str = match.group(2)
                
                # Check if array name conflicts with reserved function names
                if array_name in self.emulator.get_reserved_function_names():
                    error = self.emulator.error_context.syntax_error(
                        f"Cannot use reserved function name as array: {array_name}",
                        self.emulator.current_line,
                        suggestions=[
                            'Choose a different array name',
                            'Reserved names include built-in functions like SIN, COS, etc.',
                            'Example: Use DATA instead of SIN'
                        ]
                    )
                    return [{'type': 'error', 'message': error.format_detailed()}]
                
                # Parse dimensions (comma-separated numbers)
                try:
                    dimensions = []
                    for dim_str in dimensions_str.split(','):
                        dim_value = int(self.emulator.evaluate_expression(dim_str.strip()))
                        if dim_value <= 0:
                            error = self.emulator.error_context.syntax_error(
                                f"Array dimension must be positive: {dim_value}",
                                self.emulator.current_line,
                                suggestions=[
                                    'Array dimensions must be greater than 0',
                                    'Example: DIM A(10) not DIM A(0)',
                                    'Use positive integers for array sizes'
                                ]
                            )
                            return [{'type': 'error', 'message': error.format_detailed()}]
                        dimensions.append(dim_value)
                    
                    # Check if array is already dimensioned (after syntax validation)
                    if array_name in self.emulator.arrays:
                        error = self.emulator.error_context.runtime_error(
                            f"Array {array_name} is already dimensioned",
                            suggestions=[
                                'Arrays can only be dimensioned once',
                                'Use NEW to clear existing arrays',
                                'Choose a different array name'
                            ]
                        )
                        return [{'type': 'error', 'message': error.format_detailed()}]
                    
                    # Create multi-dimensional array initialized to 0 or ""
                    # Note: Color Computer BASIC arrays - DIM A(10) creates indices 0-10 (11 elements)
                    # Each dimension N creates N+1 elements with indices 0 to N
                    if array_name.endswith('$'):
                        # String array
                        self.emulator.arrays[array_name] = self._create_multidim_array(dimensions, "")
                    else:
                        # Numeric array
                        self.emulator.arrays[array_name] = self._create_multidim_array(dimensions, 0)
                        
                except ValueError as e:
                    error = self.emulator.error_context.syntax_error(
                        f"Invalid array dimension expression: {str(e)}",
                        self.emulator.current_line,
                        suggestions=[
                            'Array dimensions must evaluate to positive integers',
                            'Example: DIM A(N), B(X*2)',
                            'Check that all variables in dimensions are defined'
                        ]
                    )
                    return [{'type': 'error', 'message': error.format_detailed()}]
            
            return []  # DIM doesn't produce output
        except Exception as e:
            error = self.emulator.error_context.runtime_error(
                f"Unexpected error in DIM command: {str(e)}",
                suggestions=[
                    'Check DIM syntax and array declarations',
                    'Example: DIM A(10), B$(5,10)',
                    'Ensure all expressions are valid'
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
    
    def execute_let(self, args):
        try:
            # Handle both "LET X = 5" and "X = 5"
            if '=' not in args:
                error = self.emulator.error_context.syntax_error(
                    "Missing assignment operator in LET statement",
                    self.emulator.current_line,
                    suggestions=[
                        'Correct syntax: LET variable = expression',
                        'Example: LET X = 5 or X = 10',
                        'Assignment requires = operator'
                    ]
                )
                return [{'type': 'error', 'message': error.format_detailed()}]

            var_name, expression = args.split('=', 1)
            var_name = var_name.strip().upper()
            expression = expression.strip()
            
            # Validate variable name is not empty
            if not var_name:
                error = self.emulator.error_context.syntax_error(
                    "Empty variable name in assignment",
                    self.emulator.current_line,
                    suggestions=[
                        'Variable name cannot be empty',
                        'Example: X = 5 not = 5',
                        'Specify a valid variable name before ='
                    ]
                )
                return [{'type': 'error', 'message': error.format_detailed()}]
            
            # Check if this is an array assignment
            if '(' in var_name and var_name.endswith(')'):
                # Array assignment - A(5) = 42
                array_part = var_name[:var_name.find('(')]
                indices_str = var_name[var_name.find('(')+1:-1]
                
                # Check if array name conflicts with reserved function names
                if array_part in self.emulator.get_reserved_function_names():
                    error = self.emulator.error_context.syntax_error(
                        f"Cannot assign to reserved function name: {array_part}",
                        self.emulator.current_line,
                        suggestions=[
                            'Choose a different variable name',
                            'Reserved names include built-in functions',
                            'Example: Use DATA instead of SIN'
                        ]
                    )
                    return [{'type': 'error', 'message': error.format_detailed()}]
                
                # Parse indices
                indices = [int(self.emulator.evaluate_expression(idx.strip())) for idx in indices_str.split(',')]
                
                # Evaluate the expression value
                if expression.startswith('"') and expression.endswith('"'):
                    value = expression[1:-1]  # String value
                else:
                    value = self.emulator.evaluate_expression(expression)
                
                # Set array element
                error = self.set_array_element(array_part, indices, value)
                if error:
                    return [{'type': 'error', 'message': error}]
                
                return [{'type': 'text', 'text': 'OK'}]
            else:
                # Regular variable assignment
                # Check if variable name conflicts with reserved function names
                if var_name in self.emulator.get_reserved_function_names():
                    error = self.emulator.error_context.syntax_error(
                        f"Cannot assign to reserved function name: {var_name}",
                        self.emulator.current_line,
                        suggestions=[
                            'Choose a different variable name',
                            'Reserved names include built-in functions',
                            'Example: Use DATA instead of SIN'
                        ]
                    )
                    return [{'type': 'error', 'message': error.format_detailed()}]
                
                # Evaluate the expression
                if expression.startswith('"') and expression.endswith('"'):
                    value = expression[1:-1]  # String literal
                else:
                    value = self.emulator.evaluate_expression(expression)
                
                # Store the variable
                self.emulator.variables[var_name] = value
                
                return [{'type': 'text', 'text': 'OK'}]
                
        except Exception as e:
            error = self.emulator.error_context.runtime_error(
                f"Unexpected error in assignment: {str(e)}",
                suggestions=[
                    'Check assignment syntax and expression',
                    'Example: X = 5 or A$(1) = "hello"',
                    'Ensure all variables and expressions are valid'
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
    
    def get_array_element(self, array_name, indices):
        """Get value from array element using nested array structure"""
        try:
            if array_name not in self.emulator.arrays:
                return None, "UNDIM'D ARRAY"
            
            # Get the nested array structure
            array_data = self.emulator.arrays[array_name]
            
            # Navigate through the nested structure
            current = array_data
            for index in indices:
                # Check bounds - arrays are 0-indexed but DIM A(n) creates indices 0-n
                if index < 0 or index >= len(current):
                    return None, "BAD SUBSCRIPT"
                current = current[index]
            
            return current, None
                
        except Exception as e:
            return None, f"Error accessing array: {str(e)}"
    
    def set_array_element(self, array_name, indices, value):
        """Set value in array element using nested array structure"""
        try:
            if array_name not in self.emulator.arrays:
                return "UNDIM'D ARRAY"
            
            # Get the nested array structure
            array_data = self.emulator.arrays[array_name]
            
            # Navigate to the parent of the target element
            current = array_data
            for index in indices[:-1]:  # All but the last index
                # Check bounds
                if index < 0 or index >= len(current):
                    return "BAD SUBSCRIPT"
                current = current[index]
            
            # Set the final element
            final_index = indices[-1]
            if final_index < 0 or final_index >= len(current):
                return "BAD SUBSCRIPT"
            
            current[final_index] = value
            return None
            
        except Exception as e:
            return f"Error setting array element: {str(e)}"
    
    def get_variable(self, var_name):
        """Get variable value with proper type handling"""
        var_name = var_name.upper()
        
        if var_name in self.emulator.variables:
            return self.emulator.variables[var_name]
        else:
            # Return default value based on type
            return self._get_default_value(var_name)
    
    def set_variable(self, var_name, value):
        """Set variable value with type validation"""
        var_name = var_name.upper()
        
        # Type validation
        if var_name.endswith('$'):
            # String variable
            self.emulator.variables[var_name] = str(value)
        else:
            # Numeric variable
            try:
                if isinstance(value, str):
                    # Try to convert string to number
                    if '.' in value or 'E' in value.upper():
                        self.emulator.variables[var_name] = float(value)
                    else:
                        self.emulator.variables[var_name] = int(value)
                else:
                    self.emulator.variables[var_name] = value
            except (ValueError, TypeError):
                # If conversion fails, set to 0
                self.emulator.variables[var_name] = 0
    
    def _create_multidim_array(self, dimensions, init_value):
        """Create nested lists for multi-dimensional array"""
        # Create nested lists for multi-dimensional array
        if len(dimensions) == 1:
            return [init_value] * (dimensions[0] + 1)  # DIM A(10) creates 11 elements (0-10)
        else:
            return [self._create_multidim_array(dimensions[1:], init_value) for _ in range(dimensions[0] + 1)]
    
    def _calculate_linear_index(self, indices, dimensions):
        """Convert multi-dimensional indices to linear index"""
        linear_index = 0
        multiplier = 1
        
        # Calculate in reverse order
        for i in range(len(indices) - 1, -1, -1):
            linear_index += indices[i] * multiplier
            multiplier *= (dimensions[i] + 1)
        
        return linear_index
    
    def _get_default_value(self, var_name):
        """Get default value for variable based on type"""
        if var_name.endswith('$'):
            return ""  # String variables default to empty string
        else:
            return 0   # Numeric variables default to 0
    
    def _is_valid_variable_name(self, name):
        """Check if variable name is valid"""
        # Remove $ suffix for string variables
        base_name = name.rstrip('$')
        
        # Must start with letter
        if not base_name[0].isalpha():
            return False
        
        # Can contain letters and numbers
        for char in base_name[1:]:
            if not (char.isalnum()):
                return False
        
        return True
    
    def clear_variables(self):
        """Clear all variables and arrays"""
        self.emulator.variables.clear()
        self.emulator.arrays.clear()
    
    def format_number_for_output(self, value):
        """Format number for display output"""
        if isinstance(value, str):
            return value
        elif isinstance(value, int):
            return f" {value} "
        elif isinstance(value, float):
            if value.is_integer():
                return f" {int(value)} "
            else:
                # Format float with appropriate precision
                if abs(value) >= 1e6 or (abs(value) < 1e-3 and value != 0):
                    return f" {value:.6E} "
                else:
                    return f" {value:.6G} "
        else:
            return str(value)