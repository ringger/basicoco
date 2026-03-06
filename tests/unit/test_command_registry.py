#!/usr/bin/env python3

"""
Comprehensive tests for Command Registry System

Tests the plugin-like command architecture that provides extensible command registration,
metadata management, help system functionality, and plugin loading capabilities.
"""

import pytest
from emulator.commands import CommandRegistry
from emulator.core import CoCoBasic


class TestCommandRegistry:
    """Test cases for Command Registry functionality"""

    @pytest.fixture(autouse=True)
    def setup_registry(self):
        """Set up test environment"""
        self.registry = CommandRegistry()

    def test_basic_functionality(self, basic, helpers):
        """Test basic command registry functionality"""
        # Test registering a simple command
        def test_handler(args):
            return [{'type': 'text', 'text': f'Test command with args: {args}'}]
        
        self.registry.register('TEST', test_handler)
        handler = self.registry.get_handler('TEST')
        assert handler is not None
        assert handler == test_handler

    def test_command_registration_with_metadata(self, basic, helpers):
        """Test command registration with full metadata"""
        def print_handler(args):
            return [{'type': 'text', 'text': args}]
        
        self.registry.register(
            'PRINT',
            print_handler,
            min_args=0,
            max_args=None,
            aliases=['P', '?'],
            category='io',
            description='Display text and expressions',
            syntax='PRINT [expression] [; expression]...',
            examples=['PRINT "HELLO"', 'PRINT A + B', 'PRINT X; Y; Z']
        )
        
        # Test basic retrieval
        handler = self.registry.get_handler('PRINT')
        assert handler == print_handler
        
        # Test alias retrieval
        alias_handler = self.registry.get_handler('P')
        assert alias_handler == print_handler
        
        another_alias = self.registry.get_handler('?')
        assert another_alias == print_handler

    def test_command_info_retrieval(self, basic, helpers):
        """Test detailed command information retrieval"""
        def for_handler(args):
            return []
        
        self.registry.register(
            'FOR',
            for_handler,
            min_args=1,
            max_args=1,
            category='control',
            description='Begin FOR loop with counter variable',
            syntax='FOR variable = start TO end [STEP increment]',
            examples=['FOR I = 1 TO 10', 'FOR X = 0 TO 100 STEP 5']
        )
        
        info = self.registry.get_command_info('FOR')
        assert info is not None
        assert info['description'] == 'Begin FOR loop with counter variable'
        assert info['category'] == 'control'
        assert info['syntax'] == 'FOR variable = start TO end [STEP increment]'
        assert len(info['examples']) == 2
        assert info['min_args'] == 1
        assert info['max_args'] == 1

    def test_command_aliases(self, basic, helpers):
        """Test command alias functionality"""
        def cls_handler(args):
            return [{'type': 'clear_screen'}]
        
        self.registry.register('CLS', cls_handler, aliases=['CLEAR', 'CLR'])
        
        # Test all variations work
        assert self.registry.get_handler('CLS') == cls_handler
        assert self.registry.get_handler('CLEAR') == cls_handler
        assert self.registry.get_handler('CLR') == cls_handler
        
        # Test case insensitivity
        assert self.registry.get_handler('cls') == cls_handler
        assert self.registry.get_handler('clear') == cls_handler

    def test_category_management(self, basic, helpers):
        """Test command categorization functionality"""
        # Register commands in different categories
        self.registry.register('PRINT', lambda x: [], category='io')
        self.registry.register('INPUT', lambda x: [], category='io')
        self.registry.register('PMODE', lambda x: [], category='graphics')
        self.registry.register('LINE', lambda x: [], category='graphics')
        self.registry.register('IF', lambda x: [], category='control')
        self.registry.register('FOR', lambda x: [], category='control')
        
        # Test category retrieval
        io_commands = self.registry.get_commands_by_category('io')
        graphics_commands = self.registry.get_commands_by_category('graphics')
        control_commands = self.registry.get_commands_by_category('control')
        
        assert len(io_commands) == 2
        assert 'PRINT' in io_commands
        assert 'INPUT' in io_commands
        
        assert len(graphics_commands) == 2
        assert 'PMODE' in graphics_commands
        assert 'LINE' in graphics_commands
        
        assert len(control_commands) == 2
        assert 'IF' in control_commands
        assert 'FOR' in control_commands
        
        # Test getting all categories
        categories = self.registry.get_all_categories()
        expected_categories = ['control', 'data', 'graphics', 'io', 'variables', 'system', 'math', 'string']
        for cat in expected_categories:
            assert cat in categories

    def test_command_execution(self, basic, helpers):
        """Test command execution through registry"""
        def echo_handler(args):
            return [{'type': 'text', 'text': f'Echo: {args}'}]
        
        self.registry.register('ECHO', echo_handler)
        
        # Test successful execution
        result = self.registry.execute('ECHO Hello World')
        assert result is not None
        assert len(result) == 1
        assert result[0]['type'] == 'text'
        assert 'Hello World' in result[0]['text']
        
        # Test unknown command
        result = self.registry.execute('UNKNOWN_COMMAND test')
        assert result is None

    def test_command_tokenization(self, basic, helpers):
        """Test command tokenization functionality"""
        # Test basic tokenization
        tokens = CommandRegistry.tokenize_command('PRINT "HELLO WORLD"')
        assert len(tokens) == 2
        assert tokens[0] == 'PRINT'
        assert tokens[1] == '"HELLO WORLD"'
        
        # Test complex command
        tokens = CommandRegistry.tokenize_command('LINE(10,20)-(30,40)')
        assert len(tokens) == 2
        assert tokens[0] == 'LINE'
        assert tokens[1] == '(10,20)-(30,40)'
        
        # Test empty command
        tokens = CommandRegistry.tokenize_command('')
        assert len(tokens) == 0
        
        # Test command with no arguments
        tokens = CommandRegistry.tokenize_command('CLS')
        assert len(tokens) == 1
        assert tokens[0] == 'CLS'

    def test_coordinate_parsing(self, basic, helpers):
        """Test coordinate parsing utilities"""
        # Test simple coordinates
        coords = CommandRegistry.parse_coordinates('10,20')
        assert len(coords) == 2
        assert coords[0] == '10'
        assert coords[1] == '20'
        
        # Test coordinates with parentheses
        coords = CommandRegistry.parse_coordinates('(10,20)')
        assert len(coords) == 2
        assert coords[0] == '10'
        assert coords[1] == '20'
        
        # Test coordinates with spaces
        coords = CommandRegistry.parse_coordinates(' 15 , 25 ')
        assert len(coords) == 2
        assert coords[0] == '15'
        assert coords[1] == '25'

    def test_line_coordinate_parsing(self, basic, helpers):
        """Test LINE command coordinate parsing"""
        # Test basic line specification
        start_coords, end_coords = CommandRegistry.parse_line_coordinates('(10,20)-(30,40)')
        assert len(start_coords) == 2
        assert start_coords[0] == '10'
        assert start_coords[1] == '20'
        assert len(end_coords) == 2
        assert end_coords[0] == '30'
        assert end_coords[1] == '40'
        
        # Test with variables
        start_coords, end_coords = CommandRegistry.parse_line_coordinates('(X1,Y1)-(X2,Y2)')
        assert start_coords[0] == 'X1'
        assert end_coords[1] == 'Y2'

    def test_coordinate_parsing_with_array_refs(self, basic, helpers):
        """Test coordinate parsing with 2D array references like GX(R,C)"""
        coords = CommandRegistry.parse_coordinates('GX(R,C),GY(R,C)')
        assert len(coords) == 2
        assert coords[0] == 'GX(R,C)'
        assert coords[1] == 'GY(R,C)'

    def test_coordinate_parsing_with_nested_expressions(self, basic, helpers):
        """Test coordinate parsing with expressions containing commas in parens"""
        coords = CommandRegistry.parse_coordinates('(A(1,2),B(3,4))')
        assert len(coords) == 2
        assert coords[0] == 'A(1,2)'
        assert coords[1] == 'B(3,4)'

    def test_line_coordinates_with_2d_arrays(self, basic, helpers):
        """Test LINE coordinate parsing with 2D array refs"""
        start, end = CommandRegistry.parse_line_coordinates(
            '(GX(R,C),GY(R,C))-(GX(R,C+1),GY(R,C+1))')
        assert len(start) == 2
        assert start[0] == 'GX(R,C)'
        assert start[1] == 'GY(R,C)'
        assert len(end) == 2
        assert end[0] == 'GX(R,C+1)'
        assert end[1] == 'GY(R,C+1)'

    def test_help_system_general(self, basic, helpers):
        """Test general help system functionality"""
        # Register some test commands
        self.registry.register(
            'TEST1',
            lambda x: [],
            category='system',  # Use existing category
            description='First test command',
            syntax='TEST1 arg1',
            examples=['TEST1 hello']
        )
        
        self.registry.register(
            'TEST2',
            lambda x: [],
            category='system',  # Use existing category
            description='Second test command',
            syntax='TEST2 arg1 arg2',
            examples=['TEST2 foo bar']
        )
        
        # Test general help
        help_lines = self.registry.generate_help()
        help_text = '\n'.join(help_lines)
        
        assert 'Available BASIC Commands' in help_text
        assert 'TEST1' in help_text
        assert 'TEST2' in help_text
        assert 'First test command' in help_text
        assert 'Second test command' in help_text

    def test_help_system_specific_command(self, basic, helpers):
        """Test help for specific commands"""
        self.registry.register(
            'DETAILED',
            lambda x: [],
            category='system',
            description='A command with detailed help',
            syntax='DETAILED param1 [param2]',
            examples=['DETAILED value1', 'DETAILED value1 value2']
        )
        
        # Test specific command help
        help_lines = self.registry.generate_help('DETAILED')
        help_text = '\n'.join(help_lines)
        
        assert 'Command: DETAILED' in help_text
        assert 'A command with detailed help' in help_text
        assert 'DETAILED param1 [param2]' in help_text
        assert 'Category: system' in help_text
        assert 'Examples:' in help_text
        assert 'DETAILED value1' in help_text
        assert 'DETAILED value1 value2' in help_text

    def test_help_for_unknown_command(self, basic, helpers):
        """Test help for unknown commands"""
        help_lines = self.registry.generate_help('NONEXISTENT')
        help_text = '\n'.join(help_lines)
        assert 'Unknown command: NONEXISTENT' in help_text

    def test_help_for_aliases(self, basic, helpers):
        """Test help system with command aliases"""
        self.registry.register(
            'ORIGINAL',
            lambda x: [],
            aliases=['ALIAS1', 'ALIAS2'],
            description='Command with aliases'
        )
        
        # Test help for alias
        help_lines = self.registry.generate_help('ALIAS1')
        help_text = '\n'.join(help_lines)
        
        assert 'Command: ORIGINAL' in help_text
        assert 'alias for ORIGINAL' in help_text

    def test_plugin_interface_validation(self, basic, helpers):
        """Test plugin interface validation"""
        # Valid plugin
        class ValidPlugin:
            def register_commands(self, registry):
                registry.register('PLUGIN_CMD', lambda x: [])
        
        valid_plugin = ValidPlugin()
        assert self.registry.validate_plugin_interface(valid_plugin)
        
        # Invalid plugin - no register_commands method
        class InvalidPlugin:
            pass
        
        invalid_plugin = InvalidPlugin()
        assert not self.registry.validate_plugin_interface(invalid_plugin)
        
        # Invalid plugin - register_commands is not callable
        class BadPlugin:
            register_commands = "not a function"
        
        bad_plugin = BadPlugin()
        assert not self.registry.validate_plugin_interface(bad_plugin)

    def test_plugin_loading(self, basic, helpers):
        """Test plugin loading functionality"""
        # Valid plugin
        class TestPlugin:
            def register_commands(self, registry):
                registry.register('PLUGIN_TEST', lambda x: [{'type': 'text', 'text': 'Plugin works!'}])
        
        plugin = TestPlugin()
        success = self.registry.load_plugin(plugin)
        assert success
        
        # Verify plugin command was registered
        handler = self.registry.get_handler('PLUGIN_TEST')
        assert handler is not None
        
        # Test the plugin command works
        result = handler('')
        assert result[0]['text'] == 'Plugin works!'

    def test_plugin_loading_with_invalid_plugin(self, basic, helpers):
        """Test plugin loading with invalid plugins"""
        # Plugin that raises exception during registration
        class BrokenPlugin:
            def register_commands(self, registry):
                raise Exception("Plugin error!")
        
        broken_plugin = BrokenPlugin()
        success = self.registry.load_plugin(broken_plugin)
        assert not success
        
        # Plugin with invalid interface
        class NoMethodPlugin:
            pass
        
        no_method_plugin = NoMethodPlugin()
        success = self.registry.load_plugin(no_method_plugin)
        assert not success

    def test_command_list_functionality(self, basic, helpers):
        """Test command listing functionality"""
        # Register some commands with aliases
        self.registry.register('CMD1', lambda x: [], aliases=['C1'])
        self.registry.register('CMD2', lambda x: [], aliases=['C2', 'COMMAND2'])
        
        # Get all commands (including aliases)
        all_commands = self.registry.list_commands()
        
        # Check primary commands are included
        assert 'CMD1' in all_commands
        assert 'CMD2' in all_commands
        
        # Check aliases are included
        assert 'C1' in all_commands
        assert 'C2' in all_commands
        assert 'COMMAND2' in all_commands
        
        # Check list is sorted
        assert all_commands == sorted(all_commands)

    def test_integration_with_basic_emulator(self, basic, helpers):
        """Test integration with the BASIC emulator"""
        # Test that the emulator's command registry works
        commands = basic.command_registry.list_commands()
        assert len(commands) > 0
        
        # Test some known commands are registered
        # Note: PRINT, IF, FOR, GOTO, etc. are now handled by AST execution, not the registry
        assert 'HELP' in commands
        assert 'DIM' in commands
        assert 'NEXT' in commands
        
        # Test HELP command functionality
        help_handler = basic.command_registry.get_handler('HELP')
        assert help_handler is not None

    def test_argument_parsing_utilities(self, basic, helpers):
        """Test argument parsing helper functions"""
        # Test _tokenize_arguments
        args = CommandRegistry._tokenize_arguments('arg1 arg2 "arg with spaces"')
        assert len(args) == 3
        assert args[0] == 'arg1'
        assert args[1] == 'arg2'
        assert args[2] == '"arg with spaces"'
        
        # Test with parentheses
        args = CommandRegistry._tokenize_arguments('func(a,b) value')
        assert len(args) == 2
        assert args[0] == 'func(a,b)'
        assert args[1] == 'value'
        
        # Test empty arguments
        args = CommandRegistry._tokenize_arguments('')
        assert len(args) == 0

    def test_case_insensitive_commands(self, basic, helpers):
        """Test that command names are case insensitive"""
        def test_handler(args):
            return [{'type': 'text', 'text': 'Case insensitive works'}]
        
        self.registry.register('TESTCASE', test_handler)
        
        # Test various cases
        assert self.registry.get_handler('TESTCASE') == test_handler
        assert self.registry.get_handler('testcase') == test_handler
        assert self.registry.get_handler('TestCase') == test_handler
        assert self.registry.get_handler('TESTCASE') == test_handler

    def test_command_info_for_aliases(self, basic, helpers):
        """Test that command info works correctly for aliases"""
        def original_handler(args):
            return []
        
        self.registry.register(
            'ORIGINAL',
            original_handler,
            aliases=['SHORTCUT'],
            description='Original command'
        )
        
        # Test info for original command
        original_info = self.registry.get_command_info('ORIGINAL')
        assert original_info['description'] == 'Original command'
        assert not original_info.get('is_alias', False)
        
        # Test info for alias
        alias_info = self.registry.get_command_info('SHORTCUT')
        assert alias_info['description'] == 'Original command'
        assert alias_info.get('is_alias', False)
        assert alias_info.get('primary_name') == 'ORIGINAL'
