#!/usr/bin/env python3

"""
Integration tests for single-line control structure normalization.

Tests that complex single-line BASIC control structures are correctly
converted to multi-line equivalents and executed properly. This includes
testing both immediate execution and program mode execution.
"""

import pytest


class TestSingleLineControlStructures:
    """Integration test cases for single-line control structure functionality"""

    def test_basic_functionality(self, basic, helpers):
        """Test basic single-line control structure functionality"""
        # Simple single-line IF/THEN
        result = basic.process_command('IF 1=1 THEN PRINT "TRUE": A=5')
        text_outputs = helpers.get_text_output(result)
        assert 'TRUE' in text_outputs
        helpers.assert_variable_equals(basic, 'A', 5)

    def test_single_line_if_then(self, basic, helpers):
        """Test single-line IF/THEN statements"""
        # Test with multiple statements after THEN
        result = basic.process_command('IF 1=1 THEN PRINT "TRUE": A=5')
        text_outputs = helpers.get_text_output(result)

        assert len(text_outputs) == 1
        assert text_outputs[0] == 'TRUE'
        helpers.assert_variable_equals(basic, 'A', 5)

    def test_single_line_if_then_else(self, basic, helpers):
        """Test single-line IF/THEN/ELSE statements"""
        # Test TRUE condition
        result = basic.process_command('IF 1=1 THEN PRINT "TRUE": ELSE PRINT "FALSE"')
        text_outputs = helpers.get_text_output(result)
        assert 'TRUE' in text_outputs
        assert 'FALSE' not in text_outputs

        # Test FALSE condition
        result = basic.process_command('IF 0=1 THEN PRINT "TRUE": ELSE PRINT "FALSE"')
        text_outputs = helpers.get_text_output(result)
        assert 'TRUE' not in text_outputs
        assert 'FALSE' in text_outputs

    def test_single_line_for_loop(self, basic, helpers):
        """Test single-line FOR loop execution"""
        result = basic.process_command('FOR I=1 TO 3: PRINT I: NEXT I')
        text_outputs = helpers.get_text_output(result)

        expected_outputs = ['1', '2', '3']
        assert text_outputs == expected_outputs
        helpers.assert_variable_equals(basic, 'I', 4)  # After loop completion

    def test_single_line_for_loop_with_step(self, basic, helpers):
        """Test single-line FOR loop with STEP"""
        result = basic.process_command('FOR X=0 TO 6 STEP 2: PRINT X: NEXT X')
        text_outputs = helpers.get_text_output(result)

        expected_outputs = ['0', '2', '4', '6']
        assert text_outputs == expected_outputs
        helpers.assert_variable_equals(basic, 'X', 8)  # After loop completion

    def test_single_line_while_loop(self, basic, helpers):
        """Test single-line WHILE loop execution"""
        # Set up initial condition
        basic.process_command('X=1')

        result = basic.process_command('WHILE X<=3: PRINT X: X=X+1: WEND')
        text_outputs = helpers.get_text_output(result)

        expected_outputs = ['1', '2', '3']
        assert text_outputs == expected_outputs
        helpers.assert_variable_equals(basic, 'X', 4)

    def test_single_line_do_loop_while(self, basic, helpers):
        """Test single-line DO/LOOP WHILE execution"""
        # Set up initial condition
        basic.process_command('Y=1')

        result = basic.process_command('DO: PRINT Y: Y=Y+1: LOOP WHILE Y<=2')
        text_outputs = helpers.get_text_output(result)

        expected_outputs = ['1', '2']
        assert text_outputs == expected_outputs
        helpers.assert_variable_equals(basic, 'Y', 3)

    def test_single_line_do_while_loop(self, basic, helpers):
        """Test single-line DO WHILE/LOOP execution"""
        # Set up initial condition
        basic.process_command('Z=3')

        result = basic.process_command('DO WHILE Z>0: PRINT Z: Z=Z-1: LOOP')
        text_outputs = helpers.get_text_output(result)

        expected_outputs = ['3', '2', '1']
        assert text_outputs == expected_outputs
        helpers.assert_variable_equals(basic, 'Z', 0)

    def test_nested_single_line_structures(self, basic, helpers):
        """Test nested control structures in single line"""
        # Nested IF in FOR loop
        result = basic.process_command('FOR J=1 TO 3: IF J=2 THEN PRINT "TWO": NEXT J')
        text_outputs = helpers.get_text_output(result)

        # Should only print "TWO" when J=2
        expected_outputs = ['TWO']
        assert text_outputs == expected_outputs
        helpers.assert_variable_equals(basic, 'J', 4)

    def test_complex_expressions_in_single_line(self, basic, helpers):
        """Test complex expressions within single-line control structures"""
        # Set up variables
        basic.process_command('A=5: B=3: C=2')

        # Complex condition
        result = basic.process_command('IF (A+B)*C > 15 THEN PRINT "BIG": ELSE PRINT "SMALL"')
        text_outputs = helpers.get_text_output(result)

        # (5+3)*2 = 16 > 15, so should print "BIG"
        assert 'BIG' in text_outputs
        assert 'SMALL' not in text_outputs

    def test_program_mode_single_line_structures(self, basic, helpers):
        """Test single-line control structures in program mode"""
        program = [
            "10 FOR I=1 TO 2: PRINT I: NEXT I",
            "20 IF 1=1 THEN PRINT \"DONE\": END",
            "30 PRINT \"NOT REACHED\""
        ]

        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)

        expected_outputs = ['1', '2', 'DONE']
        assert text_outputs == expected_outputs

    def test_program_mode_complex_single_line(self, basic, helpers):
        """Test complex single-line structures in program mode"""
        program = [
            "10 A=0",
            "20 FOR X=1 TO 3: A=A+X: IF A>3 THEN PRINT A: NEXT X",
            "30 PRINT \"FINAL:\"; A"
        ]

        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)

        # A accumulates: 1, 3, 6. Should print when A>3 (so 6), then final value
        assert '6' in text_outputs
        assert any('FINAL:6' in output or ('FINAL:' in output and '6' in output) for output in text_outputs)

    def test_error_handling_single_line(self, basic, helpers):
        """Test error handling in malformed single-line structures"""
        # Test invalid syntax in single-line IF statement
        result = basic.process_command('IF 1=1 THEN INVALID_COMMAND')
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0, "Should produce error for invalid command in IF statement"

    def test_variable_scope_single_line(self, basic, helpers):
        """Test variable scope in single-line structures"""
        # Variables created in single-line structures should persist
        basic.process_command('FOR K=1 TO 1: TEMP=999: NEXT K')
        helpers.assert_variable_equals(basic, 'TEMP', 999)
        helpers.assert_variable_equals(basic, 'K', 2)

    def test_string_operations_single_line(self, basic, helpers):
        """Test string operations in single-line structures"""
        result = basic.process_command('FOR I=1 TO 2: S$="ITEM"+STR$(I): PRINT S$: NEXT I')
        text_outputs = helpers.get_text_output(result)

        expected_outputs = ['ITEM 1', 'ITEM 2']  # STR$ adds leading space for positive numbers
        assert text_outputs == expected_outputs

    def test_single_line_exit_for(self, basic, helpers):
        """Test EXIT FOR in single-line structures"""
        # Set up and test EXIT FOR
        result = basic.process_command('FOR I=1 TO 10: IF I=3 THEN EXIT FOR: PRINT I: NEXT I')
        text_outputs = helpers.get_text_output(result)

        # Should print 1, 2, then exit
        expected_outputs = ['1', '2']
        assert text_outputs == expected_outputs
        # I should be 3 (the value when EXIT FOR was executed)
        helpers.assert_variable_equals(basic, 'I', 3)

    def test_performance_single_line_structures(self, basic, helpers):
        """Test performance of single-line structure normalization"""
        import time

        # Time a moderately complex single-line structure
        start_time = time.time()

        for _ in range(10):
            result = basic.process_command('FOR I=1 TO 5: IF I MOD 2=0 THEN PRINT I: NEXT I')

        end_time = time.time()
        execution_time = end_time - start_time

        # Should complete reasonably quickly (within 1 second for 10 iterations)
        assert execution_time < 1.0, "Single-line structure execution should be performant"
