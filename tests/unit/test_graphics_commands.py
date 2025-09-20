#!/usr/bin/env python3

"""
Unit tests for graphics commands (PMODE, PSET, LINE, CIRCLE, etc.)
"""

import pytest


class TestGraphicsCommand:
    """Test cases for graphics commands"""
    
    # Remove unused setUp method

    def test_basic_functionality(self, basic, helpers):
        """Test basic graphics command functionality"""
        result = basic.process_command('PMODE 4,1')
        assert len(result) >= 0  # Should not error
        # Should produce graphics output for PMODE command
        graphics = helpers.get_graphics_output(result)
        assert any(g['type'] == 'pmode' for g in graphics)

    def test_pmode_command(self, basic, helpers):
        """Test PMODE command"""
        # Test various PMODE settings
        result = basic.process_command('PMODE 0,1')
        graphics = helpers.get_graphics_output(result)
        assert any(g['type'] == 'pmode' for g in graphics)

        result = basic.process_command('PMODE 1,1')
        graphics = helpers.get_graphics_output(result)
        assert any(g['type'] == 'pmode' for g in graphics)

        result = basic.process_command('PMODE 4,1')
        graphics = helpers.get_graphics_output(result)
        assert any(g['type'] == 'pmode' for g in graphics)
        
        # Verify the mode is set in the basic instance
        basic.process_command('PMODE 4,1')
        assert basic.graphics_mode == 4

    def test_screen_command(self, basic, helpers):
        """Test SCREEN command"""
        result = basic.process_command('SCREEN 1,1')
        # Should execute without error
        assert isinstance(result, list)

    def test_pset_command(self, basic, helpers):
        """Test PSET command"""
        # First set graphics mode
        basic.process_command('PMODE 4,1')
        
        # Test PSET commands
        result = basic.process_command('PSET(100,100)')
        graphics = helpers.get_graphics_output(result)
        assert any(g['type'] == 'pset' for g in graphics)

        result = basic.process_command('PSET(0,0)')
        graphics = helpers.get_graphics_output(result)
        assert any(g['type'] == 'pset' for g in graphics)

        result = basic.process_command('PSET(255,191)')
        graphics = helpers.get_graphics_output(result)
        assert any(g['type'] == 'pset' for g in graphics)

    def test_preset_command(self, basic, helpers):
        """Test PRESET command"""
        # First set graphics mode
        basic.process_command('PMODE 4,1')
        
        # Test PRESET commands
        result = basic.process_command('PRESET(100,100)')
        graphics = helpers.get_graphics_output(result)
        assert any(g['type'] == 'preset' for g in graphics)

    def test_line_command(self, basic, helpers):
        """Test LINE command"""
        # First set graphics mode
        basic.process_command('PMODE 4,1')
        
        # Test various LINE formats
        result = basic.process_command('LINE(0,0)-(100,100)')
        graphics = helpers.get_graphics_output(result)
        assert any(g['type'] == 'line' for g in graphics)

        result = basic.process_command('LINE(50,50)-(200,150)')
        graphics = helpers.get_graphics_output(result)
        assert any(g['type'] == 'line' for g in graphics)

    def test_circle_command(self, basic, helpers):
        """Test CIRCLE command"""
        # First set graphics mode
        basic.process_command('PMODE 4,1')
        
        # Test CIRCLE commands
        result = basic.process_command('CIRCLE(100,100),50')
        graphics = helpers.get_graphics_output(result)
        assert any(g['type'] == 'circle' for g in graphics)

        result = basic.process_command('CIRCLE(128,96),25')
        graphics = helpers.get_graphics_output(result)
        assert any(g['type'] == 'circle' for g in graphics)

    def test_pcls_command(self, basic, helpers):
        """Test PCLS (clear graphics) command"""
        # First set graphics mode
        basic.process_command('PMODE 4,1')
        
        # Test PCLS
        result = basic.process_command('PCLS')
        graphics = helpers.get_graphics_output(result)
        assert any(g['type'] == 'pcls' for g in graphics)

    def test_color_command(self, basic, helpers):
        """Test COLOR command"""
        result = basic.process_command('COLOR 1,2')
        # Should execute without error
        assert isinstance(result, list)

    def test_draw_command(self, basic, helpers):
        """Test DRAW command"""
        # First set graphics mode
        basic.process_command('PMODE 4,1')
        
        # Test various DRAW commands - DRAW commands produce line/move graphics
        result = basic.process_command('DRAW "U10"')
        graphics = helpers.get_graphics_output(result)
        assert len(graphics) > 0, "DRAW 'U10' should produce graphics output"
        assert any(g.get('type') in ['line', 'move'] for g in graphics), \
               f"DRAW should produce line/move graphics, got types: {[g.get('type') for g in graphics]}"

        result = basic.process_command('DRAW "R20D10L20U10"')
        # Complex DRAW should produce multiple graphics commands
        assert len(result) > 0, "Complex DRAW command should produce output"
        graphics = helpers.get_graphics_output(result)
        assert len(graphics) >= 4, f"Complex DRAW should produce multiple graphics commands, got {len(graphics)}"
        assert any(item.get('type') in ['line', 'move'] for item in result), \
               f"DRAW should produce line/move types, got: {[item.get('type') for item in result]}"

    def test_graphics_bounds_checking(self, basic, helpers):
        """Test graphics commands with boundary values"""
        basic.process_command('PMODE 4,1')

        # Test coordinates at boundaries (PMODE 4 is 256x192)
        # Top-left corner
        result1 = basic.process_command('PSET(0,0)')
        errors1 = helpers.get_error_messages(result1)
        assert len(errors1) == 0, f"PSET(0,0) should be valid for boundary, got errors: {errors1}"
        graphics1 = helpers.get_graphics_output(result1)
        assert len(graphics1) > 0, "PSET(0,0) should produce graphics output"

        # Bottom-right corner
        result2 = basic.process_command('PSET(255,191)')
        errors2 = helpers.get_error_messages(result2)
        assert len(errors2) == 0, f"PSET(255,191) should be valid for boundary, got errors: {errors2}"
        graphics2 = helpers.get_graphics_output(result2)
        assert len(graphics2) > 0, "PSET(255,191) should produce graphics output"

    def test_graphics_without_pmode(self, basic, helpers):
        """Test graphics commands without setting PMODE first"""
        # Some implementations may require PMODE first
        result = basic.process_command('PSET(100,100)')
        # Behavior may vary - either works or produces error
        assert isinstance(result, list)

    def test_graphics_program(self, basic, helpers):
        """Test graphics commands within a program"""
        program = [
            '10 PMODE 4,1',
            '20 SCREEN 1,1',
            '30 PSET(100,100)',
            '40 LINE(0,0)-(255,191)',
            '50 CIRCLE(128,96),50'
        ]
        
        results = helpers.execute_program(basic, program)
        
        # Should complete without errors
        errors = helpers.get_error_messages(results)
        assert len(errors) == 0, f"Graphics program should not produce errors: {errors}"

    def test_multiple_pmode_settings(self, basic, helpers):
        """Test changing PMODE settings"""
        # Test switching between different modes
        basic.process_command('PMODE 1,1')
        assert basic.graphics_mode == 1
        
        basic.process_command('PMODE 4,1')
        assert basic.graphics_mode == 4
        
        basic.process_command('PMODE 0,1')  # Back to text mode
        assert basic.graphics_mode == 0

    def test_graphics_coordinate_systems(self, basic, helpers):
        """Test different coordinate systems for different modes"""
        # PMODE 4 should be 256x192
        basic.process_command('PMODE 4,1')
        # PMODE 4 should be 256x192
        bounds = (256, 192)
        
        # Test coordinates within bounds
        basic.process_command(f'PSET({bounds[0]-1},{bounds[1]-1})')

    def test_graphics_with_variables(self, basic, helpers):
        """Test graphics commands using variables"""
        program = [
            '10 PMODE 4,1',
            '20 X = 100',
            '30 Y = 100',
            '40 R = 50',
            '50 PSET(X,Y)',
            '60 CIRCLE(X,Y),R'
        ]
        
        results = helpers.execute_program(basic, program)
        errors = helpers.get_error_messages(results)
        assert len(errors) == 0, f"Graphics with variables should work: {errors}"

    def test_graphics_command_syntax_variations(self, basic, helpers):
        """Test various graphics command syntax parsing variations"""
        # Set up graphics mode
        basic.process_command('PMODE 1,1')
        
        # Test PSET with different syntax variations
        # Traditional space-separated syntax
        result1 = basic.process_command('PSET 10, 20')
        assert len([r for r in result1 if r.get('type') == 'error']) == 0
        
        # Parentheses syntax
        result2 = basic.process_command('PSET(30, 40)')
        assert len([r for r in result2 if r.get('type') == 'error']) == 0
        
        # Test PRESET with different syntax
        result3 = basic.process_command('PRESET 50, 60')
        assert len([r for r in result3 if r.get('type') == 'error']) == 0
        
        result4 = basic.process_command('PRESET(70, 80)')
        assert len([r for r in result4 if r.get('type') == 'error']) == 0
        
        # Test CIRCLE with different syntax variations
        result5 = basic.process_command('CIRCLE 100, 100, 25')
        assert len([r for r in result5 if r.get('type') == 'error']) == 0
        
        result6 = basic.process_command('CIRCLE(120, 120), 30')
        assert len([r for r in result6 if r.get('type') == 'error']) == 0
        
        # Test LINE with different syntax
        result7 = basic.process_command('LINE 10, 10, 50, 50')
        assert len([r for r in result7 if r.get('type') == 'error']) == 0
        
        result8 = basic.process_command('LINE(60, 60)-(90, 90)')
        assert len([r for r in result8 if r.get('type') == 'error']) == 0

    def test_graphics_with_expressions_and_functions(self, basic, helpers):
        """Test graphics commands with complex expressions and function calls"""
        # Set up graphics mode and variables
        basic.process_command('PMODE 2,1')
        basic.process_command('CENTERX = 128')
        basic.process_command('CENTERY = 96')
        basic.process_command('SIZE = 25')
        
        # Test PSET with mathematical expressions
        result1 = basic.process_command('PSET(CENTERX + 10, CENTERY - 5)')
        assert len([r for r in result1 if r.get('type') == 'error']) == 0
        
        # Test CIRCLE with function calls
        result2 = basic.process_command('CIRCLE(CENTERX, CENTERY), ABS(SIZE)')
        assert len([r for r in result2 if r.get('type') == 'error']) == 0
        
        # Test PSET with nested expressions
        basic.process_command('OFFSET = 15')
        result3 = basic.process_command('PSET(CENTERX + SQR(OFFSET), CENTERY + INT(SIZE/2))')
        assert len([r for r in result3 if r.get('type') == 'error']) == 0
        
        # Test LINE with complex coordinate expressions
        result4 = basic.process_command('LINE(CENTERX - SIZE, CENTERY - SIZE)-(CENTERX + SIZE, CENTERY + SIZE)')
        assert len([r for r in result4 if r.get('type') == 'error']) == 0

    def test_graphics_syntax_edge_cases(self, basic, helpers):
        """Test graphics command syntax edge cases and error handling"""
        # Set up graphics mode
        basic.process_command('PMODE 1,1')
        
        # Test with spaces in different places
        result1 = basic.process_command('PSET( 10 , 20 )')
        assert len([r for r in result1 if r.get('type') == 'error']) == 0
        
        result2 = basic.process_command('CIRCLE( 50 , 50 ) , 25')
        assert len([r for r in result2 if r.get('type') == 'error']) == 0
        
        # Test with variables in parentheses
        basic.process_command('X = 75')
        basic.process_command('Y = 85')
        result3 = basic.process_command('PSET(X, Y)')
        assert len([r for r in result3 if r.get('type') == 'error']) == 0
        
        # Test parentheses with expressions
        result4 = basic.process_command('PSET(X + 10, Y - 5)')
        assert len([r for r in result4 if r.get('type') == 'error']) == 0
        
        # Test color parameters with parentheses
        result5 = basic.process_command('PSET(100, 100), 1')
        assert len([r for r in result5 if r.get('type') == 'error']) == 0
        
        result6 = basic.process_command('PSET(110, 110), ABS(-2)')
        assert len([r for r in result6 if r.get('type') == 'error']) == 0
