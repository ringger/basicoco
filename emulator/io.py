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
        # Note: INPUT and PRINT are now handled by AST execution
        pass
    
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