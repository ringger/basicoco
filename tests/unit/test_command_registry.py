#!/usr/bin/env python3

"""
Comprehensive tests for Command Registry System

Tests the plugin-like command architecture that provides extensible command registration,
metadata management, help system functionality, and plugin loading capabilities.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from test_base import BaseTestCase
from emulator.commands import CommandRegistry
from emulator.core import CoCoBasic


class CommandRegistryTest(BaseTestCase):
    """Test cases for Command Registry functionality"""

    def setUp(self):
        """Set up test environment"""
        super().setUp()
        self.registry = CommandRegistry()

    def test_basic_functionality(self):
        """Test basic command registry functionality"""
        # Test registering a simple command
        def test_handler(args):
            return [{'type': 'text', 'text': f'Test command with args: {args}'}]
        
        self.registry.register('TEST', test_handler)
        handler = self.registry.get_handler('TEST')
        self.assertTrue(handler is not None)
        self.assertEqual(handler, test_handler)

    def test_command_registration_with_metadata(self):
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
        self.assertEqual(handler, print_handler)
        
        # Test alias retrieval
        alias_handler = self.registry.get_handler('P')
        self.assertEqual(alias_handler, print_handler)
        
        another_alias = self.registry.get_handler('?')
        self.assertEqual(another_alias, print_handler)

    def test_command_info_retrieval(self):
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
        self.assertTrue(info is not None)
        self.assertEqual(info['description'], 'Begin FOR loop with counter variable')
        self.assertEqual(info['category'], 'control')
        self.assertEqual(info['syntax'], 'FOR variable = start TO end [STEP increment]')
        self.assertEqual(len(info['examples']), 2)
        self.assertEqual(info['min_args'], 1)
        self.assertEqual(info['max_args'], 1)

    def test_command_aliases(self):
        """Test command alias functionality"""
        def cls_handler(args):
            return [{'type': 'clear_screen'}]
        
        self.registry.register('CLS', cls_handler, aliases=['CLEAR', 'CLR'])
        
        # Test all variations work
        self.assertEqual(self.registry.get_handler('CLS'), cls_handler)
        self.assertEqual(self.registry.get_handler('CLEAR'), cls_handler)
        self.assertEqual(self.registry.get_handler('CLR'), cls_handler)
        
        # Test case insensitivity
        self.assertEqual(self.registry.get_handler('cls'), cls_handler)
        self.assertEqual(self.registry.get_handler('clear'), cls_handler)

    def test_category_management(self):
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
        
        self.assertEqual(len(io_commands), 2)
        self.assertIn('PRINT', io_commands)
        self.assertIn('INPUT', io_commands)
        
        self.assertEqual(len(graphics_commands), 2)
        self.assertIn('PMODE', graphics_commands)
        self.assertIn('LINE', graphics_commands)
        
        self.assertEqual(len(control_commands), 2)
        self.assertIn('IF', control_commands)
        self.assertIn('FOR', control_commands)
        
        # Test getting all categories
        categories = self.registry.get_all_categories()
        expected_categories = ['control', 'data', 'graphics', 'io', 'variables', 'system', 'math', 'string']
        for cat in expected_categories:
            self.assertIn(cat, categories)

    def test_command_execution(self):
        """Test command execution through registry"""
        def echo_handler(args):
            return [{'type': 'text', 'text': f'Echo: {args}'}]
        
        self.registry.register('ECHO', echo_handler)
        
        # Test successful execution
        result = self.registry.execute('ECHO Hello World')
        self.assertTrue(result is not None)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'text')
        self.assertIn('Hello World', result[0]['text'])
        
        # Test unknown command
        result = self.registry.execute('UNKNOWN_COMMAND test')
        self.assertTrue(result is None)

    def test_command_tokenization(self):
        """Test command tokenization functionality"""
        # Test basic tokenization
        tokens = CommandRegistry.tokenize_command('PRINT "HELLO WORLD"')
        self.assertEqual(len(tokens), 2)
        self.assertEqual(tokens[0], 'PRINT')
        self.assertEqual(tokens[1], '"HELLO WORLD"')
        
        # Test complex command
        tokens = CommandRegistry.tokenize_command('LINE(10,20)-(30,40)')
        self.assertEqual(len(tokens), 2)
        self.assertEqual(tokens[0], 'LINE')
        self.assertEqual(tokens[1], '(10,20)-(30,40)')
        
        # Test empty command
        tokens = CommandRegistry.tokenize_command('')
        self.assertEqual(len(tokens), 0)
        
        # Test command with no arguments
        tokens = CommandRegistry.tokenize_command('CLS')
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0], 'CLS')

    def test_coordinate_parsing(self):
        """Test coordinate parsing utilities"""
        # Test simple coordinates
        coords = CommandRegistry.parse_coordinates('10,20')
        self.assertEqual(len(coords), 2)
        self.assertEqual(coords[0], '10')
        self.assertEqual(coords[1], '20')
        
        # Test coordinates with parentheses
        coords = CommandRegistry.parse_coordinates('(10,20)')
        self.assertEqual(len(coords), 2)
        self.assertEqual(coords[0], '10')
        self.assertEqual(coords[1], '20')
        
        # Test coordinates with spaces
        coords = CommandRegistry.parse_coordinates(' 15 , 25 ')
        self.assertEqual(len(coords), 2)
        self.assertEqual(coords[0], '15')
        self.assertEqual(coords[1], '25')

    def test_line_coordinate_parsing(self):
        """Test LINE command coordinate parsing"""
        # Test basic line specification
        start_coords, end_coords = CommandRegistry.parse_line_coordinates('(10,20)-(30,40)')
        self.assertEqual(len(start_coords), 2)
        self.assertEqual(start_coords[0], '10')
        self.assertEqual(start_coords[1], '20')
        self.assertEqual(len(end_coords), 2)
        self.assertEqual(end_coords[0], '30')
        self.assertEqual(end_coords[1], '40')
        
        # Test with variables
        start_coords, end_coords = CommandRegistry.parse_line_coordinates('(X1,Y1)-(X2,Y2)')
        self.assertEqual(start_coords[0], 'X1')
        self.assertEqual(end_coords[1], 'Y2')

    def test_help_system_general(self):
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
        
        self.assertIn('Available BASIC Commands', help_text)
        self.assertIn('TEST1', help_text)
        self.assertIn('TEST2', help_text)
        self.assertIn('First test command', help_text)
        self.assertIn('Second test command', help_text)

    def test_help_system_specific_command(self):
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
        
        self.assertIn('Command: DETAILED', help_text)
        self.assertIn('A command with detailed help', help_text)
        self.assertIn('DETAILED param1 [param2]', help_text)
        self.assertIn('Category: system', help_text)
        self.assertIn('Examples:', help_text)
        self.assertIn('DETAILED value1', help_text)
        self.assertIn('DETAILED value1 value2', help_text)

    def test_help_for_unknown_command(self):
        """Test help for unknown commands"""
        help_lines = self.registry.generate_help('NONEXISTENT')
        help_text = '\n'.join(help_lines)
        self.assertIn('Unknown command: NONEXISTENT', help_text)

    def test_help_for_aliases(self):
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
        
        self.assertIn('Command: ORIGINAL', help_text)
        self.assertIn('alias for ORIGINAL', help_text)

    def test_plugin_interface_validation(self):
        """Test plugin interface validation"""
        # Valid plugin
        class ValidPlugin:
            def register_commands(self, registry):
                registry.register('PLUGIN_CMD', lambda x: [])
        
        valid_plugin = ValidPlugin()
        self.assertTrue(self.registry.validate_plugin_interface(valid_plugin))
        
        # Invalid plugin - no register_commands method
        class InvalidPlugin:
            pass
        
        invalid_plugin = InvalidPlugin()
        self.assertFalse(self.registry.validate_plugin_interface(invalid_plugin))
        
        # Invalid plugin - register_commands is not callable
        class BadPlugin:
            register_commands = "not a function"
        
        bad_plugin = BadPlugin()
        self.assertFalse(self.registry.validate_plugin_interface(bad_plugin))

    def test_plugin_loading(self):
        """Test plugin loading functionality"""
        # Valid plugin
        class TestPlugin:
            def register_commands(self, registry):
                registry.register('PLUGIN_TEST', lambda x: [{'type': 'text', 'text': 'Plugin works!'}])
        
        plugin = TestPlugin()
        success = self.registry.load_plugin(plugin)
        self.assertTrue(success)
        
        # Verify plugin command was registered
        handler = self.registry.get_handler('PLUGIN_TEST')
        self.assertTrue(handler is not None)
        
        # Test the plugin command works
        result = handler('')
        self.assertEqual(result[0]['text'], 'Plugin works!')

    def test_plugin_loading_with_invalid_plugin(self):
        """Test plugin loading with invalid plugins"""
        # Plugin that raises exception during registration
        class BrokenPlugin:
            def register_commands(self, registry):
                raise Exception("Plugin error!")
        
        broken_plugin = BrokenPlugin()
        success = self.registry.load_plugin(broken_plugin)
        self.assertFalse(success)
        
        # Plugin with invalid interface
        class NoMethodPlugin:
            pass
        
        no_method_plugin = NoMethodPlugin()
        success = self.registry.load_plugin(no_method_plugin)
        self.assertFalse(success)

    def test_command_list_functionality(self):
        """Test command listing functionality"""
        # Register some commands with aliases
        self.registry.register('CMD1', lambda x: [], aliases=['C1'])
        self.registry.register('CMD2', lambda x: [], aliases=['C2', 'COMMAND2'])
        
        # Get all commands (including aliases)
        all_commands = self.registry.list_commands()
        
        # Check primary commands are included
        self.assertIn('CMD1', all_commands)
        self.assertIn('CMD2', all_commands)
        
        # Check aliases are included
        self.assertIn('C1', all_commands)
        self.assertIn('C2', all_commands)
        self.assertIn('COMMAND2', all_commands)
        
        # Check list is sorted
        self.assertEqual(all_commands, sorted(all_commands))

    def test_integration_with_basic_emulator(self):
        """Test integration with the BASIC emulator"""
        # Test that the emulator's command registry works
        commands = self.basic.command_registry.list_commands()
        self.assertTrue(len(commands) > 0)
        
        # Test some known commands are registered
        self.assertIn('PRINT', commands)
        self.assertIn('IF', commands)
        self.assertIn('FOR', commands)
        self.assertIn('HELP', commands)
        
        # Test HELP command functionality
        help_handler = self.basic.command_registry.get_handler('HELP')
        self.assertTrue(help_handler is not None)

    def test_argument_parsing_utilities(self):
        """Test argument parsing helper functions"""
        # Test _tokenize_arguments
        args = CommandRegistry._tokenize_arguments('arg1 arg2 "arg with spaces"')
        self.assertEqual(len(args), 3)
        self.assertEqual(args[0], 'arg1')
        self.assertEqual(args[1], 'arg2')
        self.assertEqual(args[2], '"arg with spaces"')
        
        # Test with parentheses
        args = CommandRegistry._tokenize_arguments('func(a,b) value')
        self.assertEqual(len(args), 2)
        self.assertEqual(args[0], 'func(a,b)')
        self.assertEqual(args[1], 'value')
        
        # Test empty arguments
        args = CommandRegistry._tokenize_arguments('')
        self.assertEqual(len(args), 0)

    def test_case_insensitive_commands(self):
        """Test that command names are case insensitive"""
        def test_handler(args):
            return [{'type': 'text', 'text': 'Case insensitive works'}]
        
        self.registry.register('TESTCASE', test_handler)
        
        # Test various cases
        self.assertEqual(self.registry.get_handler('TESTCASE'), test_handler)
        self.assertEqual(self.registry.get_handler('testcase'), test_handler)
        self.assertEqual(self.registry.get_handler('TestCase'), test_handler)
        self.assertEqual(self.registry.get_handler('TESTCASE'), test_handler)

    def test_command_info_for_aliases(self):
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
        self.assertEqual(original_info['description'], 'Original command')
        self.assertFalse(original_info.get('is_alias', False))
        
        # Test info for alias
        alias_info = self.registry.get_command_info('SHORTCUT')
        self.assertEqual(alias_info['description'], 'Original command')
        self.assertTrue(alias_info.get('is_alias', False))
        self.assertEqual(alias_info.get('primary_name'), 'ORIGINAL')


if __name__ == '__main__':
    test = CommandRegistryTest("Command Registry Tests")
    results = test.run_all_tests()
    from test_base import print_test_results
    print_test_results(results, verbose=True)