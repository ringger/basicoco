"""
Text Utilities for TRS-80 Color Computer BASIC Emulator

Static utility methods for splitting BASIC statements on delimiters,
splitting arguments, and detecting control-flow keywords.
"""

import re


class StatementSplitter:
    """Static utilities for splitting and classifying BASIC text."""

    # Control-flow keywords that trigger AST conversion when colons are present.
    CONTROL_KEYWORDS = ('IF ', 'FOR ', 'WHILE ', 'DO:', 'DO ')

    @staticmethod
    def is_rem_line(code: str) -> bool:
        """Check if a line is a REM comment (should never be split on colons)."""
        return code.strip().upper().startswith('REM')

    @staticmethod
    def has_control_keyword(code: str) -> bool:
        """Check if code starts with a control-flow keyword (IF/FOR/WHILE/DO)."""
        upper = code.strip().upper()
        return any(upper.startswith(kw) for kw in StatementSplitter.CONTROL_KEYWORDS)

    @staticmethod
    def split_on_delimiter(text: str, delimiter: str = ':') -> list:
        """Split text on delimiter, respecting quoted strings. Strips parts."""
        parts = []
        current = ""
        in_quotes = False
        for char in text:
            if char == '"':
                in_quotes = not in_quotes
                current += char
            elif char == delimiter and not in_quotes:
                if current.strip():
                    parts.append(current.strip())
                current = ""
            else:
                current += char
        if current.strip():
            parts.append(current.strip())
        return parts

    @staticmethod
    def split_args(text: str) -> list:
        """Split comma-separated arguments, respecting parentheses and quotes."""
        return StatementSplitter.split_on_delimiter_paren_aware(text, delimiter=',')

    @staticmethod
    def split_on_delimiter_paren_aware(text: str, delimiter: str = ':') -> list:
        """Like split_on_delimiter but also respects parenthesized groups."""
        parts = []
        current = ""
        in_quotes = False
        paren_depth = 0
        for char in text:
            if char == '"':
                in_quotes = not in_quotes
                current += char
            elif char == '(' and not in_quotes:
                paren_depth += 1
                current += char
            elif char == ')' and not in_quotes:
                paren_depth = max(0, paren_depth - 1)
                current += char
            elif char == delimiter and not in_quotes and paren_depth == 0:
                if current.strip():
                    parts.append(current.strip())
                current = ""
            else:
                current += char
        if current.strip():
            parts.append(current.strip())
        return parts

    @staticmethod
    def parse_line(line):
        """Parse a line to extract line number and code"""
        line = line.strip()
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
        """Expand a line containing multiple statements into sublines.

        Simple colon-splitting fallback. Control structures (IF, FOR, WHILE, DO)
        are handled by core.py via AST conversion before reaching this method.
        """
        statements = StatementSplitter.split_on_delimiter(code)
        for i, statement in enumerate(statements):
            expanded_program[(line_num, i)] = statement

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
                while i < len(draw_string) and draw_string[i].upper() not in ['U', 'D', 'L', 'R', 'E', 'F', 'G', 'H', 'M', 'B', 'N', 'S', 'C', 'A', 'X']:
                    coord_str += draw_string[i]
                    i += 1

                # Parse coordinates — +/- prefix indicates relative mode
                relative = coord_str.startswith('+') or coord_str.startswith('-')

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
            
            # Angle rotation
            elif char == 'A':
                i += 1
                num_str = ""
                while i < len(draw_string) and draw_string[i].isdigit():
                    num_str += draw_string[i]
                    i += 1

                angle = int(num_str) if num_str else 0
                commands.append({'command': 'A', 'angle': angle})
                continue

            # Execute substring from variable
            elif char == 'X':
                i += 1
                var_name = ""
                while i < len(draw_string) and draw_string[i] != ';':
                    var_name += draw_string[i]
                    i += 1
                if i < len(draw_string):
                    i += 1  # skip ';'
                commands.append({'command': 'X', 'variable': var_name.upper().strip()})
                continue

            else:
                # Unknown command, skip
                i += 1
        
        return commands