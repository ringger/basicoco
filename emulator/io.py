"""
Input/Output module for TRS-80 Color Computer BASIC Emulator

This module contains I/O helper methods used by the AST-based PRINT visitor.
INKEY$ functionality is in functions.py. INPUT and PRINT execution is in ast_parser.py.
"""


class IOHandler:
    """Handler for BASIC input/output operations"""

    def __init__(self, emulator):
        """Initialize I/O handler with reference to main emulator"""
        self.emulator = emulator

    def register_commands(self, registry):
        """Register I/O commands with the command registry"""
        # Note: INPUT and PRINT are now handled by AST execution
        pass

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
