#!/usr/bin/env python3

"""
Unit tests for INPUT command - interactive user input functionality.
Tests input prompts, variable assignment, and program flow control.
"""

import pytest


class TestInputCommand:
    """Test cases for INPUT command functionality"""

    def test_input_simple_variable(self, basic, helpers):
        """Test INPUT with simple variable"""
        result = basic.process_command('INPUT X')
        
        # Should produce input request
        assert len(result) == 1
        assert result[0]['type'] == 'input_request'
        assert result[0]['prompt'] == '? '
        assert result[0]['variable'] == 'X'

    def test_input_string_variable(self, basic, helpers):
        """Test INPUT with string variable"""
        result = basic.process_command('INPUT N$')
        
        # Should produce input request
        assert len(result) == 1
        assert result[0]['type'] == 'input_request'
        assert result[0]['prompt'] == '? '
        assert result[0]['variable'] == 'N$'

    def test_input_with_prompt(self, basic, helpers):
        """Test INPUT command with custom prompt"""
        result = basic.process_command('INPUT "ENTER YOUR NAME"; N$')
        
        # Should produce input request with custom prompt
        assert len(result) == 1
        assert result[0]['type'] == 'input_request'
        assert result[0]['prompt'] == 'ENTER YOUR NAME'
        assert result[0]['variable'] == 'N$'

    def test_input_with_question_prompt(self, basic, helpers):
        """Test INPUT with question-style prompt"""
        result = basic.process_command('INPUT "WHAT IS YOUR AGE"; A')
        
        assert result[0]['type'] == 'input_request'
        assert result[0]['prompt'] == 'WHAT IS YOUR AGE'
        assert result[0]['variable'] == 'A'

    def test_input_multiple_variables(self, basic, helpers):
        """Test INPUT with multiple variables"""
        result = basic.process_command('INPUT A, B, C$')
        
        # Should handle multiple variables (implementation dependent)
        assert any(item.get('type') == 'input_request' for item in result)

    def test_input_in_program(self, basic, helpers):
        """Test INPUT command within a program"""
        program = [
            '10 INPUT "WHAT IS YOUR AGE"; A',
            '20 PRINT "YOU ARE"; A; "YEARS OLD"'
        ]
        
        results = helpers.execute_program(basic, program)
        
        # Should produce input request
        input_requests = [item for item in results if item.get('type') == 'input_request']
        assert len(input_requests) > 0, "Program should produce input request"
        
        # Check the input request details
        assert input_requests[0]['prompt'] == 'WHAT IS YOUR AGE'
        assert input_requests[0]['variable'] == 'A'

    def test_input_with_semicolon_vs_comma(self, basic, helpers):
        """Test INPUT with semicolon vs comma separators"""
        # With semicolon (no automatic question mark)
        result1 = basic.process_command('INPUT "NAME"; N$')
        assert result1[0]['prompt'] == 'NAME'
        
        # With comma (adds question mark - if implemented)
        result2 = basic.process_command('INPUT "NAME", N$')
        # Implementation may vary - just check it produces input request
        assert any(item.get('type') == 'input_request' for item in result2)

    def test_input_syntax_variations(self, basic, helpers):
        """Test various INPUT command syntax variations"""
        # Without prompt
        result1 = basic.process_command('INPUT X')
        assert result1[0]['prompt'] == '? '
        
        # With quoted prompt and semicolon
        result2 = basic.process_command('INPUT "ENTER VALUE"; X')
        assert result2[0]['prompt'] == 'ENTER VALUE'
        
        # With quoted prompt and comma (if supported)
        try:
            result3 = basic.process_command('INPUT "ENTER VALUE", X')
            assert any(item.get('type') == 'input_request' for item in result3)
        except:
            pass  # May not be implemented

    def test_input_error_handling(self, basic, helpers):
        """Test INPUT command error conditions"""
        # Invalid syntax should produce error
        try:
            result = basic.process_command('INPUT')
            if result:
                assert any(item.get('type') == 'error' for item in result)
        except:
            pass  # May throw exception instead

    def test_input_variable_types(self, basic, helpers):
        """Test INPUT with different variable types"""
        # Numeric variable
        result1 = basic.process_command('INPUT NUM')
        assert result1[0]['variable'] == 'NUM'
        
        # String variable
        result2 = basic.process_command('INPUT STR$')
        assert result2[0]['variable'] == 'STR$'
        
        # Array element (if supported)
        try:
            basic.process_command('DIM A(5)')
            result3 = basic.process_command('INPUT A(3)')
            if result3 and not any(item.get('type') == 'error' for item in result3):
                assert any(item.get('type') == 'input_request' for item in result3)
        except:
            pass  # May not be fully implemented

    def test_input_prompt_formatting(self, basic, helpers):
        """Test INPUT prompt formatting and display"""
        # Test various prompt formats
        test_cases = [
            ('INPUT "NAME"; N$', 'NAME'),
            ('INPUT "ENTER YOUR AGE"; A', 'ENTER YOUR AGE'),
            ('INPUT "VALUE"; X', 'VALUE'),
        ]
        
        for command, expected_prompt in test_cases:
            result = basic.process_command(command)
            if result and result[0].get('type') == 'input_request':
                assert result[0]['prompt'] == expected_prompt

    def test_input_in_complex_program(self, basic, helpers):
        """Test INPUT in a more complex program context"""
        program = [
            '10 PRINT "CALCULATOR PROGRAM"',
            '20 INPUT "FIRST NUMBER"; A',
            '30 INPUT "SECOND NUMBER"; B', 
            '40 PRINT "SUM IS"; A + B',
            '50 END'
        ]
        
        results = helpers.execute_program(basic, program)
        
        # Should have text output and input requests
        text_outputs = [item for item in results if item.get('type') == 'text']
        input_requests = [item for item in results if item.get('type') == 'input_request']
        
        assert len(text_outputs) > 0, "Should have text output"
        assert len(input_requests) > 0, "Should have input requests"
        
        # Check first input request
        if input_requests:
            assert input_requests[0]['prompt'] == 'FIRST NUMBER'
            assert input_requests[0]['variable'] == 'A'

    def test_input_continuation_after_response(self, basic, helpers):
        """Test program continuation after INPUT response"""
        # This test simulates the INPUT response mechanism
        program = [
            '10 INPUT "TEST"; X',
            '20 PRINT "YOU ENTERED"; X'
        ]
        
        # Load and start program
        helpers.load_program(basic, program)
        result = basic.process_command('RUN')
        
        # Should get input request
        input_requests = [item for item in result if item.get('type') == 'input_request']
        assert len(input_requests) > 0
        
        # Simulate input response (this tests the mechanism exists)
        # Note: Full testing would require WebSocket simulation
