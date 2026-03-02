#!/usr/bin/env python3

"""
Comprehensive tests for command parsing edge cases.
Tests the parsing logic that handles complex syntax scenarios.
"""

import pytest


class TestCommandParsing:
    """Test cases for command parsing edge cases and complex syntax"""

    def test_basic_functionality(self, basic, helpers):
        """Test basic command parsing functionality"""
        result = basic.process_command('PRINT "HELLO"')
        text_output = helpers.get_text_output(result)
        assert text_output == ['HELLO']

    def test_multi_statement_with_quoted_colons(self, basic, helpers):
        """Test multi-statement lines where quoted strings contain colons"""
        # This was a major bug we fixed - colons inside quotes should not split statements
        program = [
            '10 PRINT "TIME: 12:30"; ": END"'
        ]
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        # Should print the full string with colons (may have extra spaces from PRINT semicolon handling)
        assert any('TIME: 12:30' in output and ': END' in output for output in text_outputs)

    def test_multi_statement_complex_parsing(self, basic, helpers):
        """Test complex multi-statement parsing with quotes and colons"""
        # Test the exact pattern that was failing before our fix
        basic.variables['K$'] = 'X'
        
        # This should split into two statements properly
        result = basic.process_line('PRINT "YOU PRESSED: "; K$: GOTO 100')
        
        # Should contain both a text output and a jump
        has_text = any(item.get('type') == 'text' for item in result)
        has_jump = any(item.get('type') == 'jump' for item in result)
        
        assert has_text, "Should have text output from PRINT"
        assert has_jump, "Should have jump from GOTO"

    def test_string_variables_in_expressions(self, basic, helpers):
        """Test string variables with $ in complex expressions"""
        # Set up string variables
        basic.variables['NAME$'] = 'ALICE'
        basic.variables['KEY$'] = ''
        
        # Test in IF conditions
        result = basic.process_command('IF NAME$ = "ALICE" THEN PRINT "MATCH"')
        assert any('MATCH' in str(item) for item in result)
        
        # Test empty string comparison
        result = basic.process_command('IF KEY$ <> "" THEN PRINT "NOT EMPTY"')
        # Should not print anything since KEY$ is empty
        assert not any('NOT EMPTY' in str(item) for item in result)

    def test_complex_print_parsing(self, basic, helpers):
        """Test PRINT command with complex separator combinations"""
        # Test semicolon concatenation
        basic.variables['A'] = 5
        basic.variables['B$'] = 'TEST'
        
        result = basic.process_command('PRINT "A="; A; " B$="; B$')
        text = helpers.get_text_output(result)[0] if result else ""
        
        # Should concatenate properly with spaces
        assert 'A=' in text
        assert '5' in text
        assert 'B$=' in text
        assert 'TEST' in text

    def test_parentheses_in_commands(self, basic, helpers):
        """Test commands with complex parentheses structures"""
        # Set graphics mode first
        basic.process_command('PMODE 4,1')
        
        # Graphics commands with coordinates
        result = basic.process_command('PSET(100,200)')
        graphics_output = helpers.get_graphics_output(result)
        assert len(graphics_output) > 0, "PSET command should produce graphics output"

        result = basic.process_command('LINE(10,20)-(30,40)')
        graphics_output = helpers.get_graphics_output(result)
        assert len(graphics_output) > 0, "LINE command should produce graphics output"

        result = basic.process_command('CIRCLE(128,96),25')
        graphics_output = helpers.get_graphics_output(result)
        assert len(graphics_output) > 0, "CIRCLE command should produce graphics output"
        
        # Function calls with nested parentheses
        basic.variables['S$'] = 'HELLO'
        result = basic.process_command('PRINT LEFT$(RIGHT$(S$,4),2)')
        # Should work with nested function calls
        assert len(result) > 0

    def test_expression_parsing_precedence(self, basic, helpers):
        """Test mathematical expression parsing with operator precedence"""
        # Test basic precedence
        result = basic.process_command('PRINT 2 + 3 * 4')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 14 ']  # Should be 14, not 20
        result = basic.process_command('PRINT (2 + 3) * 4')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 20 ']  # Should be 20

        # Test with variables
        basic.variables['X'] = 2
        basic.variables['Y'] = 3
        result = basic.process_command('PRINT X + Y * 4')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 14 ']

    def test_string_vs_numeric_contexts(self, basic, helpers):
        """Test parsing in string vs numeric contexts"""
        # Numeric context
        basic.variables['A'] = 5
        result = basic.process_command('PRINT A + 10')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 15 ']

        # String context
        basic.variables['A$'] = 'HELLO'
        result = basic.process_command('PRINT A$')
        text_output = helpers.get_text_output(result)
        assert text_output == ['HELLO']
        
        # Mixed contexts should handle properly
        result = basic.process_command('PRINT A$; " "; A')
        text = helpers.get_text_output(result)[0] if result else ""
        assert 'HELLO' in text
        assert '5' in text

    def test_whitespace_handling(self, basic, helpers):
        """Test various whitespace scenarios in parsing"""
        # Test extra spaces
        result = basic.process_command('PRINT    "HELLO"   ')
        text_output = helpers.get_text_output(result)
        assert text_output == ['HELLO']
        
        # Test tabs (if supported)
        result = basic.process_command('PRINT\t"WORLD"')
        text_output = helpers.get_text_output(result)
        assert text_output == ['WORLD']
        
        # Test no spaces around operators
        basic.variables['X'] = 10
        result = basic.process_command('PRINT X+5')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 15 ']
        result = basic.process_command('PRINT X + 5')
        text_output = helpers.get_text_output(result)
        assert text_output == [' 15 ']

    def test_line_number_parsing(self, basic, helpers):
        """Test line number parsing in various contexts"""
        # Valid line numbers
        program = [
            '10 PRINT "LINE 10"',
            '100 PRINT "LINE 100"',
            '9999 PRINT "LINE 9999"'
        ]
        
        basic.process_command('NEW')  # Ensure clean state
        helpers.load_program(basic, program)
        assert len(basic.program) == 3, f"Expected 3 program lines, got {len(basic.program)}"
        
        # Test GOTO with line numbers
        result = basic.process_command('GOTO 100')
        assert any(item.get('type') == 'jump' and item.get('line') == 100
                           for item in result)

    def test_error_condition_parsing(self, basic, helpers):
        """Test parsing of malformed commands for proper error handling"""
        # Missing THEN in IF
        helpers.assert_error_output(basic, 'IF X > 5 PRINT "ERROR"')
        
        # Invalid variable names
        try:
            result = basic.process_command('123ABC = 5')
            # Should either error or handle gracefully
        except:
            pass  # Expected

    def test_case_sensitivity(self, basic, helpers):
        """Test case sensitivity/insensitivity in parsing"""
        # BASIC should be case insensitive for keywords
        result = basic.process_command('print "hello"')
        text_output = helpers.get_text_output(result)
        assert text_output == ['hello']
        result = basic.process_command('PRINT "HELLO"')
        text_output = helpers.get_text_output(result)
        assert text_output == ['HELLO']
        result = basic.process_command('Print "Hello"')
        text_output = helpers.get_text_output(result)
        assert text_output == ['Hello']
        
        # Variables should preserve case in values but be case insensitive in names
        basic.process_command('name$ = "Alice"')
        helpers.assert_variable_equals(basic, 'NAME$', 'Alice')

    def test_complex_for_loop_parsing(self, basic, helpers):
        """Test FOR loop parsing with complex expressions"""
        # Test floating point values
        program = [
            '10 FOR I = 0.1 TO 0.3 STEP 0.1',
            '20 PRINT I',
            '30 NEXT I'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        # Should have outputs for floating point values (precision may affect exact count)
        assert len(text_outputs) >= 2, f"Expected at least 2 outputs, got {len(text_outputs)}: {text_outputs}"

    def test_data_read_parsing(self, basic, helpers):
        """Test DATA/READ statement parsing with various data types"""
        program = [
            '10 DATA 123, "HELLO", 3.14, "WORLD"',
            '20 READ A, B$, C, D$',
            '30 PRINT A; B$; C; D$'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        # Should parse and read mixed data types correctly
        assert len(text_outputs) > 0

    def test_nested_function_calls(self, basic, helpers):
        """Test parsing of nested function calls"""
        basic.variables['TEST$'] = 'ABCDEFGH'
        
        # Test nested string functions
        # Set up test string
        basic.process_command('TEST$ = "HELLO WORLD"')

        result = basic.process_command('PRINT LEFT$(RIGHT$(TEST$,5),3)')
        # Should handle nested function parsing and return output
        assert len(result) > 0
        text_outputs = helpers.get_text_output(result)
        # RIGHT$(TEST$,5) = "WORLD", LEFT$("WORLD",3) = "WOR"
        assert "WOR" in text_outputs

    def test_comment_parsing(self, basic, helpers):
        """Test REM comment parsing and handling"""
        program = [
            '10 REM This is a comment',
            '20 PRINT "AFTER COMMENT"',
            '30 REM Another comment: with colons and "quotes"'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        # Should execute non-comment lines
        assert any('AFTER COMMENT' in output for output in text_outputs)

    def test_multi_line_program_parsing(self, basic, helpers):
        """Test parsing of complete multi-line programs"""
        program = [
            '10 REM COMPLEX PROGRAM TEST',
            '20 FOR I = 1 TO 3',
            '30 IF I = 2 THEN PRINT "MIDDLE": GOTO 50',
            '40 PRINT "VALUE: "; I',
            '50 NEXT I',
            '60 END'
        ]
        
        results = helpers.execute_program(basic, program)
        errors = [item for item in results if item.get('type') == 'error']

        # Should parse and run without syntax errors
        assert len(errors) == 0, f"Program should parse without errors: {errors}"
