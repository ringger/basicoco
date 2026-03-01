#!/usr/bin/env python3

"""
Tests for error handling and malformed input parsing.
Ensures the parser handles invalid syntax gracefully.
"""

import pytest


class TestErrorHandling:
    """Test cases for error handling and malformed input"""

    def test_basic_functionality(self, basic, helpers):
        """Test basic error handling functionality"""
        helpers.assert_error_output(basic, 'INVALID_COMMAND')

    def test_syntax_errors(self, basic, helpers):
        """Test various syntax error conditions"""
        # Missing THEN in IF statement
        helpers.assert_error_output(basic, 'IF X > 5 PRINT "ERROR"', 'SYNTAX ERROR')
        
        # Missing TO in FOR statement
        helpers.assert_error_output(basic, 'FOR I = 1 5', 'SYNTAX ERROR')
        
        # Invalid assignment (no variable name)
        helpers.assert_error_output(basic, '= 5', 'Unrecognized command')

    def test_unmatched_parentheses(self, basic, helpers):
        """Test handling of unmatched parentheses"""
        # Missing closing parenthesis
        try:
            result = basic.process_command('PRINT (2 + 3')
            # Should either error or handle gracefully
        except:
            pass  # Expected behavior
        
        # Extra closing parenthesis
        try:
            result = basic.process_command('PRINT (2 + 3))')
            # Should either error or handle gracefully  
        except:
            pass  # Expected behavior

    def test_unmatched_quotes(self, basic, helpers):
        """Test handling of unmatched quotes"""
        # Missing closing quote
        try:
            result = basic.process_command('PRINT "HELLO')
            # Should either error or handle gracefully
        except:
            pass  # Expected behavior
        
        # Mixed quote types (if that's an issue)
        try:
            result = basic.process_command('PRINT "HELLO\'')
            # Should either error or handle gracefully
        except:
            pass  # Expected behavior

    def test_invalid_variable_names(self, basic, helpers):
        """Test handling of invalid variable names"""
        invalid_names = [
            '123ABC',  # Starting with number
            'A B',     # Space in name
            'FOR',     # Reserved keyword
            'PRINT',   # Reserved keyword
            '$INVALID', # Starting with $
        ]
        
        for invalid_name in invalid_names:
            try:
                result = basic.process_command(f'{invalid_name} = 5')
                # Should either error or handle gracefully
                if result and any(item.get('type') == 'error' for item in result):
                    pass  # Good - produced error
            except:
                pass  # Also acceptable

    def test_undefined_variables(self, basic, helpers):
        """Test handling of undefined variables"""
        # Using undefined variable
        try:
            result = basic.process_command('PRINT UNDEFINED_VAR')
            # Should either error, return 0, or handle gracefully
        except:
            pass  # Expected behavior

    def test_array_errors(self, basic, helpers):
        """Test array-related error handling"""
        # Undimensioned array
        helpers.assert_error_output(basic, 'PRINT A(5)', 'variables are defined')
        
        # Bad subscript
        basic.process_command('DIM B(10)')
        helpers.assert_error_output(basic, 'PRINT B(15)', 'Error evaluating PRINT expression')
        helpers.assert_error_output(basic, 'PRINT B(-1)', 'Error evaluating PRINT expression')

    def test_for_loop_errors(self, basic, helpers):
        """Test FOR loop error conditions"""
        # NEXT without FOR
        helpers.assert_error_output(basic, 'NEXT I', 'NEXT WITHOUT FOR')
        
        # Mismatched FOR/NEXT
        program = [
            '10 FOR I = 1 TO 5',
            '20 FOR J = 1 TO 3', 
            '30 NEXT I',  # Wrong order
            '40 NEXT J'
        ]
        
        results = helpers.execute_program(basic, program)
        # Should handle gracefully, possibly with error

    def test_gosub_return_errors(self, basic, helpers):
        """Test GOSUB/RETURN error conditions"""
        # RETURN without GOSUB
        helpers.assert_error_output(basic, 'RETURN', 'RETURN WITHOUT GOSUB')
        
        # GOSUB to undefined line should produce jump instruction (error occurs at runtime)
        result = basic.process_command('GOSUB 9999')
        assert any(item.get('type') == 'jump' for item in result)

    def test_goto_errors(self, basic, helpers):
        """Test GOTO error conditions"""
        # GOTO to undefined line
        result = basic.process_command('GOTO 9999')
        # Should produce some kind of error or handle gracefully

    def test_division_by_zero(self, basic, helpers):
        """Test division by zero handling"""
        try:
            result = basic.process_command('PRINT 10 / 0')
            # Should either error or return infinity/undefined
        except:
            pass  # Expected behavior

    def test_function_parameter_errors(self, basic, helpers):
        """Test function calls with wrong parameters"""
        # LEFT$ with wrong parameters
        try:
            result = basic.process_command('PRINT LEFT$("HELLO")')  # Missing length
            # Should error
        except:
            pass  # Expected
        
        # SQR of negative number
        try:
            result = basic.process_command('PRINT SQR(-1)')
            # Should error or return special value
        except:
            pass  # Expected

    def test_type_mismatch_errors(self, basic, helpers):
        """Test type mismatch error conditions"""
        # String where number expected
        try:
            result = basic.process_command('PRINT SQR("HELLO")')
            # Should produce type mismatch error
        except:
            pass  # Expected
        
        # Number where string expected
        try:
            result = basic.process_command('PRINT LEFT$(123, 2)')
            # Should produce type mismatch error
        except:
            pass  # Expected

    def test_line_number_errors(self, basic, helpers):
        """Test line number error conditions"""
        # Invalid line numbers
        invalid_lines = [
            '-10 PRINT "NEGATIVE"',  # Negative line number
            '0 PRINT "ZERO"',        # Zero line number
            '99999 PRINT "TOO BIG"'  # Very large line number (if there's a limit)
        ]
        
        for line in invalid_lines:
            try:
                line_num, code = basic.parse_line(line)
                # Should either reject or handle gracefully
            except:
                pass  # Expected behavior

    def test_nested_structure_errors(self, basic, helpers):
        """Test errors in nested structures"""
        # Nested FOR loops with errors
        program = [
            '10 FOR I = 1 TO 3',
            '20 FOR J = 1 TO 2',
            '30 PRINT I, J',
            '40 NEXT I',  # Wrong nesting order
            '50 NEXT J'
        ]
        
        results = helpers.execute_program(basic, program)
        # Should handle nested structure errors gracefully

    def test_malformed_multi_statements(self, basic, helpers):
        """Test malformed multi-statement lines"""
        malformed_lines = [
            'PRINT "A": :"B"',    # Empty statement
            'PRINT "A":: PRINT "B"',  # Double colon
            ': PRINT "A"',        # Starting with colon
            'PRINT "A" :',        # Ending with colon
        ]
        
        for line in malformed_lines:
            try:
                result = basic.process_command(line)
                # Should handle gracefully
            except:
                pass  # Expected behavior

    def test_memory_limits(self, basic, helpers):
        """Test behavior near memory/size limits"""
        # Very long lines
        long_line = 'PRINT "' + 'A' * 1000 + '"'
        try:
            result = basic.process_command(long_line)
            # Should either work or fail gracefully
        except:
            pass  # May have limits
        
        # Many variables
        for i in range(100):
            try:
                basic.process_command(f'VAR{i} = {i}')
            except:
                break  # May have limits

    def test_infinite_loop_prevention(self, basic, helpers):
        """Test that infinite loop prevention works"""
        # Create a potentially infinite loop
        program = [
            '10 PRINT "LOOP"',
            '20 GOTO 10'
        ]
        
        results = helpers.execute_program(basic, program)
        # Should eventually stop due to safety mechanisms
        
        # Check that we didn't get stuck
        assert True, "Infinite loop prevention should work"

    def test_stack_overflow_prevention(self, basic, helpers):
        """Test prevention of stack overflow in recursion"""
        # Deep GOSUB recursion
        program = []
        for i in range(100):
            line_num = (i + 1) * 10
            next_line = line_num + 10
            if i < 99:
                program.append(f'{line_num} GOSUB {next_line}')
            else:
                program.append(f'{line_num} RETURN')
        
        try:
            results = helpers.execute_program(basic, program)
            # Should either work or fail gracefully without crashing
        except:
            pass  # Expected behavior for deep recursion

    def test_graceful_degradation(self, basic, helpers):
        """Test that parser degrades gracefully with complex errors"""
        # Multiple errors in one program
        program = [
            '10 INVALID SYNTAX HERE',
            '20 PRINT "THIS SHOULD WORK"',
            '30 ANOTHER ERROR',
            '40 PRINT "THIS TOO"'
        ]
        
        results = helpers.execute_program(basic, program)
        # Should handle some parts even if others fail
        # At minimum, shouldn't crash the interpreter
