"""
Command Registry and Tokenization System for TRS-80 Color Computer BASIC Emulator

This module provides a principled approach to command parsing and routing,
replacing the brittle hard-coded pattern matching with a registry-based system.
"""

import re
from typing import List, Dict, Callable, Any, Optional


class CommandRegistry:
    """Registry for BASIC commands with proper tokenization and routing"""
    
    def __init__(self):
        self.commands: Dict[str, Dict[str, Any]] = {}
        self.aliases: Dict[str, str] = {}
    
    def register(self, command_name: str, handler: Callable, min_args: int = 0, aliases: Optional[List[str]] = None):
        """Register a command with its handler"""
        command_name = command_name.upper()
        self.commands[command_name] = {
            'handler': handler,
            'min_args': min_args
        }
        
        # Register aliases
        if aliases:
            for alias in aliases:
                self.aliases[alias.upper()] = command_name
    
    def get_handler(self, command_name: str) -> Optional[Callable]:
        """Get handler for a command, checking aliases"""
        command_name = command_name.upper()
        
        # Check direct command
        if command_name in self.commands:
            return self.commands[command_name]['handler']
        
        # Check aliases
        if command_name in self.aliases:
            real_command = self.aliases[command_name]
            return self.commands[real_command]['handler']
        
        return None
    
    def execute(self, line: str) -> Optional[List[Dict[str, Any]]]:
        """Execute a command line using the registry"""
        if not line.strip():
            return []
        
        tokens = self.tokenize_command(line)
        if not tokens:
            return None
        
        command = tokens[0].upper()
        handler = self.get_handler(command)
        
        if handler:
            # Pass the rest of the line (after command) to the handler
            args = line[len(tokens[0]):].strip()
            return handler(args)
        
        return None
    
    @staticmethod
    def tokenize_command(line: str) -> List[str]:
        """
        Tokenize BASIC command line respecting strings, parentheses, and operators.
        
        Examples:
            "PRINT A" -> ["PRINT", "A"]
            "LINE(10,20)-(30,40)" -> ["LINE", "(10,20)-(30,40)"]
            "IF A=5 THEN PRINT \"HELLO\"" -> ["IF", "A=5", "THEN", "PRINT", "\"HELLO\""]
        """
        if not line:
            return []
        
        # First, try to identify the command name
        # BASIC commands are alphabetic, possibly ending with $
        command_match = re.match(r'^([A-Za-z][A-Za-z0-9]*\$?)', line)
        if not command_match:
            return [line]  # No clear command, return as single token
        
        command_name = command_match.group(1)
        rest_of_line = line[len(command_name):]
        
        # If there's nothing after the command, just return the command
        if not rest_of_line.strip():
            return [command_name]
        
        # If the rest starts with whitespace, it's clearly separated
        if rest_of_line[0].isspace():
            return [command_name] + CommandRegistry._tokenize_arguments(rest_of_line.strip())
        
        # If the rest starts with '(' or other operator, split there
        # This handles cases like LINE(10,20) -> ["LINE", "(10,20)"]
        return [command_name, rest_of_line]
    
    @staticmethod
    def _tokenize_arguments(args: str) -> List[str]:
        """Tokenize the arguments portion of a command"""
        if not args:
            return []
        
        tokens = []
        current_token = ""
        in_string = False
        paren_level = 0
        i = 0
        
        while i < len(args):
            char = args[i]
            
            if char == '"':
                in_string = not in_string
                current_token += char
            elif in_string:
                current_token += char
            elif char == '(':
                paren_level += 1
                current_token += char
            elif char == ')':
                paren_level -= 1
                current_token += char
            elif char.isspace() and paren_level == 0:
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
                # Skip whitespace
                while i + 1 < len(args) and args[i + 1].isspace():
                    i += 1
            else:
                current_token += char
            
            i += 1
        
        if current_token:
            tokens.append(current_token)
        
        return tokens
    
    @staticmethod 
    def parse_coordinates(coord_str: str) -> List[int]:
        """
        Parse coordinate expressions like "(10,20)" or "10,20"
        
        Returns list of evaluated coordinate values
        """
        # Remove outer parentheses if present
        coord_str = coord_str.strip()
        if coord_str.startswith('(') and coord_str.endswith(')'):
            coord_str = coord_str[1:-1]
        
        # Split by commas and return coordinate parts for evaluation
        return [part.strip() for part in coord_str.split(',')]
    
    @staticmethod
    def parse_line_coordinates(line_spec: str) -> tuple:
        """
        Parse LINE coordinate specification like "(10,20)-(30,40)"
        
        Returns (start_coords, end_coords) as string tuples for evaluation
        """
        if '-(' not in line_spec:
            raise ValueError("Invalid LINE specification - missing -(")
        
        start_part, end_part = line_spec.split('-(', 1)
        
        # Remove trailing ) from end_part
        if end_part.endswith(')'):
            end_part = end_part[:-1]
        
        # Parse start coordinates
        start_coords = CommandRegistry.parse_coordinates(start_part)
        end_coords = CommandRegistry.parse_coordinates(end_part)
        
        return start_coords, end_coords
    
    def list_commands(self) -> List[str]:
        """List all registered commands"""
        return sorted(list(self.commands.keys()) + list(self.aliases.keys()))