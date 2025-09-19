#!/usr/bin/env python3

"""
Comprehensive integration test demonstrating multiple BASIC features together
"""

import pytest


class TestComprehensiveProgram:
    """Test cases for complex programs using multiple BASIC features"""

    def test_basic_functionality(self, basic, helpers):
        """Test that comprehensive programs can run without errors"""
        program = [
            '10 PRINT "BASIC TEST"',
            '20 A = 5',
            '30 PRINT A'
        ]
        
        results = helpers.execute_program(basic, program)
        # Should complete without errors
        assert len(results > 0)

    def test_math_and_variables_program(self, basic, helpers):
        """Test program with math operations and variables"""
        program = [
            '10 REM MATH TEST PROGRAM',
            '20 A = 10',
            '30 B = 5',
            '40 C = A + B',
            '50 D = A - B',
            '60 E = A * B',
            '70 F = A / B',
            '80 PRINT "ADDITION: "; A; " + "; B; " = "; C',
            '90 PRINT "SUBTRACTION: "; A; " - "; B; " = "; D',
            '100 PRINT "MULTIPLICATION: "; A; " * "; B; " = "; E',
            '110 PRINT "DIVISION: "; A; " / "; B; " = "; F'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        # Should produce mathematical results
        assert len(text_outputs >= 4)
        assert any('15' in output for output in text_outputs)  # A + B
        assert any('5' in output for output in text_outputs)   # A - B
        assert any('50' in output for output in text_outputs)  # A * B

    def test_string_operations_program(self, basic, helpers):
        """Test program with string operations"""
        program = [
            '10 REM STRING TEST PROGRAM',
            '20 A$ = "HELLO"',
            '30 B$ = "WORLD"',
            '40 PRINT A$; " "; B$',
            '50 C$ = "COLOR COMPUTER"',
            '60 PRINT "LENGTH OF "; C$; " IS"; LEN(C$)' if self.has_string_functions() else '60 PRINT C$',
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        # Should handle string operations
        assert len(text_outputs >= 2)
        assert any('HELLO' in output and 'WORLD' in output for output in text_outputs)

    def test_for_loop_with_calculations(self, basic, helpers):
        """Test FOR loop doing calculations"""
        program = [
            '10 REM CALCULATE FACTORIAL OF 5',
            '20 FACTORIAL = 1',
            '30 FOR I = 1 TO 5',
            '40 FACTORIAL = FACTORIAL * I',
            '50 PRINT I; "! = "; FACTORIAL',
            '60 NEXT I',
            '70 PRINT "FINAL: 5! = "; FACTORIAL'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        # Should calculate factorial: 5! = 120
        assert len(text_outputs >= 5)
        assert any('120' in output for output in text_outputs)

    def test_if_then_logic_program(self, basic, helpers):
        """Test program with IF/THEN logic"""
        program = [
            '10 REM TEST IF/THEN LOGIC',
            '20 FOR I = 1 TO 10',
            '30 IF I <= 5 THEN PRINT I; " IS SMALL"',
            '40 IF I > 5 THEN PRINT I; " IS BIG"',
            '50 NEXT I'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        # Should have outputs for both conditions
        assert len(text_outputs >= 10)
        assert any('SMALL' in output for output in text_outputs)
        assert any('BIG' in output for output in text_outputs)

    def test_gosub_return_program(self, basic, helpers):
        """Test program with subroutines"""
        program = [
            '10 REM MAIN PROGRAM',
            '20 PRINT "CALLING SUBROUTINE"',
            '30 GOSUB 100',
            '40 PRINT "BACK FROM SUBROUTINE"',
            '50 END',
            '100 REM SUBROUTINE',
            '110 PRINT "IN SUBROUTINE"',
            '120 RETURN'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        # Should show subroutine call and return
        assert any('CALLING SUBROUTINE' in output for output in text_outputs)
        assert any('IN SUBROUTINE' in output for output in text_outputs)
        assert any('BACK FROM SUBROUTINE' in output for output in text_outputs)

    def test_nested_structures_program(self, basic, helpers):
        """Test program with nested FOR loops and IF statements"""
        program = [
            '10 REM MULTIPLICATION TABLE',
            '20 FOR I = 1 TO 3',
            '30 FOR J = 1 TO 3',
            '40 PRODUCT = I * J',
            '50 PRINT I; " * "; J; " = "; PRODUCT',
            '60 IF PRODUCT > 6 THEN PRINT "  (LARGE)"',
            '70 NEXT J',
            '80 PRINT',  # Blank line
            '90 NEXT I'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        # Should produce multiplication table with conditional output
        assert len(text_outputs >= 9)  # 3x3 = 9 products
        assert any('LARGE' in output for output in text_outputs)

    def test_data_read_program(self, basic, helpers):
        """Test program using DATA/READ statements"""
        program = [
            '10 REM DATA PROCESSING PROGRAM',
            '20 DATA "APPLE", 1.25, "BANANA", 0.75, "CHERRY", 2.50',
            '30 FOR I = 1 TO 3',
            '40 READ ITEM$, PRICE',
            '50 PRINT ITEM$; " COSTS $"; PRICE',
            '60 NEXT I'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        # Should process all data items
        assert len(text_outputs >= 3)
        assert any('APPLE' in output for output in text_outputs)
        assert any('BANANA' in output for output in text_outputs)
        assert any('CHERRY' in output for output in text_outputs)

    def test_complex_mathematical_program(self, basic, helpers):
        """Test program with complex mathematical operations"""
        program = [
            '10 REM COMPLEX MATH PROGRAM',
            '20 PI = 3.14159',
            '30 RADIUS = 5',
            '40 AREA = PI * RADIUS * RADIUS',
            '50 CIRCUMFERENCE = 2 * PI * RADIUS',
            '60 PRINT "RADIUS: "; RADIUS',
            '70 PRINT "AREA: "; AREA',
            '80 PRINT "CIRCUMFERENCE: "; CIRCUMFERENCE',
            '90 IF AREA > 50 THEN PRINT "LARGE CIRCLE"',
            '100 IF AREA <= 50 THEN PRINT "SMALL CIRCLE"'
        ]
        
        results = helpers.execute_program(basic, program)
        text_outputs = helpers.get_text_output(results)
        
        # Should calculate circle properties
        assert len(text_outputs >= 4)
        assert any('RADIUS' in output for output in text_outputs)
        assert any('AREA' in output for output in text_outputs)
        assert any('LARGE CIRCLE' in output for output in text_outputs)

    def has_string_functions(self):
        """Helper to check if string functions are implemented"""
        try:
            result = basic.process_command('PRINT LEN("TEST")')
            return len(result) > 0 and result[0].get('type') != 'error'
        except:
            return False
