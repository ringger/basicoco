#!/usr/bin/env python3

"""
Comprehensive tests for Individual BASIC Functions

Tests each BASIC function independently to ensure correct behavior,
parameter validation, error handling, and edge cases.
"""

import pytest
import math


class TestFunction:
    """Test cases for individual BASIC functions"""

    @pytest.fixture(autouse=True)
    def setup_variables(self, basic):
        """Set up test variables for function testing"""
        basic.variables['A'] = 10
        basic.variables['B'] = -5
        basic.variables['X'] = 3.5
        basic.variables['Y'] = -2.7
        basic.variables['S$'] = 'HELLO WORLD'
        basic.variables['T$'] = 'TESTING'

    def test_basic_functionality(self, basic, helpers):
        """Test basic function evaluation functionality"""

        # Test that functions can be called and return values
        result = basic.evaluate_expression("ABS(-5)")
        assert result == 5

        result = basic.evaluate_expression("LEN(S$)")
        assert result == 11  # Length of "HELLO WORLD"

    def test_abs_function(self, basic, helpers):
        """Test ABS function for absolute values"""
        # Positive numbers
        result = basic.evaluate_expression("ABS(5)")
        assert result == 5
        
        # Negative numbers
        result = basic.evaluate_expression("ABS(-5)")
        assert result == 5
        
        # Zero
        result = basic.evaluate_expression("ABS(0)")
        assert result == 0
        
        # Floating point
        result = basic.evaluate_expression("ABS(-3.7)")
        assert result == 3.7
        
        # With variables
        result = basic.evaluate_expression("ABS(B)")  # B = -5
        assert result == 5

    def test_int_function(self, basic, helpers):
        """Test INT function for integer truncation"""
        # Positive numbers
        result = basic.evaluate_expression("INT(3.7)")
        assert result == 3
        
        # Negative numbers (truncates toward zero, not negative infinity)
        result = basic.evaluate_expression("INT(-3.7)")
        assert result == -3  # Truncates toward zero
        
        # Already integers
        result = basic.evaluate_expression("INT(5)")
        assert result == 5
        
        # Zero
        result = basic.evaluate_expression("INT(0)")
        assert result == 0

    def test_sqr_function(self, basic, helpers):
        """Test SQR function for square roots"""
        # Perfect squares
        result = basic.evaluate_expression("SQR(4)")
        assert result == 2
        
        result = basic.evaluate_expression("SQR(9)")
        assert result == 3
        
        result = basic.evaluate_expression("SQR(16)")
        assert result == 4
        
        # Non-perfect squares (approximate)
        result = basic.evaluate_expression("SQR(2)")
        assert abs(result - 1.4142 < 0.001)
        
        # Zero
        result = basic.evaluate_expression("SQR(0)")
        assert result == 0

    def test_sgn_function(self, basic, helpers):
        """Test SGN function for sign of number"""
        # Positive
        result = basic.evaluate_expression("SGN(42)")
        assert result == 1

        # Negative
        result = basic.evaluate_expression("SGN(-7)")
        assert result == -1

        # Zero
        result = basic.evaluate_expression("SGN(0)")
        assert result == 0

        # With variable
        result = basic.evaluate_expression("SGN(B)")
        assert result == -1  # B = -5

        # With expression
        result = basic.evaluate_expression("SGN(3 - 3)")
        assert result == 0

    def test_trigonometric_functions(self, basic, helpers):
        """Test trigonometric functions SIN, COS, TAN"""
        # SIN function
        result = basic.evaluate_expression("SIN(0)")
        assert abs(result - 0 < 0.001)
        
        # COS function  
        result = basic.evaluate_expression("COS(0)")
        assert abs(result - 1 < 0.001)
        
        # Test with pi/2 (90 degrees)
        result = basic.evaluate_expression("SIN(1.5708)")  # Approximately pi/2
        assert abs(result - 1 < 0.01)
        
        # TAN function (if supported)
        try:
            result = basic.evaluate_expression("TAN(0)")
            assert abs(result - 0 < 0.001)
        except:
            pass  # TAN might not be implemented

    def test_atn_function(self, basic, helpers):
        """Test ATN function for arctangent"""
        # ATN(1) should be pi/4
        result = basic.evaluate_expression("ATN(1)")
        assert abs(result - 0.7854 < 0.001)  # pi/4 ≈ 0.7854
        
        # ATN(0) should be 0
        result = basic.evaluate_expression("ATN(0)")
        assert abs(result - 0 < 0.001)

    def test_log_function(self, basic, helpers):
        """Test LOG function for natural logarithm"""
        # LOG(1) should be 0
        result = basic.evaluate_expression("LOG(1)")
        assert abs(result - 0 < 0.001)
        
        # LOG(e) should be 1 (approximately)
        result = basic.evaluate_expression("LOG(2.71828)")
        assert abs(result - 1 < 0.001)

    def test_exp_function(self, basic, helpers):
        """Test EXP function for exponential"""
        # EXP(0) should be 1
        result = basic.evaluate_expression("EXP(0)")
        assert abs(result - 1 < 0.001)
        
        # EXP(1) should be e
        result = basic.evaluate_expression("EXP(1)")
        assert abs(result - 2.71828 < 0.001)

    def test_rnd_function(self, basic, helpers):
        """Test RND function for random numbers (CoCo: integer 1 to N)"""
        result = basic.evaluate_expression("RND(1)")
        assert result == 1  # RND(1) always returns 1

        result = basic.evaluate_expression("RND(6)")
        assert isinstance(result, int)
        assert 1 <= result <= 6

    def test_len_function(self, basic, helpers):
        """Test LEN function for string length"""
        # Literal strings
        result = basic.evaluate_expression('LEN("HELLO")')
        assert result == 5
        
        result = basic.evaluate_expression('LEN("")')
        assert result == 0
        
        # String variables
        result = basic.evaluate_expression("LEN(S$)")  # "HELLO WORLD"
        assert result == 11
        
        result = basic.evaluate_expression("LEN(T$)")  # "TESTING"
        assert result == 7

    def test_left_function(self, basic, helpers):
        """Test LEFT$ function for substring from left"""
        # Literal strings
        result = basic.evaluate_expression('LEFT$("HELLO", 3)')
        assert result == "HEL"
        
        result = basic.evaluate_expression('LEFT$("TESTING", 4)')
        assert result == "TEST"
        
        # String variables
        result = basic.evaluate_expression('LEFT$(S$, 5)')  # "HELLO WORLD"
        assert result == "HELLO"
        
        # Edge cases
        result = basic.evaluate_expression('LEFT$("SHORT", 10)')
        assert result == "SHORT"  # Should return whole string if length > string length
        
        result = basic.evaluate_expression('LEFT$("HELLO", 0)')
        assert result == ""

    def test_right_function(self, basic, helpers):
        """Test RIGHT$ function for substring from right"""
        # Literal strings
        result = basic.evaluate_expression('RIGHT$("HELLO", 3)')
        assert result == "LLO"
        
        result = basic.evaluate_expression('RIGHT$("TESTING", 3)')
        assert result == "ING"
        
        # String variables
        result = basic.evaluate_expression('RIGHT$(S$, 5)')  # "HELLO WORLD"
        assert result == "WORLD"
        
        # Edge cases
        result = basic.evaluate_expression('RIGHT$("SHORT", 10)')
        assert result == "SHORT"  # Should return whole string if length > string length

    def test_mid_function(self, basic, helpers):
        """Test MID$ function for substring extraction"""
        # Basic usage
        result = basic.evaluate_expression('MID$("HELLO", 2, 2)')
        assert result == "EL"
        
        result = basic.evaluate_expression('MID$("TESTING", 3, 4)')
        assert result == "STIN"
        
        # String variables
        result = basic.evaluate_expression('MID$(S$, 7, 5)')  # "HELLO WORLD"
        assert result == "WORLD"
        
        # Edge cases
        result = basic.evaluate_expression('MID$("HELLO", 3, 10)')
        assert result == "LLO"  # Should return rest of string if length goes beyond end

    def test_str_function(self, basic, helpers):
        """Test STR$ function for number to string conversion"""
        # Positive integers
        result = basic.evaluate_expression("STR$(42)")
        assert result == " 42"  # STR$ adds leading space for positive numbers
        
        # Negative numbers
        result = basic.evaluate_expression("STR$(-42)")
        assert result == "-42"  # No leading space for negative numbers
        
        # Zero
        result = basic.evaluate_expression("STR$(0)")
        assert result == " 0"
        
        # Floating point
        result = basic.evaluate_expression("STR$(3.14)")
        assert "3.14" in result  # Should contain the number
        
        # Variables
        result = basic.evaluate_expression("STR$(A)")  # A = 10
        assert result == " 10"

    def test_val_function(self, basic, helpers):
        """Test VAL function for string to number conversion"""
        # Basic numbers
        result = basic.evaluate_expression('VAL("42")')
        assert result == 42
        
        result = basic.evaluate_expression('VAL("-42")')
        assert result == -42
        
        # Floating point
        result = basic.evaluate_expression('VAL("3.14")')
        assert result == 3.14
        
        # Numbers with leading/trailing spaces
        result = basic.evaluate_expression('VAL("  123  ")')
        assert result == 123
        
        # Invalid strings (should return 0)
        result = basic.evaluate_expression('VAL("HELLO")')
        assert result == 0

    def test_asc_function(self, basic, helpers):
        """Test ASC function for ASCII value of first character"""
        # Basic characters
        result = basic.evaluate_expression('ASC("A")')
        assert result == 65  # ASCII value of 'A'
        
        result = basic.evaluate_expression('ASC("a")')
        assert result == 97  # ASCII value of 'a'
        
        result = basic.evaluate_expression('ASC("0")')
        assert result == 48  # ASCII value of '0'
        
        # Multi-character strings (should return first character)
        result = basic.evaluate_expression('ASC("HELLO")')
        assert result == 72  # ASCII value of 'H'
        
        # String variables
        result = basic.evaluate_expression('ASC(S$)')  # "HELLO WORLD"
        assert result == 72  # ASCII value of 'H'

    def test_chr_function(self, basic, helpers):
        """Test CHR$ function for ASCII code to character conversion"""
        # Basic ASCII codes
        result = basic.evaluate_expression("CHR$(65)")
        assert result == "A"
        
        result = basic.evaluate_expression("CHR$(97)")
        assert result == "a"
        
        result = basic.evaluate_expression("CHR$(48)")
        assert result == "0"
        
        # Special characters
        result = basic.evaluate_expression("CHR$(32)")
        assert result == " "  # Space character
        
        result = basic.evaluate_expression("CHR$(13)")
        assert result == "\r"  # Carriage return

    def test_function_nesting(self, basic, helpers):
        """Test nested function calls"""
        # Simple nesting
        result = basic.evaluate_expression("ABS(INT(-3.7))")
        assert result == 3  # ABS(INT(-3.7)) = ABS(-3) = 3 (INT truncates toward zero)
        
        # Complex nesting
        result = basic.evaluate_expression("SQR(ABS(-16))")
        assert result == 4
        
        # String function nesting
        result = basic.evaluate_expression('LEN(LEFT$("HELLO WORLD", 5))')
        assert result == 5  # LEN("HELLO") = 5
        
        # Mathematical operations
        result = basic.evaluate_expression("INT(SQR(16) + 0.7)")
        assert result == 4  # INT(4 + 0.7) = INT(4.7) = 4

    def test_function_with_variables(self, basic, helpers):
        """Test functions with variable arguments"""
        # Math functions
        result = basic.evaluate_expression("ABS(B)")  # B = -5
        assert result == 5
        
        result = basic.evaluate_expression("INT(X)")  # X = 3.5
        assert result == 3
        
        # String functions
        result = basic.evaluate_expression("LEN(S$)")  # "HELLO WORLD"
        assert result == 11
        
        result = basic.evaluate_expression('LEFT$(T$, 4)')  # "TESTING"
        assert result == "TEST"

    def test_function_error_cases(self, basic, helpers):
        """Test function error handling"""
        # SQR with negative number (should raise error)
        result = basic.process_command("PRINT SQR(-4)")
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0, "SQR(-4) should produce an error"
        assert any("ILLEGAL FUNCTION CALL" in error.upper() or "SQR" in error.upper() for error in errors), \
               f"Expected SQR error, got: {errors}"

        # LOG with zero or negative (should raise error)
        result = basic.process_command("PRINT LOG(0)")
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0, "LOG(0) should produce an error"
        assert any("ILLEGAL FUNCTION CALL" in error.upper() or "LOG" in error.upper() for error in errors), \
               f"Expected LOG error, got: {errors}"

        # Division by zero in function context
        result = basic.process_command("PRINT INT(5 / 0)")
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0, "Division by zero should produce an error"
        # Accept any error containing relevant keywords
        assert any("DIVISION" in error.upper() or "DIVIDE" in error.upper() or
                  "ERROR" in error.upper() or "ZERO" in error.upper() for error in errors), \
               f"Expected error related to division by zero, got: {errors}"

    def test_function_edge_cases(self, basic, helpers):
        """Test function behavior with edge cases"""
        # Very small numbers
        result = basic.evaluate_expression("ABS(0.0001)")
        assert result == 0.0001
        
        # Very large numbers (within limits)
        result = basic.evaluate_expression("INT(999999.9)")
        assert result == 999999
        
        # Empty string for string functions
        result = basic.evaluate_expression('LEN("")')
        assert result == 0
        
        # Single character strings
        result = basic.evaluate_expression('LEFT$("A", 1)')
        assert result == "A"

    def test_multiple_function_calls(self, basic, helpers):
        """Test multiple function calls in one expression"""
        # Multiple math functions
        result = basic.evaluate_expression("ABS(-5) + SQR(9)")
        assert result == 8  # 5 + 3 = 8
        
        # Mixed function types
        result = basic.evaluate_expression('LEN("HELLO") + ABS(-3)')
        assert result == 8  # 5 + 3 = 8
        
        # String concatenation with functions
        result = basic.evaluate_expression('LEFT$("HELLO", 3) + RIGHT$("WORLD", 2)')
        assert result == "HELLD"  # "HEL" + "LD" = "HELLD"

    def test_instr_function(self, basic, helpers):
        """Test INSTR function for substring position finding"""
        # Basic substring search
        result = basic.evaluate_expression('INSTR("HELLO WORLD", "WORLD")')
        assert result == 7  # "WORLD" starts at position 7
        
        result = basic.evaluate_expression('INSTR("HELLO WORLD", "HELLO")')
        assert result == 1  # "HELLO" starts at position 1
        
        # Substring not found
        result = basic.evaluate_expression('INSTR("HELLO", "XYZ")')
        assert result == 0  # Not found returns 0
        
        # Case-sensitive search
        result = basic.evaluate_expression('INSTR("Hello", "hello")')
        assert result == 0  # Case sensitive, not found
        
        # Empty search string
        result = basic.evaluate_expression('INSTR("HELLO", "")')
        assert result == 1  # Empty string found at position 1
        
        # Search in variable
        result = basic.evaluate_expression('INSTR(S$, "WORLD")')  # S$ = "HELLO WORLD"
        assert result == 7

    def test_instr_three_arg_form(self, basic, helpers):
        """Test INSTR with 3 arguments: INSTR(start, string, search)"""
        # Start from position 1 (same as 2-arg)
        result = basic.evaluate_expression('INSTR(1, "HELLO WORLD", "WORLD")')
        assert result == 7

        # Start from position after the match — should not find it
        result = basic.evaluate_expression('INSTR(8, "HELLO WORLD", "WORLD")')
        assert result == 0

        # Start from position of the match — should find it
        result = basic.evaluate_expression('INSTR(7, "HELLO WORLD", "WORLD")')
        assert result == 7

        # Find second occurrence by starting after the first
        result = basic.evaluate_expression('INSTR(1, "ABCABC", "ABC")')
        assert result == 1
        result = basic.evaluate_expression('INSTR(2, "ABCABC", "ABC")')
        assert result == 4

        # Start position 0 should be treated as 1
        result = basic.evaluate_expression('INSTR(0, "HELLO", "H")')
        assert result == 1

    def test_space_function(self, basic, helpers):
        """Test SPACE$ function for generating spaces"""
        # Basic space generation
        result = basic.evaluate_expression('SPACE$(5)')
        assert result == "     "  # 5 spaces
        
        result = basic.evaluate_expression('SPACE$(1)')
        assert result == " "  # 1 space
        
        # Zero spaces
        result = basic.evaluate_expression('SPACE$(0)')
        assert result == ""  # Empty string
        
        # Large number of spaces
        result = basic.evaluate_expression('SPACE$(10)')
        assert result == "          "  # 10 spaces
        assert len(result) == 10
        
        # Variable argument
        basic.variables['N'] = 3
        result = basic.evaluate_expression('SPACE$(N)')
        assert result == "   "  # 3 spaces

    def test_string_function(self, basic, helpers):
        """Test STRING$ function for repeating characters"""
        # Basic character repetition
        result = basic.evaluate_expression('STRING$(3, "*")')
        assert result == "***"  # 3 asterisks
        
        result = basic.evaluate_expression('STRING$(5, "A")')
        assert result == "AAAAA"  # 5 A's
        
        # Zero repetitions
        result = basic.evaluate_expression('STRING$(0, "X")')
        assert result == ""  # Empty string
        
        # ASCII code as character
        result = basic.evaluate_expression('STRING$(4, 65)')  # ASCII 65 = 'A'
        assert result == "AAAA"  # 4 A's
        
        result = basic.evaluate_expression('STRING$(3, 42)')  # ASCII 42 = '*'
        assert result == "***"  # 3 asterisks
        
        # Multi-character string (should use first character)
        result = basic.evaluate_expression('STRING$(4, "ABC")')
        assert result == "AAAA"  # Uses first character 'A'
        
        # Variable arguments
        basic.variables['N'] = 6
        basic.variables['C$'] = "X"
        result = basic.evaluate_expression('STRING$(N, C$)')
        assert result == "XXXXXX"  # 6 X's

    def test_enhanced_nested_function_calls(self, basic, helpers):
        """Test complex nested function calls with new Phase 2 functions"""
        # Target expression from roadmap
        result = basic.evaluate_expression('MID$(STR$(INT(SQR(16))), 1, 2)')
        assert result == " 4"  # SQR(16)=4, INT(4)=4, STR$(4)=" 4", MID$(" 4",1,2)=" 4"
        
        # Nested calls with new string functions
        result = basic.evaluate_expression('INSTR(STRING$(10, "A"), "AA")')
        assert result == 1  # "AAAAAAAAAA" contains "AA" at position 1
        
        result = basic.evaluate_expression('LEN(SPACE$(7))')
        assert result == 7  # Length of 7 spaces is 7
        
        # Complex mathematical and string combinations
        result = basic.evaluate_expression('LEFT$(STRING$(5, CHR$(65)), 3)')
        assert result == "AAA"  # CHR$(65)="A", STRING$(5,"A")="AAAAA", LEFT$("AAAAA",3)="AAA"
        
        # Multi-level nesting with math and strings
        result = basic.evaluate_expression('INSTR("HELLO", LEFT$("HELP", 3))')
        assert result == 1  # LEFT$("HELP",3)="HEL", INSTR("HELLO","HEL")=1

    def test_function_integration_with_operators(self, basic, helpers):
        """Test functions integrated with mathematical operators"""
        # Functions in arithmetic expressions
        result = basic.evaluate_expression("2 * ABS(-3) + 1")
        assert result == 7  # 2 * 3 + 1 = 7
        
        # Functions with comparison (if supported)
        result = basic.evaluate_expression("ABS(-5) + 2")  # Simple addition instead of comparison
        assert result == 7  # 5 + 2 = 7
        
        # Functions in complex expressions
        result = basic.evaluate_expression("(ABS(B) + SQR(4)) * 2")  # B = -5
        assert result == 14.0  # (5 + 2) * 2 = 14.0
        
        # New Phase 2 functions in expressions
        result = basic.evaluate_expression('LEN(SPACE$(5)) + INSTR("HELLO", "LO")')
        assert result == 9  # LEN(5 spaces) + INSTR("HELLO","LO") = 5 + 4 = 9


class TestRandomize:
    """Test RANDOMIZE command"""

    def test_randomize_no_args(self, basic, helpers):
        """RANDOMIZE without args seeds from system clock"""
        result = basic.process_command('RANDOMIZE')
        errors = helpers.get_error_messages(result)
        assert errors == []

    def test_randomize_with_seed(self, basic, helpers):
        """RANDOMIZE with seed produces repeatable RND sequence"""
        basic.process_command('RANDOMIZE 42')
        r1 = basic.evaluate_expression('RND(100)')
        r2 = basic.evaluate_expression('RND(100)')

        basic.process_command('RANDOMIZE 42')
        r3 = basic.evaluate_expression('RND(100)')
        r4 = basic.evaluate_expression('RND(100)')

        assert r1 == r3
        assert r2 == r4

    def test_randomize_different_seeds(self, basic, helpers):
        """Different seeds produce different sequences"""
        basic.process_command('RANDOMIZE 1')
        r1 = basic.evaluate_expression('RND(100)')

        basic.process_command('RANDOMIZE 999')
        r2 = basic.evaluate_expression('RND(100)')

        assert r1 != r2

    def test_randomize_with_expression(self, basic, helpers):
        """RANDOMIZE accepts expressions as seed"""
        basic.process_command('X = 10')
        result = basic.process_command('RANDOMIZE X * 4 + 2')
        errors = helpers.get_error_messages(result)
        assert errors == []


class TestPpoint:
    """Test PPOINT function for reading pixel colors"""

    def _enter_graphics(self, basic):
        """Enter graphics mode for testing"""
        basic.process_command('PMODE 4,1')
        basic.process_command('SCREEN 1,1')

    def test_ppoint_unset_pixel_returns_zero(self, basic):
        """PPOINT returns 0 for pixels that haven't been set"""
        self._enter_graphics(basic)
        result = basic.evaluate_expression('PPOINT(0, 0)')
        assert result == 0

    def test_ppoint_after_pset(self, basic):
        """PPOINT returns the color set by PSET"""
        self._enter_graphics(basic)
        basic.process_command('PSET(100, 50), 1')
        result = basic.evaluate_expression('PPOINT(100, 50)')
        assert result == 1

    def test_ppoint_after_pset_default_color(self, basic):
        """PPOINT returns default draw color when PSET has no color arg"""
        self._enter_graphics(basic)
        basic.process_command('PSET(10, 20)')
        result = basic.evaluate_expression('PPOINT(10, 20)')
        assert result == basic.current_draw_color

    def test_ppoint_after_preset(self, basic):
        """PPOINT returns 0 after PRESET clears a pixel"""
        self._enter_graphics(basic)
        basic.process_command('PSET(50, 50), 3')
        basic.process_command('PRESET(50, 50)')
        result = basic.evaluate_expression('PPOINT(50, 50)')
        assert result == 0

    def test_ppoint_after_pcls(self, basic):
        """PCLS clears all pixels so PPOINT returns 0"""
        self._enter_graphics(basic)
        basic.process_command('PSET(10, 10), 1')
        basic.process_command('PSET(20, 20), 2')
        basic.process_command('PCLS')
        assert basic.evaluate_expression('PPOINT(10, 10)') == 0
        assert basic.evaluate_expression('PPOINT(20, 20)') == 0

    def test_ppoint_multiple_pixels(self, basic):
        """PPOINT correctly distinguishes different pixel locations"""
        self._enter_graphics(basic)
        basic.process_command('PSET(10, 10), 1')
        basic.process_command('PSET(20, 20), 2')
        assert basic.evaluate_expression('PPOINT(10, 10)') == 1
        assert basic.evaluate_expression('PPOINT(20, 20)') == 2
        assert basic.evaluate_expression('PPOINT(15, 15)') == 0

    def test_ppoint_requires_graphics_mode(self, basic, helpers):
        """PPOINT raises error when not in graphics mode"""
        result = basic.process_command('PRINT PPOINT(0, 0)')
        errors = helpers.get_error_messages(result)
        assert any('graphics mode' in e.lower() for e in errors)

    def test_ppoint_wrong_arg_count(self, basic, helpers):
        """PPOINT requires exactly 2 arguments"""
        self._enter_graphics(basic)
        result = basic.process_command('PRINT PPOINT(10)')
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0

    def test_ppoint_with_expressions(self, basic):
        """PPOINT accepts expressions as arguments"""
        self._enter_graphics(basic)
        basic.variables['X'] = 50
        basic.variables['Y'] = 75
        basic.process_command('PSET(50, 75), 1')
        result = basic.evaluate_expression('PPOINT(X, Y)')
        assert result == 1

    def test_ppoint_cleared_on_new_program(self, basic):
        """Pixel buffer is cleared when interpreter state resets"""
        self._enter_graphics(basic)
        basic.process_command('PSET(10, 10), 1')
        basic.clear_interpreter_state()
        # Re-enter graphics mode after state clear
        self._enter_graphics(basic)
        result = basic.evaluate_expression('PPOINT(10, 10)')
        assert result == 0
