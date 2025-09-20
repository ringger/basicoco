#!/usr/bin/env python3

"""
Unit tests for PAINT command - flood fill graphics operations.
Tests the PAINT command syntax, parameter handling, and error conditions.
"""

import pytest


class TestPaintCommand:
    """Test cases for PAINT command functionality"""

    def test_basic_functionality(self, basic, helpers):
        """Test basic PAINT command functionality"""
        # Switch to graphics mode first
        basic.process_command('PMODE 2,1')
        basic.process_command('SCREEN 1,1')
        
        # Test basic PAINT command
        result = basic.process_command('PAINT(64,48),3')
        graphics = helpers.get_graphics_output(result)
        assert len(graphics) == 1
        assert graphics[0]['type'] == 'paint'

    def test_paint_in_text_mode_error(self, basic, helpers):
        """Test PAINT command fails in text mode"""
        # Ensure we're in text mode
        basic.process_command('NEW')
        
        # PAINT should fail in text mode
        helpers.assert_error_output(basic, 'PAINT(10, 10),2', 'ILLEGAL FUNCTION CALL')

    def test_paint_with_boundary_color(self, basic, helpers):
        """Test PAINT command with boundary color parameter"""
        # Switch to graphics mode
        basic.process_command('PMODE 3,1')
        basic.process_command('SCREEN 1,1')
        
        result = basic.process_command('PAINT(100,80),2,1')
        assert any(item.get('type') == 'paint' for item in result)
        
        paint_item = next(item for item in result if item.get('type') == 'paint')
        assert paint_item['x'] == 100
        assert paint_item['y'] == 80
        assert paint_item['fill_color'] == 2
        assert paint_item['boundary_color'] == 1

    def test_paint_with_variables(self, basic, helpers):
        """Test PAINT command with variable parameters"""
        # Switch to graphics mode and set variables
        basic.process_command('PMODE 2,1')
        basic.process_command('SCREEN 1,1')
        basic.variables['X'] = 50
        basic.variables['Y'] = 60
        basic.variables['C'] = 4
        
        result = basic.process_command('PAINT(X,Y),C')
        assert any(item.get('type') == 'paint' for item in result)
        
        paint_item = next(item for item in result if item.get('type') == 'paint')
        assert paint_item['x'] == 50
        assert paint_item['y'] == 60
        assert paint_item['fill_color'] == 4

    def test_paint_with_expressions(self, basic, helpers):
        """Test PAINT command with mathematical expressions"""
        # Switch to graphics mode
        basic.process_command('PMODE 1,1')
        basic.process_command('SCREEN 1,1')
        
        result = basic.process_command('PAINT(10+5,20*2),2+1')
        assert any(item.get('type') == 'paint' for item in result)
        
        paint_item = next(item for item in result if item.get('type') == 'paint')
        assert paint_item['x'] == 15
        assert paint_item['y'] == 40
        assert paint_item['fill_color'] == 3

    def test_paint_floating_point_coordinates(self, basic, helpers):
        """Test PAINT command with floating point coordinates"""
        # Switch to graphics mode
        basic.process_command('PMODE 2,1')
        basic.process_command('SCREEN 1,1')
        
        result = basic.process_command('PAINT(25.7,30.3),2')
        assert any(item.get('type') == 'paint' for item in result)
        
        paint_item = next(item for item in result if item.get('type') == 'paint')
        assert paint_item['x'] == 25  # Should be converted to int
        assert paint_item['y'] == 30  # Should be converted to int
        assert paint_item['fill_color'] == 2

    def test_paint_syntax_errors(self, basic, helpers):
        """Test PAINT command syntax error handling"""
        # Switch to graphics mode first
        basic.process_command('PMODE 2,1')
        basic.process_command('SCREEN 1,1')
        
        # Missing parentheses
        helpers.assert_error_output(basic, 'PAINT 10, 10,2')
        
        # Missing coordinates
        helpers.assert_error_output(basic, 'PAINT(10), 2')
        
        # Missing color
        helpers.assert_error_output(basic, 'PAINT(10, 10)')
        
        # Missing closing parenthesis
        helpers.assert_error_output(basic, 'PAINT(10, 10,2')
        
        # Too many coordinates
        helpers.assert_error_output(basic, 'PAINT(10, 20,30),2')

    def test_paint_in_program(self, basic, helpers):
        """Test PAINT command within a program"""
        program = [
            '10 PMODE 2,1: SCREEN 1,1',
            '20 PAINT(32,24),1',
            '30 PAINT(64,48),2,3'
        ]
        
        results = helpers.execute_program(basic, program)
        
        # Should have paint operations
        paint_results = [item for item in results if item.get('type') == 'paint']
        assert len(paint_results) == 2
        
        # Check first PAINT
        assert paint_results[0]['x'] == 32
        assert paint_results[0]['y'] == 24
        assert paint_results[0]['fill_color'] == 1
        assert paint_results[0]['boundary_color'] == None
        
        # Check second PAINT
        assert paint_results[1]['x'] == 64
        assert paint_results[1]['y'] == 48
        assert paint_results[1]['fill_color'] == 2
        assert paint_results[1]['boundary_color'] == 3

    def test_paint_with_other_graphics(self, basic, helpers):
        """Test PAINT command combined with other graphics commands"""
        program = [
            '10 PMODE 3,1: SCREEN 1,1',
            '20 LINE(10,10)-(50,30),1',
            '30 PAINT(30,20),2,1',
            '40 CIRCLE(100,100),20,3',
            '50 PAINT(100,100),4'
        ]
        
        results = helpers.execute_program(basic, program)
        
        # Should have line, paint, circle, and paint operations
        line_results = [item for item in results if item.get('type') == 'line']
        circle_results = [item for item in results if item.get('type') == 'circle']
        paint_results = [item for item in results if item.get('type') == 'paint']
        
        assert len(line_results) == 1
        assert len(circle_results) == 1
        assert len(paint_results) == 2

    def test_paint_edge_coordinates(self, basic, helpers):
        """Test PAINT command at screen boundaries"""
        # Switch to graphics mode
        basic.process_command('PMODE 1,1')
        basic.process_command('SCREEN 1,1')
        
        # Test corner coordinates
        test_coords = [(0, 0), (127, 95), (0, 95), (127, 0)]
        
        for x, y in test_coords:
            result = basic.process_command(f'PAINT({x},{y}),1')
            assert any(item.get('type') == 'paint' for item in result), \
                          f"PAINT should work at ({x},{y})"

    def test_paint_zero_color(self, basic, helpers):
        """Test PAINT command with color 0 (background)"""
        # Switch to graphics mode
        basic.process_command('PMODE 2,1')
        basic.process_command('SCREEN 1,1')
        
        result = basic.process_command('PAINT(64,48),0')
        assert any(item.get('type') == 'paint' for item in result)
        
        paint_item = next(item for item in result if item.get('type') == 'paint')
        assert paint_item['fill_color'] == 0

    def test_paint_multi_statement_line(self, basic, helpers):
        """Test PAINT command in multi-statement lines"""
        # Switch to graphics mode
        basic.process_command('PMODE 2,1')
        basic.process_command('SCREEN 1,1')
        
        result = basic.process_command('PSET(10,10): PAINT(10,10),2: PSET(20,20)')
        
        # Should have pset, paint, pset operations
        pset_results = [item for item in result if item.get('type') == 'pset']
        paint_results = [item for item in result if item.get('type') == 'paint']
        
        assert len(pset_results) == 2
        assert len(paint_results) == 1
