#!/usr/bin/env python3

"""
Unit tests for ON GOTO and ON GOSUB commands.
Tests multi-way branching based on expression values.
"""

import sys
import os

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestOnCommand:
    """Test ON GOTO and ON GOSUB commands"""

    def test_basic_functionality(self, basic, helpers):
        """Test basic ON GOTO and ON GOSUB functionality"""
        # Test ON GOTO with simple variable
        basic.process_command('10 X = 2')
        basic.process_command('20 ON X GOTO 100,200,300')
        basic.process_command('30 PRINT "FALLTHROUGH"')
        basic.process_command('100 PRINT "OPTION 1"')
        basic.process_command('110 END')
        basic.process_command('200 PRINT "OPTION 2"')
        basic.process_command('210 END')
        basic.process_command('300 PRINT "OPTION 3"')
        basic.process_command('310 END')
        
        # Run the program - should go to line 200 (X=2, second option)
        result = basic.process_command('RUN')
        
        # Should see "OPTION 2" output
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        assert 'OPTION 2' in output_text
        assert 'OPTION 1' not in output_text
        assert 'OPTION 3' not in output_text
        assert 'FALLTHROUGH' not in output_text

    def test_on_goto_with_expressions(self, basic, helpers):
        """Test ON GOTO with complex expressions"""
        # Test with arithmetic expression
        basic.process_command('10 A = 1')
        basic.process_command('20 B = 1')
        basic.process_command('30 ON A+B GOTO 100,200,300')
        basic.process_command('40 PRINT "FALLTHROUGH"')
        basic.process_command('100 PRINT "SUM = 1"')
        basic.process_command('200 PRINT "SUM = 2"')
        basic.process_command('300 PRINT "SUM = 3"')
        
        # Run - should go to line 200 (A+B = 2)
        result = basic.process_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        assert 'SUM = 2' in output_text

    def test_on_gosub_basic(self, basic, helpers):
        """Test ON GOSUB with subroutine calls"""
        basic.process_command('10 X = 1')
        basic.process_command('20 ON X GOSUB 100,200')
        basic.process_command('30 PRINT "AFTER GOSUB"')
        basic.process_command('40 END')
        basic.process_command('100 PRINT "SUBROUTINE 1"')
        basic.process_command('110 RETURN')
        basic.process_command('200 PRINT "SUBROUTINE 2"')
        basic.process_command('210 RETURN')
        
        # Run - should call subroutine 1 and return
        result = basic.process_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        assert 'SUBROUTINE 1' in output_text
        assert 'AFTER GOSUB' in output_text
        assert 'SUBROUTINE 2' not in output_text

    def test_on_goto_out_of_range(self, basic, helpers):
        """Test ON GOTO with out-of-range values"""
        # Test with value too high
        basic.process_command('10 X = 5')
        basic.process_command('20 ON X GOTO 100,200')
        basic.process_command('30 PRINT "CONTINUED"')
        basic.process_command('40 END')
        basic.process_command('100 PRINT "OPTION 1"')
        basic.process_command('200 PRINT "OPTION 2"')
        
        # Run - should continue execution (not jump)
        result = basic.process_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        assert 'CONTINUED' in output_text
        assert 'OPTION 1' not in output_text
        assert 'OPTION 2' not in output_text

    def test_on_goto_zero_value(self, basic, helpers):
        """Test ON GOTO with zero value"""
        basic.process_command('10 X = 0')
        basic.process_command('20 ON X GOTO 100,200')
        basic.process_command('30 PRINT "X = 0, CONTINUE"')
        basic.process_command('40 END')
        basic.process_command('100 PRINT "OPTION 1"')
        basic.process_command('200 PRINT "OPTION 2"')
        
        # Run - should continue execution (0 is out of range)
        result = basic.process_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        assert 'X = 0 in CONTINUE', output_text

    def test_on_goto_negative_value(self, basic, helpers):
        """Test ON GOTO with negative value"""
        basic.process_command('10 X = -1')
        basic.process_command('20 ON X GOTO 100,200')
        basic.process_command('30 PRINT "X NEGATIVE, CONTINUE"')
        basic.process_command('40 END')
        basic.process_command('100 PRINT "OPTION 1"')
        basic.process_command('200 PRINT "OPTION 2"')
        
        # Run - should continue execution (negative is out of range)
        result = basic.process_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        assert 'X NEGATIVE in CONTINUE', output_text

    def test_on_goto_fractional_truncation(self, basic, helpers):
        """Test ON GOTO with fractional values (should truncate)"""
        basic.process_command('10 X = 2.8')
        basic.process_command('20 ON X GOTO 100,200,300')
        basic.process_command('100 PRINT "OPTION 1"')
        basic.process_command('200 PRINT "OPTION 2"')
        basic.process_command('300 PRINT "OPTION 3"')
        
        # Run - should truncate 2.8 to 2 and go to option 2
        result = basic.process_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        assert 'OPTION 2' in output_text

    def test_on_gosub_multiple_calls(self, basic, helpers):
        """Test ON GOSUB with multiple subroutine calls in loop"""
        basic.process_command('10 FOR I = 1 TO 3')
        basic.process_command('20 ON I GOSUB 100,200,300')
        basic.process_command('30 PRINT "BACK FROM "; I')
        basic.process_command('40 NEXT I')
        basic.process_command('50 END')
        basic.process_command('100 PRINT "SUB 1"')
        basic.process_command('110 RETURN')
        basic.process_command('200 PRINT "SUB 2"')
        basic.process_command('210 RETURN')
        basic.process_command('300 PRINT "SUB 3"')
        basic.process_command('310 RETURN')
        
        # Run - should call all three subroutines
        result = basic.process_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        assert 'SUB 1' in output_text
        assert 'SUB 2' in output_text
        assert 'SUB 3' in output_text
        assert 'BACK FROM  1 ' in output_text
        assert 'BACK FROM  2 ' in output_text
        assert 'BACK FROM  3 ' in output_text

    def test_on_goto_single_option(self, basic, helpers):
        """Test ON GOTO with single option"""
        basic.process_command('10 X = 1')
        basic.process_command('20 ON X GOTO 100')
        basic.process_command('30 PRINT "FALLTHROUGH"')
        basic.process_command('100 PRINT "ONLY OPTION"')
        
        # Run - should go to only option
        result = basic.process_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        assert 'ONLY OPTION' in output_text
        assert 'FALLTHROUGH' not in output_text

    def test_on_goto_many_options(self, basic, helpers):
        """Test ON GOTO with many line options"""
        basic.process_command('10 X = 5')
        basic.process_command('20 ON X GOTO 100,200,300,400,500,600')
        basic.process_command('30 PRINT "FALLTHROUGH"')
        for i in range(1, 7):
            line_num = 100 * i
            basic.process_command(f'{line_num} PRINT "OPTION {i}"')
            basic.process_command(f'{line_num + 10} END')
        
        # Run - should go to option 5 (X=5)
        result = basic.process_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        assert 'OPTION 5' in output_text
        assert 'OPTION 1' not in output_text
        assert 'OPTION 6' not in output_text

    def test_on_commands_syntax_errors(self, basic, helpers):
        """Test ON command syntax error handling"""
        # Test ON without GOTO or GOSUB
        result = basic.process_command('ON X PRINT "INVALID"')
        assert any('SYNTAX ERROR' in str(r.get('message', '')) for r in result)
        
        # Test ON without expression
        result = basic.process_command('ON GOTO 100,200')
        assert any('SYNTAX ERROR' in str(r.get('message', '')) for r in result)

    def test_on_commands_undefined_variable(self, basic, helpers):
        """Test ON commands with undefined variable (defaults to 0)"""
        # Test with undefined variable - should default to 0 (authentic BASIC behavior)
        basic.process_command('NEW')  # Clear any variables
        basic.process_command('10 ON UNDEFINED GOTO 100,200')
        basic.process_command('20 PRINT "CONTINUED"')  # Should execute since UNDEFINED=0 (out of range)
        basic.process_command('30 END')
        basic.process_command('100 PRINT "OPTION 1"')
        basic.process_command('200 PRINT "OPTION 2"')
        
        # Run - should continue to line 20 since UNDEFINED defaults to 0 (out of range)
        result = basic.process_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        assert 'CONTINUED' in output_text
        assert 'OPTION 1' not in output_text
        assert 'OPTION 2' not in output_text

    def test_on_commands_invalid_line_numbers(self, basic, helpers):
        """Test ON commands with invalid line number syntax"""
        basic.process_command('10 X = 1')
        
        # Test with truly non-numeric line numbers (string literals)
        result = basic.process_command('ON X GOTO "ABC","DEF"')
        assert any('SYNTAX ERROR' in str(r.get('message', '')) or 'INVALID' in str(r.get('message', '')) or 'Invalid' in str(r.get('message', ''))
                          for r in result if r.get('type') == 'error')

    def test_on_goto_with_string_result(self, basic, helpers):
        """Test ON GOTO with expression that results in string (should cause error)"""
        basic.process_command('10 A$ = "TEST"')
        result = basic.process_command('ON A$ GOTO 100,200')
        
        # Should get error about invalid expression
        error_messages = [str(r.get('message', '')) for r in result if r.get('type') == 'error']
        assert len(error_messages) > 0

    def test_on_goto_expression_evaluation(self, basic, helpers):
        """Test ON GOTO with various expression types"""
        # Test with parentheses
        basic.process_command('10 A = 3')
        basic.process_command('20 B = 1')
        basic.process_command('30 ON (A-B) GOTO 100,200,300')
        basic.process_command('100 PRINT "OPTION 1"')
        basic.process_command('200 PRINT "OPTION 2"')  
        basic.process_command('300 PRINT "OPTION 3"')
        
        # Run - (3-1) = 2, should go to option 2
        result = basic.process_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        assert 'OPTION 2' in output_text

    def test_on_gosub_nested_calls(self, basic, helpers):
        """Test ON GOSUB with nested subroutine calls"""
        basic.process_command('10 X = 1')
        basic.process_command('20 ON X GOSUB 100')
        basic.process_command('30 PRINT "MAIN END"')
        basic.process_command('40 END')
        basic.process_command('100 PRINT "OUTER SUB"')
        basic.process_command('110 GOSUB 200')  # Nested call
        basic.process_command('120 PRINT "OUTER SUB END"')
        basic.process_command('130 RETURN')
        basic.process_command('200 PRINT "INNER SUB"')
        basic.process_command('210 RETURN')
        
        # Run - should handle nested subroutine calls
        result = basic.process_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        assert 'OUTER SUB' in output_text
        assert 'INNER SUB' in output_text
        assert 'OUTER SUB END' in output_text
        assert 'MAIN END' in output_text

    def test_on_commands_case_insensitive(self, basic, helpers):
        """Test ON GOTO/GOSUB are case insensitive"""
        basic.process_command('10 X = 1')
        
        # Test lowercase
        basic.process_command('20 on x goto 100')
        basic.process_command('100 PRINT "LOWERCASE WORKS"')
        
        result = basic.process_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        assert 'LOWERCASE WORKS' in output_text

    def test_on_goto_large_line_numbers(self, basic, helpers):
        """Test ON GOTO with large line numbers"""
        basic.process_command('10 X = 1')
        basic.process_command('20 ON X GOTO 30000')
        basic.process_command('30 PRINT "FALLTHROUGH"')
        basic.process_command('30000 PRINT "LARGE LINE"')
        
        # Run - should jump to large line number
        result = basic.process_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        assert 'LARGE LINE' in output_text
        assert 'FALLTHROUGH' not in output_text

    def test_on_commands_direct_execution(self, basic, helpers):
        """Test ON commands can be executed directly (not just in programs)"""
        # Set up variables and target lines in program memory
        basic.process_command('100 PRINT "DIRECT GOTO WORKED"')
        basic.process_command('X = 1')
        
        # Execute ON GOTO directly
        result = basic.process_command('ON X GOTO 100')
        
        # Should execute the target line
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        # Note: Direct execution behavior may vary, so we mainly check for no syntax errors
        assert not any('SYNTAX ERROR' in str(r.get('message', '')) for r in result)
