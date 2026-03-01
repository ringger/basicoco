#!/usr/bin/env python3

"""
Unit tests for PRINT command functionality
"""

import pytest


class TestPrintCommand:
    """Test cases for PRINT command"""

    def test_basic_functionality(self, basic, helpers):
        """Test basic PRINT command functionality"""
        result = basic.process_command('PRINT "HELLO"')
        text_output = helpers.get_text_output(result)
        assert text_output == ['HELLO']

    def test_print_string_literal(self, basic, helpers):
        """Test PRINT with string literals"""
        result = basic.process_command('PRINT "TEST STRING"')
        text_output = helpers.get_text_output(result)
        assert text_output == ['TEST STRING']

        result = basic.process_command('PRINT ""')
        text_output = helpers.get_text_output(result)
        assert text_output == ['']

    def test_print_numeric_literal(self, basic, helpers):
        """Test PRINT with numeric literals"""
        result = basic.process_command('PRINT 42')
        text_output = helpers.get_text_output(result)
        assert text_output == ['42']

        result = basic.process_command('PRINT 3.14')
        text_output = helpers.get_text_output(result)
        assert text_output == ['3.14']

        result = basic.process_command('PRINT -7')
        text_output = helpers.get_text_output(result)
        assert text_output == ['-7']

    def test_print_variables(self, basic, helpers):
        """Test PRINT with variables"""
        # Set up variables
        basic.process_command('A = 42')
        basic.process_command('B$ = "HELLO"')
        basic.process_command('C = 3.14')

        # Test printing variables
        result = basic.process_command('PRINT A')
        text_output = helpers.get_text_output(result)
        assert text_output == ['42']

        result = basic.process_command('PRINT B$')
        text_output = helpers.get_text_output(result)
        assert text_output == ['HELLO']

        result = basic.process_command('PRINT C')
        text_output = helpers.get_text_output(result)
        assert text_output == ['3.14']

    def test_print_expressions(self, basic, helpers):
        """Test PRINT with mathematical expressions"""
        result = basic.process_command('PRINT 2 + 3')
        text_output = helpers.get_text_output(result)
        assert text_output == ['5']

        result = basic.process_command('PRINT 10 - 4')
        text_output = helpers.get_text_output(result)
        assert text_output == ['6']

        result = basic.process_command('PRINT 3 * 4')
        text_output = helpers.get_text_output(result)
        assert text_output == ['12']

        result = basic.process_command('PRINT 15 / 3')
        text_output = helpers.get_text_output(result)
        assert text_output == ['5']

    def test_print_concatenated(self, basic, helpers):
        """Test PRINT with semicolons (concatenation)"""
        # This tests the PRINT parsing with multiple items
        result = basic.process_command('PRINT "A"; "B"; "C"')
        assert len(result) > 0
        assert result[0]['type'] == 'text'
        # Semicolons should concatenate without spaces
        assert result[0]['text'] == 'ABC'

    def test_print_with_separators(self, basic, helpers):
        """Test PRINT with commas and semicolons"""
        # Test semicolon separator (no spaces)
        result = basic.process_command('PRINT "A";"B"')
        assert len(result) > 0
        assert result[0]['type'] == 'text'
        assert result[0]['text'] == 'AB'  # Semicolon concatenates without spaces

        # Test comma separator (with spacing)
        result = basic.process_command('PRINT "A","B"')
        assert len(result) > 0
        assert result[0]['type'] == 'text'
        # Comma should add spacing - exact format depends on implementation
        assert 'A' in result[0]['text'] and 'B' in result[0]['text']

    def test_print_empty(self, basic, helpers):
        """Test PRINT with no arguments (blank line)"""
        result = basic.process_command('PRINT')
        assert len(result) > 0
        assert result[0]['type'] == 'text'
        # Should produce empty or whitespace line

    def test_print_in_program(self, basic, helpers):
        """Test PRINT commands within a program"""
        program = [
            '10 PRINT "LINE 1"',
            '20 PRINT "LINE 2"',
            '30 PRINT "LINE 3"'
        ]

        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)

        assert len(text_outputs) >= 3
        assert 'LINE 1' in text_outputs[0]
        assert 'LINE 2' in text_outputs[1]
        assert 'LINE 3' in text_outputs[2]

    def test_print_string_functions(self, basic, helpers):
        """Test PRINT with string functions"""
        # Test LEN function if implemented
        result = basic.process_command('PRINT LEN("HELLO")')
        errors = helpers.get_error_messages(result)
        if not errors:  # Function is implemented
            text_output = helpers.get_text_output(result)
            assert text_output == ['5'], f"LEN function should return 5, got {text_output}"
        else:
            # Function not implemented - verify we get appropriate error
            assert any('LEN' in error or 'FUNCTION' in error for error in errors), \
                   f"Should get appropriate error for unimplemented LEN function: {errors}"

        # Test LEFT$ function if implemented
        result = basic.process_command('PRINT LEFT$("HELLO", 3)')
        errors = helpers.get_error_messages(result)
        if not errors:  # Function is implemented
            text_output = helpers.get_text_output(result)
            assert text_output == ['HEL'], f"LEFT$ function should return 'HEL', got {text_output}"
        else:
            # Function not implemented - verify we get appropriate error
            assert any('LEFT$' in error or 'FUNCTION' in error for error in errors), \
                   f"Should get appropriate error for unimplemented LEFT$ function: {errors}"

    def test_comprehensive_separator_behavior(self, basic, helpers):
        """Test comprehensive PRINT separator behavior with mixed types"""
        # Set up test variables
        basic.process_command('A = 42')
        basic.process_command('B = 3.14')
        basic.process_command('S$ = "HELLO"')
        basic.process_command('T$ = "WORLD"')

        # Test semicolon separator (no spaces - concatenation)
        result = basic.process_command('PRINT "A";"B";"C"')
        assert len(result) > 0 and result[0]['type'] == 'text'
        # Should be "ABC" with no spaces
        assert 'ABC' in result[0]['text']
        
        # Test comma separator (tab spacing)
        result = basic.process_command('PRINT "A","B","C"')
        assert len(result) > 0 and result[0]['type'] == 'text'
        # Should have spacing between items
        output_text = result[0]['text']
        assert 'A' in output_text
        assert 'B' in output_text
        assert 'C' in output_text
        # Test mixed types with semicolons (no spaces)
        result = basic.process_command('PRINT "NUMBER:";A;"!"')
        assert len(result) > 0 and result[0]['type'] == 'text'
        assert 'NUMBER:42!' in result[0]['text']

        # Test mixed types with commas (spacing)
        result = basic.process_command('PRINT "VALUE",A,"DONE"')
        assert len(result) > 0 and result[0]['type'] == 'text'
        output_text = result[0]['text']
        assert 'VALUE' in output_text
        assert '42' in output_text
        assert 'DONE' in output_text
        # Should have spaces/tabs between items
        assert len(output_text) > len('VALUE42DONE')

        # Test string variables with semicolons
        result = basic.process_command('PRINT S$;"!";T$')
        assert len(result) > 0 and result[0]['type'] == 'text'
        assert 'HELLO!WORLD' in result[0]['text']

        # Test mixed variable types with different separators
        result = basic.process_command('PRINT S$;":";A;",";B')
        assert len(result) > 0 and result[0]['type'] == 'text'
        assert 'HELLO:42' in result[0]['text']  # Semicolons concatenate without spaces
        assert '3.14' in result[0]['text']

        # Test complex expression with separators
        result = basic.process_command('PRINT "RESULT:";"(";"A+B=";" ";A+B;")"')
        assert len(result) > 0 and result[0]['type'] == 'text'
        # Should show something like "RESULT:(A+B= 45.14)"
        output_text = result[0]['text']
        assert 'RESULT:' in output_text
        assert '45.14' in output_text

        # Test trailing separator behavior
        result = basic.process_command('PRINT "LINE1";')
        assert len(result) > 0 and result[0]['type'] == 'text'
        # Trailing semicolon should suppress newline (but this might vary by implementation)

        result = basic.process_command('PRINT "LINE2",')
        assert len(result) > 0 and result[0]['type'] == 'text'
        # Trailing comma should position cursor at next tab stop

    def test_advanced_separator_patterns(self, basic, helpers):
        """Test advanced separator patterns and edge cases"""
        # Test alternating separators
        result = basic.process_command('PRINT "A";"B","C";"D"')
        assert len(result) > 0 and result[0]['type'] == 'text'
        output_text = result[0]['text']
        assert 'A' in output_text
        assert 'B' in output_text
        assert 'C' in output_text
        assert 'D' in output_text

        # Test function results with separators
        basic.process_command('X = 16')
        result = basic.process_command('PRINT "SQRT(";X;")=";SQR(X)')
        assert len(result) > 0 and result[0]['type'] == 'text'
        # Semicolons concatenate without spaces
        output_text = result[0]['text']
        assert 'SQRT(' in output_text
        assert '16' in output_text
        assert ')=' in output_text
        assert '4' in output_text

        # Test empty strings with separators
        result = basic.process_command('PRINT "";"";"CONTENT";""')
        assert len(result) > 0 and result[0]['type'] == 'text'
        assert 'CONTENT' in result[0]['text']


class TestPrintOkNotSuppressed:
    """Regression: PRINT "OK" in a program must not be filtered out."""

    def test_print_ok_in_program(self, basic, helpers):
        program = [
            '10 PRINT "OK"',
            '20 END',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert 'OK' in text

    def test_print_ok_immediate(self, basic, helpers):
        result = basic.process_command('PRINT "OK"')
        text = helpers.get_text_output(result)
        assert 'OK' in text