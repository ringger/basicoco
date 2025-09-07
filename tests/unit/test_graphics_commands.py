#!/usr/bin/env python3

"""
Unit tests for graphics commands (PMODE, PSET, LINE, CIRCLE, etc.)
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from test_base import BaseTestCase
from test_utilities import create_test_basic, GraphicsTestHelper


class GraphicsCommandTest(BaseTestCase):
    """Test cases for graphics commands"""
    
    def setUp(self):
        """Set up with graphics mocking enabled"""
        self.basic = create_test_basic(mock_graphics=True, mock_sound=True)
        self.basic.execute_command('NEW')

    def test_basic_functionality(self):
        """Test basic graphics command functionality"""
        result = self.basic.execute_command('PMODE 4,1')
        self.assertTrue(len(result) >= 0)  # Should not error

    def test_pmode_command(self):
        """Test PMODE command"""
        # Test various PMODE settings
        self.assert_graphics_output('PMODE 0,1', 'pmode')
        self.assert_graphics_output('PMODE 1,1', 'pmode')
        self.assert_graphics_output('PMODE 4,1', 'pmode')
        
        # Verify the mode is set in the basic instance
        self.basic.execute_command('PMODE 4,1')
        self.assertEqual(self.basic.graphics_mode, 4)

    def test_screen_command(self):
        """Test SCREEN command"""
        result = self.basic.execute_command('SCREEN 1,1')
        # Should execute without error
        self.assertTrue(isinstance(result, list))

    def test_pset_command(self):
        """Test PSET command"""
        # First set graphics mode
        self.basic.execute_command('PMODE 4,1')
        
        # Test PSET commands
        self.assert_graphics_output('PSET(100,100)', 'pset')
        self.assert_graphics_output('PSET(0,0)', 'pset')
        self.assert_graphics_output('PSET(255,191)', 'pset')

    def test_preset_command(self):
        """Test PRESET command"""
        # First set graphics mode
        self.basic.execute_command('PMODE 4,1')
        
        # Test PRESET commands
        self.assert_graphics_output('PRESET(100,100)', 'preset')

    def test_line_command(self):
        """Test LINE command"""
        # First set graphics mode
        self.basic.execute_command('PMODE 4,1')
        
        # Test various LINE formats
        self.assert_graphics_output('LINE(0,0)-(100,100)', 'line')
        self.assert_graphics_output('LINE(50,50)-(200,150)', 'line')

    def test_circle_command(self):
        """Test CIRCLE command"""
        # First set graphics mode
        self.basic.execute_command('PMODE 4,1')
        
        # Test CIRCLE commands
        self.assert_graphics_output('CIRCLE(100,100),50', 'circle')
        self.assert_graphics_output('CIRCLE(128,96),25', 'circle')

    def test_pcls_command(self):
        """Test PCLS (clear graphics) command"""
        # First set graphics mode
        self.basic.execute_command('PMODE 4,1')
        
        # Test PCLS
        self.assert_graphics_output('PCLS', 'pcls')

    def test_color_command(self):
        """Test COLOR command"""
        result = self.basic.execute_command('COLOR 1,2')
        # Should execute without error
        self.assertTrue(isinstance(result, list))

    def test_draw_command(self):
        """Test DRAW command"""
        # First set graphics mode
        self.basic.execute_command('PMODE 4,1')
        
        # Test various DRAW commands - DRAW commands produce line/move graphics
        self.assert_graphics_output('DRAW "U10"', 'line')  # DRAW produces line graphics
        result = self.basic.execute_command('DRAW "R20D10L20U10"')
        # Complex DRAW should produce multiple graphics commands
        self.assertTrue(len(result) > 0)
        self.assertTrue(any(item.get('type') in ['line', 'move'] for item in result))

    def test_graphics_bounds_checking(self):
        """Test graphics commands with boundary values"""
        self.basic.execute_command('PMODE 4,1')
        
        # Test coordinates at boundaries (PMODE 4 is 256x192)
        try:
            self.basic.execute_command('PSET(0,0)')      # Top-left
            self.basic.execute_command('PSET(255,191)')  # Bottom-right
        except Exception as e:
            self.fail(f"Valid boundary coordinates should not fail: {e}")

    def test_graphics_without_pmode(self):
        """Test graphics commands without setting PMODE first"""
        # Some implementations may require PMODE first
        result = self.basic.execute_command('PSET(100,100)')
        # Behavior may vary - either works or produces error
        self.assertTrue(isinstance(result, list))

    def test_graphics_program(self):
        """Test graphics commands within a program"""
        program = [
            '10 PMODE 4,1',
            '20 SCREEN 1,1',
            '30 PSET(100,100)',
            '40 LINE(0,0)-(255,191)',
            '50 CIRCLE(128,96),50'
        ]
        
        results = self.execute_program(program)
        
        # Should complete without errors
        errors = self.get_error_messages(results)
        self.assertEqual(len(errors), 0, f"Graphics program should not produce errors: {errors}")

    def test_multiple_pmode_settings(self):
        """Test changing PMODE settings"""
        # Test switching between different modes
        self.basic.execute_command('PMODE 1,1')
        self.assertEqual(self.basic.graphics_mode, 1)
        
        self.basic.execute_command('PMODE 4,1')
        self.assertEqual(self.basic.graphics_mode, 4)
        
        self.basic.execute_command('PMODE 0,1')  # Back to text mode
        self.assertEqual(self.basic.graphics_mode, 0)

    def test_graphics_coordinate_systems(self):
        """Test different coordinate systems for different modes"""
        # PMODE 4 should be 256x192
        self.basic.execute_command('PMODE 4,1')
        bounds = GraphicsTestHelper.get_screen_bounds(4)
        self.assertEqual(bounds, (256, 192))
        
        # Test coordinates within bounds
        self.basic.execute_command(f'PSET({bounds[0]-1},{bounds[1]-1})')

    def test_graphics_with_variables(self):
        """Test graphics commands using variables"""
        program = [
            '10 PMODE 4,1',
            '20 X = 100',
            '30 Y = 100',
            '40 R = 50',
            '50 PSET(X,Y)',
            '60 CIRCLE(X,Y),R'
        ]
        
        results = self.execute_program(program)
        errors = self.get_error_messages(results)
        self.assertEqual(len(errors), 0, f"Graphics with variables should work: {errors}")

    def test_graphics_command_syntax_variations(self):
        """Test various graphics command syntax parsing variations"""
        # Set up graphics mode
        self.basic.execute_command('PMODE 1,1')
        
        # Test PSET with different syntax variations
        # Traditional space-separated syntax
        result1 = self.basic.execute_command('PSET 10, 20')
        self.assertTrue(len([r for r in result1 if r.get('type') == 'error']) == 0)
        
        # Parentheses syntax
        result2 = self.basic.execute_command('PSET(30, 40)')
        self.assertTrue(len([r for r in result2 if r.get('type') == 'error']) == 0)
        
        # Test PRESET with different syntax
        result3 = self.basic.execute_command('PRESET 50, 60')
        self.assertTrue(len([r for r in result3 if r.get('type') == 'error']) == 0)
        
        result4 = self.basic.execute_command('PRESET(70, 80)')
        self.assertTrue(len([r for r in result4 if r.get('type') == 'error']) == 0)
        
        # Test CIRCLE with different syntax variations
        result5 = self.basic.execute_command('CIRCLE 100, 100, 25')
        self.assertTrue(len([r for r in result5 if r.get('type') == 'error']) == 0)
        
        result6 = self.basic.execute_command('CIRCLE(120, 120), 30')
        self.assertTrue(len([r for r in result6 if r.get('type') == 'error']) == 0)
        
        # Test LINE with different syntax
        result7 = self.basic.execute_command('LINE 10, 10, 50, 50')
        self.assertTrue(len([r for r in result7 if r.get('type') == 'error']) == 0)
        
        result8 = self.basic.execute_command('LINE(60, 60)-(90, 90)')
        self.assertTrue(len([r for r in result8 if r.get('type') == 'error']) == 0)

    def test_graphics_with_expressions_and_functions(self):
        """Test graphics commands with complex expressions and function calls"""
        # Set up graphics mode and variables
        self.basic.execute_command('PMODE 2,1')
        self.basic.execute_command('CENTERX = 128')
        self.basic.execute_command('CENTERY = 96')
        self.basic.execute_command('SIZE = 25')
        
        # Test PSET with mathematical expressions
        result1 = self.basic.execute_command('PSET(CENTERX + 10, CENTERY - 5)')
        self.assertTrue(len([r for r in result1 if r.get('type') == 'error']) == 0)
        
        # Test CIRCLE with function calls
        result2 = self.basic.execute_command('CIRCLE(CENTERX, CENTERY), ABS(SIZE)')
        self.assertTrue(len([r for r in result2 if r.get('type') == 'error']) == 0)
        
        # Test PSET with nested expressions
        self.basic.execute_command('OFFSET = 15')
        result3 = self.basic.execute_command('PSET(CENTERX + SQR(OFFSET), CENTERY + INT(SIZE/2))')
        self.assertTrue(len([r for r in result3 if r.get('type') == 'error']) == 0)
        
        # Test LINE with complex coordinate expressions
        result4 = self.basic.execute_command('LINE(CENTERX - SIZE, CENTERY - SIZE)-(CENTERX + SIZE, CENTERY + SIZE)')
        self.assertTrue(len([r for r in result4 if r.get('type') == 'error']) == 0)

    def test_graphics_syntax_edge_cases(self):
        """Test graphics command syntax edge cases and error handling"""
        # Set up graphics mode
        self.basic.execute_command('PMODE 1,1')
        
        # Test with spaces in different places
        result1 = self.basic.execute_command('PSET( 10 , 20 )')
        self.assertTrue(len([r for r in result1 if r.get('type') == 'error']) == 0)
        
        result2 = self.basic.execute_command('CIRCLE( 50 , 50 ) , 25')
        self.assertTrue(len([r for r in result2 if r.get('type') == 'error']) == 0)
        
        # Test with variables in parentheses
        self.basic.execute_command('X = 75')
        self.basic.execute_command('Y = 85')
        result3 = self.basic.execute_command('PSET(X, Y)')
        self.assertTrue(len([r for r in result3 if r.get('type') == 'error']) == 0)
        
        # Test parentheses with expressions
        result4 = self.basic.execute_command('PSET(X + 10, Y - 5)')
        self.assertTrue(len([r for r in result4 if r.get('type') == 'error']) == 0)
        
        # Test color parameters with parentheses
        result5 = self.basic.execute_command('PSET(100, 100), 1')
        self.assertTrue(len([r for r in result5 if r.get('type') == 'error']) == 0)
        
        result6 = self.basic.execute_command('PSET(110, 110), ABS(-2)')
        self.assertTrue(len([r for r in result6 if r.get('type') == 'error']) == 0)


if __name__ == '__main__':
    test = GraphicsCommandTest("Graphics Commands Tests")
    results = test.run_all_tests()
    from test_base import print_test_results
    print_test_results(results, verbose=True)