#!/usr/bin/env python3

"""
Unit tests for INKEY$ command - non-blocking keyboard input functionality.
Tests key buffer management and integration with web interface.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from test_base import BaseTestCase


class InkeyCommandTest(BaseTestCase):
    """Test cases for INKEY$ function functionality"""

    def test_basic_functionality(self):
        """Test basic INKEY$ function functionality"""
        # INKEY$ should return empty string when no keys in buffer
        self.assert_text_output('PRINT INKEY$', '')

    def test_inkey_empty_buffer(self):
        """Test INKEY$ with empty key buffer"""
        # Clear any existing keys
        self.basic.key_buffer = []
        
        # Should return empty string
        result = self.basic.execute_command('PRINT INKEY$')
        self.assertTrue(any(item.get('text') == '' for item in result if item.get('type') == 'text'))

    def test_inkey_with_keys_in_buffer(self):
        """Test INKEY$ with keys in buffer"""
        # Add keys to buffer manually
        self.basic.key_buffer = ['A', 'B', 'C']
        
        # First call should return 'A'
        result1 = self.basic.execute_command('PRINT INKEY$')
        self.assertTrue(any('A' in item.get('text', '') for item in result1 if item.get('type') == 'text'))
        
        # Second call should return 'B'
        result2 = self.basic.execute_command('PRINT INKEY$')
        self.assertTrue(any('B' in item.get('text', '') for item in result2 if item.get('type') == 'text'))
        
        # Third call should return 'C'
        result3 = self.basic.execute_command('PRINT INKEY$')
        self.assertTrue(any('C' in item.get('text', '') for item in result3 if item.get('type') == 'text'))
        
        # Fourth call should return empty string
        result4 = self.basic.execute_command('PRINT INKEY$')
        self.assertTrue(any(item.get('text') == '' for item in result4 if item.get('type') == 'text'))

    def test_inkey_variable_assignment(self):
        """Test assigning INKEY$ result to variable"""
        # Add key to buffer
        self.basic.key_buffer = ['X']
        
        # Assign to variable
        self.basic.execute_command('K$ = INKEY$')
        self.assert_variable_equals('K$', 'X')

    def test_inkey_in_if_statement(self):
        """Test INKEY$ in conditional statements"""
        # Test with empty buffer
        result = self.basic.execute_command('IF INKEY$ = "" THEN PRINT "NO KEY"')
        self.assertTrue(any('NO KEY' in item.get('text', '') for item in result if item.get('type') == 'text'))
        
        # Test with key in buffer
        self.basic.key_buffer = ['Y']
        result = self.basic.execute_command('IF INKEY$ <> "" THEN PRINT "KEY PRESSED"')
        self.assertTrue(any('KEY PRESSED' in item.get('text', '') for item in result if item.get('type') == 'text'))

    def test_inkey_in_loop(self):
        """Test INKEY$ in a loop context"""
        program = [
            '10 FOR I = 1 TO 3',
            '20 K$ = INKEY$',
            '30 IF K$ <> "" THEN PRINT "KEY: "; K$',
            '40 NEXT I'
        ]
        
        # Add some keys to buffer
        self.basic.key_buffer = ['1', '2']
        
        results = self.execute_program(program)
        
        # Should have some output
        text_outputs = self.get_text_output(results)
        errors = self.get_error_messages(results)
        
        # Should run without errors
        self.assertEqual(len(errors), 0, f"Program should run without errors: {errors}")

    def test_inkey_buffer_management(self):
        """Test that INKEY$ properly manages the key buffer"""
        # Start with known state
        self.basic.key_buffer = ['A', 'B', 'C']
        initial_length = len(self.basic.key_buffer)
        
        # Call INKEY$ - should remove one key
        self.basic.execute_command('K$ = INKEY$')
        self.assertEqual(len(self.basic.key_buffer), initial_length - 1)
        
        # Call again - should remove another key
        self.basic.execute_command('K$ = INKEY$')
        self.assertEqual(len(self.basic.key_buffer), initial_length - 2)

    def test_inkey_with_parentheses(self):
        """Test INKEY$() syntax variation"""
        # Add key to buffer
        self.basic.key_buffer = ['Z']
        
        # Test with parentheses
        result = self.basic.execute_command('PRINT INKEY$()')
        self.assertTrue(any('Z' in item.get('text', '') for item in result if item.get('type') == 'text'))

    def test_inkey_special_characters(self):
        """Test INKEY$ with special characters"""
        special_chars = [' ', '!', '@', '#', '$', '%']
        
        for char in special_chars:
            self.basic.key_buffer = [char]
            self.basic.execute_command('K$ = INKEY$')
            self.assert_variable_equals('K$', char)

    def test_inkey_in_program_context(self):
        """Test INKEY$ in a realistic program scenario"""
        program = [
            '10 PRINT "PRESS ANY KEY (OR WAIT FOR TIMEOUT)..."',
            '20 FOR I = 1 TO 5',
            '30 K$ = INKEY$',
            '40 IF K$ <> "" THEN PRINT "YOU PRESSED: "; K$: GOTO 60',
            '50 PRINT "LOOP "; I; " - NO KEY PRESSED"',
            '55 NEXT I',
            '60 PRINT "DONE!"'
        ]
        
        # Test with no key pressed
        self.basic.key_buffer = []
        results1 = self.execute_program(program)
        text_outputs1 = self.get_text_output(results1)
        
        # Should have loop messages
        loop_messages = [output for output in text_outputs1 if 'LOOP' in output]
        self.assertTrue(len(loop_messages) > 0, "Should have loop iteration messages")
        
        # Test with key pressed early
        self.basic.execute_command('NEW')  # Clear program state
        self.load_program(program)
        self.basic.key_buffer = ['Q']
        results2 = self.basic.execute_command('RUN')
        text_outputs2 = self.get_text_output(results2)
        
        # Should have the key press message
        key_press_messages = [output for output in text_outputs2 if 'YOU PRESSED' in output]
        self.assertTrue(len(key_press_messages) > 0, "Should detect key press")

    def test_inkey_multiple_calls(self):
        """Test multiple consecutive INKEY$ calls"""
        # Fill buffer with multiple keys
        keys = ['Q', 'W', 'E', 'R', 'T', 'Y']
        self.basic.key_buffer = keys.copy()
        
        # Call INKEY$ multiple times in one statement
        result = self.basic.execute_command('PRINT INKEY$; INKEY$; INKEY$')
        
        # Should have consumed multiple keys
        self.assertTrue(len(self.basic.key_buffer) < len(keys))

    def test_inkey_case_sensitivity(self):
        """Test INKEY$ case sensitivity"""
        # Test lowercase and uppercase
        test_cases = ['a', 'A', 'z', 'Z']
        
        for char in test_cases:
            self.basic.key_buffer = [char]
            self.basic.execute_command('K$ = INKEY$')
            self.assert_variable_equals('K$', char)
            
            # Buffer should be empty after retrieval
            self.assertEqual(len(self.basic.key_buffer), 0)

    def test_inkey_numeric_keys(self):
        """Test INKEY$ with numeric key input"""
        numeric_keys = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        
        for key in numeric_keys:
            self.basic.key_buffer = [key]
            result = self.basic.execute_command('PRINT INKEY$')
            self.assertTrue(any(key in item.get('text', '') for item in result if item.get('type') == 'text'))

    def test_inkey_empty_after_clear(self):
        """Test INKEY$ returns empty after buffer is manually cleared"""
        # Add keys then clear
        self.basic.key_buffer = ['A', 'B', 'C']
        self.basic.key_buffer.clear()
        
        # Should return empty
        result = self.basic.execute_command('PRINT INKEY$')
        self.assertTrue(any(item.get('text') == '' for item in result if item.get('type') == 'text'))


if __name__ == '__main__':
    test = InkeyCommandTest("INKEY$ Command Tests")
    results = test.run_all_tests()
    from test_base import print_test_results
    print_test_results(results, verbose=True)