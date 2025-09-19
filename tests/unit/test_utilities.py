#!/usr/bin/env python3

"""
Test utilities for TRS-80 Color Computer BASIC emulator testing.
Provides mock objects, simulation helpers, and testing utilities.
"""

import sys
import os
from typing import List, Dict, Any, Optional, Tuple
from unittest.mock import Mock, patch
import io

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

from app import CoCoBasic


class MockGraphicsOutput:
    """Mock object for capturing graphics commands during testing"""
    
    def __init__(self):
        self.commands = []
        self.mode = 0
        self.screen_mode = 1
        
    def record_command(self, command_type: str, **kwargs):
        """Record a graphics command"""
        self.commands.append({
            'type': command_type,
            'timestamp': len(self.commands),
            **kwargs
        })
    
    def pmode(self, mode: int, page: int = 1):
        """Mock PMODE command"""
        self.mode = mode
        self.record_command('pmode', mode=mode, page=page)
    
    def pset(self, x: int, y: int, color: int = None):
        """Mock PSET command"""
        self.record_command('pset', x=x, y=y, color=color)
    
    def preset(self, x: int, y: int):
        """Mock PRESET command"""
        self.record_command('preset', x=x, y=y)
    
    def line(self, x1: int, y1: int, x2: int, y2: int, color: int = None):
        """Mock LINE command"""
        self.record_command('line', x1=x1, y1=y1, x2=x2, y2=y2, color=color)
    
    def circle(self, x: int, y: int, radius: int, color: int = None):
        """Mock CIRCLE command"""
        self.record_command('circle', x=x, y=y, radius=radius, color=color)
    
    def draw(self, command: str):
        """Mock DRAW command"""
        self.record_command('draw', command=command)
    
    def pcls(self):
        """Mock PCLS command"""
        self.record_command('pcls')
    
    def get_commands_by_type(self, command_type: str) -> List[Dict[str, Any]]:
        """Get all commands of a specific type"""
        return [cmd for cmd in self.commands if cmd['type'] == command_type]
    
    def clear_commands(self):
        """Clear all recorded commands"""
        self.commands.clear()
    
    def get_last_command(self) -> Optional[Dict[str, Any]]:
        """Get the last command recorded"""
        return self.commands[-1] if self.commands else None


class MockSoundOutput:
    """Mock object for capturing sound commands during testing"""
    
    def __init__(self):
        self.sounds = []
    
    def sound(self, frequency: int, duration: int):
        """Mock SOUND command"""
        self.sounds.append({
            'frequency': frequency,
            'duration': duration,
            'timestamp': len(self.sounds)
        })
    
    def get_sounds(self) -> List[Dict[str, Any]]:
        """Get all recorded sounds"""
        return self.sounds.copy()
    
    def clear_sounds(self):
        """Clear all recorded sounds"""
        self.sounds.clear()


class InputSimulator:
    """Simulates user input for INPUT and INKEY$ commands"""
    
    def __init__(self):
        self.input_queue = []
        self.key_buffer = []
    
    def queue_input(self, value: str):
        """Queue an input value for INPUT commands"""
        self.input_queue.append(value)
    
    def queue_key(self, key: str):
        """Queue a key for INKEY$ commands"""
        self.key_buffer.append(key)
    
    def get_next_input(self) -> Optional[str]:
        """Get the next queued input value"""
        return self.input_queue.pop(0) if self.input_queue else None
    
    def get_next_key(self) -> Optional[str]:
        """Get the next queued key"""
        return self.key_buffer.pop(0) if self.key_buffer else None
    
    def clear_all(self):
        """Clear all queued input and keys"""
        self.input_queue.clear()
        self.key_buffer.clear()


class TestCoCoBasic(CoCoBasic):
    """Extended CoCoBasic class with testing utilities"""
    
    def __init__(self, mock_graphics: bool = True, mock_sound: bool = True):
        super().__init__()
        
        # Set up mock objects
        self.mock_graphics = MockGraphicsOutput() if mock_graphics else None
        self.mock_sound = MockSoundOutput() if mock_sound else None
        self.input_simulator = InputSimulator()
        
        # Override graphics and sound methods if mocking
        if mock_graphics:
            self._patch_graphics_methods()
        if mock_sound:
            self._patch_sound_methods()
    
    def _patch_graphics_methods(self):
        """Replace graphics methods with mock versions"""
        # This would patch the actual graphics methods in the CoCoBasic class
        # The exact implementation depends on how graphics are handled
        pass
    
    def _patch_sound_methods(self):
        """Replace sound methods with mock versions"""
        # This would patch the actual sound methods in the CoCoBasic class
        pass
    
    def simulate_input_response(self, input_value: str):
        """Simulate a response to an INPUT command"""
        self.input_simulator.queue_input(input_value)
    
    def simulate_key_press(self, key: str):
        """Simulate a key press for INKEY$"""
        self.input_simulator.queue_key(key)
        # Also add to keyboard buffer if it exists
        if hasattr(self, 'keyboard_buffer'):
            self.keyboard_buffer.append(key)
    
    def get_graphics_commands(self) -> List[Dict[str, Any]]:
        """Get all recorded graphics commands"""
        return self.mock_graphics.commands if self.mock_graphics else []
    
    def get_sound_commands(self) -> List[Dict[str, Any]]:
        """Get all recorded sound commands"""
        return self.mock_sound.sounds if self.mock_sound else []
    
    def clear_mock_data(self):
        """Clear all mock data"""
        if self.mock_graphics:
            self.mock_graphics.clear_commands()
        if self.mock_sound:
            self.mock_sound.clear_sounds()
        self.input_simulator.clear_all()


class GraphicsTestHelper:
    """Helper class for graphics testing utilities"""
    
    @staticmethod
    def assert_pmode_called(graphics_mock: MockGraphicsOutput, mode: int, page: int = None):
        """Assert that PMODE was called with specific parameters"""
        pmode_commands = graphics_mock.get_commands_by_type('pmode')
        
        matching_commands = [cmd for cmd in pmode_commands if cmd['mode'] == mode]
        if page is not None:
            matching_commands = [cmd for cmd in matching_commands if cmd.get('page') == page]
        
        if not matching_commands:
            raise AssertionError(f"PMODE {mode}" + (f",{page}" if page else "") + " was not called")
    
    @staticmethod
    def assert_pixel_set(graphics_mock: MockGraphicsOutput, x: int, y: int, color: int = None):
        """Assert that a pixel was set at specific coordinates"""
        pset_commands = graphics_mock.get_commands_by_type('pset')
        
        matching_commands = [cmd for cmd in pset_commands if cmd['x'] == x and cmd['y'] == y]
        if color is not None:
            matching_commands = [cmd for cmd in matching_commands if cmd.get('color') == color]
        
        if not matching_commands:
            color_str = f" with color {color}" if color is not None else ""
            raise AssertionError(f"PSET({x},{y}){color_str} was not called")
    
    @staticmethod
    def assert_line_drawn(graphics_mock: MockGraphicsOutput, x1: int, y1: int, x2: int, y2: int):
        """Assert that a line was drawn between two points"""
        line_commands = graphics_mock.get_commands_by_type('line')
        
        matching_commands = [cmd for cmd in line_commands 
                           if cmd['x1'] == x1 and cmd['y1'] == y1 and 
                              cmd['x2'] == x2 and cmd['y2'] == y2]
        
        if not matching_commands:
            raise AssertionError(f"LINE({x1},{y1})-({x2},{y2}) was not drawn")
    
    @staticmethod
    def assert_circle_drawn(graphics_mock: MockGraphicsOutput, x: int, y: int, radius: int):
        """Assert that a circle was drawn"""
        circle_commands = graphics_mock.get_commands_by_type('circle')
        
        matching_commands = [cmd for cmd in circle_commands 
                           if cmd['x'] == x and cmd['y'] == y and cmd['radius'] == radius]
        
        if not matching_commands:
            raise AssertionError(f"CIRCLE({x},{y}),{radius} was not drawn")
    
    @staticmethod
    def get_screen_bounds(mode: int) -> Tuple[int, int]:
        """Get screen bounds for a given graphics mode"""
        mode_bounds = {
            0: (32, 16),    # Text mode
            1: (128, 96),   # 2-color
            2: (128, 96),   # 4-color
            3: (128, 192),  # 2-color high res
            4: (256, 192)   # 4-color high res
        }
        return mode_bounds.get(mode, (256, 192))


class ProgramTestHelper:
    """Helper class for program testing utilities"""
    
    @staticmethod
    def create_simple_program(*lines: str) -> List[str]:
        """Create a simple program with automatic line numbering"""
        program = []
        for i, line in enumerate(lines, 10):
            if not line.strip():
                continue
            # Add line number if not present
            if not line.strip()[0].isdigit():
                line = f"{i * 10} {line}"
            program.append(line)
        return program
    
    @staticmethod
    def extract_numeric_outputs(results: List[Dict[str, Any]]) -> List[float]:
        """Extract numeric values from program output"""
        numbers = []
        for result in results:
            if result.get('type') == 'text':
                text = result['text']
                # Try to extract numbers from the text
                import re
                numeric_matches = re.findall(r'-?\d+(?:\.\d+)?', text)
                for match in numeric_matches:
                    try:
                        numbers.append(float(match))
                    except ValueError:
                        pass
        return numbers
    
    @staticmethod
    def count_output_lines(results: List[Dict[str, Any]]) -> int:
        """Count the number of text output lines"""
        return sum(1 for result in results if result.get('type') == 'text')


class TestDataGenerator:
    """Generate test data for various testing scenarios"""
    
    @staticmethod
    def generate_for_loop_test(start: int, end: int, step: int = 1) -> List[str]:
        """Generate a FOR loop test program"""
        return [
            f'10 FOR I = {start} TO {end}' + (f' STEP {step}' if step != 1 else ''),
            '20 PRINT I',
            '30 NEXT I'
        ]
    
    @staticmethod
    def generate_math_test_program() -> List[str]:
        """Generate a program that tests mathematical operations"""
        return [
            '10 A = 10',
            '20 B = 5',
            '30 PRINT "A + B = "; A + B',
            '40 PRINT "A - B = "; A - B',
            '50 PRINT "A * B = "; A * B',
            '60 PRINT "A / B = "; A / B'
        ]
    
    @staticmethod
    def generate_string_test_program() -> List[str]:
        """Generate a program that tests string operations"""
        return [
            '10 A$ = "HELLO"',
            '20 B$ = "WORLD"',
            '30 PRINT A$; " "; B$',
            '40 C$ = A$ + B$',  # String concatenation if supported
            '50 PRINT C$'
        ]
    
    @staticmethod
    def generate_graphics_test_program() -> List[str]:
        """Generate a program that tests graphics commands"""
        return [
            '10 PMODE 4, 1',
            '20 SCREEN 1, 1',
            '30 PSET(100, 100)',
            '40 LINE(0, 0)-(255, 191)',
            '50 CIRCLE(128, 96), 50'
        ]


# Convenience functions for common test patterns
def create_test_basic(mock_graphics: bool = True, mock_sound: bool = True) -> TestCoCoBasic:
    """Create a TestCoCoBasic instance for testing"""
    return TestCoCoBasic(mock_graphics=mock_graphics, mock_sound=mock_sound)

def run_test_program(basic_instance: CoCoBasic, program_lines: List[str]) -> List[Dict[str, Any]]:
    """Load and run a test program, returning results"""
    basic_instance.process_command('NEW')  # Clear any existing program
    
    for line in program_lines:
        line_num, code = basic_instance.parse_line(line)
        if line_num is not None:
            basic_instance.program[line_num] = code
            basic_instance.expand_line_to_sublines(line_num, code)
    
    return basic_instance.process_command('RUN')

def assert_output_contains(results: List[Dict[str, Any]], expected_text: str):
    """Assert that program output contains specific text"""
    all_text = []
    for result in results:
        if result.get('type') == 'text':
            all_text.append(result['text'])
    
    combined_text = ' '.join(all_text)
    if expected_text not in combined_text:
        raise AssertionError(f"Expected '{expected_text}' in output, got: {combined_text}")

def assert_no_errors(results: List[Dict[str, Any]]):
    """Assert that program execution produced no errors"""
    errors = [result for result in results if result.get('type') == 'error']
    if errors:
        error_messages = [error.get('message', 'Unknown error') for error in errors]
        raise AssertionError(f"Unexpected errors: {error_messages}")


if __name__ == '__main__':
    # Demo of the test utilities
    print("TRS-80 Test Utilities Demo")
    print("=" * 40)
    
    # Create a test instance
    test_basic = create_test_basic()
    
    # Test basic functionality
    result = test_basic.process_command('PRINT "HELLO WORLD"')
    print(f"PRINT result: {result}")
    
    # Test program execution
    program = TestDataGenerator.generate_math_test_program()
    print(f"\nTest program: {program}")
    
    results = run_test_program(test_basic, program)
    print(f"Program results: {results}")
    
    # Test graphics mocking
    if test_basic.mock_graphics:
        test_basic.process_command('PMODE 4,1')
        test_basic.process_command('PSET(100,100)')
        graphics_commands = test_basic.get_graphics_commands()
        print(f"\nGraphics commands recorded: {graphics_commands}")
    
    print("\nDemo completed!")