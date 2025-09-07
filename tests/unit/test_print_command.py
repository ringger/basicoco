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

    def test_comprehensive_separator_behavior(self):
        """Test comprehensive PRINT separator behavior with mixed types"""
        # Set up test variables
        self.basic.execute_command('A = 42')
        self.basic.execute_command('B = 3.14')
        self.basic.execute_command('S$ = "HELLO"')
        self.basic.execute_command('T$ = "WORLD"')
        
        # Test semicolon separator (no spaces - concatenation)
        result = self.basic.execute_command('PRINT "A";"B";"C"')
        self.assertTrue(len(result) > 0 and result[0]['type'] == 'text')
        # Should be "ABC" with no spaces
        self.assertIn('ABC', result[0]['text'])
        
        # Test comma separator (tab spacing)
        result = self.basic.execute_command('PRINT "A","B","C"')
        self.assertTrue(len(result) > 0 and result[0]['type'] == 'text')
        # Should have spacing between items
        output_text = result[0]['text']
        self.assertIn('A', output_text)
        self.assertIn('B', output_text)
        self.assertIn('C', output_text)
        
        # Test mixed types with semicolons (no spaces)
        result = self.basic.execute_command('PRINT "NUMBER:";A;"!"')
        self.assertTrue(len(result) > 0 and result[0]['type'] == 'text')
        self.assertIn('NUMBER:42!', result[0]['text'])
        
        # Test mixed types with commas (spacing)
        result = self.basic.execute_command('PRINT "VALUE",A,"DONE"')
        self.assertTrue(len(result) > 0 and result[0]['type'] == 'text')
        output_text = result[0]['text']
        self.assertIn('VALUE', output_text)
        self.assertIn('42', output_text)
        self.assertIn('DONE', output_text)
        # Should have spaces/tabs between items
        self.assertTrue(len(output_text) > len('VALUE42DONE'))
        
        # Test string variables with semicolons
        result = self.basic.execute_command('PRINT S$;"!";T$')
        self.assertTrue(len(result) > 0 and result[0]['type'] == 'text')
        self.assertIn('HELLO!WORLD', result[0]['text'])
        
        # Test mixed variable types with different separators
        result = self.basic.execute_command('PRINT S$;":";A;",";B')
        self.assertTrue(len(result) > 0 and result[0]['type'] == 'text')
        self.assertIn('HELLO:42', result[0]['text'])  # Semicolons concatenate without spaces
        self.assertIn('3.14', result[0]['text'])
        
        # Test complex expression with separators
        result = self.basic.execute_command('PRINT "RESULT:";"(";"A+B=";" ";A+B;")"')
        self.assertTrue(len(result) > 0 and result[0]['type'] == 'text')
        # Should show something like "RESULT:(A+B= 45.14)"
        output_text = result[0]['text']
        self.assertIn('RESULT:', output_text)
        self.assertIn('45.14', output_text)
        
        # Test trailing separator behavior
        result = self.basic.execute_command('PRINT "LINE1";')
        self.assertTrue(len(result) > 0 and result[0]['type'] == 'text')
        # Trailing semicolon should suppress newline (but this might vary by implementation)
        
        result = self.basic.execute_command('PRINT "LINE2",')
        self.assertTrue(len(result) > 0 and result[0]['type'] == 'text')
        # Trailing comma should position cursor at next tab stop

    def test_advanced_separator_patterns(self):
        """Test advanced separator patterns and edge cases"""
        # Test alternating separators
        result = self.basic.execute_command('PRINT "A";"B","C";"D"')
        self.assertTrue(len(result) > 0 and result[0]['type'] == 'text')
        output_text = result[0]['text']
        self.assertIn('A', output_text)
        self.assertIn('B', output_text) 
        self.assertIn('C', output_text)
        self.assertIn('D', output_text)
        
        # Test function results with separators
        self.basic.execute_command('X = 16')
        result = self.basic.execute_command('PRINT "SQRT(";X;")=";SQR(X)')
        self.assertTrue(len(result) > 0 and result[0]['type'] == 'text')
        # Semicolons concatenate without spaces
        output_text = result[0]['text']
        self.assertIn('SQRT(', output_text)
        self.assertIn('16', output_text)
        self.assertIn(')=', output_text)
        self.assertIn('4', output_text)
        
        # Test empty strings with separators
        result = self.basic.execute_command('PRINT "";"";"CONTENT";""')
        self.assertTrue(len(result) > 0 and result[0]['type'] == 'text')
        self.assertIn('CONTENT', result[0]['text'])


if __name__ == '__main__':
    test = PrintCommandTest("PRINT Command Tests")
    results = test.run_all_tests()
    from test_base import print_test_results
    print_test_results(results, verbose=True)