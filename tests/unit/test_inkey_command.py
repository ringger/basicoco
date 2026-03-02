#!/usr/bin/env python3

"""
Unit tests for INKEY$ command - non-blocking keyboard input functionality.
Tests key buffer management and integration with web interface.
"""

import pytest


class TestInkeyCommand:
    """Test cases for INKEY$ function functionality"""

    def test_basic_functionality(self, basic, helpers):
        """Test basic INKEY$ function functionality"""
        # INKEY$ should return empty string when no keys in buffer
        result = basic.process_command('PRINT INKEY$')
        text_output = helpers.get_text_output(result)
        assert text_output == ['']

    def test_inkey_empty_buffer(self, basic, helpers):
        """Test INKEY$ with empty key buffer"""
        # Clear any existing keys
        basic.keyboard_buffer = []
        
        # Should return empty string
        result = basic.process_command('PRINT INKEY$')
        assert '' in helpers.get_text_output(result)

    def test_inkey_with_keys_in_buffer(self, basic, helpers):
        """Test INKEY$ with keys in buffer"""
        # Add keys to buffer manually
        basic.keyboard_buffer = ['A', 'B', 'C']

        # First call should return 'A'
        result1 = basic.process_command('PRINT INKEY$')
        assert any('A' in text for text in helpers.get_text_output(result1))

        # Second call should return 'B'
        result2 = basic.process_command('PRINT INKEY$')
        assert any('B' in text for text in helpers.get_text_output(result2))

        # Third call should return 'C'
        result3 = basic.process_command('PRINT INKEY$')
        assert any('C' in text for text in helpers.get_text_output(result3))

        # Fourth call should return empty string
        result4 = basic.process_command('PRINT INKEY$')
        assert '' in helpers.get_text_output(result4)

    def test_inkey_variable_assignment(self, basic, helpers):
        """Test assigning INKEY$ result to variable"""
        # Add key to buffer
        basic.keyboard_buffer = ['X']
        
        # Assign to variable
        basic.process_command('K$ = INKEY$')
        helpers.assert_variable_equals(basic, 'K$', 'X')

    def test_inkey_in_if_statement(self, basic, helpers):
        """Test INKEY$ in conditional statements"""
        # Test with empty buffer
        result = basic.process_command('IF INKEY$ = "" THEN PRINT "NO KEY"')
        assert any('NO KEY' in text for text in helpers.get_text_output(result))

        # Test with key in buffer
        basic.keyboard_buffer = ['Y']
        result = basic.process_command('IF INKEY$ <> "" THEN PRINT "KEY PRESSED"')
        assert any('KEY PRESSED' in text for text in helpers.get_text_output(result))

    def test_inkey_in_loop(self, basic, helpers):
        """Test INKEY$ in a loop context"""
        program = [
            '10 FOR I = 1 TO 3',
            '20 K$ = INKEY$',
            '30 IF K$ <> "" THEN PRINT "KEY: "; K$',
            '40 NEXT I'
        ]
        
        # Add some keys to buffer
        basic.keyboard_buffer = ['1', '2']
        
        results = helpers.execute_program(basic, program)
        
        # Should have some output
        text_outputs = helpers.get_text_output(results)
        errors = helpers.get_error_messages(results)
        
        # Should run without errors
        assert len(errors) == 0, f"Program should run without errors: {errors}"

    def test_inkeyboard_buffer_management(self, basic, helpers):
        """Test that INKEY$ properly manages the key buffer"""
        # Start with known state
        basic.keyboard_buffer = ['A', 'B', 'C']
        initial_length = len(basic.keyboard_buffer)
        
        # Call INKEY$ - should remove one key
        basic.process_command('K$ = INKEY$')
        assert len(basic.keyboard_buffer) == initial_length - 1
        
        # Call again - should remove another key
        basic.process_command('K$ = INKEY$')
        assert len(basic.keyboard_buffer) == initial_length - 2

    def test_inkey_with_parentheses(self, basic, helpers):
        """Test INKEY$() syntax variation"""
        # Add key to buffer
        basic.keyboard_buffer = ['Z']
        
        # Test with parentheses
        result = basic.process_command('PRINT INKEY$()')
        assert any('Z' in text for text in helpers.get_text_output(result))

    def test_inkey_special_characters(self, basic, helpers):
        """Test INKEY$ with special characters"""
        special_chars = [' ', '!', '@', '#', '$', '%']
        
        for char in special_chars:
            basic.keyboard_buffer = [char]
            basic.process_command('K$ = INKEY$')
            helpers.assert_variable_equals(basic, 'K$', char)

    def test_inkey_in_program_context(self, basic, helpers):
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
        basic.keyboard_buffer = []
        results1 = helpers.execute_program(basic, program)
        text_outputs1 = helpers.get_text_output(results1)
        
        # Should have loop messages
        loop_messages = [output for output in text_outputs1 if 'LOOP' in output]
        assert len(loop_messages) > 0, "Should have loop iteration messages"
        
        # Test with key pressed early
        basic.process_command('NEW')  # Clear program state
        helpers.load_program(basic, program)
        basic.keyboard_buffer = ['Q']
        results2 = basic.process_command('RUN')
        text_outputs2 = helpers.get_text_output(results2)
        
        # Should have the key press message
        key_press_messages = [output for output in text_outputs2 if 'YOU PRESSED' in output]
        assert len(key_press_messages) > 0, "Should detect key press"

    def test_inkey_multiple_calls(self, basic, helpers):
        """Test multiple consecutive INKEY$ calls"""
        # Fill buffer with multiple keys
        keys = ['Q', 'W', 'E', 'R', 'T', 'Y']
        basic.keyboard_buffer = keys.copy()
        
        # Call INKEY$ multiple times in one statement
        result = basic.process_command('PRINT INKEY$; INKEY$; INKEY$')
        
        # Should have consumed multiple keys
        assert len(basic.keyboard_buffer) < len(keys)

    def test_inkey_case_sensitivity(self, basic, helpers):
        """Test INKEY$ case sensitivity"""
        # Test lowercase and uppercase
        test_cases = ['a', 'A', 'z', 'Z']
        
        for char in test_cases:
            basic.keyboard_buffer = [char]
            basic.process_command('K$ = INKEY$')
            helpers.assert_variable_equals(basic, 'K$', char)
            
            # Buffer should be empty after retrieval
            assert len(basic.keyboard_buffer) == 0

    def test_inkey_numeric_keys(self, basic, helpers):
        """Test INKEY$ with numeric key input"""
        numeric_keys = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        
        for key in numeric_keys:
            basic.keyboard_buffer = [key]
            result = basic.process_command('PRINT INKEY$')
            assert any(key in text for text in helpers.get_text_output(result))

    def test_inkey_empty_after_clear(self, basic, helpers):
        """Test INKEY$ returns empty after buffer is manually cleared"""
        # Add keys then clear
        basic.keyboard_buffer = ['A', 'B', 'C']
        basic.keyboard_buffer.clear()
        
        # Should return empty
        result = basic.process_command('PRINT INKEY$')
        assert '' in helpers.get_text_output(result)

    def test_function_syntax_variations(self, basic, helpers):
        """Test various function syntax variations across different functions"""
        # Set up test data
        basic.process_command('N = 16')
        basic.process_command('S$ = "HELLO"')
        basic.keyboard_buffer = ['X']
        
        # Test INKEY$ variations (with and without parentheses)
        result1 = basic.process_command('K1$ = INKEY$')
        result2 = basic.process_command('K2$ = INKEY$()')
        # Both should work (though second might be empty if buffer consumed)
        assert len(helpers.get_error_messages(result1)) == 0
        assert len(helpers.get_error_messages(result2)) == 0
        
        # Test mathematical functions (should work with parentheses)
        result = basic.process_command('PRINT SQR(N)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 4 ']
        result = basic.process_command('PRINT ABS(-5)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 5 ']
        result = basic.process_command('PRINT INT(3.7)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 3 ']

        # Test string functions with proper parentheses
        result = basic.process_command('PRINT LEN(S$)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 5 ']
        result = basic.process_command('PRINT ASC("A")')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 65 ']
        result = basic.process_command('PRINT CHR$(65)')
        text_output = helpers.get_text_output(result)
        assert text_output == ['A']
        
        # Test functions in expressions with variables
        result = basic.process_command('PRINT SQR(N) + LEN(S$)')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 9 ']  # 4 + 5 = 9

        # Test nested function syntax
        result = basic.process_command('PRINT LEN(CHR$(65))')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 1 ']  # Length of "A"
        result = basic.process_command('PRINT ASC(CHR$(66))')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 66 ']  # Round trip B
        
        # Test function calls in different contexts
        basic.process_command('RESULT = SQR(N)')
        helpers.assert_variable_equals(basic, 'RESULT', 4)
        
        basic.process_command('LENGTH = LEN(S$)')
        helpers.assert_variable_equals(basic, 'LENGTH', 5)
        
        # Test functions in conditional contexts (IF statements)
        program = [
            '10 N = 16',
            '20 S$ = "HELLO"',
            '30 IF LEN(S$) > 3 THEN PRINT "LONG"',
            '40 IF SQR(N) = 4 THEN PRINT "PERFECT"'
        ]
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        assert 'LONG' in ' '.join(text_outputs)
        assert 'PERFECT' in ' '.join(text_outputs)
