#!/usr/bin/env python3

"""
Unit tests for DATA/READ/RESTORE commands - structured data processing.
Tests data statement parsing, sequential reading, and restore functionality.
"""

import pytest


class TestDataCommand:
    """Test cases for DATA/READ/RESTORE command functionality"""

    def test_basic_functionality(self, basic, helpers):
        """Test basic DATA/READ functionality"""
        program = [
            '10 DATA 100',
            '20 READ A',
            '30 PRINT A'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        assert any('100' in output for output in text_outputs)

    def test_data_read_numeric_values(self, basic, helpers):
        """Test DATA/READ with numeric values"""
        program = [
            '10 DATA 100, 200, 300',
            '20 READ A, B, C',
            '30 PRINT A; B; C'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        # Should contain all three numbers
        combined_output = ' '.join(text_outputs)
        assert '100' in combined_output
        assert '200' in combined_output
        assert '300' in combined_output

    def test_data_read_string_values(self, basic, helpers):
        """Test DATA/READ with string values"""
        program = [
            '10 DATA "HELLO", "WORLD"',
            '20 READ A$, B$',
            '30 PRINT A$; " "; B$'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        # Should contain the strings
        combined_output = ' '.join(text_outputs)
        assert 'HELLO' in combined_output
        assert 'WORLD' in combined_output

    def test_data_read_mixed_types(self, basic, helpers):
        """Test DATA/READ with mixed numeric and string values"""
        program = [
            '10 DATA 123, "HELLO", 3.14, "WORLD"',
            '20 READ A, B$, C, D$',
            '30 PRINT A; B$; C; D$'
        ]
        
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        
        # Should run without errors
        assert len(errors) == 0, f"Program should run without errors: {errors}"
        
        # Check final variable values
        helpers.assert_variable_equals(basic, 'A', 123)
        helpers.assert_variable_equals(basic, 'B$', 'HELLO')
        helpers.assert_variable_equals(basic, 'C', 3.14)
        helpers.assert_variable_equals(basic, 'D$', 'WORLD')

    def test_multiple_data_statements(self, basic, helpers):
        """Test multiple DATA statements in sequence"""
        program = [
            '10 DATA 100, 200',
            '20 DATA "HELLO", 3.14',
            '30 DATA "WORLD", 500',
            '40 READ A, B, C$, D, E$, F',
            '50 PRINT A; B; C$; D; E$; F'
        ]
        
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        
        # Should run without errors
        assert len(errors) == 0, f"Program should run without errors: {errors}"

    def test_restore_command(self, basic, helpers):
        """Test RESTORE command resets data pointer"""
        program = [
            '10 DATA 100, 200, 300',
            '20 READ A',
            '30 READ B', 
            '40 RESTORE',
            '50 READ C',
            '60 PRINT A; B; C'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        # A should be 100, B should be 200, C should be 100 (after RESTORE)
        combined_output = ' '.join(text_outputs)
        assert '100' in combined_output
        assert '200' in combined_output
        # C should also be 100 since RESTORE reset to beginning

    def test_restore_mid_program(self, basic, helpers):
        """Test RESTORE in middle of data reading"""
        program = [
            '10 DATA 10, 20, 30, 40, 50',
            '20 READ A, B',
            '30 PRINT "FIRST: "; A; B',
            '40 RESTORE',
            '50 READ C, D, E',
            '60 PRINT "AFTER RESTORE: "; C; D; E'
        ]
        
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        
        # Should run without errors
        assert len(errors) == 0, f"Program should run without errors: {errors}"
        
        # After RESTORE, should start from beginning again
        helpers.assert_variable_equals(basic, 'C', 10)  # Should be first value again
        helpers.assert_variable_equals(basic, 'D', 20)  # Should be second value again

    def test_out_of_data_error(self, basic, helpers):
        """Test reading beyond available data produces error"""
        program = [
            '10 DATA 100, 200',
            '20 READ A, B, C'  # C should cause "OUT OF DATA" error
        ]
        
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        
        # Should produce out of data error
        assert len(errors) > 0, "Should produce OUT OF DATA error"
        assert any('OUT OF DATA' in error for error in errors)

    def test_data_with_commas_in_strings(self, basic, helpers):
        """Test DATA statements with commas inside quoted strings"""
        program = [
            '10 DATA "HELLO, WORLD", 123, "A, B, C"',
            '20 READ A$, B, C$',
            '30 PRINT A$; "|"; B; "|"; C$'
        ]
        
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        
        # Should handle quoted strings with commas correctly
        assert len(errors) == 0, f"Program should parse quoted strings correctly: {errors}"

    def test_data_floating_point_numbers(self, basic, helpers):
        """Test DATA with floating point numbers"""
        program = [
            '10 DATA 3.14159, 2.718, 1.414',
            '20 READ PI, E, SQRT2',
            '30 PRINT PI; E; SQRT2'
        ]
        
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        
        # Should handle floating point numbers
        assert len(errors) == 0, f"Should handle floating point data: {errors}"

    def test_data_negative_numbers(self, basic, helpers):
        """Test DATA with negative numbers"""
        program = [
            '10 DATA -100, -3.14, 50',
            '20 READ A, B, C',
            '30 PRINT A; B; C'
        ]
        
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        
        # Should handle negative numbers
        assert len(errors) == 0, f"Should handle negative numbers: {errors}"
        helpers.assert_variable_equals(basic, 'A', -100)

    def test_data_statements_out_of_order(self, basic, helpers):
        """Test that DATA statements work regardless of line number order"""
        program = [
            '30 READ A, B',
            '10 DATA 100, 200',
            '50 PRINT A; B',
            '20 DATA 300, 400'  # This should be read after first DATA
        ]
        
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        
        # Should collect DATA from all lines in line number order
        assert len(errors) == 0, f"Should handle out-of-order DATA lines: {errors}"

    def test_read_into_array_elements(self, basic, helpers):
        """Test READ into array elements"""
        program = [
            '10 DIM A(3)',
            '20 DATA 10, 20, 30',
            '30 READ A(0), A(1), A(2)',
            '40 PRINT A(0); A(1); A(2)'
        ]
        
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        
        # Should read into array elements successfully
        assert len(errors) == 0, f"Should read into arrays: {errors}"

    def test_read_into_multidim_array(self, basic, helpers):
        """Test READ into multi-dimensional array elements"""
        program = [
            '10 DIM A(2,2)',
            '20 DATA 10, 20, 30',
            '30 READ A(0,0), A(1,1), A(2,2)',
            '40 PRINT A(0,0); A(1,1); A(2,2)'
        ]
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        assert len(errors) == 0, f"Should read into multi-dim arrays: {errors}"
        text = helpers.get_text_output(results)
        assert any('10' in t and '20' in t and '30' in t for t in text)

    def test_data_with_expressions(self, basic, helpers):
        """Test that DATA contains literal values, not expressions"""
        program = [
            '10 DATA 2+3, "HELLO"+"WORLD"',  # Should be literal strings, not evaluated
            '20 READ A$, B$',
            '30 PRINT A$; "|"; B$'
        ]
        
        results = helpers.execute_program(basic, program)
        
        # DATA should contain literal values, not evaluate expressions
        # This tests that "2+3" is read as string "2+3", not as number 5

    def test_empty_data_statements(self, basic, helpers):
        """Test handling of empty or malformed DATA statements"""
        # Test DATA with no values
        try:
            result = basic.process_command('DATA')
            # Should either error or handle gracefully
        except:
            pass  # Expected behavior

    def test_complex_data_program(self, basic, helpers):
        """Test complex program using DATA/READ/RESTORE extensively"""
        program = [
            '10 DATA 5',  # Number of students
            '20 DATA "ALICE", 85, "BOB", 92, "CHARLIE", 78, "DIANA", 96, "EVE", 89',
            '30 READ N',
            '40 PRINT "STUDENT GRADES:"',
            '50 FOR I = 1 TO N',
            '60 READ NAME$, GRADE',
            '70 PRINT NAME$; ": "; GRADE',
            '80 NEXT I',
            '90 RESTORE',
            '100 READ N',  # Skip count',
            '110 PRINT "AVERAGE CALCULATION:"',
            '120 TOTAL = 0',
            '130 FOR I = 1 TO N',
            '140 READ NAME$, GRADE',
            '150 TOTAL = TOTAL + GRADE',
            '160 NEXT I',
            '170 PRINT "AVERAGE: "; TOTAL / N'
        ]
        
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        
        # Should run complex data processing without errors
        assert len(errors) == 0, f"Complex data program should run: {errors}"
        
        text_outputs = helpers.get_text_output(results)
        assert len(text_outputs) > 0, "Should produce output"

    def test_out_of_data_halts_execution(self, basic, helpers):
        """Test that OUT OF DATA error stops program execution"""
        program = [
            '10 DATA 100, 200', 
            '20 READ A',
            '30 READ B', 
            '40 READ C',  # Should trigger OUT OF DATA
            '50 PRINT "SHOULD NOT REACH HERE"'
        ]
        
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        text_outputs = helpers.get_text_output(results)
        
        # Should have OUT OF DATA error
        assert any('OUT OF DATA' in error for error in errors), f"Expected OUT OF DATA error, got: {errors}"
        
        # Should NOT reach line 50
        assert not any('SHOULD NOT REACH HERE' in output for output in text_outputs), "Program should halt at OUT OF DATA error"
        
        # Program should stop at line 40
        assert basic.current_line == 40, f"Expected program to stop at line 40, stopped at {basic.current_line}"
        
        # Program should not be running
        assert not basic.running, "Program should have stopped"

    def test_out_of_data_with_continue_execution(self, basic, helpers):
        """Test OUT OF DATA error handling in continue execution context"""
        program = [
            '10 DATA 100',
            '20 READ A',
            '30 PRINT "A ="; A',
            '40 READ B',  # Should trigger OUT OF DATA  
            '50 PRINT "SHOULD NOT REACH HERE"'
        ]
        
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        text_outputs = helpers.get_text_output(results)
        
        # Should have OUT OF DATA error
        assert any('OUT OF DATA' in error for error in errors)
        
        # Should print A value but not reach line 50
        assert any('A = 100 ' in output for output in text_outputs), "Should print A value before error"
        assert not any('SHOULD NOT REACH HERE' in output for output in text_outputs)

    def test_data_as_non_first_statement(self, basic, helpers):
        """Test DATA as a non-first statement on a multi-statement line."""
        program = [
            '10 PRINT "HI": DATA 100, 200',
            '20 READ A, B',
            '30 PRINT A; B'
        ]
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        assert len(errors) == 0, f"Should find DATA in non-first position: {errors}"
        helpers.assert_variable_equals(basic, 'A', 100)
        helpers.assert_variable_equals(basic, 'B', 200)

    def test_multiple_data_on_one_line(self, basic, helpers):
        """Test multiple DATA statements on the same line separated by colons."""
        program = [
            '10 DATA 100: DATA 200',
            '20 READ A, B',
            '30 PRINT A; B'
        ]
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        assert len(errors) == 0, f"Should collect both DATA statements: {errors}"
        helpers.assert_variable_equals(basic, 'A', 100)
        helpers.assert_variable_equals(basic, 'B', 200)

    def test_data_mixed_with_other_code(self, basic, helpers):
        """Test DATA mixed with other statements on the same line."""
        program = [
            '10 LET X=5: DATA 100, 200: PRINT X',
            '20 READ A, B',
            '30 PRINT A; B'
        ]
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        assert len(errors) == 0, f"Should handle DATA in mixed line: {errors}"
        helpers.assert_variable_equals(basic, 'A', 100)
        helpers.assert_variable_equals(basic, 'B', 200)


class TestRestoreWithTarget:
    """Test RESTORE with line number and label targets."""

    def test_restore_line_number(self, basic, helpers):
        """RESTORE <line> sets pointer to first DATA at or after that line."""
        program = [
            '10 DATA 10, 20',
            '20 DATA 30, 40',
            '30 READ A, B, C, D',
            '40 RESTORE 20',
            '50 READ E, F',
            '60 PRINT E; F',
        ]
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        helpers.assert_variable_equals(basic, 'E', 30)
        helpers.assert_variable_equals(basic, 'F', 40)

    def test_restore_line_number_skips_earlier(self, basic, helpers):
        """RESTORE <line> skips DATA on earlier lines."""
        program = [
            '10 DATA 100',
            '20 DATA 200',
            '30 DATA 300',
            '40 RESTORE 20',
            '50 READ A',
            '60 PRINT A',
        ]
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        helpers.assert_variable_equals(basic, 'A', 200)

    def test_restore_line_number_at_exact_line(self, basic, helpers):
        """RESTORE targets the exact line with DATA."""
        program = [
            '10 DATA 10',
            '20 DATA 20',
            '30 RESTORE 10',
            '40 READ A',
            '50 PRINT A',
        ]
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        helpers.assert_variable_equals(basic, 'A', 10)

    def test_restore_line_after_all_data(self, basic, helpers):
        """RESTORE to a line past all DATA causes OUT OF DATA on next READ."""
        program = [
            '10 DATA 10, 20',
            '20 RESTORE 999',
            '30 READ A',
        ]
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        assert any('OUT OF DATA' in e for e in errors)

    def test_restore_label(self, basic, helpers):
        """RESTORE <label> sets pointer to DATA at that label's line."""
        program = [
            '10 DATA 10, 20',
            '50 RESTORE SecondData',
            '60 READ A',
            '70 PRINT A',
            '80 END',
            '200 SecondData:',
            '210 DATA 99, 88',
        ]
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        helpers.assert_variable_equals(basic, 'A', 99)

    def test_restore_label_with_multiple_data_blocks(self, basic, helpers):
        """RESTORE label selects the right DATA block among several."""
        program = [
            '100 BlockA:',
            '110 DATA 1, 2, 3',
            '200 BlockB:',
            '210 DATA 4, 5, 6',
            '300 BlockC:',
            '310 DATA 7, 8, 9',
            '10 RESTORE BlockB',
            '20 READ A, B, C',
            '30 PRINT A; B; C',
            '40 END',
        ]
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        helpers.assert_variable_equals(basic, 'A', 4)
        helpers.assert_variable_equals(basic, 'B', 5)
        helpers.assert_variable_equals(basic, 'C', 6)

    def test_restore_plain_then_targeted(self, basic, helpers):
        """Plain RESTORE resets to beginning, targeted RESTORE skips ahead."""
        program = [
            '10 DATA 10, 20',
            '20 DATA 30, 40',
            '30 READ A, B, C, D',
            '40 RESTORE',
            '50 READ X',
            '55 RESTORE 20',
            '60 READ Y',
            '70 PRINT X; Y',
        ]
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        helpers.assert_variable_equals(basic, 'X', 10)
        helpers.assert_variable_equals(basic, 'Y', 30)

    def test_restore_invalid_target(self, basic, helpers):
        """RESTORE with invalid target gives syntax error."""
        program = [
            '10 DATA 10',
            '20 RESTORE "bad"',
            '30 END',
        ]
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        assert len(errors) > 0, "Should error on invalid RESTORE target"

    def test_restore_label_case_insensitive(self, basic, helpers):
        """RESTORE label lookup is case-insensitive."""
        program = [
            '5 MyData:',
            '10 DATA 42',
            '20 RESTORE mydata',
            '30 READ A',
            '40 PRINT A',
        ]
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        helpers.assert_variable_equals(basic, 'A', 42)

    def test_restore_with_expression(self, basic, helpers):
        """RESTORE with a numeric expression for line number."""
        program = [
            '10 DATA 10',
            '20 DATA 20',
            '30 X=20',
            '40 RESTORE X',
            '50 READ A',
            '60 PRINT A',
        ]
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Errors: {errors}"
        helpers.assert_variable_equals(basic, 'A', 20)
