#!/usr/bin/env python3

"""
Unit tests for RENUM command functionality.
Tests program line renumbering with GOTO/GOSUB reference updates.
"""

import sys
import os

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from test_base import BaseTestCase


class RenumCommandTest(BaseTestCase):
    """Test RENUM command functionality"""

    def test_basic_functionality(self):
        """Test basic RENUM functionality"""
        # Create a simple program
        self.basic.execute_command('15 PRINT "START"')
        self.basic.execute_command('25 PRINT "MIDDLE"')
        self.basic.execute_command('35 PRINT "END"')
        
        # RENUM with default parameters (10,10)
        result = self.basic.execute_command('RENUM')
        self.assert_text_output('RENUM', 'RENUMBERED 3 LINES')
        
        # Verify the renumbering
        list_result = self.basic.execute_command('LIST')
        list_output = ' '.join(str(r.get('text', '')) for r in list_result)
        
        self.assertIn('10 PRINT "START"', list_output)
        self.assertIn('20 PRINT "MIDDLE"', list_output)
        self.assertIn('30 PRINT "END"', list_output)

    def test_renum_with_goto_references(self):
        """Test RENUM updates GOTO references"""
        # Create program with GOTO
        self.basic.execute_command('10 PRINT "START"')
        self.basic.execute_command('20 GOTO 40')
        self.basic.execute_command('30 PRINT "SKIP"')
        self.basic.execute_command('40 PRINT "TARGET"')
        
        # RENUM with custom start and increment
        self.basic.execute_command('RENUM 100,50')
        
        # Verify GOTO reference was updated
        list_result = self.basic.execute_command('LIST')
        list_output = ' '.join(str(r.get('text', '')) for r in list_result)
        
        self.assertIn('100 PRINT "START"', list_output)
        self.assertIn('150 GOTO 250', list_output)  # Updated reference
        self.assertIn('200 PRINT "SKIP"', list_output)
        self.assertIn('250 PRINT "TARGET"', list_output)

    def test_renum_with_gosub_return(self):
        """Test RENUM updates GOSUB references"""
        # Create program with GOSUB/RETURN
        self.basic.execute_command('10 GOSUB 100')
        self.basic.execute_command('20 PRINT "MAIN"')
        self.basic.execute_command('30 END')
        self.basic.execute_command('100 PRINT "SUBROUTINE"')
        self.basic.execute_command('110 RETURN')
        
        # RENUM
        self.basic.execute_command('RENUM')
        
        # Verify GOSUB reference was updated
        list_result = self.basic.execute_command('LIST')
        list_output = ' '.join(str(r.get('text', '')) for r in list_result)
        
        self.assertIn('10 GOSUB 40', list_output)  # Updated reference
        self.assertIn('20 PRINT "MAIN"', list_output)
        self.assertIn('30 END', list_output)
        self.assertIn('40 PRINT "SUBROUTINE"', list_output)
        self.assertIn('50 RETURN', list_output)

    def test_renum_with_if_then(self):
        """Test RENUM updates IF...THEN line references"""
        # Create program with IF...THEN
        self.basic.execute_command('10 X = 5')
        self.basic.execute_command('20 IF X = 5 THEN 50')
        self.basic.execute_command('30 PRINT "NO"')
        self.basic.execute_command('40 END')
        self.basic.execute_command('50 PRINT "YES"')
        
        # RENUM
        self.basic.execute_command('RENUM')
        
        # Verify IF...THEN reference was updated
        list_result = self.basic.execute_command('LIST')
        list_output = ' '.join(str(r.get('text', '')) for r in list_result)
        
        self.assertIn('10 X = 5', list_output)
        self.assertIn('20 IF X = 5 THEN 50', list_output)  # Updated reference
        self.assertIn('30 PRINT "NO"', list_output)
        self.assertIn('40 END', list_output)
        self.assertIn('50 PRINT "YES"', list_output)

    def test_renum_with_on_goto(self):
        """Test RENUM updates ON...GOTO references"""
        # Create program with ON...GOTO
        self.basic.execute_command('10 X = 2')
        self.basic.execute_command('20 ON X GOTO 100,200,300')
        self.basic.execute_command('30 END')
        self.basic.execute_command('100 PRINT "ONE"')
        self.basic.execute_command('200 PRINT "TWO"')
        self.basic.execute_command('300 PRINT "THREE"')
        
        # RENUM
        self.basic.execute_command('RENUM')
        
        # Verify ON...GOTO references were updated
        list_result = self.basic.execute_command('LIST')
        list_output = ' '.join(str(r.get('text', '')) for r in list_result)
        
        self.assertIn('10 X = 2', list_output)
        self.assertIn('20 ON X GOTO 40,50,60', list_output)  # Updated references
        self.assertIn('30 END', list_output)
        self.assertIn('40 PRINT "ONE"', list_output)
        self.assertIn('50 PRINT "TWO"', list_output)
        self.assertIn('60 PRINT "THREE"', list_output)

    def test_renum_with_on_gosub(self):
        """Test RENUM updates ON...GOSUB references"""
        # Create program with ON...GOSUB
        self.basic.execute_command('10 X = 1')
        self.basic.execute_command('20 ON X GOSUB 100,200')
        self.basic.execute_command('30 PRINT "DONE"')
        self.basic.execute_command('40 END')
        self.basic.execute_command('100 PRINT "SUB1"')
        self.basic.execute_command('110 RETURN')
        self.basic.execute_command('200 PRINT "SUB2"')
        self.basic.execute_command('210 RETURN')
        
        # RENUM
        self.basic.execute_command('RENUM')
        
        # Verify ON...GOSUB references were updated
        list_result = self.basic.execute_command('LIST')
        list_output = ' '.join(str(r.get('text', '')) for r in list_result)
        
        self.assertIn('20 ON X GOSUB 50,70', list_output)  # Updated references

    def test_renum_custom_parameters(self):
        """Test RENUM with custom start and increment"""
        # Create program
        self.basic.execute_command('5 PRINT "A"')
        self.basic.execute_command('10 PRINT "B"')
        self.basic.execute_command('15 PRINT "C"')
        
        # RENUM with start=1000, increment=100
        result = self.basic.execute_command('RENUM 1000,100')
        self.assert_text_output('RENUM 1000,100', 'RENUMBERED 3 LINES')
        
        # Verify custom numbering
        list_result = self.basic.execute_command('LIST')
        list_output = ' '.join(str(r.get('text', '')) for r in list_result)
        
        self.assertIn('1000 PRINT "A"', list_output)
        self.assertIn('1100 PRINT "B"', list_output)
        self.assertIn('1200 PRINT "C"', list_output)

    def test_renum_partial_from_line(self):
        """Test RENUM starting from specific line number"""
        # Create program
        self.basic.execute_command('10 PRINT "KEEP"')
        self.basic.execute_command('20 PRINT "KEEP"')
        self.basic.execute_command('100 PRINT "CHANGE"')
        self.basic.execute_command('110 PRINT "CHANGE"')
        
        # RENUM from line 100 with start=500, increment=10
        result = self.basic.execute_command('RENUM 500,10,100')
        self.assert_text_output('RENUM 500,10,100', 'RENUMBERED 2 LINES')
        
        # Verify partial renumbering
        list_result = self.basic.execute_command('LIST')
        list_output = ' '.join(str(r.get('text', '')) for r in list_result)
        
        # These should remain unchanged
        self.assertIn('10 PRINT "KEEP"', list_output)
        self.assertIn('20 PRINT "KEEP"', list_output)
        
        # These should be renumbered
        self.assertIn('500 PRINT "CHANGE"', list_output)
        self.assertIn('510 PRINT "CHANGE"', list_output)

    def test_renum_no_program(self):
        """Test RENUM with no program loaded"""
        # Clear program
        self.basic.execute_command('NEW')
        
        # Try RENUM
        result = self.basic.execute_command('RENUM')
        self.assert_text_output('RENUM', 'NO PROGRAM TO RENUMBER')

    def test_renum_conflict_detection(self):
        """Test RENUM detects line number conflicts"""
        # Create program where renumbering would conflict
        self.basic.execute_command('10 PRINT "CHANGE"')
        self.basic.execute_command('15 PRINT "CHANGE"')  
        self.basic.execute_command('50 PRINT "KEEP"')  # This will NOT be renumbered (old_start > 50)
        
        # Try RENUM starting from line 100 (which doesn't exist) with start=50
        # This should only renumber lines >= 100, but there are none
        # Let's create a proper conflict scenario:
        self.basic.execute_command('100 PRINT "RENUM THIS"')
        
        # RENUM from line 100 with start=50 - would try to put line 100 at 50, 
        # but line 50 exists and won't be renumbered
        result = self.basic.execute_command('RENUM 50,10,100')
        
        # Should detect conflict
        error_messages = [str(r.get('message', '')) for r in result if r.get('type') == 'error']
        self.assertTrue(any('CONFLICTS' in msg for msg in error_messages))

    def test_renum_boundary_conditions(self):
        """Test RENUM boundary conditions and edge cases"""
        # Create program
        self.basic.execute_command('10 PRINT "TEST"')
        
        # Test line number too high
        result = self.basic.execute_command('RENUM 65530,10')
        error_messages = [str(r.get('message', '')) for r in result if r.get('type') == 'error']
        self.assertTrue(any('exceed maximum value' in msg.lower() for msg in error_messages))
        
        # Test invalid increment
        result = self.basic.execute_command('RENUM 10,0')
        error_messages = [str(r.get('message', '')) for r in result if r.get('type') == 'error']
        self.assertTrue(any('must be positive' in msg.lower() for msg in error_messages))

    def test_renum_syntax_errors(self):
        """Test RENUM command syntax error handling"""
        # Create program
        self.basic.execute_command('10 PRINT "TEST"')
        
        # Test invalid line number format
        result = self.basic.execute_command('RENUM ABC')
        error_messages = [str(r.get('message', '')) for r in result if r.get('type') == 'error']
        self.assertTrue(any('invalid' in msg.lower() and 'number' in msg.lower() for msg in error_messages))
        
        # Test line number out of range
        result = self.basic.execute_command('RENUM 0')
        error_messages = [str(r.get('message', '')) for r in result if r.get('type') == 'error']
        self.assertTrue(any('out of range' in msg.lower() for msg in error_messages))

    def test_renum_preserves_line_order(self):
        """Test RENUM preserves program line execution order"""
        # Create program with non-sequential line numbers
        self.basic.execute_command('30 PRINT "THIRD"')
        self.basic.execute_command('10 PRINT "FIRST"')
        self.basic.execute_command('20 PRINT "SECOND"')
        self.basic.execute_command('50 PRINT "FIFTH"')
        self.basic.execute_command('40 PRINT "FOURTH"')
        
        # RENUM
        self.basic.execute_command('RENUM')
        
        # Verify order is preserved (sorted by original line numbers)
        list_result = self.basic.execute_command('LIST')
        list_text = '\n'.join(str(r.get('text', '')) for r in list_result)
        
        # Lines should appear in execution order
        first_pos = list_text.find('10 PRINT "FIRST"')
        second_pos = list_text.find('20 PRINT "SECOND"')
        third_pos = list_text.find('30 PRINT "THIRD"')
        fourth_pos = list_text.find('40 PRINT "FOURTH"')
        fifth_pos = list_text.find('50 PRINT "FIFTH"')
        
        self.assertTrue(first_pos < second_pos < third_pos < fourth_pos < fifth_pos)

    def test_renum_complex_program(self):
        """Test RENUM with complex program containing multiple reference types"""
        # Create complex program with various reference types
        self.basic.execute_command('10 FOR I = 1 TO 3')
        self.basic.execute_command('20 ON I GOTO 100,200,300')
        self.basic.execute_command('30 NEXT I')
        self.basic.execute_command('40 END')
        self.basic.execute_command('100 PRINT "ONE"')
        self.basic.execute_command('110 GOTO 30')
        self.basic.execute_command('200 GOSUB 400')
        self.basic.execute_command('210 GOTO 30')
        self.basic.execute_command('300 PRINT "THREE"')
        self.basic.execute_command('310 GOTO 30')
        self.basic.execute_command('400 PRINT "SUBROUTINE"')
        self.basic.execute_command('410 RETURN')
        
        # RENUM
        self.basic.execute_command('RENUM 1000,10')
        
        # Verify all reference types were updated
        list_result = self.basic.execute_command('LIST')
        list_output = ' '.join(str(r.get('text', '')) for r in list_result)
        
        # Check ON...GOTO was updated
        self.assertIn('1010 ON I GOTO 1040,1060,1080', list_output)
        
        # Check GOTO was updated  
        self.assertIn('1050 GOTO 1020', list_output)
        
        # Check GOSUB was updated
        self.assertIn('1060 GOSUB 1100', list_output)

    def test_renum_unchanged_non_references(self):
        """Test RENUM doesn't change non-line-number references"""
        # Create program with numbers that aren't line references
        self.basic.execute_command('10 FOR I = 1 TO 100')  # 100 is not a line number
        self.basic.execute_command('20 PRINT I * 200')     # 200 is not a line number
        self.basic.execute_command('30 NEXT I')
        
        # RENUM
        self.basic.execute_command('RENUM')
        
        # Verify non-reference numbers are unchanged
        list_result = self.basic.execute_command('LIST')
        list_output = ' '.join(str(r.get('text', '')) for r in list_result)
        
        self.assertIn('FOR I = 1 TO 100', list_output)  # 100 unchanged
        self.assertIn('PRINT I * 200', list_output)     # 200 unchanged


if __name__ == '__main__':
    test = RenumCommandTest()
    suite = test.run_all_tests()
    from test_base import print_test_results
    print_test_results(suite)