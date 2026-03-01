"""
Input/Output module for TRS-80 Color Computer BASIC Emulator

This module contains all input/output handling functionality including
INPUT, PRINT, INKEY$, and keyboard buffer management.
Extracted from the main CoCoBasic class for better organization.
"""

import re


class IOHandler:
    """Handler for BASIC input/output operations"""
    
    def __init__(self, emulator):
        """Initialize I/O handler with reference to main emulator"""
        self.emulator = emulator
    
    def register_commands(self, registry):
        """Register I/O commands with the command registry"""
        registry.register('INPUT', self.execute_input)
        registry.register('PRINT', self.execute_print)
    
    def execute_input(self, args):
        try:
            # INPUT can have optional prompt: INPUT "Enter value"; variable1, variable2, variable3
            # Or just: INPUT variable1, variable2, variable3
            prompt_text = "? "
            variables = []
            
            # Check if there's a prompt string
            if '"' in args:
                # Extract prompt
                first_quote = args.find('"')
                second_quote = args.find('"', first_quote + 1)
                if second_quote != -1:
                    prompt_text = args[first_quote + 1:second_quote]
                    remainder = args[second_quote + 1:].strip()
                    
                    # Remove semicolon or comma after prompt
                    if remainder.startswith(';') or remainder.startswith(','):
                        remainder = remainder[1:].strip()
                    
                    # Parse variables from remainder
                    if remainder:
                        variables = [var.strip().upper() for var in remainder.split(',')]
                else:
                    # No closing quote - syntax error
                    error = self.emulator.error_context.syntax_error(
                        "Missing closing quote in INPUT prompt",
                        self.emulator.current_line,
                        suggestions=[
                            'Correct syntax: INPUT "prompt"; variable',
                            'Example: INPUT "Enter value"; X',
                            'Make sure prompt string has closing quote'
                        ]
                    )
                    return [{'type': 'error', 'message': error.format_detailed()}]
            else:
                # No prompt, just variables
                variables = [var.strip().upper() for var in args.split(',')]
            
            if not variables:
                error = self.emulator.error_context.syntax_error(
                    "No variables specified in INPUT statement",
                    self.emulator.current_line,
                    suggestions=[
                        'Correct syntax: INPUT variable1, variable2, ...',
                        'Example: INPUT X, Y, NAME$',
                        'Specify at least one variable to input'
                    ]
                )
                return [{'type': 'error', 'message': error.format_detailed()}]
            
            # Validate all variable names
            for variable in variables:
                if not self._is_valid_variable_name(variable):
                    error = self.emulator.error_context.syntax_error(
                        f"Invalid variable name: {variable}",
                        self.emulator.current_line,
                        suggestions=[
                            'Variable names must start with a letter',
                            'Use only letters, numbers, and $ for strings',
                            'Examples: X, NAME$, COUNT, SCORE1'
                        ]
                    )
                    return [{'type': 'error', 'message': error.format_detailed()}]
            
            # Store multi-variable INPUT state
            self.emulator.input_variables = variables
            self.emulator.input_prompt = prompt_text
            self.emulator.current_input_index = 0
            
            # Set flags and request input from client for first variable
            self.emulator.waiting_for_input = True
            self.emulator.program_counter = (self.emulator.current_line, self.emulator.current_sub_line)
            
            return [{'type': 'input_request', 'prompt': prompt_text, 'variable': variables[0]}]
            
        except Exception as e:
            error = self.emulator.error_context.runtime_error(
                f"Unexpected error in INPUT statement: {str(e)}",
                suggestions=[
                    'Check INPUT syntax and variable names',
                    'Example: INPUT "prompt"; variable',
                    'Ensure all variables are valid'
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
    
    def execute_print(self, args):
        try:
            if not args:
                # Just print a blank line
                return [{'type': 'text', 'text': ''}]

            # Handle PRINT with arguments
            result_text = ""

            # Split by semicolons and commas outside of strings, preserving separator info
            parts_with_separators = self._split_print_arguments_with_separators(args)

            for i, (part, separator) in enumerate(parts_with_separators):
                part = part.strip()
                if not part:
                    continue

                # Evaluate the expression
                try:
                    value = self.emulator.evaluate_expression(part)
                    result_text += self._format_print_value(value)

                    # Add spacing based on separator type (if not the last part)
                    if i < len(parts_with_separators) - 1:
                        if separator == ',':
                            # Comma adds tab spacing (typically 14-character columns in BASIC)
                            result_text += "\t"
                        # Semicolon adds no spacing

                except Exception as e:
                    error = self.emulator.error_context.runtime_error(
                        f"Error evaluating PRINT expression: {part}",
                        suggestions=[
                            'Check that all variables are defined',
                            'Verify expression syntax is correct',
                            'Example: PRINT X, "Hello", Y+5'
                        ]
                    )
                    return [{'type': 'error', 'message': error.format_detailed()}]

            # Check if the last part had a trailing separator (semicolon or comma)
            has_trailing_separator = False
            if parts_with_separators and parts_with_separators[-1][1] is not None:
                has_trailing_separator = True

            # Check if result contains carriage return (CHR$(13)) or has trailing separator
            if '\r' in result_text or has_trailing_separator:
                # Handle inline output (carriage return or trailing semicolon)
                return [{'type': 'text', 'text': result_text, 'inline': True}]
            else:
                return [{'type': 'text', 'text': result_text}]
        except Exception as e:
            error = self.emulator.error_context.runtime_error(
                f"Unexpected error in PRINT statement: {str(e)}",
                suggestions=[
                    'Check PRINT syntax and expressions',
                    'Example: PRINT expression1; expression2',
                    'Verify all variables and functions are valid'
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
    
    # INKEY$ functionality consolidated in functions.py function registry
    # Keyboard buffer managed directly by emulator, not through I/O handler
    
    def _split_print_arguments_with_separators(self, args):
        """Split PRINT arguments by semicolon/comma, preserving separator info"""
        parts_with_separators = []
        current_part = ""
        in_string = False
        paren_depth = 0
        
        for char in args:
            if char == '"':
                in_string = not in_string
                current_part += char
            elif char == '(' and not in_string:
                paren_depth += 1
                current_part += char
            elif char == ')' and not in_string:
                paren_depth -= 1
                current_part += char
            elif char in [';', ','] and not in_string and paren_depth == 0:
                # Store the part with its separator
                parts_with_separators.append((current_part, char))
                current_part = ""
            else:
                current_part += char
        
        # Check if the string ends with a separator (indicates no newline)
        trailing_separator = args.rstrip()[-1:] if args.rstrip() and args.rstrip()[-1] in [';', ','] else None
        
        # Add the last part with trailing separator info
        parts_with_separators.append((current_part, trailing_separator))
        return parts_with_separators
    
    def _split_print_arguments(self, args):
        """Split PRINT arguments by semicolon/comma, respecting strings and parentheses"""
        parts = []
        current_part = ""
        in_string = False
        paren_depth = 0
        
        for char in args:
            if char == '"':
                in_string = not in_string
                current_part += char
            elif char == '(' and not in_string:
                paren_depth += 1
                current_part += char
            elif char == ')' and not in_string:
                paren_depth -= 1
                current_part += char
            elif char in [';', ','] and not in_string and paren_depth == 0:
                parts.append(current_part)
                current_part = ""
            else:
                current_part += char
        
        # Add the last part
        parts.append(current_part)
        return parts
    
    def _format_print_value(self, value):
        """Format value for PRINT output"""
        if isinstance(value, str):
            return value
        elif isinstance(value, (int, float)):
            # Format numbers - TRS-80 Color Computer BASIC doesn't add spaces around numbers
            if isinstance(value, float) and value.is_integer():
                return str(int(value))
            else:
                return str(value)
        else:
            return str(value)
    
    def _is_valid_variable_name(self, name):
        """Check if variable name is valid (including array elements)"""
        # Check if this is an array element syntax: A$(1) or A(5)
        if '(' in name and name.endswith(')'):
            # Array element syntax
            paren_pos = name.find('(')
            array_name = name[:paren_pos]
            index_part = name[paren_pos+1:-1]
            
            # Validate array name part (same as simple variable)
            base_array_name = array_name.rstrip('$')
            if not base_array_name:
                return False
            if not base_array_name[0].isalpha():
                return False
            for char in base_array_name[1:]:
                if not char.isalnum():
                    return False
            
            # Validate index part (should be a number or expression)
            # For now, just check it's not empty
            if not index_part.strip():
                return False
            
            return True
        else:
            # Simple variable name
            base_name = name.rstrip('$')
            
            if not base_name:
                return False
            
            # Must start with letter
            if not base_name[0].isalpha():
                return False
            
            # Can contain letters and numbers
            for char in base_name[1:]:
                if not (char.isalnum()):
                    return False
            
            return True