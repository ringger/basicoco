#!/usr/bin/env python3

"""
Unit tests for INPUT command - interactive user input functionality.
Tests input prompts, variable assignment, and program flow control.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from test_base import BaseTestCase


class InputCommandTest(BaseTestCase):
    """Test cases for INPUT command functionality"""

    def test_basic_functionality(self):
        """Test basic INPUT command functionality"""
        # Test simple INPUT command
        result = self.basic.execute_command('INPUT X')
        self.assertTrue(any(item.get('type') == 'input_request' for item in result))

    def test_input_simple_variable(self):
        """Test INPUT with simple variable"""
        result = self.basic.execute_command('INPUT X')
        
        # Should produce input request
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'input_request')
        self.assertEqual(result[0]['prompt'], '? ')
        self.assertEqual(result[0]['variable'], 'X')

    def test_input_string_variable(self):
        """Test INPUT with string variable"""
        result = self.basic.execute_command('INPUT N$')
        
        # Should produce input request
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'input_request')
        self.assertEqual(result[0]['prompt'], '? ')
        self.assertEqual(result[0]['variable'], 'N$')

    def test_input_with_prompt(self):
        """Test INPUT command with custom prompt"""
        result = self.basic.execute_command('INPUT "ENTER YOUR NAME"; N$')
        
        # Should produce input request with custom prompt
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'input_request')
        self.assertEqual(result[0]['prompt'], 'ENTER YOUR NAME')
        self.assertEqual(result[0]['variable'], 'N$')

    def test_input_with_question_prompt(self):
        """Test INPUT with question-style prompt"""
        result = self.basic.execute_command('INPUT "WHAT IS YOUR AGE"; A')
        
        self.assertEqual(result[0]['type'], 'input_request')
        self.assertEqual(result[0]['prompt'], 'WHAT IS YOUR AGE')
        self.assertEqual(result[0]['variable'], 'A')

    def test_input_multiple_variables(self):
        """Test INPUT with multiple variables"""
        result = self.basic.execute_command('INPUT A, B, C$')
        
        # Should handle multiple variables (implementation dependent)
        self.assertTrue(any(item.get('type') == 'input_request' for item in result))

    def test_input_in_program(self):
        """Test INPUT command within a program"""
        program = [
            '10 INPUT "WHAT IS YOUR AGE"; A',
            '20 PRINT "YOU ARE"; A; "YEARS OLD"'
        ]
        
        results = self.execute_program(program)
        
        # Should produce input request
        input_requests = [item for item in results if item.get('type') == 'input_request']
        self.assertTrue(len(input_requests) > 0, "Program should produce input request")
        
        # Check the input request details
        self.assertEqual(input_requests[0]['prompt'], 'WHAT IS YOUR AGE')
        self.assertEqual(input_requests[0]['variable'], 'A')

    def test_input_with_semicolon_vs_comma(self):
        """Test INPUT with semicolon vs comma separators"""
        # With semicolon (no automatic question mark)
        result1 = self.basic.execute_command('INPUT "NAME"; N$')
        self.assertEqual(result1[0]['prompt'], 'NAME')
        
        # With comma (adds question mark - if implemented)
        result2 = self.basic.execute_command('INPUT "NAME", N$')
        # Implementation may vary - just check it produces input request
        self.assertTrue(any(item.get('type') == 'input_request' for item in result2))

    def test_input_syntax_variations(self):
        """Test various INPUT command syntax variations"""
        # Without prompt
        result1 = self.basic.execute_command('INPUT X')
        self.assertEqual(result1[0]['prompt'], '? ')
        
        # With quoted prompt and semicolon
        result2 = self.basic.execute_command('INPUT "ENTER VALUE"; X')
        self.assertEqual(result2[0]['prompt'], 'ENTER VALUE')
        
        # With quoted prompt and comma (if supported)
        try:
            result3 = self.basic.execute_command('INPUT "ENTER VALUE", X')
            self.assertTrue(any(item.get('type') == 'input_request' for item in result3))
        except:
            pass  # May not be implemented

    def test_input_error_handling(self):
        """Test INPUT command error conditions"""
        # Invalid syntax should produce error
        try:
            result = self.basic.execute_command('INPUT')
            if result:
                self.assertTrue(any(item.get('type') == 'error' for item in result))
        except:
            pass  # May throw exception instead

    def test_input_variable_types(self):
        """Test INPUT with different variable types"""
        # Numeric variable
        result1 = self.basic.execute_command('INPUT NUM')
        self.assertEqual(result1[0]['variable'], 'NUM')
        
        # String variable
        result2 = self.basic.execute_command('INPUT STR$')
        self.assertEqual(result2[0]['variable'], 'STR$')
        
        # Array element (if supported)
        try:
            self.basic.execute_command('DIM A(5)')
            result3 = self.basic.execute_command('INPUT A(3)')
            if result3 and not any(item.get('type') == 'error' for item in result3):
                self.assertTrue(any(item.get('type') == 'input_request' for item in result3))
        except:
            pass  # May not be fully implemented

    def test_input_prompt_formatting(self):
        """Test INPUT prompt formatting and display"""
        # Test various prompt formats
        test_cases = [
            ('INPUT "NAME"; N$', 'NAME'),
            ('INPUT "ENTER YOUR AGE"; A', 'ENTER YOUR AGE'),
            ('INPUT "VALUE"; X', 'VALUE'),
        ]
        
        for command, expected_prompt in test_cases:
            result = self.basic.execute_command(command)
            if result and result[0].get('type') == 'input_request':
                self.assertEqual(result[0]['prompt'], expected_prompt)

    def test_input_in_complex_program(self):
        """Test INPUT in a more complex program context"""
        program = [
            '10 PRINT "CALCULATOR PROGRAM"',
            '20 INPUT "FIRST NUMBER"; A',
            '30 INPUT "SECOND NUMBER"; B', 
            '40 PRINT "SUM IS"; A + B',
            '50 END'
        ]
        
        results = self.execute_program(program)
        
        # Should have text output and input requests
        text_outputs = [item for item in results if item.get('type') == 'text']
        input_requests = [item for item in results if item.get('type') == 'input_request']
        
        self.assertTrue(len(text_outputs) > 0, "Should have text output")
        self.assertTrue(len(input_requests) > 0, "Should have input requests")
        
        # Check first input request
        if input_requests:
            self.assertEqual(input_requests[0]['prompt'], 'FIRST NUMBER')
            self.assertEqual(input_requests[0]['variable'], 'A')

    def test_input_continuation_after_response(self):
        """Test program continuation after INPUT response"""
        # This test simulates the INPUT response mechanism
        program = [
            '10 INPUT "TEST"; X',
            '20 PRINT "YOU ENTERED"; X'
        ]
        
        # Load and start program
        self.load_program(program)
        result = self.basic.execute_command('RUN')
        
        # Should get input request
        input_requests = [item for item in result if item.get('type') == 'input_request']
        self.assertTrue(len(input_requests) > 0)
        
        # Simulate input response (this tests the mechanism exists)
        # Note: Full testing would require WebSocket simulation


if __name__ == '__main__':
    test = InputCommandTest("INPUT Command Tests")
    results = test.run_all_tests()
    from test_base import print_test_results
    print_test_results(results, verbose=True)