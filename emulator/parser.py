"""
Parser module for TRS-80 Color Computer BASIC Emulator

This module contains parsing and tokenization logic for BASIC commands and expressions.
Extracted from the main CoCoBasic class for better organization.
"""

import re


class BasicParser:
    """Parser for BASIC language constructs"""
    
    @staticmethod
    def parse_line(line):
        """Parse a line to extract line number and code"""
        line = line.strip().upper()
        if not line:
            return None, None
            
        # Check if line starts with a number (with optional code after it)
        match = re.match(r'^(\d+)(?:\s+(.*))?$', line)
        if match:
            line_num = int(match.group(1))
            code = match.group(2) or ""  # Empty string if no code after line number
            return line_num, code
        else:
            # Direct command (no line number)
            return None, line
    
    @staticmethod
    def expand_line_to_sublines(line_num, code, expanded_program):
        """Expand a line containing multiple statements into sublines"""
        # Split by colons, but be careful about strings
        statements = BasicParser._split_by_colon_outside_strings(code)
        
        # Store each statement as a sub-line
        for i, statement in enumerate(statements):
            statement = statement.strip()
            if statement:
                expanded_program[(line_num, i)] = statement
    
    @staticmethod
    def _split_by_colon_outside_strings(code):
        """Split code by colons, but ignore colons inside strings and respect IF/THEN constructs"""
        # Check if this line contains an IF/THEN construct that starts the line
        code_upper = code.upper().strip()
        if_pos = code_upper.find('IF ')
        then_pos = code_upper.find(' THEN ')
        
        # If this line STARTS with an IF/THEN statement, don't split after THEN
        if if_pos == 0 and then_pos > if_pos:
            # This line starts with IF/THEN - treat the whole thing as one statement
            return [code.strip()]
        
        # Normal colon splitting for other statements (including FOR loops)
        statements = []
        current_statement = ""
        in_string = False
        
        for char in code:
            if char == '"' and not in_string:
                in_string = True
                current_statement += char
            elif char == '"' and in_string:
                in_string = False
                current_statement += char
            elif char == ':' and not in_string:
                statements.append(current_statement)
                current_statement = ""
            else:
                current_statement += char
        
        # Add the last statement
        statements.append(current_statement)
        return statements
    
    @staticmethod
    def parse_function_arguments(args_str, expected_count):
        """Parse function arguments from argument string"""
        if not args_str:
            return []
            
        # Simple comma splitting for now
        # TODO: Handle nested function calls and expressions
        args = [arg.strip() for arg in args_str.split(',')]
        
        if len(args) != expected_count:
            raise ValueError(f"Expected {expected_count} arguments, got {len(args)}")
            
        return args
    
    @staticmethod
    def parse_draw_commands(draw_string):
        """Parse DRAW command string into individual drawing commands"""
        commands = []
        i = 0
        while i < len(draw_string):
            char = draw_string[i].upper()
            
            # Movement commands that may have parameters
            if char in ['U', 'D', 'L', 'R', 'E', 'F', 'G', 'H']:
                # Extract number if present
                i += 1
                num_str = ""
                while i < len(draw_string) and draw_string[i].isdigit():
                    num_str += draw_string[i]
                    i += 1
                
                distance = int(num_str) if num_str else 1
                commands.append({'command': char, 'distance': distance})
                continue
            
            # Move without drawing
            elif char == 'M':
                # M+X,Y or M-X,Y or MX,Y format
                i += 1
                coord_str = ""
                while i < len(draw_string) and draw_string[i] not in ['U', 'D', 'L', 'R', 'E', 'F', 'G', 'H', 'M', 'B', 'N', 'S', 'C']:
                    coord_str += draw_string[i]
                    i += 1
                
                # Parse coordinates
                relative = coord_str.startswith('+') or coord_str.startswith('-')
                if coord_str.startswith(('+', '-')):
                    coord_str = coord_str[1:]
                
                if ',' in coord_str:
                    x_str, y_str = coord_str.split(',', 1)
                    try:
                        x = int(x_str)
                        y = int(y_str)
                        commands.append({'command': 'M', 'x': x, 'y': y, 'relative': relative})
                    except ValueError:
                        # Invalid coordinates, skip
                        pass
                continue
            
            # Pen up/down
            elif char == 'B':
                commands.append({'command': 'B'})  # Pen up (move without drawing)
                i += 1
            elif char == 'N':
                commands.append({'command': 'N'})  # Return to original position
                i += 1
            
            # Scale
            elif char == 'S':
                i += 1
                num_str = ""
                while i < len(draw_string) and draw_string[i].isdigit():
                    num_str += draw_string[i]
                    i += 1
                
                scale = int(num_str) if num_str else 1
                commands.append({'command': 'S', 'scale': scale})
                continue
            
            # Color
            elif char == 'C':
                i += 1
                num_str = ""
                while i < len(draw_string) and draw_string[i].isdigit():
                    num_str += draw_string[i]
                    i += 1
                
                color = int(num_str) if num_str else 1
                commands.append({'command': 'C', 'color': color})
                continue
            
            else:
                # Unknown command, skip
                i += 1
        
        return commands