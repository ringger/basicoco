"""
Command Registry and Tokenization System for TRS-80 Color Computer BASIC Emulator

This module provides a principled approach to command parsing and routing,
replacing the brittle hard-coded pattern matching with a registry-based system.
"""

import re
from typing import List, Dict, Callable, Any, Optional


class CommandRegistry:
    """
    Enhanced registry for BASIC commands with plugin-like architecture.
    
    Supports command metadata, categories, help text, and modular command registration.
    """
    
    def __init__(self):
        self.commands: Dict[str, Dict[str, Any]] = {}
        self.aliases: Dict[str, str] = {}
        self.categories: Dict[str, List[str]] = {
            'control': [],      # IF, FOR, GOTO, etc.
            'data': [],         # DATA, READ, RESTORE
            'graphics': [],     # PMODE, PSET, LINE, etc.
            'io': [],          # PRINT, INPUT
            'variables': [],    # LET, DIM
            'system': [],      # NEW, LIST, RUN, etc.
            'math': [],        # Functions like SQR, SIN, etc.
            'string': []       # String functions
        }
    
    def register(self, command_name: str, handler: Callable, 
                min_args: int = 0, max_args: Optional[int] = None,
                aliases: Optional[List[str]] = None, 
                category: str = 'system',
                description: str = "",
                syntax: str = "",
                examples: Optional[List[str]] = None):
        """
        Register a command with its handler and metadata.
        
        Args:
            command_name: The primary command name
            handler: Function to handle the command
            min_args: Minimum number of arguments required
            max_args: Maximum number of arguments allowed (None = unlimited)
            aliases: Alternative names for the command
            category: Command category for organization
            description: Brief description of what the command does
            syntax: Syntax description (e.g., "PRINT expression [; expression]...")
            examples: List of usage examples
        """
        command_name = command_name.upper()
        self.commands[command_name] = {
            'handler': handler,
            'min_args': min_args,
            'max_args': max_args,
            'category': category,
            'description': description,
            'syntax': syntax,
            'examples': examples or []
        }
        
        # Add to category
        if category in self.categories:
            self.categories[category].append(command_name)
        
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
        """Execute a single command line using the registry.

        Multi-statement lines are already split by process_line before
        reaching the registry, so no colon detection is needed here.
        """
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
    
    # Pattern matching (x1,y1)-(x2,y2) with optional spaces around the dash
    _COORD_PAIR_RE = re.compile(r'\)\s*-\s*\(')

    @staticmethod
    def is_coordinate_pair_syntax(args: str) -> bool:
        """Check if args use (x1,y1)-(x2,y2) coordinate pair syntax."""
        return bool(CommandRegistry._COORD_PAIR_RE.search(args))

    @staticmethod
    def parse_line_coordinates(line_spec: str) -> tuple:
        """
        Parse LINE coordinate specification like "(10,20)-(30,40)"
        or "(10, 20) - (30, 40)" with optional spaces around the dash.

        Returns (start_coords, end_coords) as string tuples for evaluation
        """
        match = CommandRegistry._COORD_PAIR_RE.search(line_spec)
        if not match:
            raise ValueError("Invalid LINE specification - expected (x1,y1)-(x2,y2)")

        start_part = line_spec[:match.start() + 1]  # up to and including the first ')'
        end_part = line_spec[match.end() - 1:]       # from the second '(' onward

        # Parse start coordinates
        start_coords = CommandRegistry.parse_coordinates(start_part)
        end_coords = CommandRegistry.parse_coordinates(end_part)

        return start_coords, end_coords
    
    def list_commands(self) -> List[str]:
        """List all registered commands"""
        return sorted(list(self.commands.keys()) + list(self.aliases.keys()))
    
    def get_command_info(self, command_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a command"""
        command_name = command_name.upper()
        
        # Check direct command
        if command_name in self.commands:
            return self.commands[command_name].copy()
        
        # Check aliases
        if command_name in self.aliases:
            real_command = self.aliases[command_name]
            info = self.commands[real_command].copy()
            info['is_alias'] = True
            info['primary_name'] = real_command
            return info
        
        return None
    
    def get_commands_by_category(self, category: str) -> List[str]:
        """Get all commands in a specific category"""
        return self.categories.get(category, [])
    
    def get_all_categories(self) -> List[str]:
        """Get list of all command categories"""
        return list(self.categories.keys())
    
    def generate_help(self, command_name: Optional[str] = None) -> List[str]:
        """
        Generate help text for a command or all commands.
        
        Args:
            command_name: Specific command to get help for, or None for all commands
            
        Returns:
            List of help text lines
        """
        if command_name:
            return self._generate_command_help(command_name)
        else:
            return self._generate_general_help()
    
    def _generate_command_help(self, command_name: str) -> List[str]:
        """Generate help for a specific command"""
        info = self.get_command_info(command_name)
        if not info:
            return [f"Unknown command: {command_name}"]
        
        help_lines = []
        primary_name = info.get('primary_name', command_name.upper())
        
        help_lines.append(f"Command: {primary_name}")
        
        if info.get('description'):
            help_lines.append(f"Description: {info['description']}")
        
        if info.get('syntax'):
            help_lines.append(f"Syntax: {info['syntax']}")
        
        help_lines.append(f"Category: {info.get('category', 'unknown')}")
        
        if info.get('examples'):
            help_lines.append("Examples:")
            for example in info['examples']:
                help_lines.append(f"  {example}")
        
        if info.get('is_alias'):
            help_lines.append(f"Note: This is an alias for {primary_name}")
        
        return help_lines
    
    def _generate_general_help(self) -> List[str]:
        """Generate general help showing all commands by category"""
        help_lines = ["Available BASIC Commands:"]
        help_lines.append("=" * 40)
        
        for category in sorted(self.categories.keys()):
            commands = self.get_commands_by_category(category)
            if commands:
                help_lines.append(f"\n{category.title()} Commands:")
                for cmd in sorted(commands):
                    info = self.commands[cmd]
                    description = info.get('description', 'No description')
                    help_lines.append(f"  {cmd:<12} - {description}")
        
        help_lines.append("\nUse HELP <command> for detailed help on a specific command.")
        return help_lines
    
    def validate_plugin_interface(self, plugin) -> bool:
        """
        Validate that a plugin follows the expected interface.
        
        A valid plugin should have a register_commands(registry) method.
        """
        return hasattr(plugin, 'register_commands') and callable(getattr(plugin, 'register_commands'))
    
    def load_plugin(self, plugin) -> bool:
        """
        Load a plugin by calling its register_commands method.
        
        Args:
            plugin: Object with register_commands(registry) method
            
        Returns:
            True if plugin loaded successfully, False otherwise
        """
        if not self.validate_plugin_interface(plugin):
            return False
        
        try:
            plugin.register_commands(self)
            return True
        except Exception:
            return False