"""
Text Utilities for TRS-80 Color Computer BASIC Emulator

Static utility methods for splitting BASIC statements on delimiters and
splitting arguments. (Control-structure detection lives in
ast_converter.starts_control_structure.)
"""

import re


class StatementSplitter:
    """Static utilities for splitting and classifying BASIC text."""

    # Commands whose filename argument may be written in single quotes
    _SINGLE_QUOTE_COMMANDS = frozenset({'SAVE', 'LOAD', 'KILL', 'MERGE', 'CHAIN', 'CD'})

    @staticmethod
    def is_rem_line(code: str) -> bool:
        """Check if a statement is a comment — never split on colons.

        REM matches as a prefix, as on the CoCo (which crunches keywords):
        REMARK and REMEMBER=5 are comments. ' is the Extended Color BASIC
        shorthand.
        """
        stripped = code.strip()
        return stripped.upper().startswith('REM') or stripped.startswith("'")

    @staticmethod
    def split_on_delimiter(text: str, delimiter: str = ':') -> list:
        """Split text on delimiter, respecting quoted strings and comments.

        When splitting on colons, a comment consumes the rest of the line
        (colons inside it are not delimiters): a segment starting with REM,
        or a ' outside quotes, which becomes its own part (``SOUND 100,5 '
        beep`` gives ``['SOUND 100,5', "' beep"]``). Exception: file
        commands accept single-quoted names (SAVE 'GAME'), so after SAVE,
        LOAD, KILL, MERGE, CHAIN or CD a ' quotes instead.
        """
        parts = []
        current = ""
        in_quotes = False
        in_single_quotes = False
        for pos, char in enumerate(text):
            if char == '"' and not in_single_quotes:
                in_quotes = not in_quotes
                current += char
            elif delimiter == ':' and char == "'" and not in_quotes:
                first_word = current.strip().split(None, 1)[0].upper() if current.strip() else ''
                if in_single_quotes or first_word in StatementSplitter._SINGLE_QUOTE_COMMANDS:
                    in_single_quotes = not in_single_quotes
                    current += char
                    continue
                if current.strip():
                    parts.append(current.strip())
                parts.append(text[pos:].strip())
                return parts
            elif char == delimiter and not in_quotes and not in_single_quotes:
                # If current segment is REM, it consumes everything to end of line
                if delimiter == ':' and StatementSplitter.is_rem_line(current):
                    parts.append((current + text[pos:]).strip())
                    return parts
                if current.strip():
                    parts.append(current.strip())
                current = ""
            else:
                current += char
        if current.strip():
            parts.append(current.strip())
        return parts

    @staticmethod
    def split_args(text: str, keep_empty: bool = False) -> list:
        """Split comma-separated arguments, respecting parentheses and quotes.

        With keep_empty=True, empty items are kept as '' (DATA 1,,3 has three
        items, the middle one empty); otherwise they are dropped.
        """
        return StatementSplitter.split_on_delimiter_paren_aware(
            text, delimiter=',', keep_empty=keep_empty)

    @staticmethod
    def split_on_delimiter_paren_aware(text: str, delimiter: str = ':',
                                       keep_empty: bool = False) -> list:
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
                if current.strip() or keep_empty:
                    parts.append(current.strip())
                current = ""
            else:
                current += char
        if current.strip() or (keep_empty and text.strip()):
            parts.append(current.strip())
        return parts

    @staticmethod
    def parse_line(line):
        """Parse a line to extract line number and code"""
        line = line.strip()
        if not line:
            return None, None
            
        # Check if line starts with a number (with optional code after it)
        # A leading number is a line number even without a space (10PRINT),
        # as on the CoCo
        match = re.match(r'^(\d+)\s*(.*)$', line)
        if match:
            line_num = int(match.group(1))
            code = match.group(2) or ""  # Empty string if no code after line number
            return line_num, code
        else:
            # Direct command (no line number)
            return None, line
    
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