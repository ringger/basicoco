#!/usr/bin/env python3

"""
Unit tests for error recovery and state consistency.
Tests that errors don't leave the interpreter in inconsistent states.
"""

import pytest


class TestErrorRecovery:
    """Test cases for error recovery and state consistency"""

    def test_basic_functionality(self, basic, helpers):
        """Basic test to ensure error recovery tests work"""
        # Simple error that should be handled
        result = basic.process_command('PRINT 1 / 0')  # Division by zero
        # Should handle gracefully (returns infinity in authentic BASIC)
        assert len(result) > 0

    def test_error_recovery_state_consistency(self, basic, helpers):
        """Test interpreter state after various errors"""
        # Test each error type leaves clean state
        error_tests = [
            ('READ X', 'OUT OF DATA'),  # No DATA statements
            ('DIM A(5): DIM A(10)', "already dimensioned"),
            ('UNDIM(999) = 5', "UNDIM'D ARRAY")  # Undimensioned array error
        ]
        
        for command, expected_error in error_tests:
            basic.process_command('NEW')  # Start fresh
            result = basic.process_command(command)
            
            # Should have expected error
            error_messages = [item.get('message', '') for item in result if item.get('type') == 'error']
            assert any(expected_error in msg for msg in error_messages), \
                           f"Expected {expected_error} for command: {command}"
            
            # Interpreter should be in clean state
            assert not basic.running, f"Program should not be running after error: {command}"
            assert basic.program_counter is None, f"Program counter should be None after error: {command}"

    def test_program_error_state_recovery(self, basic, helpers):
        """Test state consistency after program errors"""
        # Program with multiple errors
        program = [
            '10 DIM A(3)',
            '20 A(0) = 10',
            '30 A(5) = 50',  # BAD SUBSCRIPT error
            '40 PRINT "UNREACHABLE"'
        ]
        
        # Execute program
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        
        # Should have BAD SUBSCRIPT error  
        assert any("BAD SUBSCRIPT" in error for error in errors)
        
        # State should be consistent
        assert not basic.running
        assert basic.current_line == 30  # Stopped at error line
        
        # Array should have valid values set before error
        assert basic.arrays['A'][0] == 10
        
        # Should be able to execute new commands after error
        result = basic.process_command('PRINT "RECOVERY TEST"')
        text_messages = [item.get("text", "") for item in result if item.get("type") == "text"]
        assert any("RECOVERY TEST" in msg for msg in text_messages)

    def test_nested_error_recovery(self, basic, helpers):
        """Test recovery from nested errors in complex programs"""
        program = [
            '10 DIM A(5)',
            '20 FOR I = 1 TO 10',  # Loop beyond array bounds
            '30 A(I) = I * 10',   # This will fail when I > 5 (BAD SUBSCRIPT)
            '40 PRINT "SET A("; I; ") ="; A(I)',
            '50 NEXT I',
            '60 PRINT "COMPLETED"'
        ]
        
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        text_outputs = helpers.get_text_output(results)
        
        # Should get BAD SUBSCRIPT error when I exceeds array bounds
        assert any("BAD SUBSCRIPT" in error for error in errors), \
                       f"Expected BAD SUBSCRIPT error, got: {errors}"
        
        # Should not complete the loop
        assert not any('COMPLETED' in output for output in text_outputs), \
                        "Should not complete loop after error"
        
        # Should have executed some iterations successfully (I = 1 to 5)
        successful_outputs = [output for output in text_outputs if 'SET A(' in output]
        assert len(successful_outputs) > 0, "Should have some successful iterations"
        assert len(successful_outputs) < 10, "Should not complete all 10 iterations"
        
        # FOR stack should be cleared after error  
        assert len(basic.for_stack) == 0, "FOR stack should be empty after error"

    def test_error_in_gosub_recovery(self, basic, helpers):
        """Test recovery from errors in GOSUB subroutines"""
        program = [
            '10 PRINT "MAIN START"',
            '20 GOSUB 100',
            '30 PRINT "BACK IN MAIN"',  # Should not reach here
            '40 END',
            '100 PRINT "IN SUBROUTINE"',
            '110 UNDIM(999) = 5',  # UNDIM'D ARRAY error
            '120 PRINT "AFTER ERROR"',  # Should not reach here
            '130 RETURN'
        ]
        
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        text_outputs = helpers.get_text_output(results)
        
        # Should have UNDIM'D ARRAY error
        assert any("UNDIM'D ARRAY" in error for error in errors)
        
        # Should reach subroutine but not return
        assert any('IN SUBROUTINE' in output for output in text_outputs)
        assert not any('BACK IN MAIN' in output for output in text_outputs)
        assert not any('AFTER ERROR' in output for output in text_outputs)
        
        # Call stack should be cleared after error
        assert len(basic.call_stack) == 0, "Call stack should be empty after error"

    def test_data_pointer_consistency_after_error(self, basic, helpers):
        """Test DATA pointer consistency after READ errors"""
        program = [
            '10 DATA 100, 200, 300',
            '20 READ A',
            '30 READ B', 
            '40 READ C',
            '50 READ D',  # Should trigger OUT OF DATA
            '60 PRINT "UNREACHABLE"'
        ]
        
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        
        # Should have OUT OF DATA error
        assert any('OUT OF DATA' in error for error in errors)
        
        # Data pointer should be at end
        assert basic.data_pointer == len(basic.data_statements)
        
        # Variables should have been set before error
        assert basic.variables.get('A') == 100
        assert basic.variables.get('B') == 200
        assert basic.variables.get('C') == 300
        assert 'D' not in basic.variables  # D should not be set

    def test_syntax_error_recovery(self, basic, helpers):
        """Test recovery from syntax errors"""
        # Test various syntax errors and runtime errors
        error_tests = [
            ('FOR I = 1 TO', 'Unexpected end of expression'),  # Incomplete FOR
            ('IF THEN 10', 'Unexpected token'),  # Missing condition
            ('DIM A()', 'Invalid array declaration'),  # Empty dimensions
            ('GOSUB', 'Unexpected end of expression'),  # Missing line number
            ('NEXT I', 'NEXT WITHOUT FOR'),  # NEXT without matching FOR (runtime error)
        ]
        
        for bad_command, expected_error in error_tests:
            basic.process_command('NEW')  # Fresh start
            result = basic.process_command(bad_command)
            
            # Should produce expected error
            has_expected_error = any(expected_error in item.get('message', '') 
                                   for item in result if item.get('type') == 'error')
            assert has_expected_error, f"Expected {expected_error} for: {bad_command}"
            
            # Should be able to execute valid command after error
            recovery_result = basic.process_command('PRINT "OK"')
            text_messages = [item.get('text', '') for item in recovery_result if item.get('type') == 'text']
            assert any('OK' in msg for msg in text_messages), \
                           f"Should recover after error: {bad_command}"
    def test_memory_consistency_after_errors(self, basic, helpers):
        """Test that memory structures remain consistent after errors"""
        # Create some initial state
        setup_commands = [
            'A = 42',
            'B$ = "HELLO"',
            'DIM C(5)',
            'C(0) = 100'
        ]
        
        for cmd in setup_commands:
            basic.process_command(cmd)
        
        initial_var_count = len(basic.variables)
        initial_array_count = len(basic.arrays)
        
        # Try to cause various errors
        error_commands = [
            'READ X',  # OUT OF DATA
            'D(999) = 5',  # UNDIM'D ARRAY error
            'DIM C(10)',  # REDIM'D ARRAY
        ]
        
        for error_cmd in error_commands:
            basic.process_command(error_cmd)
        
        # Original variables and arrays should still exist and be valid
        assert basic.variables.get('A') == 42
        assert basic.variables.get('B$') == 'HELLO'
        assert basic.arrays['C'][0] == 100
        
        # Memory structures should not have grown unexpectedly from errors
        # (though new undimensioned arrays might be created)
        assert len(basic.variables) >= initial_var_count
        assert len(basic.arrays) >= initial_array_count

    def test_program_counter_reset_after_error(self, basic, helpers):
        """Test that program counter is properly reset after errors"""
        program = [
            '10 PRINT "LINE 10"',
            '20 UNDIM(999) = 5',  # UNDIM'D ARRAY
            '30 PRINT "LINE 30"'  # Should not reach
        ]
        
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        
        # Should have error
        assert any("UNDIM'D ARRAY" in error for error in errors)
        
        # Program counter should be reset
        assert basic.program_counter is None
        assert not basic.running
        
        # Should be able to run a different program
        new_program = ['10 PRINT "NEW PROGRAM"']
        new_results = helpers.execute_program(basic, new_program)
        new_text = helpers.get_text_output(new_results)
        
        assert any('NEW PROGRAM' in output for output in new_text)

    def test_state_consistency_after_multiple_errors(self, basic, helpers):
        """Test state consistency after multiple consecutive errors"""
        # Generate multiple errors in sequence
        error_commands = [
            'READ X',  # OUT OF DATA
            'UNDIM(999) = 5',  # UNDIM'D ARRAY
            'DIM A(5): DIM A(10)',  # REDIM'D ARRAY
        ]
        
        for i, cmd in enumerate(error_commands):
            result = basic.process_command(cmd)
            
            # Each should produce an error
            errors = [item for item in result if item.get('type') == 'error']
            assert len(errors) > 0, f"Command {i+1} should produce error: {cmd}"
            
            # State should remain consistent
            assert not basic.running, f"Should not be running after error {i+1}"
            assert basic.program_counter is None, f"Program counter should be None after error {i+1}"
        
        # Should be able to execute valid command after all errors
        result = basic.process_command('PRINT "RECOVERY SUCCESSFUL"')
        text_outputs = helpers.get_text_output(result)
        assert any('RECOVERY SUCCESSFUL' in output for output in text_outputs)


class TestMultiStatementErrorPropagation:
    """Test that errors in multi-statement immediate mode lines stop subsequent statements"""

    def test_error_stops_subsequent_statements(self, basic, helpers):
        """Error in second statement should prevent third from executing"""
        basic.process_command('NEW')
        basic.process_command('A = 0')
        basic.process_command('C = 0')
        result = basic.process_command('A = 1: UNDIM(999) = 5: C = 99')

        # A should be set (first statement ran)
        helpers.assert_variable_equals(basic, 'A', 1)
        # C should NOT be set to 99 (third statement should not run)
        helpers.assert_variable_equals(basic, 'C', 0)
        # Should have an error in results
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0

    def test_print_before_error_appears(self, basic, helpers):
        """Output from statements before the error should still appear"""
        basic.process_command('NEW')
        result = basic.process_command('PRINT "BEFORE": UNDIM(999) = 5: PRINT "AFTER"')

        text_outputs = helpers.get_text_output(result)
        assert 'BEFORE' in text_outputs
        assert 'AFTER' not in text_outputs
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0

    def test_jump_stops_subsequent_statements(self, basic, helpers):
        """Jump directive in multi-statement line should stop remaining statements"""
        basic.process_command('NEW')
        basic.process_command('Z = 0')
        result = basic.process_line('PRINT "HELLO": GOTO 100: Z = 99')

        text_outputs = helpers.get_text_output(result)
        assert 'HELLO' in text_outputs
        # Z should not be set (statement after GOTO should not run)
        helpers.assert_variable_equals(basic, 'Z', 0)
        # Should have jump in results
        has_jump = any(item.get('type') == 'jump' for item in result)
        assert has_jump

    def test_all_statements_run_when_no_error(self, basic, helpers):
        """All statements should execute when there are no errors"""
        basic.process_command('NEW')
        basic.process_command('A = 5: B = 10: C = A + B')
        helpers.assert_variable_equals(basic, 'A', 5)
        helpers.assert_variable_equals(basic, 'B', 10)
        helpers.assert_variable_equals(basic, 'C', 15)
