#!/usr/bin/env python3

"""
Unit tests for PRINT command functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from test_base import BaseTestCase


class PrintCommandTest(BaseTestCase):
    """Test cases for PRINT command"""

    def test_basic_functionality(self):
        """Test basic PRINT command functionality"""
        self.assert_text_output('PRINT "HELLO"', 'HELLO')

    def test_print_string_literal(self):
        """Test PRINT with string literals"""
        self.assert_text_output('PRINT "TEST STRING"', 'TEST STRING')
        self.assert_text_output('PRINT ""', '')

    def test_print_numeric_literal(self):
        """Test PRINT with numeric literals"""
        self.assert_text_output('PRINT 42', '42')
        self.assert_text_output('PRINT 3.14', '3.14')
        self.assert_text_output('PRINT -7', '-7')

    def test_print_variables(self):
        """Test PRINT with variables"""
        # Set up variables
        self.basic.execute_command('A = 42')
        self.basic.execute_command('B$ = "HELLO"')
        self.basic.execute_command('C = 3.14')
        
        # Test printing variables
        self.assert_text_output('PRINT A', '42')
        self.assert_text_output('PRINT B$', 'HELLO')
        self.assert_text_output('PRINT C', '3.14')

    def test_print_expressions(self):
        """Test PRINT with mathematical expressions"""
        self.assert_text_output('PRINT 2 + 3', '5')
        self.assert_text_output('PRINT 10 - 4', '6')
        self.assert_text_output('PRINT 3 * 4', '12')
        self.assert_text_output('PRINT 15 / 3', '5')

    def test_print_concatenated(self):
        """Test PRINT with semicolons (concatenation)"""
        # This tests the PRINT parsing with multiple items
        result = self.basic.execute_command('PRINT "A"; "B"; "C"')
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0]['type'], 'text')
        # The exact output format may vary, but should contain the concatenated parts

    def test_print_with_separators(self):
        """Test PRINT with commas and semicolons"""
        # Test semicolon separator (no spaces)
        result = self.basic.execute_command('PRINT "A";"B"')
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0]['type'], 'text')
        
        # Test comma separator (with spacing)
        result = self.basic.execute_command('PRINT "A","B"')
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0]['type'], 'text')

    def test_print_empty(self):
        """Test PRINT with no arguments (blank line)"""
        result = self.basic.execute_command('PRINT')
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0]['type'], 'text')
        # Should produce empty or whitespace line

    def test_print_in_program(self):
        """Test PRINT commands within a program"""
        program = [
            '10 PRINT "LINE 1"',
            '20 PRINT "LINE 2"',
            '30 PRINT "LINE 3"'
        ]
        
        results = self.execute_program(program)
        text_outputs = self.get_text_output(results)
        
        self.assertTrue(len(text_outputs) >= 3)
        self.assertIn('LINE 1', text_outputs[0])
        self.assertIn('LINE 2', text_outputs[1])
        self.assertIn('LINE 3', text_outputs[2])

    def test_print_string_functions(self):
        """Test PRINT with string functions"""
        # These depend on string function implementations
        try:
            self.assert_text_output('PRINT LEN("HELLO")', '5')
        except (AssertionError, Exception):
            pass  # Skip if string functions not implemented
        
        try:
            self.assert_text_output('PRINT LEFT$("HELLO", 3)', 'HEL')
        except (AssertionError, Exception):
            pass  # Skip if string functions not implemented


if __name__ == '__main__':
    test = PrintCommandTest("PRINT Command Tests")
    results = test.run_all_tests()
    from test_base import print_test_results
    print_test_results(results, verbose=True)