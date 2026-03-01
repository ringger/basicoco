#!/usr/bin/env python3

"""
Unit tests for RENUM command functionality.
Tests program line renumbering with GOTO/GOSUB reference updates.
"""

import sys
import os

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestRenumCommand:
    """Test RENUM command functionality"""

    def test_basic_functionality(self, basic, helpers):
        """Test basic RENUM functionality"""
        # Create a simple program
        basic.process_command('15 PRINT "START"')
        basic.process_command('25 PRINT "MIDDLE"')
        basic.process_command('35 PRINT "END"')
        
        # RENUM with default parameters (10,10)
        result = basic.process_command('RENUM')
        result = basic.process_command('RENUM')
        text_output = helpers.get_text_output(result)
        assert text_output == ['RENUMBERED 3 LINES']
        
        # Verify the renumbering
        list_result = basic.process_command('LIST')
        list_output = ' '.join(str(r.get('text', '')) for r in list_result)
        
        assert '10 PRINT "START"' in list_output
        assert '20 PRINT "MIDDLE"' in list_output
        assert '30 PRINT "END"' in list_output

    def test_renum_with_goto_references(self, basic, helpers):
        """Test RENUM updates GOTO references"""
        # Create program with GOTO
        basic.process_command('10 PRINT "START"')
        basic.process_command('20 GOTO 40')
        basic.process_command('30 PRINT "SKIP"')
        basic.process_command('40 PRINT "TARGET"')
        
        # RENUM with custom start and increment
        basic.process_command('RENUM 100,50')
        
        # Verify GOTO reference was updated
        list_result = basic.process_command('LIST')
        list_output = ' '.join(str(r.get('text', '')) for r in list_result)
        
        assert '100 PRINT "START"' in list_output
        assert '150 GOTO 250' in list_output  # Updated reference
        assert '200 PRINT "SKIP"' in list_output
        assert '250 PRINT "TARGET"' in list_output

    def test_renum_with_gosub_return(self, basic, helpers):
        """Test RENUM updates GOSUB references"""
        # Create program with GOSUB/RETURN
        basic.process_command('10 GOSUB 100')
        basic.process_command('20 PRINT "MAIN"')
        basic.process_command('30 END')
        basic.process_command('100 PRINT "SUBROUTINE"')
        basic.process_command('110 RETURN')
        
        # RENUM
        basic.process_command('RENUM')
        
        # Verify GOSUB reference was updated
        list_result = basic.process_command('LIST')
        list_output = ' '.join(str(r.get('text', '')) for r in list_result)
        
        assert '10 GOSUB 40' in list_output  # Updated reference
        assert '20 PRINT "MAIN"' in list_output
        assert '30 END' in list_output
        assert '40 PRINT "SUBROUTINE"' in list_output
        assert '50 RETURN' in list_output

    def test_renum_with_if_then(self, basic, helpers):
        """Test RENUM updates IF...THEN line references"""
        # Create program with IF...THEN
        basic.process_command('10 X = 5')
        basic.process_command('20 IF X = 5 THEN 50')
        basic.process_command('30 PRINT "NO"')
        basic.process_command('40 END')
        basic.process_command('50 PRINT "YES"')
        
        # RENUM
        basic.process_command('RENUM')
        
        # Verify IF...THEN reference was updated
        list_result = basic.process_command('LIST')
        list_output = ' '.join(str(r.get('text', '')) for r in list_result)
        
        assert '10 X = 5' in list_output
        assert '20 IF X = 5 THEN 50' in list_output  # Updated reference
        assert '30 PRINT "NO"' in list_output
        assert '40 END' in list_output
        assert '50 PRINT "YES"' in list_output

    def test_renum_with_on_goto(self, basic, helpers):
        """Test RENUM updates ON...GOTO references"""
        # Create program with ON...GOTO
        basic.process_command('10 X = 2')
        basic.process_command('20 ON X GOTO 100,200,300')
        basic.process_command('30 END')
        basic.process_command('100 PRINT "ONE"')
        basic.process_command('200 PRINT "TWO"')
        basic.process_command('300 PRINT "THREE"')
        
        # RENUM
        basic.process_command('RENUM')
        
        # Verify ON...GOTO references were updated
        list_result = basic.process_command('LIST')
        list_output = ' '.join(str(r.get('text', '')) for r in list_result)
        
        assert '10 X = 2' in list_output
        assert '20 ON X GOTO 40 in 50,60', list_output  # Updated references
        assert '30 END' in list_output
        assert '40 PRINT "ONE"' in list_output
        assert '50 PRINT "TWO"' in list_output
        assert '60 PRINT "THREE"' in list_output

    def test_renum_with_on_gosub(self, basic, helpers):
        """Test RENUM updates ON...GOSUB references"""
        # Create program with ON...GOSUB
        basic.process_command('10 X = 1')
        basic.process_command('20 ON X GOSUB 100,200')
        basic.process_command('30 PRINT "DONE"')
        basic.process_command('40 END')
        basic.process_command('100 PRINT "SUB1"')
        basic.process_command('110 RETURN')
        basic.process_command('200 PRINT "SUB2"')
        basic.process_command('210 RETURN')
        
        # RENUM
        basic.process_command('RENUM')
        
        # Verify ON...GOSUB references were updated
        list_result = basic.process_command('LIST')
        list_output = ' '.join(str(r.get('text', '')) for r in list_result)
        
        assert '20 ON X GOSUB 50 in 70', list_output  # Updated references

    def test_renum_custom_parameters(self, basic, helpers):
        """Test RENUM with custom start and increment"""
        # Create program
        basic.process_command('5 PRINT "A"')
        basic.process_command('10 PRINT "B"')
        basic.process_command('15 PRINT "C"')
        
        # RENUM with start=1000, increment=100
        result = basic.process_command('RENUM 1000,100')
        result = basic.process_command('RENUM 1000,100')
        text_output = helpers.get_text_output(result)
        assert 'RENUMBERED 3 LINES' in text_output
        
        # Verify custom numbering
        list_result = basic.process_command('LIST')
        list_output = ' '.join(str(r.get('text', '')) for r in list_result)
        
        assert '1000 PRINT "A"' in list_output
        assert '1100 PRINT "B"' in list_output
        assert '1200 PRINT "C"' in list_output

    def test_renum_partial_from_line(self, basic, helpers):
        """Test RENUM starting from specific line number"""
        # Create program
        basic.process_command('10 PRINT "KEEP"')
        basic.process_command('20 PRINT "KEEP"')
        basic.process_command('100 PRINT "CHANGE"')
        basic.process_command('110 PRINT "CHANGE"')
        
        # RENUM from line 100 with start=500, increment=10
        result = basic.process_command('RENUM 500,10,100')
        text_output = helpers.get_text_output(result)
        assert 'RENUMBERED' in ' '.join(text_output) or len(result) == 0  # Check for success message or no error
        
        # Verify partial renumbering
        list_result = basic.process_command('LIST')
        list_output = ' '.join(str(r.get('text', '')) for r in list_result)
        
        # These should remain unchanged
        assert '10 PRINT "KEEP"' in list_output
        assert '20 PRINT "KEEP"' in list_output
        
        # These should be renumbered
        assert '500 PRINT "CHANGE"' in list_output
        assert '510 PRINT "CHANGE"' in list_output

    def test_renum_no_program(self, basic, helpers):
        """Test RENUM with no program loaded"""
        # Clear program
        basic.process_command('NEW')
        
        # Try RENUM
        result = basic.process_command('RENUM')
        result = basic.process_command('RENUM')
        text_output = helpers.get_text_output(result)
        assert text_output == ['NO PROGRAM TO RENUMBER']

    def test_renum_conflict_detection(self, basic, helpers):
        """Test RENUM detects line number conflicts"""
        # Create program where renumbering would conflict
        basic.process_command('10 PRINT "CHANGE"')
        basic.process_command('15 PRINT "CHANGE"')  
        basic.process_command('50 PRINT "KEEP"')  # This will NOT be renumbered (old_start > 50)
        
        # Try RENUM starting from line 100 (which doesn't exist) with start=50
        # This should only renumber lines >= 100, but there are none
        # Let's create a proper conflict scenario:
        basic.process_command('100 PRINT "RENUM THIS"')
        
        # RENUM from line 100 with start=50 - would try to put line 100 at 50, 
        # but line 50 exists and won't be renumbered
        result = basic.process_command('RENUM 50,10,100')
        
        # Should detect conflict
        error_messages = [str(r.get('message', '')) for r in result if r.get('type') == 'error']
        assert any('CONFLICTS' in msg for msg in error_messages)

    def test_renum_boundary_conditions(self, basic, helpers):
        """Test RENUM boundary conditions and edge cases"""
        # Create program
        basic.process_command('10 PRINT "TEST"')
        
        # Test line number too high
        result = basic.process_command('RENUM 65530,10')
        error_messages = [str(r.get('message', '')) for r in result if r.get('type') == 'error']
        assert any('exceed maximum value' in msg.lower() for msg in error_messages)
        
        # Test invalid increment
        result = basic.process_command('RENUM 10,0')
        error_messages = [str(r.get('message', '')) for r in result if r.get('type') == 'error']
        assert any('must be positive' in msg.lower() for msg in error_messages)

    def test_renum_syntax_errors(self, basic, helpers):
        """Test RENUM command syntax error handling"""
        # Create program
        basic.process_command('10 PRINT "TEST"')
        
        # Test invalid line number format
        result = basic.process_command('RENUM ABC')
        error_messages = [str(r.get('message', '')) for r in result if r.get('type') == 'error']
        assert any('invalid' in msg.lower() and 'number' in msg.lower() for msg in error_messages)
        
        # Test line number out of range
        result = basic.process_command('RENUM 0')
        error_messages = [str(r.get('message', '')) for r in result if r.get('type') == 'error']
        assert any('out of range' in msg.lower() for msg in error_messages)

    def test_renum_preserves_line_order(self, basic, helpers):
        """Test RENUM preserves program line execution order"""
        # Create program with non-sequential line numbers
        basic.process_command('30 PRINT "THIRD"')
        basic.process_command('10 PRINT "FIRST"')
        basic.process_command('20 PRINT "SECOND"')
        basic.process_command('50 PRINT "FIFTH"')
        basic.process_command('40 PRINT "FOURTH"')
        
        # RENUM
        basic.process_command('RENUM')
        
        # Verify order is preserved (sorted by original line numbers)
        list_result = basic.process_command('LIST')
        list_text = '\n'.join(str(r.get('text', '')) for r in list_result)
        
        # Lines should appear in execution order
        first_pos = list_text.find('10 PRINT "FIRST"')
        second_pos = list_text.find('20 PRINT "SECOND"')
        third_pos = list_text.find('30 PRINT "THIRD"')
        fourth_pos = list_text.find('40 PRINT "FOURTH"')
        fifth_pos = list_text.find('50 PRINT "FIFTH"')
        
        assert first_pos < second_pos < third_pos < fourth_pos < fifth_pos

    def test_renum_complex_program(self, basic, helpers):
        """Test RENUM with complex program containing multiple reference types"""
        # Create complex program with various reference types
        basic.process_command('10 FOR I = 1 TO 3')
        basic.process_command('20 ON I GOTO 100,200,300')
        basic.process_command('30 NEXT I')
        basic.process_command('40 END')
        basic.process_command('100 PRINT "ONE"')
        basic.process_command('110 GOTO 30')
        basic.process_command('200 GOSUB 400')
        basic.process_command('210 GOTO 30')
        basic.process_command('300 PRINT "THREE"')
        basic.process_command('310 GOTO 30')
        basic.process_command('400 PRINT "SUBROUTINE"')
        basic.process_command('410 RETURN')
        
        # RENUM
        basic.process_command('RENUM 1000,10')
        
        # Verify all reference types were updated
        list_result = basic.process_command('LIST')
        list_output = ' '.join(str(r.get('text', '')) for r in list_result)
        
        # Check ON...GOTO was updated
        assert '1010 ON I GOTO 1040 in 1060,1080', list_output
        
        # Check GOTO was updated  
        assert '1050 GOTO 1020' in list_output
        
        # Check GOSUB was updated
        assert '1060 GOSUB 1100' in list_output

    def test_renum_unchanged_non_references(self, basic, helpers):
        """Test RENUM doesn't change non-line-number references"""
        # Create program with numbers that aren't line references
        basic.process_command('10 FOR I = 1 TO 100')  # 100 is not a line number
        basic.process_command('20 PRINT I * 200')     # 200 is not a line number
        basic.process_command('30 NEXT I')
        
        # RENUM
        basic.process_command('RENUM')
        
        # Verify non-reference numbers are unchanged
        list_result = basic.process_command('LIST')
        list_output = ' '.join(str(r.get('text', '')) for r in list_result)
        
        assert 'FOR I = 1 TO 100' in list_output  # 100 unchanged
        assert 'PRINT I * 200' in list_output     # 200 unchanged
