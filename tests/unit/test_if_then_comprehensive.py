#!/usr/bin/env python3

"""
Comprehensive unit tests for IF THEN statement contexts.
Tests all variations of THEN clauses to prevent parsing regressions.
"""

import sys
import os

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))



class TestIfThenComprehensive:
    """Comprehensive test cases for IF THEN statement contexts"""

    def test_basic_functionality(self, basic, helpers):
        """Test basic IF THEN functionality"""
        result = basic.process_command('A = 1: IF A = 1 THEN PRINT "BASIC"')
        text_outputs = helpers.get_text_output(result)
        assert 'BASIC' in ' '.join(text_outputs)

    def test_then_with_line_numbers(self, basic, helpers):
        """Test IF THEN with line number jumps"""
        # Simple line number
        program = [
            '10 A = 5',
            '20 IF A = 5 THEN 50',
            '30 PRINT "SKIP"',
            '40 END',
            '50 PRINT "JUMPED"'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        assert 'JUMPED' in ' '.join(text_outputs)
        assert 'SKIP' not in ' '.join(text_outputs)

    def test_then_with_line_number_expressions(self, basic, helpers):
        """Test IF THEN with line number expressions"""
        program = [
            '10 A = 5',
            '20 B = 10', 
            '30 IF A = 5 THEN A * B',  # Should jump to line 50
            '40 PRINT "SKIP"',
            '50 PRINT "EXPRESSION JUMP"'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        assert 'EXPRESSION JUMP' in ' '.join(text_outputs)
        assert 'SKIP' not in ' '.join(text_outputs)

    def test_then_with_print_commands(self, basic, helpers):
        """Test IF THEN with PRINT commands"""
        # Simple PRINT
        result = basic.process_command('A = 1: IF A = 1 THEN PRINT "TRUE"')
        text_outputs = helpers.get_text_output(result)
        assert 'TRUE' in ' '.join(text_outputs)
        
        # PRINT with expressions
        result = basic.process_command('X = 10: IF X > 5 THEN PRINT "LARGE"; X')
        text_outputs = helpers.get_text_output(result)
        assert 'LARGE' in ' '.join(text_outputs)
        assert '10' in ' '.join(text_outputs)

    def test_then_with_assignment_commands(self, basic, helpers):
        """Test IF THEN with variable assignments"""
        # Direct assignment
        basic.process_command('A = 1')
        basic.process_command('IF A = 1 THEN B = 99')
        assert basic.variables.get('B') == 99
        
        # LET assignment
        basic.process_command('C = 1') 
        basic.process_command('IF C = 1 THEN LET D = 88')
        assert basic.variables.get('D') == 88

    def test_then_with_goto_commands(self, basic, helpers):
        """Test IF THEN with GOTO commands"""
        program = [
            '10 A = 1',
            '20 IF A = 1 THEN GOTO 50',
            '30 PRINT "SKIP"',
            '40 END',
            '50 PRINT "GOTO WORKED"'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        assert 'GOTO WORKED' in ' '.join(text_outputs)
        assert 'SKIP' not in ' '.join(text_outputs)

    def test_then_with_gosub_commands(self, basic, helpers):
        """Test IF THEN with GOSUB commands"""
        program = [
            '10 A = 1',
            '20 IF A = 1 THEN GOSUB 100',
            '30 PRINT "MAIN"',
            '40 END',
            '100 PRINT "SUBROUTINE"',
            '110 RETURN'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        assert 'SUBROUTINE' in ' '.join(text_outputs)
        assert 'MAIN' in ' '.join(text_outputs)

    def test_then_with_exit_for(self, basic, helpers):
        """Test IF THEN with EXIT FOR commands"""
        program = [
            '10 FOR I = 1 TO 10',
            '20 PRINT I',
            '30 IF I = 3 THEN EXIT FOR',
            '40 NEXT I',
            '50 PRINT "DONE"'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        assert '1' in ' '.join(text_outputs)
        assert '2' in ' '.join(text_outputs)
        assert '3' in ' '.join(text_outputs)
        assert 'DONE' in ' '.join(text_outputs)
        assert '4' not in ' '.join(text_outputs)

    def test_then_with_end_stop_commands(self, basic, helpers):
        """Test IF THEN with END and STOP commands"""
        # END command
        program = [
            '10 A = 1',
            '20 IF A = 1 THEN END',
            '30 PRINT "NEVER"'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        assert 'NEVER' not in ' '.join(text_outputs)
        
        # STOP command
        program = [
            '10 B = 1',
            '20 IF B = 1 THEN STOP',
            '30 PRINT "NEVER"'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        assert 'NEVER' not in ' '.join(text_outputs)

    def test_then_with_multi_statement(self, basic, helpers):
        """Test IF THEN with multiple statements"""
        program = [
            '10 A = 1',
            '20 IF A = 1 THEN PRINT "FIRST": PRINT "SECOND": B = 99',
            '30 PRINT B'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        assert 'FIRST' in ' '.join(text_outputs)
        assert 'SECOND' in ' '.join(text_outputs)
        assert '99' in ' '.join(text_outputs)

    def test_then_with_for_loop_commands(self, basic, helpers):
        """Test IF THEN with FOR loop commands"""
        program = [
            '10 A = 1',
            '20 IF A = 1 THEN FOR I = 1 TO 3: PRINT I: NEXT I',
            '30 PRINT "DONE"'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        assert '1' in ' '.join(text_outputs)
        assert '2' in ' '.join(text_outputs)
        assert '3' in ' '.join(text_outputs)
        assert 'DONE' in ' '.join(text_outputs)

    def test_then_with_input_commands(self, basic, helpers):
        """Test IF THEN with INPUT commands (should handle input requests)"""
        # This would normally wait for input, but we test that it generates proper input request
        result = basic.process_command('A = 1: IF A = 1 THEN INPUT "Enter value"; X')
        
        # Should generate input request
        has_input_request = any(item.get('type') == 'input_request' for item in result)
        assert has_input_request

    def test_then_with_on_commands(self, basic, helpers):
        """Test IF THEN with ON GOTO/GOSUB commands"""
        program = [
            '10 A = 1',
            '20 B = 2', 
            '30 IF A = 1 THEN ON B GOTO 100, 200',
            '40 PRINT "SKIP"',
            '50 END',
            '100 PRINT "OPTION 1"',
            '110 END',
            '200 PRINT "OPTION 2"'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        assert 'OPTION 2' in ' '.join(text_outputs)
        assert 'OPTION 1' not in ' '.join(text_outputs)
        assert 'SKIP' not in ' '.join(text_outputs)

    def test_then_false_conditions(self, basic, helpers):
        """Test IF THEN when condition is false (should skip THEN clause)"""
        # False condition with line number
        program = [
            '10 A = 1',
            '20 IF A = 2 THEN 100',
            '30 PRINT "CONTINUED"',
            '40 END',
            '100 PRINT "JUMPED"'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        assert 'CONTINUED' in ' '.join(text_outputs)
        assert 'JUMPED' not in ' '.join(text_outputs)
        
        # False condition with command
        result = basic.process_command('A = 1: IF A = 2 THEN PRINT "FALSE"')
        text_outputs = helpers.get_text_output(result)
        assert 'FALSE' not in ' '.join(text_outputs)

    def test_then_with_string_conditions(self, basic, helpers):
        """Test IF THEN with string conditions"""
        # String equality
        result = basic.process_command('A$ = "TEST": IF A$ = "TEST" THEN PRINT "MATCH"')
        text_outputs = helpers.get_text_output(result)
        assert 'MATCH' in ' '.join(text_outputs)
        
        # String inequality
        result = basic.process_command('B$ = "X": IF B$ <> "Y" THEN PRINT "DIFFERENT"')
        text_outputs = helpers.get_text_output(result)
        assert 'DIFFERENT' in ' '.join(text_outputs)

    def test_then_with_complex_expressions(self, basic, helpers):
        """Test IF THEN with complex conditional expressions"""
        # Mathematical expressions
        result = basic.process_command('A = 5: B = 3: IF A * B = 15 THEN PRINT "MATH"')
        text_outputs = helpers.get_text_output(result)
        assert 'MATH' in ' '.join(text_outputs)
        
        # Function calls
        result = basic.process_command('A = -5: IF ABS(A) = 5 THEN PRINT "FUNCTION"')
        text_outputs = helpers.get_text_output(result)
        assert 'FUNCTION' in ' '.join(text_outputs)

    def test_then_edge_cases(self, basic, helpers):
        """Test IF THEN edge cases that might cause parsing issues"""
        # THEN with whitespace
        result = basic.process_command('A = 1: IF A = 1 THEN   PRINT "SPACE"')
        text_outputs = helpers.get_text_output(result)
        assert 'SPACE' in ' '.join(text_outputs)
        
        # THEN with line number 0 (should error)
        result = basic.process_command('A = 1: IF A = 1 THEN 0')
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0  # Should produce error
        
        # THEN with negative line number (should error or handle gracefully)
        result = basic.process_command('A = 1: IF A = 1 THEN -10')
        # Behavior may vary - either error or handle gracefully

    def test_nested_if_then(self, basic, helpers):
        """Test nested IF THEN statements"""
        program = [
            '10 A = 1',
            '20 B = 2',
            '30 IF A = 1 THEN IF B = 2 THEN PRINT "NESTED"',
            '40 PRINT "DONE"'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        assert 'NESTED' in ' '.join(text_outputs)
        assert 'DONE' in ' '.join(text_outputs)

    def test_multiline_if_then_endif(self, basic, helpers):
        """Test multi-line IF THEN ENDIF structure"""
        program = [
            '10 A = 1',
            '20 IF A = 1 THEN',
            '30 PRINT "INSIDE IF"',
            '40 B = 99',
            '50 ENDIF',
            '60 PRINT B'
        ]

        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)

        assert 'INSIDE IF' in ' '.join(text_outputs)
        assert '99' in ' '.join(text_outputs)


class TestNestedIfElseEndif:
    """Tests for nested multi-line IF/ELSE/ENDIF blocks.

    Regression tests for a bug where a false inner single-line IF
    (expanded to IF/ENDIF by the AST converter) caused the outer
    ELSE block to execute incorrectly because skip_if_block jumped
    past ENDIF without popping the if_stack.
    """

    def test_false_inner_if_does_not_enter_outer_else(self, basic, helpers):
        """When outer IF is true and inner IF is false (no ELSE),
        the outer ELSE body must NOT execute."""
        program = [
            '10 R$ = ""',
            '20 A = 75',
            '30 IF A >= 65 AND A <= 90 THEN',
            '40 IF A > 90 THEN A = A - 26',
            '50 R$ = R$ + CHR$(A)',
            '60 ELSE',
            '70 R$ = R$ + "X"',
            '80 ENDIF',
            '90 PRINT R$',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        # R$ should be exactly "K" (CHR$(75)), not "KX"
        assert 'K' in text
        assert 'X' not in ' '.join(text)

    def test_true_inner_if_does_not_enter_outer_else(self, basic, helpers):
        """When outer IF is true and inner IF is also true,
        the outer ELSE body must NOT execute."""
        program = [
            '10 R$ = ""',
            '20 A = 95',
            '30 IF A >= 65 AND A <= 90 + 10 THEN',
            '40 IF A > 90 THEN A = A - 26',
            '50 R$ = R$ + CHR$(A)',
            '60 ELSE',
            '70 R$ = R$ + "X"',
            '80 ENDIF',
            '90 PRINT R$',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        # A=95, inner IF is true so A=95-26=69, CHR$(69)="E"
        assert 'E' in text
        assert 'X' not in ' '.join(text)

    def test_false_outer_if_skips_to_else(self, basic, helpers):
        """When outer IF is false, it should skip to ELSE and execute that."""
        program = [
            '10 R$ = ""',
            '20 A = 50',
            '30 IF A >= 65 AND A <= 90 THEN',
            '40 IF A > 90 THEN A = A - 26',
            '50 R$ = R$ + CHR$(A)',
            '60 ELSE',
            '70 R$ = "ELSE"',
            '80 ENDIF',
            '90 PRINT R$',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert 'ELSE' in text

    def test_nested_if_in_for_loop(self, basic, helpers):
        """Nested IF inside FOR loop should work correctly each iteration."""
        program = [
            '10 R$ = ""',
            '20 FOR I = 1 TO 3',
            '30 IF I <= 2 THEN',
            '40 IF I = 1 THEN R$ = R$ + "A"',
            '50 IF I = 2 THEN R$ = R$ + "B"',
            '60 ELSE',
            '70 R$ = R$ + "C"',
            '80 ENDIF',
            '90 NEXT I',
            '100 PRINT R$',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert 'ABC' in text

    def test_print_with_if_then_in_string(self, basic, helpers):
        """PRINT "IF...THEN" inside an IF block must not confuse nesting."""
        program = [
            '10 IF 0=1 THEN',
            '20 PRINT "IF YOU THEN DO THIS"',
            '30 ELSE',
            '40 PRINT "CORRECT"',
            '50 ENDIF',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        errors = helpers.get_error_messages(results)
        assert errors == []
        assert 'CORRECT' in text

    def test_cipher_pattern(self, basic, helpers):
        """Full Caesar cipher pattern — the original failing scenario."""
        program = [
            '5 T$ = "HELLO"',
            '6 S = 3',
            '7 R$ = ""',
            '10 FOR I = 1 TO LEN(T$)',
            '20 CH$ = MID$(T$, I, 1)',
            '30 A = ASC(CH$)',
            '40 IF A >= 65 AND A <= 90 THEN',
            '50 A = A + S',
            '60 IF A > 90 THEN A = A - 26',
            '70 R$ = R$ + CHR$(A)',
            '80 ELSE',
            '90 R$ = R$ + CH$',
            '100 ENDIF',
            '110 NEXT I',
            '120 PRINT R$',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert 'KHOOR' in text


class TestIfThenRegistryCommands:
    """Test registry commands (SOUND, POKE, PAINT, etc.) in IF/THEN bodies.

    These commands are not handled by the AST parser — they must be passed
    through verbatim to the command registry. The AST converter must not
    silently drop their arguments.
    """

    def test_sound_in_then_body(self, basic, helpers):
        """SOUND with arguments should not be silently truncated"""
        program = [
            '10 F = 440',
            '20 IF F > 0 THEN SOUND F, 1',
            '30 PRINT "DONE"',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert 'DONE' in text
        # Should have a sound output (not an error about missing args)
        assert not any('ERROR' in t.upper() for t in text)

    def test_sound_with_expression_in_then(self, basic, helpers):
        """SOUND with expression args in IF/THEN body"""
        program = [
            '10 F1 = 200',
            '20 RF = 100',
            '30 SC = 5',
            '40 IF SC >= 3 THEN SOUND F1+RF, 8: SC = 0',
            '50 PRINT SC',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert any('0' in t for t in text), "SC should be 0 after assignment"

    def test_sound_preserves_both_args(self, basic, helpers):
        """SOUND with two arguments should not lose the second arg"""
        program = [
            '10 IF 1=1 THEN SOUND 440, 1',
            '20 PRINT "DONE"',
        ]
        results = helpers.execute_program(basic, program)
        # Should produce a sound event, not an error
        has_sound = any(item.get('type') == 'sound' for item in results)
        assert has_sound, "Should produce sound output"
        text = helpers.get_text_output(results)
        assert 'DONE' in text

    def test_registry_command_with_colon_and_assignment(self, basic, helpers):
        """Registry command followed by assignment in IF/THEN body"""
        program = [
            '10 X = 1',
            '20 IF X = 1 THEN SOUND 440, 1: X = 99',
            '30 PRINT X',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert any('99' in t for t in text)

    def test_multiple_registry_commands_in_then(self, basic, helpers):
        """Multiple registry commands separated by colons in IF/THEN"""
        program = [
            '10 IF 1=1 THEN SOUND 440, 1: SOUND 880, 1',
            '20 PRINT "DONE"',
        ]
        results = helpers.execute_program(basic, program)
        sound_count = sum(1 for item in results if item.get('type') == 'sound')
        assert sound_count == 2, f"Should produce 2 sound events, got {sound_count}"

    def test_dim_in_then_body(self, basic, helpers):
        """DIM in IF/THEN body should work"""
        program = [
            '10 IF 1=1 THEN DIM A(5)',
            '20 A(3) = 42',
            '30 PRINT A(3)',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert any('42' in t for t in text)

    def test_registry_command_in_else_body(self, basic, helpers):
        """Registry command in ELSE body should preserve arguments"""
        program = [
            '10 IF 0=1 THEN PRINT "NO" ELSE SOUND 880, 1',
            '20 PRINT "DONE"',
        ]
        results = helpers.execute_program(basic, program)
        has_sound = any(item.get('type') == 'sound' for item in results)
        assert has_sound, "ELSE body should produce sound output"
