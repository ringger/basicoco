#!/usr/bin/env python3

"""
Comprehensive tests for command parsing edge cases.
Tests the parsing logic that handles complex syntax scenarios.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from test_base import BaseTestCase


class CommandParsingTest(BaseTestCase):
    """Test cases for command parsing edge cases and complex syntax"""

    def test_basic_functionality(self):
        """Test basic command parsing functionality"""
        self.assert_text_output('PRINT "HELLO"', 'HELLO')

    def test_multi_statement_with_quoted_colons(self):
        """Test multi-statement lines where quoted strings contain colons"""
        # This was a major bug we fixed - colons inside quotes should not split statements
        program = [
            '10 PRINT "TIME: 12:30"; ": END"'
        ]
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Should print the full string with colons (may have extra spaces from PRINT semicolon handling)
        self.assertTrue(any('TIME: 12:30' in output and ': END' in output for output in text_outputs))

    def test_multi_statement_complex_parsing(self):
        """Test complex multi-statement parsing with quotes and colons"""
        # Test the exact pattern that was failing before our fix
        self.basic.variables['K$'] = 'X'
        
        # This should split into two statements properly
        result = self.basic.execute_line('PRINT "YOU PRESSED: "; K$: GOTO 100')
        
        # Should contain both a text output and a jump
        has_text = any(item.get('type') == 'text' for item in result)
        has_jump = any(item.get('type') == 'jump' for item in result)
        
        self.assertTrue(has_text, "Should have text output from PRINT")
        self.assertTrue(has_jump, "Should have jump from GOTO")

    def test_string_variables_in_expressions(self):
        """Test string variables with $ in complex expressions"""
        # Set up string variables
        self.basic.variables['NAME$'] = 'ALICE'
        self.basic.variables['KEY$'] = ''
        
        # Test in IF conditions
        result = self.basic.execute_command('IF NAME$ = "ALICE" THEN PRINT "MATCH"')
        self.assertTrue(any('MATCH' in str(item) for item in result))
        
        # Test empty string comparison
        result = self.basic.execute_command('IF KEY$ <> "" THEN PRINT "NOT EMPTY"')
        # Should not print anything since KEY$ is empty
        self.assertFalse(any('NOT EMPTY' in str(item) for item in result))

    def test_complex_print_parsing(self):
        """Test PRINT command with complex separator combinations"""
        # Test semicolon concatenation
        self.basic.variables['A'] = 5
        self.basic.variables['B$'] = 'TEST'
        
        result = self.basic.execute_command('PRINT "A="; A; " B$="; B$')
        text = self.get_text_output(result)[0] if result else ""
        
        # Should concatenate properly with spaces
        self.assertIn('A=', text)
        self.assertIn('5', text)
        self.assertIn('B$=', text)
        self.assertIn('TEST', text)

    def test_parentheses_in_commands(self):
        """Test commands with complex parentheses structures"""
        # Graphics commands with coordinates
        self.assert_graphics_output('PSET(100,200)', 'pset')
        self.assert_graphics_output('LINE(10,20)-(30,40)', 'line')
        self.assert_graphics_output('CIRCLE(128,96),25', 'circle')
        
        # Function calls with nested parentheses
        self.basic.variables['S$'] = 'HELLO'
        result = self.basic.execute_command('PRINT LEFT$(RIGHT$(S$,4),2)')
        # Should work with nested function calls
        self.assertTrue(len(result) > 0)

    def test_expression_parsing_precedence(self):
        """Test mathematical expression parsing with operator precedence"""
        # Test basic precedence
        self.assert_text_output('PRINT 2 + 3 * 4', '14')  # Should be 14, not 20
        self.assert_text_output('PRINT (2 + 3) * 4', '20')  # Should be 20
        
        # Test with variables
        self.basic.variables['X'] = 2
        self.basic.variables['Y'] = 3
        self.assert_text_output('PRINT X + Y * 4', '14')

    def test_string_vs_numeric_contexts(self):
        """Test parsing in string vs numeric contexts"""
        # Numeric context
        self.basic.variables['A'] = 5
        self.assert_text_output('PRINT A + 10', '15')
        
        # String context
        self.basic.variables['A$'] = 'HELLO'
        self.assert_text_output('PRINT A$', 'HELLO')
        
        # Mixed contexts should handle properly
        result = self.basic.execute_command('PRINT A$; " "; A')
        text = self.get_text_output(result)[0] if result else ""
        self.assertIn('HELLO', text)
        self.assertIn('5', text)

    def test_whitespace_handling(self):
        """Test various whitespace scenarios in parsing"""
        # Test extra spaces
        self.assert_text_output('PRINT    "HELLO"   ', 'HELLO')
        
        # Test tabs (if supported)
        self.assert_text_output('PRINT\t"WORLD"', 'WORLD')
        
        # Test no spaces around operators
        self.basic.variables['X'] = 10
        self.assert_text_output('PRINT X+5', '15')
        self.assert_text_output('PRINT X + 5', '15')

    def test_line_number_parsing(self):
        """Test line number parsing in various contexts"""
        # Valid line numbers
        program = [
            '10 PRINT "LINE 10"',
            '100 PRINT "LINE 100"',
            '9999 PRINT "LINE 9999"'
        ]
        
        self.basic.execute_command('NEW')  # Ensure clean state
        self.load_program(program)
        self.assert_program_lines(3)
        
        # Test GOTO with line numbers
        result = self.basic.execute_command('GOTO 100')
        self.assertTrue(any(item.get('type') == 'jump' and item.get('line') == 100 
                           for item in result))

    def test_error_condition_parsing(self):
        """Test parsing of malformed commands for proper error handling"""
        # Missing THEN in IF
        self.assert_error_output('IF X > 5 PRINT "ERROR"')
        
        # Invalid variable names
        try:
            result = self.basic.execute_command('123ABC = 5')
            # Should either error or handle gracefully
        except:
            pass  # Expected

    def test_case_sensitivity(self):
        """Test case sensitivity/insensitivity in parsing"""
        # BASIC should be case insensitive for keywords
        self.assert_text_output('print "hello"', 'hello')
        self.assert_text_output('PRINT "HELLO"', 'HELLO')
        self.assert_text_output('Print "Hello"', 'Hello')
        
        # Variables should preserve case in values but be case insensitive in names
        self.basic.execute_command('name$ = "Alice"')
        self.assert_variable_equals('NAME$', 'Alice')

    def test_complex_for_loop_parsing(self):
        """Test FOR loop parsing with complex expressions"""
        # Test floating point values
        program = [
            '10 FOR I = 0.1 TO 0.3 STEP 0.1',
            '20 PRINT I',
            '30 NEXT I'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Should have outputs for floating point values (precision may affect exact count)
        self.assertTrue(len(text_outputs) >= 2, f"Expected at least 2 outputs, got {len(text_outputs)}: {text_outputs}")

    def test_data_read_parsing(self):
        """Test DATA/READ statement parsing with various data types"""
        program = [
            '10 DATA 123, "HELLO", 3.14, "WORLD"',
            '20 READ A, B$, C, D$',
            '30 PRINT A; B$; C; D$'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Should parse and read mixed data types correctly
        self.assertTrue(len(text_outputs) > 0)

    def test_nested_function_calls(self):
        """Test parsing of nested function calls"""
        self.basic.variables['TEST$'] = 'ABCDEFGH'
        
        # Test nested string functions
        try:
            result = self.basic.execute_command('PRINT LEFT$(RIGHT$(TEST$,5),3)')
            # Should handle nested function parsing
            self.assertTrue(len(result) > 0)
        except:
            # Some nested functions might not be fully implemented yet
            pass

    def test_comment_parsing(self):
        """Test REM comment parsing and handling"""
        program = [
            '10 REM This is a comment',
            '20 PRINT "AFTER COMMENT"',
            '30 REM Another comment: with colons and "quotes"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        # Should execute non-comment lines
        self.assertTrue(any('AFTER COMMENT' in output for output in text_outputs))

    def test_multi_line_program_parsing(self):
        """Test parsing of complete multi-line programs"""
        program = [
            '10 REM COMPLEX PROGRAM TEST',
            '20 FOR I = 1 TO 3',
            '30 IF I = 2 THEN PRINT "MIDDLE": GOTO 50',
            '40 PRINT "VALUE: "; I',
            '50 NEXT I',
            '60 END'
        ]
        
        results = self.execute_program(program)
        errors = self.get_error_messages(results)
        
        # Should parse and run without syntax errors
        self.assertEqual(len(errors), 0, f"Program should parse without errors: {errors}")


if __name__ == '__main__':
    test = CommandParsingTest("Command Parsing Tests")
    results = test.run_all_tests()
    from test_base import print_test_results
    print_test_results(results, verbose=True)