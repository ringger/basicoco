#!/usr/bin/env python3

"""
Comprehensive tests for Expression Evaluation System

Tests the expression parser and evaluator that handles BASIC expressions,
operator precedence, function calls, and variable resolution.
"""

import pytest
from emulator.core import CoCoBasic


class TestExpressionEvaluation:
    """Test cases for Expression Evaluation functionality"""

    @pytest.fixture(autouse=True)
    def setup_variables(self, basic):
        """Set up test environment"""
        # Set up test variables
        basic.variables['A'] = 10
        basic.variables['B'] = 5
        basic.variables['C'] = 2
        basic.variables['D'] = 1
        basic.variables['X'] = 3.5
        basic.variables['Y'] = 2.5
        basic.variables['S$'] = 'HELLO'
        basic.variables['T$'] = 'WORLD'

    def test_basic_arithmetic_expressions(self, basic, helpers):
        """Test basic arithmetic operations"""
        # Addition
        result = basic.evaluate_expression("2 + 3")
        assert result == 5
        
        # Subtraction
        result = basic.evaluate_expression("10 - 4")
        assert result == 6
        
        # Multiplication
        result = basic.evaluate_expression("3 * 4")
        assert result == 12
        
        # Division
        result = basic.evaluate_expression("15 / 3")
        assert result == 5
        
        # Integer division (using INT function instead of backslash)
        result = basic.evaluate_expression("INT(7 / 2)")
        assert result == 3

    def test_operator_precedence(self, basic, helpers):
        """Test operator precedence rules"""
        # Multiplication before addition
        result = basic.evaluate_expression("2 + 3 * 4")
        assert result == 14
        
        # Division before subtraction
        result = basic.evaluate_expression("12 - 8 / 2")
        assert result == 8
        
        # Parentheses override precedence
        result = basic.evaluate_expression("(2 + 3) * 4")
        assert result == 20
        
        # Nested parentheses
        result = basic.evaluate_expression("((2 + 3) * 4) - 5")
        assert result == 15

    def test_variable_resolution(self, basic, helpers):
        """Test variable access and resolution"""
        # Simple variable access
        result = basic.evaluate_expression("A")
        assert result == 10
        
        # Variables in expressions
        result = basic.evaluate_expression("A + B")
        assert result == 15
        
        # Complex variable expressions
        result = basic.evaluate_expression("A * B - C")
        assert result == 48
        
        # String variables
        result = basic.evaluate_expression("S$")
        assert result == "HELLO"

    def test_string_expressions(self, basic, helpers):
        """Test string operations and concatenation"""
        # String literals
        result = basic.evaluate_expression('"HELLO"')
        assert result == "HELLO"
        
        # String concatenation
        result = basic.evaluate_expression('"HELLO" + " " + "WORLD"')
        assert result == "HELLO WORLD"
        
        # String variables
        result = basic.evaluate_expression('S$ + " " + T$')
        assert result == "HELLO WORLD"
        
        # Mixed string and variable
        result = basic.evaluate_expression('"Value: " + S$')
        assert result == "Value: HELLO"

    def test_comparison_operations(self, basic, helpers):
        """Comparison operators return -1 (true) or 0 (false), matching CoCo BASIC."""
        # Greater than (true)
        text = helpers.get_text_output(basic.process_command("PRINT A > B"))
        assert text[0].strip() == "-1"

        # Less than (false)
        text = helpers.get_text_output(basic.process_command("PRINT A < B"))
        assert text[0].strip() == "0"

        # Equal (true)
        text = helpers.get_text_output(basic.process_command("PRINT A = 10"))
        assert text[0].strip() == "-1"

        # Equal (false)
        text = helpers.get_text_output(basic.process_command("PRINT A = 5"))
        assert text[0].strip() == "0"

        # Not equal (true)
        text = helpers.get_text_output(basic.process_command("PRINT A <> B"))
        assert text[0].strip() == "-1"

        # Not equal (false)
        text = helpers.get_text_output(basic.process_command("PRINT B <> 5"))
        assert text[0].strip() == "0"

        # Less than or equal
        text = helpers.get_text_output(basic.process_command("PRINT B <= 5"))
        assert text[0].strip() == "-1"
        text = helpers.get_text_output(basic.process_command("PRINT A <= 5"))
        assert text[0].strip() == "0"

        # Greater than or equal
        text = helpers.get_text_output(basic.process_command("PRINT A >= 10"))
        assert text[0].strip() == "-1"
        text = helpers.get_text_output(basic.process_command("PRINT B >= 10"))
        assert text[0].strip() == "0"

    def test_comparison_returns_integers(self, basic, helpers):
        """Comparisons return integer -1/0, not Python bool."""
        result = basic.evaluate_expression("A > 5")
        assert result == -1
        assert type(result) is int

        result = basic.evaluate_expression("B < 3")
        assert result == 0
        assert type(result) is int

    def test_comparison_in_arithmetic(self, basic, helpers):
        """Comparison results can be used in arithmetic (CoCo idiom)."""
        # X = X + (condition) uses -1/0 to conditionally subtract
        basic.variables['X'] = 100
        result = basic.evaluate_expression("X + (X > 50)")
        assert result == 99  # 100 + (-1)

        result = basic.evaluate_expression("X + (X < 50)")
        assert result == 100  # 100 + 0

    def test_comparison_with_string(self, basic, helpers):
        """String comparisons also return -1/0."""
        result = basic.evaluate_expression('"A" < "B"')
        assert result == -1
        result = basic.evaluate_expression('"B" < "A"')
        assert result == 0
        result = basic.evaluate_expression('"HELLO" = "HELLO"')
        assert result == -1

    def test_bitwise_and(self, basic, helpers):
        """AND is bitwise on integers, matching CoCo BASIC."""
        assert basic.evaluate_expression("82 AND 223") == 82
        assert basic.evaluate_expression("255 AND 15") == 15
        assert basic.evaluate_expression("170 AND 85") == 0
        assert basic.evaluate_expression("7 AND 3") == 3
        assert basic.evaluate_expression("0 AND 255") == 0
        assert basic.evaluate_expression("-1 AND 255") == 255

    def test_bitwise_or(self, basic, helpers):
        """OR is bitwise on integers, matching CoCo BASIC."""
        assert basic.evaluate_expression("5 OR 3") == 7
        assert basic.evaluate_expression("170 OR 85") == 255
        assert basic.evaluate_expression("0 OR 0") == 0
        assert basic.evaluate_expression("0 OR 255") == 255
        assert basic.evaluate_expression("-1 OR 0") == -1

    def test_bitwise_not(self, basic, helpers):
        """NOT is bitwise complement, matching CoCo BASIC."""
        assert basic.evaluate_expression("NOT 0") == -1
        assert basic.evaluate_expression("NOT -1") == 0
        assert basic.evaluate_expression("NOT 1") == -2
        assert basic.evaluate_expression("NOT 255") == -256

    def test_and_or_with_comparisons(self, basic, helpers):
        """AND/OR work as logical when applied to comparison results (-1/0)."""
        # -1 AND -1 = -1
        assert basic.evaluate_expression("(A > 5) AND (B > 3)") == -1
        # -1 AND 0 = 0
        assert basic.evaluate_expression("(A > 5) AND (B > 10)") == 0
        # 0 OR -1 = -1
        assert basic.evaluate_expression("(A < 5) OR (B > 3)") == -1
        # 0 OR 0 = 0
        assert basic.evaluate_expression("(A < 5) OR (B > 10)") == 0

    def test_not_with_comparisons(self, basic, helpers):
        """NOT works as logical negation on comparison results (-1/0)."""
        assert basic.evaluate_expression("NOT (A > 5)") == 0    # NOT -1 = 0
        assert basic.evaluate_expression("NOT (A < 5)") == -1   # NOT 0 = -1

    def test_and_with_chr_asc_pattern(self, basic, helpers):
        """CHR$(ASC(x) AND 223) uppercase conversion pattern."""
        text = helpers.get_text_output(
            basic.process_command('PRINT CHR$(ASC("r") AND 223)'))
        assert text[0].strip() == "R"
        text = helpers.get_text_output(
            basic.process_command('PRINT CHR$(ASC("R") AND 223)'))
        assert text[0].strip() == "R"

    def test_print_not_expression(self, basic, helpers):
        """PRINT NOT expr works without parentheses."""
        text = helpers.get_text_output(basic.process_command('PRINT NOT 0'))
        assert text[0].strip() == "-1"
        text = helpers.get_text_output(basic.process_command('PRINT NOT -1'))
        assert text[0].strip() == "0"

    def test_print_not_after_semicolon(self, basic, helpers):
        """PRINT "X=";NOT 0 works."""
        text = helpers.get_text_output(
            basic.process_command('PRINT "X=";NOT 0'))
        output = ''.join(text)
        assert 'X=-1' in output or 'X= -1' in output

    def test_function_calls(self, basic, helpers):
        """Test function calls in expressions"""
        # ABS function
        result = basic.evaluate_expression("ABS(-5)")
        assert result == 5
        
        # SQR function
        result = basic.evaluate_expression("SQR(16)")
        assert result == 4
        
        # INT function
        result = basic.evaluate_expression("INT(3.7)")
        assert result == 3
        
        # Functions with variables
        result = basic.evaluate_expression("ABS(A - B)")
        assert result == 5

    def test_string_functions(self, basic, helpers):
        """Test string functions in expressions"""
        # LEN function
        result = basic.evaluate_expression('LEN("HELLO")')
        assert result == 5
        
        result = basic.evaluate_expression("LEN(S$)")
        assert result == 5
        
        # LEFT$ function
        result = basic.evaluate_expression('LEFT$("HELLO", 3)')
        assert result == "HEL"
        
        # RIGHT$ function
        result = basic.evaluate_expression('RIGHT$("HELLO", 3)')
        assert result == "LLO"
        
        # MID$ function
        result = basic.evaluate_expression('MID$("HELLO", 2, 2)')
        assert result == "EL"

    def test_math_functions(self, basic, helpers):
        """Test mathematical functions"""
        # SIN, COS functions (approximate comparisons due to floating point)
        result = basic.evaluate_expression("INT(SIN(0) * 100)")
        assert result == 0
        
        result = basic.evaluate_expression("INT(COS(0) * 100)")
        assert result == 100
        
        # ATN function
        result = basic.evaluate_expression("ATN(1)")
        # Should be approximately PI/4
        assert abs(result - 0.7854 < 0.001)
        
        # LOG function
        result = basic.evaluate_expression("LOG(2.71828)")
        # Should be approximately 1
        assert abs(result - 1 < 0.001)
        
        # EXP function
        result = basic.evaluate_expression("EXP(1)")
        # Should be approximately e
        assert abs(result - 2.71828 < 0.001)

    def test_nested_function_calls(self, basic, helpers):
        """Test nested function calls"""
        # Simple nesting
        result = basic.evaluate_expression("ABS(INT(-3.7))")
        assert result == 3
        
        # Complex nesting
        result = basic.evaluate_expression("SQR(ABS(-16))")
        assert result == 4
        
        # Mixed with operators
        result = basic.evaluate_expression("ABS(-5) + SQR(9)")
        assert result == 8

    def test_complex_expressions(self, basic, helpers):
        """Test complex mixed expressions"""
        # Arithmetic with variables and functions
        result = basic.evaluate_expression("A + ABS(B - C * 3)")
        assert result == 11  # 10 + ABS(5 - 6) = 10 + 1
        
        # String concatenation with functions
        result = basic.evaluate_expression('S$ + " LENGTH=" + STR$(LEN(S$))')
        assert result == "HELLO LENGTH= 5"
        
        # Complex arithmetic expression  
        result = basic.evaluate_expression("(A + B) - (C * 5)")
        assert result == 5  # (10 + 5) - (2 * 5) = 15 - 10 = 5

    def test_error_handling(self, basic, helpers):
        """Test error handling in expression evaluation"""
        # Undefined variable should return 0 (BASIC default) or raise error
        result = basic.process_command("PRINT UNDEFINED_VAR")
        text_output = helpers.get_text_output(result)
        errors = helpers.get_error_messages(result)

        # Either should print 0 or produce error about undefined variable
        if errors:
            assert any("UNDEFINED" in error.upper() or "VARIABLE" in error.upper() for error in errors), \
                   f"Expected undefined variable error, got: {errors}"
        else:
            assert text_output == [' 0 '], f"Undefined variable should default to 0, got: {text_output}"

        # Division by zero should produce specific error
        result = basic.process_command("PRINT 5 / 0")
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0, "Division by zero should produce an error"
        # Accept any error containing relevant keywords
        assert any("DIVISION" in error.upper() or "DIVIDE" in error.upper() or
                  "ERROR" in error.upper() or "ZERO" in error.upper() for error in errors), \
               f"Expected error related to division by zero, got: {errors}"

        # Invalid function should produce function error
        result = basic.process_command("PRINT INVALID_FUNC(5)")
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0, "Invalid function should produce an error"
        # Accept any error containing relevant keywords
        assert any("FUNCTION" in error.upper() or "UNDEFINED" in error.upper() or
                  "ERROR" in error.upper() or "INVALID" in error.upper() for error in errors), \
               f"Expected error related to invalid function, got: {errors}"

    def test_parentheses_handling(self, basic, helpers):
        """Test complex parentheses handling"""
        # Nested parentheses
        result = basic.evaluate_expression("((2 + 3) * (4 - 1))")
        assert result == 15
        
        # Parentheses with functions
        result = basic.evaluate_expression("ABS((A - B) * -2)")
        assert result == 10
        
        # Mixed parentheses and operators
        result = basic.evaluate_expression("(A + B) * 2 - (C + D)")
        assert result == 27  # (10 + 5) * 2 - (2 + 1) = 30 - 3 = 27

    def test_type_coercion(self, basic, helpers):
        """Test type coercion between numbers and strings"""
        # String to number in arithmetic
        basic.variables['NUM$'] = '123'
        result = basic.evaluate_expression('VAL(NUM$) + 5')
        assert result == 128
        
        # Number to string
        result = basic.evaluate_expression('STR$(A) + " UNITS"')
        assert result == " 10 UNITS"  # STR$ adds leading space for positive numbers

    def test_variable_modification_effects(self, basic, helpers):
        """Test that variable changes affect expression results"""
        expr = "A + B"
        
        # Initial result
        result1 = basic.evaluate_expression(expr)
        assert result1 == 15
        
        # Change variable
        basic.variables['A'] = 20
        result2 = basic.evaluate_expression(expr)
        assert result2 == 25
        
        # Restore variable
        basic.variables['A'] = 10
        result3 = basic.evaluate_expression(expr)
        assert result3 == 15

    def test_empty_and_whitespace_expressions(self, basic, helpers):
        """Test handling of empty and whitespace expressions"""
        # Empty expression
        try:
            result = basic.evaluate_expression("")
            # Should either raise error or return 0
        except:
            pass  # Error is acceptable
        
        # Whitespace only
        try:
            result = basic.evaluate_expression("   ")
            # Should either raise error or return 0
        except:
            pass  # Error is acceptable

    def test_special_numeric_values(self, basic, helpers):
        """Test handling of special numeric values"""
        # Very large numbers
        result = basic.evaluate_expression("999999 + 1")
        assert result == 1000000
        
        # Decimal numbers
        result = basic.evaluate_expression("3.14 + 1.86")
        assert abs(result - 5.0 < 0.001)
        
        # Negative numbers
        result = basic.evaluate_expression("-5 + 3")
        assert result == -2

    def test_integration_with_basic_interpreter(self, basic, helpers):
        """Test integration with the BASIC interpreter"""
        # Test that expression evaluator works with interpreter context
        # This tests the evaluator when called from PRINT statements, etc.
        
        # Set up a variable through interpreter
        basic.variables['TEST_VAR'] = 42
        
        # Evaluate expression that depends on interpreter state
        result = basic.evaluate_expression("TEST_VAR * 2")
        assert result == 84

    def test_expression_cache_performance(self, basic, helpers):
        """Expression cache should measurably speed up repeated evaluations."""
        import time

        basic.variables['X'] = 5
        basic.variables['Y'] = 10
        expr = "X * X + Y * Y + X * Y - 3"
        iterations = 5000

        # Warm up cache with one call
        basic.evaluate_expression(expr)

        # Time with cache (already populated)
        start = time.perf_counter()
        for _ in range(iterations):
            basic.evaluate_expression(expr)
        cached_time = time.perf_counter() - start

        # Time without cache (clear it each iteration)
        start = time.perf_counter()
        for _ in range(iterations):
            basic._expr_cache.clear()
            basic.evaluate_expression(expr)
        uncached_time = time.perf_counter() - start

        # Cache should be at least 1.5x faster
        speedup = uncached_time / cached_time
        assert speedup > 1.5, f"Expected >1.5x speedup, got {speedup:.2f}x"
        # Print for visibility when run with -s
        print(f"\n  Expression cache: {speedup:.1f}x speedup "
              f"({uncached_time*1000:.0f}ms vs {cached_time*1000:.0f}ms "
              f"for {iterations} evals)")

    def test_expression_cache_reuses_parsed_ast(self, basic, helpers):
        """Repeated evaluate_expression calls should cache the parsed AST."""
        basic.variables['X'] = 10
        result1 = basic.evaluate_expression("X * 2 + 1")
        assert result1 == 21
        assert "X * 2 + 1" in basic._expr_cache

        # Change variable — cached AST should still evaluate correctly
        basic.variables['X'] = 20
        result2 = basic.evaluate_expression("X * 2 + 1")
        assert result2 == 41

    def test_evaluate_condition_uses_cache(self, basic, helpers):
        """evaluate_condition should cache parsed AST like evaluate_expression."""
        basic.variables['X'] = 10
        result1 = basic.evaluate_condition("X > 5")
        assert result1 is True
        assert "X > 5" in basic._expr_cache

        # Change variable — cached AST should still evaluate correctly
        basic.variables['X'] = 3
        result2 = basic.evaluate_condition("X > 5")
        assert result2 is False

    def test_compiled_registry_commands_performance(self, basic, helpers):
        """Pre-compiled registry commands should be faster than string dispatch."""
        import time
        from emulator.commands import CompiledCommand

        # Build a straight-line program heavy on registry commands.
        # DIM, SOUND, RESTORE, PAUSE 0, STOP are all registry commands.
        lines = []
        ln = 10
        for i in range(50):
            lines.append(f'{ln} DIM Z{i}(5)')
            ln += 10
        lines.append(f'{ln} DATA 1,2,3')
        ln += 10
        for i in range(20):
            lines.append(f'{ln} RESTORE')
            ln += 10
        helpers.load_program(basic, lines)
        iterations = 100

        # Run with compiled commands (default)
        start = time.perf_counter()
        for _ in range(iterations):
            basic.process_command('RUN')
        compiled_time = time.perf_counter() - start

        # Decompile: replace CompiledCommand entries with original strings
        helpers.load_program(basic, lines)
        for key, val in list(basic.expanded_program.items()):
            if isinstance(val, CompiledCommand):
                for cmd_name, info in basic.command_registry.commands.items():
                    if info['handler'] == val.handler:
                        basic.expanded_program[key] = f"{cmd_name} {val.args}".strip()
                        break

        start = time.perf_counter()
        for _ in range(iterations):
            basic.process_command('RUN')
        string_time = time.perf_counter() - start

        speedup = string_time / compiled_time
        assert speedup > 1.05, f"Expected compiled to be faster, got {speedup:.2f}x"
        print(f"\n  Compiled commands: {speedup:.2f}x speedup "
              f"({string_time*1000:.0f}ms vs {compiled_time*1000:.0f}ms "
              f"for {iterations} runs)")

    def test_compiled_commands_execute_correctly(self, basic, helpers):
        """Programs with compiled NEXT/ELSE/ENDIF/WEND/LOOP should run correctly."""
        from emulator.commands import CompiledCommand

        # FOR/NEXT loop
        helpers.load_program(basic, [
            '10 S = 0',
            '20 FOR I = 1 TO 5',
            '30 S = S + I',
            '40 NEXT I',
            '50 PRINT S',
        ])
        # Verify NEXT is compiled
        next_entries = [v for v in basic.expanded_program.values()
                        if isinstance(v, CompiledCommand) and v.keyword == 'NEXT']
        assert len(next_entries) == 1

        result = basic.process_command('RUN')
        text = helpers.get_text_output(result)
        assert any('15' in t for t in text)

        # IF/ELSE/ENDIF
        helpers.load_program(basic, [
            '10 X = 10',
            '20 IF X > 5 THEN',
            '30 PRINT "BIG"',
            '40 ELSE',
            '50 PRINT "SMALL"',
            '60 ENDIF',
        ])
        # Verify ELSE and ENDIF are compiled
        compiled_kws = [v.keyword for v in basic.expanded_program.values()
                        if isinstance(v, CompiledCommand)]
        assert 'ELSE' in compiled_kws
        assert 'ENDIF' in compiled_kws

        result = basic.process_command('RUN')
        text = helpers.get_text_output(result)
        assert any('BIG' in t for t in text)
        assert not any('SMALL' in t for t in text)
