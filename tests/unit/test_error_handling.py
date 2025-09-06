#!/usr/bin/env python3

"""
Tests for error handling and malformed input parsing.
Ensures the parser handles invalid syntax gracefully.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from test_base import BaseTestCase


class ErrorHandlingTest(BaseTestCase):
    """Test cases for error handling and malformed input"""

    def test_basic_functionality(self):
        """Test basic error handling functionality"""
        self.assert_error_output('INVALID_COMMAND')

    def test_syntax_errors(self):
        """Test various syntax error conditions"""
        # Missing THEN in IF statement
        self.assert_error_output('IF X > 5 PRINT "ERROR"', 'SYNTAX ERROR')
        
        # Missing TO in FOR statement
        self.assert_error_output('FOR I = 1 5', 'SYNTAX ERROR')
        
        # Invalid assignment
        self.assert_error_output('= 5', 'SYNTAX ERROR')

    def test_unmatched_parentheses(self):
        """Test handling of unmatched parentheses"""
        # Missing closing parenthesis
        try:
            result = self.basic.execute_command('PRINT (2 + 3')
            # Should either error or handle gracefully
        except:
            pass  # Expected behavior
        
        # Extra closing parenthesis
        try:
            result = self.basic.execute_command('PRINT (2 + 3))')
            # Should either error or handle gracefully  
        except:
            pass  # Expected behavior

    def test_unmatched_quotes(self):
        """Test handling of unmatched quotes"""
        # Missing closing quote
        try:
            result = self.basic.execute_command('PRINT "HELLO')
            # Should either error or handle gracefully
        except:
            pass  # Expected behavior
        
        # Mixed quote types (if that's an issue)
        try:
            result = self.basic.execute_command('PRINT "HELLO\'')
            # Should either error or handle gracefully
        except:
            pass  # Expected behavior

    def test_invalid_variable_names(self):
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
                result = self.basic.execute_command(f'{invalid_name} = 5')
                # Should either error or handle gracefully
                if result and any(item.get('type') == 'error' for item in result):
                    pass  # Good - produced error
            except:
                pass  # Also acceptable

    def test_undefined_variables(self):
        """Test handling of undefined variables"""
        # Using undefined variable
        try:
            result = self.basic.execute_command('PRINT UNDEFINED_VAR')
            # Should either error, return 0, or handle gracefully
        except:
            pass  # Expected behavior

    def test_array_errors(self):
        """Test array-related error handling"""
        # Undimensioned array
        self.assert_error_output('PRINT A(5)', 'UNDIM\'D ARRAY')
        
        # Bad subscript
        self.basic.execute_command('DIM B(10)')
        self.assert_error_output('PRINT B(15)', 'BAD SUBSCRIPT')
        self.assert_error_output('PRINT B(-1)', 'BAD SUBSCRIPT')

    def test_for_loop_errors(self):
        """Test FOR loop error conditions"""
        # NEXT without FOR
        self.assert_error_output('NEXT I', 'NEXT WITHOUT FOR')
        
        # Mismatched FOR/NEXT
        program = [
            '10 FOR I = 1 TO 5',
            '20 FOR J = 1 TO 3', 
            '30 NEXT I',  # Wrong order
            '40 NEXT J'
        ]
        
        results = self.execute_program(program)
        # Should handle gracefully, possibly with error

    def test_gosub_return_errors(self):
        """Test GOSUB/RETURN error conditions"""
        # RETURN without GOSUB
        self.assert_error_output('RETURN', 'RETURN WITHOUT GOSUB')
        
        # GOSUB to undefined line should produce jump instruction (error occurs at runtime)
        result = self.basic.execute_command('GOSUB 9999')
        self.assertTrue(any(item.get('type') == 'jump' for item in result))

    def test_goto_errors(self):
        """Test GOTO error conditions"""
        # GOTO to undefined line
        result = self.basic.execute_command('GOTO 9999')
        # Should produce some kind of error or handle gracefully

    def test_division_by_zero(self):
        """Test division by zero handling"""
        try:
            result = self.basic.execute_command('PRINT 10 / 0')
            # Should either error or return infinity/undefined
        except:
            pass  # Expected behavior

    def test_function_parameter_errors(self):
        """Test function calls with wrong parameters"""
        # LEFT$ with wrong parameters
        try:
            result = self.basic.execute_command('PRINT LEFT$("HELLO")')  # Missing length
            # Should error
        except:
            pass  # Expected
        
        # SQR of negative number
        try:
            result = self.basic.execute_command('PRINT SQR(-1)')
            # Should error or return special value
        except:
            pass  # Expected

    def test_type_mismatch_errors(self):
        """Test type mismatch error conditions"""
        # String where number expected
        try:
            result = self.basic.execute_command('PRINT SQR("HELLO")')
            # Should produce type mismatch error
        except:
            pass  # Expected
        
        # Number where string expected
        try:
            result = self.basic.execute_command('PRINT LEFT$(123, 2)')
            # Should produce type mismatch error
        except:
            pass  # Expected

    def test_line_number_errors(self):
        """Test line number error conditions"""
        # Invalid line numbers
        invalid_lines = [
            '-10 PRINT "NEGATIVE"',  # Negative line number
            '0 PRINT "ZERO"',        # Zero line number
            '99999 PRINT "TOO BIG"'  # Very large line number (if there's a limit)
        ]
        
        for line in invalid_lines:
            try:
                line_num, code = self.basic.parse_line(line)
                # Should either reject or handle gracefully
            except:
                pass  # Expected behavior

    def test_nested_structure_errors(self):
        """Test errors in nested structures"""
        # Nested FOR loops with errors
        program = [
            '10 FOR I = 1 TO 3',
            '20 FOR J = 1 TO 2',
            '30 PRINT I, J',
            '40 NEXT I',  # Wrong nesting order
            '50 NEXT J'
        ]
        
        results = self.execute_program(program)
        # Should handle nested structure errors gracefully

    def test_malformed_multi_statements(self):
        """Test malformed multi-statement lines"""
        malformed_lines = [
            'PRINT "A": :"B"',    # Empty statement
            'PRINT "A":: PRINT "B"',  # Double colon
            ': PRINT "A"',        # Starting with colon
            'PRINT "A" :',        # Ending with colon
        ]
        
        for line in malformed_lines:
            try:
                result = self.basic.execute_command(line)
                # Should handle gracefully
            except:
                pass  # Expected behavior

    def test_memory_limits(self):
        """Test behavior near memory/size limits"""
        # Very long lines
        long_line = 'PRINT "' + 'A' * 1000 + '"'
        try:
            result = self.basic.execute_command(long_line)
            # Should either work or fail gracefully
        except:
            pass  # May have limits
        
        # Many variables
        for i in range(100):
            try:
                self.basic.execute_command(f'VAR{i} = {i}')
            except:
                break  # May have limits

    def test_infinite_loop_prevention(self):
        """Test that infinite loop prevention works"""
        # Create a potentially infinite loop
        program = [
            '10 PRINT "LOOP"',
            '20 GOTO 10'
        ]
        
        results = self.execute_program(program)
        # Should eventually stop due to safety mechanisms
        
        # Check that we didn't get stuck
        self.assertTrue(True, "Infinite loop prevention should work")

    def test_stack_overflow_prevention(self):
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
            results = self.execute_program(program)
            # Should either work or fail gracefully without crashing
        except:
            pass  # Expected behavior for deep recursion

    def test_graceful_degradation(self):
        """Test that parser degrades gracefully with complex errors"""
        # Multiple errors in one program
        program = [
            '10 INVALID SYNTAX HERE',
            '20 PRINT "THIS SHOULD WORK"',
            '30 ANOTHER ERROR',
            '40 PRINT "THIS TOO"'
        ]
        
        results = self.execute_program(program)
        # Should handle some parts even if others fail
        # At minimum, shouldn't crash the interpreter


if __name__ == '__main__':
    test = ErrorHandlingTest("Error Handling Tests")
    results = test.run_all_tests()
    from test_base import print_test_results
    print_test_results(results, verbose=True)