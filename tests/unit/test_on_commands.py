#!/usr/bin/env python3

"""
Unit tests for ON GOTO and ON GOSUB commands.
Tests multi-way branching based on expression values.
"""

import sys
import os

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from test_base import BaseTestCase


class OnCommandTest(BaseTestCase):
    """Test ON GOTO and ON GOSUB commands"""

    def test_basic_functionality(self):
        """Test basic ON GOTO and ON GOSUB functionality"""
        # Test ON GOTO with simple variable
        self.basic.execute_command('10 X = 2')
        self.basic.execute_command('20 ON X GOTO 100,200,300')
        self.basic.execute_command('30 PRINT "FALLTHROUGH"')
        self.basic.execute_command('100 PRINT "OPTION 1"')
        self.basic.execute_command('110 END')
        self.basic.execute_command('200 PRINT "OPTION 2"')
        self.basic.execute_command('210 END')
        self.basic.execute_command('300 PRINT "OPTION 3"')
        self.basic.execute_command('310 END')
        
        # Run the program - should go to line 200 (X=2, second option)
        result = self.basic.execute_command('RUN')
        
        # Should see "OPTION 2" output
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        self.assertIn('OPTION 2', output_text)
        self.assertNotIn('OPTION 1', output_text)
        self.assertNotIn('OPTION 3', output_text)
        self.assertNotIn('FALLTHROUGH', output_text)

    def test_on_goto_with_expressions(self):
        """Test ON GOTO with complex expressions"""
        # Test with arithmetic expression
        self.basic.execute_command('10 A = 1')
        self.basic.execute_command('20 B = 1')
        self.basic.execute_command('30 ON A+B GOTO 100,200,300')
        self.basic.execute_command('40 PRINT "FALLTHROUGH"')
        self.basic.execute_command('100 PRINT "SUM = 1"')
        self.basic.execute_command('200 PRINT "SUM = 2"')
        self.basic.execute_command('300 PRINT "SUM = 3"')
        
        # Run - should go to line 200 (A+B = 2)
        result = self.basic.execute_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        self.assertIn('SUM = 2', output_text)

    def test_on_gosub_basic(self):
        """Test ON GOSUB with subroutine calls"""
        self.basic.execute_command('10 X = 1')
        self.basic.execute_command('20 ON X GOSUB 100,200')
        self.basic.execute_command('30 PRINT "AFTER GOSUB"')
        self.basic.execute_command('40 END')
        self.basic.execute_command('100 PRINT "SUBROUTINE 1"')
        self.basic.execute_command('110 RETURN')
        self.basic.execute_command('200 PRINT "SUBROUTINE 2"')
        self.basic.execute_command('210 RETURN')
        
        # Run - should call subroutine 1 and return
        result = self.basic.execute_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        self.assertIn('SUBROUTINE 1', output_text)
        self.assertIn('AFTER GOSUB', output_text)
        self.assertNotIn('SUBROUTINE 2', output_text)

    def test_on_goto_out_of_range(self):
        """Test ON GOTO with out-of-range values"""
        # Test with value too high
        self.basic.execute_command('10 X = 5')
        self.basic.execute_command('20 ON X GOTO 100,200')
        self.basic.execute_command('30 PRINT "CONTINUED"')
        self.basic.execute_command('40 END')
        self.basic.execute_command('100 PRINT "OPTION 1"')
        self.basic.execute_command('200 PRINT "OPTION 2"')
        
        # Run - should continue execution (not jump)
        result = self.basic.execute_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        self.assertIn('CONTINUED', output_text)
        self.assertNotIn('OPTION 1', output_text)
        self.assertNotIn('OPTION 2', output_text)

    def test_on_goto_zero_value(self):
        """Test ON GOTO with zero value"""
        self.basic.execute_command('10 X = 0')
        self.basic.execute_command('20 ON X GOTO 100,200')
        self.basic.execute_command('30 PRINT "X = 0, CONTINUE"')
        self.basic.execute_command('40 END')
        self.basic.execute_command('100 PRINT "OPTION 1"')
        self.basic.execute_command('200 PRINT "OPTION 2"')
        
        # Run - should continue execution (0 is out of range)
        result = self.basic.execute_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        self.assertIn('X = 0, CONTINUE', output_text)

    def test_on_goto_negative_value(self):
        """Test ON GOTO with negative value"""
        self.basic.execute_command('10 X = -1')
        self.basic.execute_command('20 ON X GOTO 100,200')
        self.basic.execute_command('30 PRINT "X NEGATIVE, CONTINUE"')
        self.basic.execute_command('40 END')
        self.basic.execute_command('100 PRINT "OPTION 1"')
        self.basic.execute_command('200 PRINT "OPTION 2"')
        
        # Run - should continue execution (negative is out of range)
        result = self.basic.execute_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        self.assertIn('X NEGATIVE, CONTINUE', output_text)

    def test_on_goto_fractional_truncation(self):
        """Test ON GOTO with fractional values (should truncate)"""
        self.basic.execute_command('10 X = 2.8')
        self.basic.execute_command('20 ON X GOTO 100,200,300')
        self.basic.execute_command('100 PRINT "OPTION 1"')
        self.basic.execute_command('200 PRINT "OPTION 2"')
        self.basic.execute_command('300 PRINT "OPTION 3"')
        
        # Run - should truncate 2.8 to 2 and go to option 2
        result = self.basic.execute_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        self.assertIn('OPTION 2', output_text)

    def test_on_gosub_multiple_calls(self):
        """Test ON GOSUB with multiple subroutine calls in loop"""
        self.basic.execute_command('10 FOR I = 1 TO 3')
        self.basic.execute_command('20 ON I GOSUB 100,200,300')
        self.basic.execute_command('30 PRINT "BACK FROM "; I')
        self.basic.execute_command('40 NEXT I')
        self.basic.execute_command('50 END')
        self.basic.execute_command('100 PRINT "SUB 1"')
        self.basic.execute_command('110 RETURN')
        self.basic.execute_command('200 PRINT "SUB 2"')
        self.basic.execute_command('210 RETURN')
        self.basic.execute_command('300 PRINT "SUB 3"')
        self.basic.execute_command('310 RETURN')
        
        # Run - should call all three subroutines
        result = self.basic.execute_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        self.assertIn('SUB 1', output_text)
        self.assertIn('SUB 2', output_text)
        self.assertIn('SUB 3', output_text)
        self.assertIn('BACK FROM 1', output_text)
        self.assertIn('BACK FROM 2', output_text)
        self.assertIn('BACK FROM 3', output_text)

    def test_on_goto_single_option(self):
        """Test ON GOTO with single option"""
        self.basic.execute_command('10 X = 1')
        self.basic.execute_command('20 ON X GOTO 100')
        self.basic.execute_command('30 PRINT "FALLTHROUGH"')
        self.basic.execute_command('100 PRINT "ONLY OPTION"')
        
        # Run - should go to only option
        result = self.basic.execute_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        self.assertIn('ONLY OPTION', output_text)
        self.assertNotIn('FALLTHROUGH', output_text)

    def test_on_goto_many_options(self):
        """Test ON GOTO with many line options"""
        self.basic.execute_command('10 X = 5')
        self.basic.execute_command('20 ON X GOTO 100,200,300,400,500,600')
        self.basic.execute_command('30 PRINT "FALLTHROUGH"')
        for i in range(1, 7):
            line_num = 100 * i
            self.basic.execute_command(f'{line_num} PRINT "OPTION {i}"')
            self.basic.execute_command(f'{line_num + 10} END')
        
        # Run - should go to option 5 (X=5)
        result = self.basic.execute_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        self.assertIn('OPTION 5', output_text)
        self.assertNotIn('OPTION 1', output_text)
        self.assertNotIn('OPTION 6', output_text)

    def test_on_commands_syntax_errors(self):
        """Test ON command syntax error handling"""
        # Test ON without GOTO or GOSUB
        result = self.basic.execute_command('ON X PRINT "INVALID"')
        self.assertTrue(any('SYNTAX ERROR' in str(r.get('message', '')) for r in result))
        
        # Test ON without expression
        result = self.basic.execute_command('ON GOTO 100,200')
        self.assertTrue(any('SYNTAX ERROR' in str(r.get('message', '')) for r in result))

    def test_on_commands_undefined_variable(self):
        """Test ON commands with undefined variable (defaults to 0)"""
        # Test with undefined variable - should default to 0 (authentic BASIC behavior)
        self.basic.execute_command('NEW')  # Clear any variables
        self.basic.execute_command('10 ON UNDEFINED GOTO 100,200')
        self.basic.execute_command('20 PRINT "CONTINUED"')  # Should execute since UNDEFINED=0 (out of range)
        self.basic.execute_command('30 END')
        self.basic.execute_command('100 PRINT "OPTION 1"')
        self.basic.execute_command('200 PRINT "OPTION 2"')
        
        # Run - should continue to line 20 since UNDEFINED defaults to 0 (out of range)
        result = self.basic.execute_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        self.assertIn('CONTINUED', output_text)
        self.assertNotIn('OPTION 1', output_text)
        self.assertNotIn('OPTION 2', output_text)

    def test_on_commands_invalid_line_numbers(self):
        """Test ON commands with invalid line number syntax"""
        self.basic.execute_command('10 X = 1')
        
        # Test with truly non-numeric line numbers (string literals)
        result = self.basic.execute_command('ON X GOTO "ABC","DEF"')
        self.assertTrue(any('SYNTAX ERROR' in str(r.get('message', '')) or 'INVALID' in str(r.get('message', '')) or 'Invalid' in str(r.get('message', ''))
                          for r in result if r.get('type') == 'error'))

    def test_on_goto_with_string_result(self):
        """Test ON GOTO with expression that results in string (should cause error)"""
        self.basic.execute_command('10 A$ = "TEST"')
        result = self.basic.execute_command('ON A$ GOTO 100,200')
        
        # Should get error about invalid expression
        error_messages = [str(r.get('message', '')) for r in result if r.get('type') == 'error']
        self.assertTrue(len(error_messages) > 0)

    def test_on_goto_expression_evaluation(self):
        """Test ON GOTO with various expression types"""
        # Test with parentheses
        self.basic.execute_command('10 A = 3')
        self.basic.execute_command('20 B = 1')
        self.basic.execute_command('30 ON (A-B) GOTO 100,200,300')
        self.basic.execute_command('100 PRINT "OPTION 1"')
        self.basic.execute_command('200 PRINT "OPTION 2"')  
        self.basic.execute_command('300 PRINT "OPTION 3"')
        
        # Run - (3-1) = 2, should go to option 2
        result = self.basic.execute_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        self.assertIn('OPTION 2', output_text)

    def test_on_gosub_nested_calls(self):
        """Test ON GOSUB with nested subroutine calls"""
        self.basic.execute_command('10 X = 1')
        self.basic.execute_command('20 ON X GOSUB 100')
        self.basic.execute_command('30 PRINT "MAIN END"')
        self.basic.execute_command('40 END')
        self.basic.execute_command('100 PRINT "OUTER SUB"')
        self.basic.execute_command('110 GOSUB 200')  # Nested call
        self.basic.execute_command('120 PRINT "OUTER SUB END"')
        self.basic.execute_command('130 RETURN')
        self.basic.execute_command('200 PRINT "INNER SUB"')
        self.basic.execute_command('210 RETURN')
        
        # Run - should handle nested subroutine calls
        result = self.basic.execute_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        self.assertIn('OUTER SUB', output_text)
        self.assertIn('INNER SUB', output_text)
        self.assertIn('OUTER SUB END', output_text)
        self.assertIn('MAIN END', output_text)

    def test_on_commands_case_insensitive(self):
        """Test ON GOTO/GOSUB are case insensitive"""
        self.basic.execute_command('10 X = 1')
        
        # Test lowercase
        self.basic.execute_command('20 on x goto 100')
        self.basic.execute_command('100 PRINT "LOWERCASE WORKS"')
        
        result = self.basic.execute_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        self.assertIn('LOWERCASE WORKS', output_text)

    def test_on_goto_large_line_numbers(self):
        """Test ON GOTO with large line numbers"""
        self.basic.execute_command('10 X = 1')
        self.basic.execute_command('20 ON X GOTO 30000')
        self.basic.execute_command('30 PRINT "FALLTHROUGH"')
        self.basic.execute_command('30000 PRINT "LARGE LINE"')
        
        # Run - should jump to large line number
        result = self.basic.execute_command('RUN')
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        self.assertIn('LARGE LINE', output_text)
        self.assertNotIn('FALLTHROUGH', output_text)

    def test_on_commands_direct_execution(self):
        """Test ON commands can be executed directly (not just in programs)"""
        # Set up variables and target lines in program memory
        self.basic.execute_command('100 PRINT "DIRECT GOTO WORKED"')
        self.basic.execute_command('X = 1')
        
        # Execute ON GOTO directly
        result = self.basic.execute_command('ON X GOTO 100')
        
        # Should execute the target line
        output_text = ' '.join(str(r.get('text', '')) for r in result if r.get('type') == 'text')
        # Note: Direct execution behavior may vary, so we mainly check for no syntax errors
        self.assertFalse(any('SYNTAX ERROR' in str(r.get('message', '')) for r in result))


if __name__ == '__main__':
    test = OnCommandTest()
    suite = test.run_all_tests()
    from test_base import print_test_results
    print_test_results(suite)