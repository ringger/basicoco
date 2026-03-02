"""
Graphics module for TRS-80 Color Computer BASIC Emulator

This module contains all graphics-related commands and operations including
PMODE, SCREEN, PSET, LINE, CIRCLE, PAINT, GET, PUT, and DRAW commands.
Extracted from the main CoCoBasic class for better organization.
"""

from .parser import BasicParser
from .commands import CommandRegistry
from .error_context import error_response

_split_args = BasicParser.split_args  # Shared comma-split helper


def _graphics_command(command_name):
    """Decorator that wraps a graphics method with standard error handling."""
    def decorator(method):
        def wrapper(self, args):
            try:
                return method(self, args)
            except Exception as e:
                err = self.emulator.error_context.runtime_error(
                    f"Error in {command_name}: {e}",
                    self.emulator.current_line)
                return error_response(err)
        wrapper.__name__ = method.__name__
        wrapper.__doc__ = method.__doc__
        return wrapper
    return decorator


class BasicGraphics:
    """Handler for BASIC graphics commands"""
    
    def __init__(self, emulator):
        """Initialize graphics handler with reference to main emulator"""
        self.emulator = emulator
    
    def register_commands(self, registry):
        """Register graphics commands with the command registry"""
        registry.register('PMODE', self.execute_pmode)
        registry.register('SCREEN', self.execute_screen)
        registry.register('COLOR', self.execute_color)
        registry.register('PSET', self.execute_pset)
        registry.register('PRESET', self.execute_preset)
        registry.register('LINE', self.execute_line_graphics)
        registry.register('CIRCLE', self.execute_circle)
        registry.register('PAINT', self.execute_paint)
        registry.register('GET', self.execute_get)
        registry.register('PUT', self.execute_put)
        registry.register('DRAW', self.execute_draw)
        registry.register('PCLS', lambda args: [{'type': 'pcls'}])
    
    def _eval_int(self, expr):
        """Evaluate an expression string and return an integer."""
        return int(self.emulator.evaluate_expression(expr.strip()))

    def _syntax_error(self, message, suggestions):
        """Create a standardized syntax error response list."""
        error = self.emulator.error_context.syntax_error(
            message, self.emulator.current_line, suggestions=suggestions)
        return error_response(error)

    @staticmethod
    def _illegal_function_call():
        """Return an ILLEGAL FUNCTION CALL error response."""
        return [{'type': 'error', 'message': 'ILLEGAL FUNCTION CALL'}]

    def _require_graphics_mode(self):
        """Return error response if not in graphics mode, else None."""
        if self.emulator.graphics_mode == 0:
            return self._illegal_function_call()
        return None

    def _parse_coord_pair(self, args, command_name):
        """Parse (x,y) from args. Returns (x, y, remainder_after_paren) or error list."""
        if not (args.startswith('(') and ')' in args):
            return self._syntax_error(
                f"{command_name} requires parenthesized coordinates",
                [f'Correct syntax: {command_name}(x,y)', f'Example: {command_name}(100,50)'])
        coords_end = self._find_matching_parenthesis(args, 0)
        if coords_end == -1:
            return self._syntax_error(
                f"Missing closing parenthesis in {command_name} coordinates",
                [f'Correct syntax: {command_name}(x,y)',
                 f'Example: {command_name}(100,50)',
                 'Make sure parentheses are properly matched'])
        coords = args[1:coords_end]
        coord_parts = _split_args(coords)
        if len(coord_parts) != 2:
            return self._syntax_error(
                f"{command_name} requires exactly two coordinates",
                [f'Correct syntax: {command_name}(x,y)',
                 f'Example: {command_name}(100,50)',
                 'Specify both X and Y coordinates'])
        x = self._eval_int(coord_parts[0])
        y = self._eval_int(coord_parts[1])
        remainder = args[coords_end + 1:].strip()
        return (x, y, remainder)

    def _find_matching_parenthesis(self, text, start):
        """Find the matching closing parenthesis for the opening one at start"""
        if start >= len(text) or text[start] != '(':
            return -1
        
        paren_count = 0
        for i in range(start, len(text)):
            if text[i] == '(':
                paren_count += 1
            elif text[i] == ')':
                paren_count -= 1
                if paren_count == 0:
                    return i
        return -1
    
    
    @_graphics_command('PMODE')
    def execute_pmode(self, args):
        """Execute PMODE command to set graphics mode"""
        # Parse arguments: PMODE mode[,page]
        parts = _split_args(args)
        mode = self._eval_int(parts[0])
        page = 1

        if len(parts) > 1:
            page = self._eval_int(parts[1])

        if mode < 0 or mode > 4:
            return self._illegal_function_call()

        self.emulator.graphics_mode = mode

        return [{'type': 'pmode', 'mode': mode, 'page': page}]
    
    @_graphics_command('SCREEN')
    def execute_screen(self, args):
        """Execute SCREEN command to set screen/color mode"""
        # Parse SCREEN mode[,page] parameters
        if ',' in args:
            parts = _split_args(args)
            mode = self._eval_int(parts[0])
            page = self._eval_int(parts[1])
        else:
            mode = self._eval_int(args)
            page = 1  # Default page

        if mode < 1 or mode > 2:
            return self._illegal_function_call()

        self.emulator.screen_mode = mode

        return [{'type': 'set_screen', 'mode': mode, 'page': page}]
    
    @_graphics_command('COLOR')
    def execute_color(self, args):
        """Execute COLOR command to set foreground/background colors"""
        if ',' in args:
            parts = _split_args(args)
            fg = self._eval_int(parts[0]) if parts[0] else None
            bg = self._eval_int(parts[1]) if len(parts) > 1 and parts[1] else None
        else:
            fg = self._eval_int(args)
            bg = None

        return [{'type': 'set_color', 'fg': fg, 'bg': bg}]
    
    @_graphics_command('PSET')
    def execute_pset(self, args):
        """Execute PSET command to set a pixel"""
        err = self._require_graphics_mode()
        if err:
            return err

        if args.startswith('(') and ')' in args:
            result = self._parse_coord_pair(args, 'PSET')
            if isinstance(result, list):
                return result
            x, y, remainder = result
            color = None
            if remainder.startswith(','):
                color_str = remainder[1:].strip()
                if color_str:
                    color = self._eval_int(color_str)
            return [{'type': 'pset', 'x': x, 'y': y, 'color': color}]
        else:
            parts = _split_args(args)
            if len(parts) < 2:
                return self._syntax_error("PSET requires X and Y coordinates",
                    ['Correct syntax: PSET x,y or PSET x,y,color',
                     'Example: PSET 100,50',
                     'Specify both X and Y coordinates'])
            x = self._eval_int(parts[0])
            y = self._eval_int(parts[1])
            color = None
            if len(parts) > 2 and parts[2].strip():
                color = self._eval_int(parts[2])
            return [{'type': 'pset', 'x': x, 'y': y, 'color': color}]
    
    @_graphics_command('PRESET')
    def execute_preset(self, args):
        """Execute PRESET command to reset a pixel to background color"""
        err = self._require_graphics_mode()
        if err:
            return err

        if args.startswith('(') and ')' in args:
            result = self._parse_coord_pair(args, 'PRESET')
            if isinstance(result, list):
                return result
            x, y, _ = result
            return [{'type': 'preset', 'x': x, 'y': y}]
        else:
            parts = _split_args(args)
            if len(parts) != 2:
                return self._syntax_error("PRESET requires exactly two coordinates",
                    ['Correct syntax: PRESET x,y', 'Example: PRESET 100,50',
                     'Specify both X and Y coordinates'])
            x = self._eval_int(parts[0])
            y = self._eval_int(parts[1])
            return [{'type': 'preset', 'x': x, 'y': y}]
    
    @_graphics_command('LINE')
    def execute_line_graphics(self, args):
        """Execute LINE command to draw a line"""
        err = self._require_graphics_mode()
        if err:
            return err

        # Parse LINE (x1,y1)-(x2,y2)[,PSET|PRESET|color][,B|BF]
        # or LINE x1,y1,x2,y2[,color]
        if CommandRegistry.is_coordinate_pair_syntax(args):
            # Extract coordinate spec and trailing parameters
            last_paren = args.rfind(')')
            coord_spec = args[:last_paren + 1]
            trailing = args[last_paren + 1:].strip().lstrip(',')
            parts = [p.strip().upper() for p in trailing.split(',') if p.strip()]

            mode = 'PSET'
            color = None
            box_type = None

            for part in parts:
                if part in ('PSET', 'PRESET'):
                    mode = part
                elif part in ('B', 'BF'):
                    box_type = part
                elif part:
                    color = self._eval_int(part)

            start_coords, end_coords = CommandRegistry.parse_line_coordinates(coord_spec)

            x1 = self._eval_int(start_coords[0].strip())
            y1 = self._eval_int(start_coords[1].strip())
            x2 = self._eval_int(end_coords[0].strip())
            y2 = self._eval_int(end_coords[1].strip())

            return [{'type': 'line', 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                     'color': color, 'mode': mode, 'box_type': box_type}]
        else:
            # Space-separated syntax: LINE x1,y1,x2,y2[,color]
            parts = _split_args(args)
            if len(parts) < 4:
                return self._syntax_error("LINE requires four coordinates", ['Correct syntax: LINE x1,y1,x2,y2 or LINE(x1,y1)-(x2,y2)',
                        'Example: LINE 10,10,100,100',
                        'Specify start and end coordinates'])

            x1 = self._eval_int(parts[0].strip())
            y1 = self._eval_int(parts[1].strip())
            x2 = self._eval_int(parts[2].strip())
            y2 = self._eval_int(parts[3].strip())

            color = None
            if len(parts) > 4 and parts[4].strip():
                color = self._eval_int(parts[4].strip())

            return [{'type': 'line', 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'color': color}]
    
    @_graphics_command('CIRCLE')
    def execute_circle(self, args):
        """Execute CIRCLE command to draw a circle"""
        err = self._require_graphics_mode()
        if err:
            return err

        # Parse CIRCLE (x,y),radius[,color] or CIRCLE x,y,radius[,color]
        if args.startswith('(') and ')' in args:
            result = self._parse_coord_pair(args, 'CIRCLE')
            if isinstance(result, list):
                return result
            x, y, remainder = result

            if remainder.startswith(','):
                remainder = remainder[1:].strip()
            parts = _split_args(remainder)
            radius = self._eval_int(parts[0])

            color = None
            if len(parts) > 1 and parts[1]:
                color = self._eval_int(parts[1])

            return [{'type': 'circle', 'x': x, 'y': y, 'radius': radius, 'color': color}]
        else:
            # Space-separated syntax: CIRCLE x,y,radius[,color]
            parts = _split_args(args)
            if len(parts) < 3:
                return self._syntax_error("CIRCLE requires center coordinates and radius", ['Correct syntax: CIRCLE x,y,radius or CIRCLE x,y,radius,color',
                        'Example: CIRCLE 100,50,25',
                        'Specify center X, Y coordinates and radius'])

            x = self._eval_int(parts[0].strip())
            y = self._eval_int(parts[1].strip())
            radius = self._eval_int(parts[2].strip())

            color = None
            if len(parts) > 3 and parts[3].strip():
                color = self._eval_int(parts[3].strip())

            return [{'type': 'circle', 'x': x, 'y': y, 'radius': radius, 'color': color}]
    
    @_graphics_command('PAINT')
    def execute_paint(self, args):
        """Execute PAINT command for flood fill"""
        err = self._require_graphics_mode()
        if err:
            return err

        if args.startswith('(') and ')' in args:
            result = self._parse_coord_pair(args, 'PAINT')
            if isinstance(result, list):
                return result
            x, y, remainder = result

            paint_color = 1  # Default paint color
            border_color = None

            if remainder.startswith(','):
                parts = _split_args(remainder[1:])
                if parts[0]:
                    paint_color = self._eval_int(parts[0])
                if len(parts) > 1 and parts[1]:
                    border_color = self._eval_int(parts[1])
            elif remainder == '':
                return self._syntax_error("PAINT requires color parameter",
                    ['Correct syntax: PAINT(x,y),color',
                     'Example: PAINT(100,50),1',
                     'Specify the fill color after coordinates'])

            return [{'type': 'paint', 'x': x, 'y': y, 'fill_color': paint_color, 'boundary_color': border_color}]
        else:
            return self._syntax_error("Invalid PAINT syntax",
                ['Correct syntax: PAINT(x,y),color or PAINT(x,y),color,boundary',
                 'Example: PAINT(100,50),1',
                 'Coordinates must be enclosed in parentheses'])
    
    @_graphics_command('GET')
    def execute_get(self, args):
        """Execute GET command to capture graphics area"""
        err = self._require_graphics_mode()
        if err:
            return err

        # Parse GET (x1,y1)-(x2,y2), array_name
        if '-(' in args and ',' in args:
            coords_part, array_name = args.rsplit(',', 1)
            array_name = array_name.strip()

            start_coords, end_coords = coords_part.split('-(', 1)
            if start_coords.startswith('('):
                start_coords = start_coords[1:]

            end_coords = end_coords.rstrip(')')

            x1_str, y1_str = start_coords.split(',')
            x2_str, y2_str = end_coords.split(',')

            x1 = self._eval_int(x1_str.strip())
            y1 = self._eval_int(y1_str.strip())
            x2 = self._eval_int(x2_str.strip())
            y2 = self._eval_int(y2_str.strip())

            return [{'type': 'get', 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'array': array_name}]
        else:
            return self._syntax_error("Invalid GET syntax", ['Correct syntax: GET(x1,y1)-(x2,y2),array_name',
                    'Example: GET(0,0)-(50,50),A',
                    'Specify rectangular area and target array'])
    
    @_graphics_command('PUT')
    def execute_put(self, args):
        """Execute PUT command to display stored graphics"""
        err = self._require_graphics_mode()
        if err:
            return err

        # Parse PUT (x,y), array_name [,action]
        if args.strip().startswith('('):
            result = self._parse_coord_pair(args, 'PUT')
            if isinstance(result, list):
                return result
            x, y, remainder = result

            if remainder.startswith(','):
                parts = _split_args(remainder[1:])
            else:
                return self._syntax_error("Invalid PUT syntax", ['Correct syntax: PUT(x,y),array_name',
                        'Example: PUT(100,50),A',
                        'Specify array name after coordinates'])

            array_name = parts[0].strip()
            action = 'PSET'  # Default action
            if len(parts) > 1 and parts[1]:
                action = parts[1].strip().upper()

            return [{'type': 'put', 'x': x, 'y': y, 'array': array_name, 'action': action}]
        else:
            return self._syntax_error("Invalid PUT syntax", ['Correct syntax: PUT(x,y),array_name or PUT(x,y),array_name,action',
                    'Example: PUT(100,50),A,PSET',
                    'Specify coordinates, array name, and optional action'])
    
    @_graphics_command('DRAW')
    def execute_draw(self, args):
        """Execute DRAW command for turtle graphics"""
        err = self._require_graphics_mode()
        if err:
            return err

        draw_string = self.emulator.evaluate_expression(args)
        if not isinstance(draw_string, str):
            return self._syntax_error('DRAW requires string argument',
                                      ['DRAW takes a string of drawing commands',
                                       'Example: DRAW "U10R10D10L10"'])

        commands = BasicParser.parse_draw_commands(draw_string)

        output = []
        for command in commands:
            result = self._execute_draw_command(command)
            if result:
                output.extend(result)

        return output
    
    def _execute_draw_command(self, command):
        """Execute a single DRAW command"""
        cmd_type = command.get('command', '')
        
        if cmd_type in ['U', 'D', 'L', 'R', 'E', 'F', 'G', 'H']:
            # Movement commands
            distance = command.get('distance', 1)
            
            old_x, old_y = self.emulator.turtle_x, self.emulator.turtle_y
            
            # Calculate new position
            if cmd_type == 'U':
                self.emulator.turtle_y -= distance
            elif cmd_type == 'D':
                self.emulator.turtle_y += distance
            elif cmd_type == 'L':
                self.emulator.turtle_x -= distance
            elif cmd_type == 'R':
                self.emulator.turtle_x += distance
            elif cmd_type == 'E':  # Up-Right diagonal
                self.emulator.turtle_x += distance
                self.emulator.turtle_y -= distance
            elif cmd_type == 'F':  # Down-Right diagonal
                self.emulator.turtle_x += distance
                self.emulator.turtle_y += distance
            elif cmd_type == 'G':  # Down-Left diagonal
                self.emulator.turtle_x -= distance
                self.emulator.turtle_y += distance
            elif cmd_type == 'H':  # Up-Left diagonal
                self.emulator.turtle_x -= distance
                self.emulator.turtle_y -= distance
            
            # Draw line from old position to new position
            return [{'type': 'line', 'x1': old_x, 'y1': old_y, 
                    'x2': self.emulator.turtle_x, 'y2': self.emulator.turtle_y, 
                    'color': self.emulator.current_draw_color}]
        
        elif cmd_type == 'M':
            # Move to position
            x = command.get('x', self.emulator.turtle_x)
            y = command.get('y', self.emulator.turtle_y)
            relative = command.get('relative', False)
            
            if relative:
                self.emulator.turtle_x += x
                self.emulator.turtle_y += y
            else:
                self.emulator.turtle_x = x
                self.emulator.turtle_y = y
        
        elif cmd_type == 'C':
            # Set color
            color = command.get('color', 1)
            self.emulator.current_draw_color = color
        
        return []