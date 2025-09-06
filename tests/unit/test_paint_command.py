#!/usr/bin/env python3

"""
Unit tests for PAINT command - flood fill graphics operations.
Tests the PAINT command syntax, parameter handling, and error conditions.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from test_base import BaseTestCase


class PaintCommandTest(BaseTestCase):
    """Test cases for PAINT command functionality"""

    def test_basic_functionality(self):
        """Test basic PAINT command functionality"""
        # Switch to graphics mode first
        self.basic.execute_command('PMODE 2,1')
        self.basic.execute_command('SCREEN 1,1')
        
        # Test basic PAINT command
        self.assert_graphics_output('PAINT(64,48),3', 'paint')

    def test_paint_in_text_mode_error(self):
        """Test PAINT command fails in text mode"""
        # Ensure we're in text mode
        self.basic.execute_command('NEW')
        
        # PAINT should fail in text mode
        self.assert_error_output('PAINT(10,10),2', 'ILLEGAL FUNCTION CALL')

    def test_paint_with_boundary_color(self):
        """Test PAINT command with boundary color parameter"""
        # Switch to graphics mode
        self.basic.execute_command('PMODE 3,1')
        self.basic.execute_command('SCREEN 1,1')
        
        result = self.basic.execute_command('PAINT(100,80),2,1')
        self.assertTrue(any(item.get('type') == 'paint' for item in result))
        
        paint_item = next(item for item in result if item.get('type') == 'paint')
        self.assertEqual(paint_item['x'], 100)
        self.assertEqual(paint_item['y'], 80)
        self.assertEqual(paint_item['fill_color'], 2)
        self.assertEqual(paint_item['boundary_color'], 1)

    def test_paint_with_variables(self):
        """Test PAINT command with variable parameters"""
        # Switch to graphics mode and set variables
        self.basic.execute_command('PMODE 2,1')
        self.basic.execute_command('SCREEN 1,1')
        self.basic.variables['X'] = 50
        self.basic.variables['Y'] = 60
        self.basic.variables['C'] = 4
        
        result = self.basic.execute_command('PAINT(X,Y),C')
        self.assertTrue(any(item.get('type') == 'paint' for item in result))
        
        paint_item = next(item for item in result if item.get('type') == 'paint')
        self.assertEqual(paint_item['x'], 50)
        self.assertEqual(paint_item['y'], 60)
        self.assertEqual(paint_item['fill_color'], 4)

    def test_paint_with_expressions(self):
        """Test PAINT command with mathematical expressions"""
        # Switch to graphics mode
        self.basic.execute_command('PMODE 1,1')
        self.basic.execute_command('SCREEN 1,1')
        
        result = self.basic.execute_command('PAINT(10+5,20*2),2+1')
        self.assertTrue(any(item.get('type') == 'paint' for item in result))
        
        paint_item = next(item for item in result if item.get('type') == 'paint')
        self.assertEqual(paint_item['x'], 15)
        self.assertEqual(paint_item['y'], 40)
        self.assertEqual(paint_item['fill_color'], 3)

    def test_paint_floating_point_coordinates(self):
        """Test PAINT command with floating point coordinates"""
        # Switch to graphics mode
        self.basic.execute_command('PMODE 2,1')
        self.basic.execute_command('SCREEN 1,1')
        
        result = self.basic.execute_command('PAINT(25.7,30.3),2')
        self.assertTrue(any(item.get('type') == 'paint' for item in result))
        
        paint_item = next(item for item in result if item.get('type') == 'paint')
        self.assertEqual(paint_item['x'], 25)  # Should be converted to int
        self.assertEqual(paint_item['y'], 30)  # Should be converted to int
        self.assertEqual(paint_item['fill_color'], 2)

    def test_paint_syntax_errors(self):
        """Test PAINT command syntax error handling"""
        # Switch to graphics mode first
        self.basic.execute_command('PMODE 2,1')
        self.basic.execute_command('SCREEN 1,1')
        
        # Missing parentheses
        self.assert_error_output('PAINT 10,10,2')
        
        # Missing coordinates
        self.assert_error_output('PAINT(10),2')
        
        # Missing color
        self.assert_error_output('PAINT(10,10)')
        
        # Missing closing parenthesis
        self.assert_error_output('PAINT(10,10,2')
        
        # Too many coordinates
        self.assert_error_output('PAINT(10,20,30),2')

    def test_paint_in_program(self):
        """Test PAINT command within a program"""
        program = [
            '10 PMODE 2,1: SCREEN 1,1',
            '20 PAINT(32,24),1',
            '30 PAINT(64,48),2,3'
        ]
        
        results = self.execute_program(program)
        
        # Should have paint operations
        paint_results = [item for item in results if item.get('type') == 'paint']
        self.assertEqual(len(paint_results), 2)
        
        # Check first PAINT
        self.assertEqual(paint_results[0]['x'], 32)
        self.assertEqual(paint_results[0]['y'], 24)
        self.assertEqual(paint_results[0]['fill_color'], 1)
        self.assertEqual(paint_results[0]['boundary_color'], None)
        
        # Check second PAINT
        self.assertEqual(paint_results[1]['x'], 64)
        self.assertEqual(paint_results[1]['y'], 48)
        self.assertEqual(paint_results[1]['fill_color'], 2)
        self.assertEqual(paint_results[1]['boundary_color'], 3)

    def test_paint_with_other_graphics(self):
        """Test PAINT command combined with other graphics commands"""
        program = [
            '10 PMODE 3,1: SCREEN 1,1',
            '20 LINE(10,10)-(50,30),1',
            '30 PAINT(30,20),2,1',
            '40 CIRCLE(100,100),20,3',
            '50 PAINT(100,100),4'
        ]
        
        results = self.execute_program(program)
        
        # Should have line, paint, circle, and paint operations
        line_results = [item for item in results if item.get('type') == 'line']
        circle_results = [item for item in results if item.get('type') == 'circle']
        paint_results = [item for item in results if item.get('type') == 'paint']
        
        self.assertEqual(len(line_results), 1)
        self.assertEqual(len(circle_results), 1)
        self.assertEqual(len(paint_results), 2)

    def test_paint_edge_coordinates(self):
        """Test PAINT command at screen boundaries"""
        # Switch to graphics mode
        self.basic.execute_command('PMODE 1,1')
        self.basic.execute_command('SCREEN 1,1')
        
        # Test corner coordinates
        test_coords = [(0, 0), (127, 95), (0, 95), (127, 0)]
        
        for x, y in test_coords:
            result = self.basic.execute_command(f'PAINT({x},{y}),1')
            self.assertTrue(any(item.get('type') == 'paint' for item in result),
                          f"PAINT should work at ({x},{y})")

    def test_paint_zero_color(self):
        """Test PAINT command with color 0 (background)"""
        # Switch to graphics mode
        self.basic.execute_command('PMODE 2,1')
        self.basic.execute_command('SCREEN 1,1')
        
        result = self.basic.execute_command('PAINT(64,48),0')
        self.assertTrue(any(item.get('type') == 'paint' for item in result))
        
        paint_item = next(item for item in result if item.get('type') == 'paint')
        self.assertEqual(paint_item['fill_color'], 0)

    def test_paint_multi_statement_line(self):
        """Test PAINT command in multi-statement lines"""
        # Switch to graphics mode
        self.basic.execute_command('PMODE 2,1')
        self.basic.execute_command('SCREEN 1,1')
        
        result = self.basic.execute_command('PSET(10,10): PAINT(10,10),2: PSET(20,20)')
        
        # Should have pset, paint, pset operations
        pset_results = [item for item in result if item.get('type') == 'pset']
        paint_results = [item for item in result if item.get('type') == 'paint']
        
        self.assertEqual(len(pset_results), 2)
        self.assertEqual(len(paint_results), 1)


if __name__ == '__main__':
    test = PaintCommandTest("PAINT Command Tests")
    results = test.run_all_tests()
    from test_base import print_test_results
    print_test_results(results, verbose=True)