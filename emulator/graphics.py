"""
Graphics module for TRS-80 Color Computer BASIC Emulator

Graphics commands: PMODE, SCREEN, PSET, PRESET, LINE, CIRCLE, PAINT,
GET, PUT, DRAW, COLOR, PCLEAR, PCLS, and GPRINT.
"""

from .text_utils import StatementSplitter
from .error_context import error_response
from .ast_nodes import format_basic_number

_split_args = StatementSplitter.split_args  # Shared comma-split helper

# How PUT combines the stored block with the screen
_PUT_ACTIONS = frozenset({'PSET', 'PRESET', 'AND', 'OR', 'NOT'})


def _graphics_command(command_name, require_graphics=False):
    """Decorator that wraps a graphics method with standard error handling."""
    def decorator(method):
        def wrapper(self, args):
            if require_graphics:
                err = self._require_graphics_mode()
                if err:
                    return err
            try:
                return method(self, args)
            except Exception as e:
                err = self.emulator.error_context.wrapped_error(
                    f"Error in {command_name}: ", e,
                    self.emulator.current_line,
                    suggestions=[f'Type HELP {command_name} for the syntax',
                                 'Coordinates, colors and modes must be numbers'])
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
        self.pixel_buffer = {}  # Sparse dict: (x, y) -> color
        self.clear_color = 0  # Color of undrawn pixels (set by PCLS c)
        self.last_line_end = (0, 0)  # Start point for LINE -(x,y)
    
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
        registry.register('PCLS', self.execute_pcls)
        registry.register('PCLEAR', self.execute_pclear)
        registry.register('GPRINT', self.execute_gprint)
    
    def _syntax_error(self, message, suggestions):
        """Create a standardized syntax error response list."""
        error = self.emulator.error_context.syntax_error(
            message, self.emulator.current_line, suggestions=suggestions)
        return error_response(error)

    def _illegal_function_call(self, detail=None, suggestions=None):
        """Return an ILLEGAL FUNCTION CALL error response."""
        message = f"ILLEGAL FUNCTION CALL: {detail}" if detail else "ILLEGAL FUNCTION CALL"
        error = self.emulator.error_context.runtime_error(
            message, self.emulator.current_line,
            suggestions=suggestions or ['Check the argument ranges with HELP <command>',
                                        'Graphics commands need PMODE and SCREEN 1,1 first'])
        return error_response(error)

    def _require_graphics_mode(self):
        """Return error response if not in graphics mode, else None."""
        if self.emulator.graphics_mode == 0:
            return self._illegal_function_call()
        return None

    def execute_pclear(self, args):
        """Execute PCLEAR command - allocate graphics pages (no-op in emulator)"""
        args = args.strip()
        if not args:
            return self._syntax_error(
                "PCLEAR requires a number of pages",
                suggestions=["Correct syntax: PCLEAR n (where n is 1-8)",
                             "Example: PCLEAR 4"])
        try:
            pages = self.emulator.eval_int(args)
        except (ValueError, TypeError):
            return self._syntax_error(
                "PCLEAR requires a numeric argument",
                suggestions=["Correct syntax: PCLEAR n (where n is 1-8)",
                             "Example: PCLEAR 4"])
        if pages < 1 or pages > 8:
            error = self.emulator.error_context.runtime_error(
                f"PCLEAR pages must be 1-8, got {pages}",
                self.emulator.current_line,
                suggestions=["PCLEAR n allocates n graphics pages (1-8)",
                             "Example: PCLEAR 4"])
            return error_response(error)
        return self.emulator._system_ok()

    def execute_pcls(self, args):
        """PCLS [color] - clear the graphics screen (to color, if given)"""
        color = self.emulator.eval_int(args) if args.strip() else None
        self.pixel_buffer.clear()
        self.clear_color = color if color is not None else 0
        return [{'type': 'pcls', 'color': color}]

    # ── Pixel tracking (for PPOINT) ──────────────────────────────────
    # The client renders; the server keeps a sparse copy of what was drawn
    # so PPOINT can answer. Coordinates are clipped to the 256x192 screen.
    SCREEN_WIDTH, SCREEN_HEIGHT = 256, 192
    _TRACK_LIMIT = 4096  # lines/circles beyond this are not pixel-tracked

    def get_pixel(self, x, y):
        """Return color at (x, y): what was drawn there, else the clear color."""
        return self.pixel_buffer.get((x, y), self.clear_color)

    def clear_pixel_buffer(self):
        """Clear the pixel buffer."""
        self.pixel_buffer.clear()
        self.clear_color = 0

    def _plot(self, x, y, color):
        if 0 <= x < self.SCREEN_WIDTH and 0 <= y < self.SCREEN_HEIGHT:
            self.pixel_buffer[(x, y)] = color

    def _record_line(self, x1, y1, x2, y2, color):
        """Record a line's pixels (Bresenham, as the client draws it)."""
        if max(abs(x1), abs(y1), abs(x2), abs(y2)) > self._TRACK_LIMIT:
            return  # far off-screen: not worth (or safe) to walk pixel by pixel
        dx, dy = abs(x2 - x1), -abs(y2 - y1)
        sx, sy = (1 if x1 < x2 else -1), (1 if y1 < y2 else -1)
        err = dx + dy
        for _ in range(self.SCREEN_WIDTH + self.SCREEN_HEIGHT + dx - dy):
            self._plot(x1, y1, color)
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x1 += sx
            if e2 <= dx:
                err += dx
                y1 += sy

    def _record_box(self, x1, y1, x2, y2, color, filled):
        if filled:
            for y in range(max(0, min(y1, y2)), min(self.SCREEN_HEIGHT, max(y1, y2) + 1)):
                self._record_line(x1, y, x2, y, color)
        else:
            for a, b, c, d in ((x1, y1, x2, y1), (x2, y1, x2, y2), (x2, y2, x1, y2), (x1, y2, x1, y1)):
                self._record_line(a, b, c, d, color)

    def _record_circle(self, cx, cy, radius, color):
        """Record a circle outline (midpoint algorithm)."""
        if max(abs(cx), abs(cy), abs(radius)) > self._TRACK_LIMIT:
            return
        x, y, err = radius, 0, 1 - radius
        while x >= y:
            for px, py in ((x, y), (y, x), (-y, x), (-x, y), (-x, -y), (-y, -x), (y, -x), (x, -y)):
                self._plot(cx + px, cy + py, color)
            y += 1
            if err < 0:
                err += 2 * y + 1
            else:
                x -= 1
                err += 2 * (y - x) + 1

    def _parse_coord_pair(self, args, command_name):
        """Parse (x,y) from args. Returns (x, y, remainder_after_paren) or error list."""
        args = args.strip()
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
        x = self.emulator.eval_int(coord_parts[0])
        y = self.emulator.eval_int(coord_parts[1])
        remainder = args[coords_end + 1:].strip()
        return (x, y, remainder)

    def _parse_point(self, args, command_name):
        """Parse (x,y) or x,y coordinates with optional trailing args.
        Returns (x, y, extra_parts) or error list.
        extra_parts is a list of comma-separated strings after the coordinates."""
        if args.startswith('(') and ')' in args:
            result = self._parse_coord_pair(args, command_name)
            if isinstance(result, list):
                return result
            x, y, remainder = result
            extra_parts = []
            if remainder.startswith(','):
                extra_parts = _split_args(remainder[1:])
            return (x, y, extra_parts)
        else:
            parts = _split_args(args)
            if len(parts) < 2:
                return self._syntax_error(
                    f"{command_name} requires X and Y coordinates",
                    [f'Correct syntax: {command_name}(x,y) or {command_name} x,y',
                     f'Example: {command_name}(100,50)',
                     'Specify both X and Y coordinates'])
            x = self.emulator.eval_int(parts[0])
            y = self.emulator.eval_int(parts[1])
            return (x, y, parts[2:])

    def _parse_coord_range(self, args, command_name):
        """Parse (x1,y1)-(x2,y2) or -(x2,y2) plus trailing ,args.

        Coordinates are matched by parenthesis depth (so C(1), MAX(1,2) or
        P(1)-(2) inside a coordinate are fine). ``-(x2,y2)`` starts at the
        end of the previous LINE. Returns (x1, y1, x2, y2, extra_parts) or an
        error response list.
        """
        args = args.strip()
        if args.startswith('-'):
            x1, y1 = self.last_line_end
            rest = args[1:].strip()
        else:
            first = self._parse_coord_pair(args, command_name)
            if isinstance(first, list):
                return first
            x1, y1, rest = first
            if not rest.startswith('-'):
                return self._syntax_error(
                    f"{command_name} requires (x1,y1)-(x2,y2)",
                    [f'Correct syntax: {command_name}(x1,y1)-(x2,y2)',
                     f'Example: {command_name}(0,0)-(50,50)',
                     'Put a dash between the two coordinate pairs'])
            rest = rest[1:].strip()
        second = self._parse_coord_pair(rest, command_name)
        if isinstance(second, list):
            return second
        x2, y2, remainder = second
        extra = _split_args(remainder[1:]) if remainder.startswith(',') else []
        if remainder and not remainder.startswith(','):
            return self._syntax_error(
                f"Unexpected text after {command_name} coordinates: {remainder}",
                [f'Example: {command_name}(0,0)-(50,50),PSET',
                 'Separate options with commas',
                 'Check for a missing comma'])
        return x1, y1, x2, y2, extra

    def _parse_optional_int(self, parts, index):
        """Parse an optional integer from parts[index]. Returns int or None."""
        if len(parts) > index and parts[index].strip():
            return self.emulator.eval_int(parts[index])
        return None

    def _find_matching_parenthesis(self, text, start):
        """Find the matching closing parenthesis for the opening one at start
        (parentheses inside quoted strings don't count)."""
        if start >= len(text) or text[start] != '(':
            return -1

        paren_count = 0
        in_quotes = False
        for i in range(start, len(text)):
            if text[i] == '"':
                in_quotes = not in_quotes
            elif in_quotes:
                continue
            elif text[i] == '(':
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
        mode = self.emulator.eval_int(parts[0])
        page = 1

        if len(parts) > 1:
            page = self.emulator.eval_int(parts[1])

        if mode < 0 or mode > 4:
            return self._illegal_function_call(
                f"PMODE mode {mode} is outside 0-4",
                ['PMODE 4,1 is 256x192, two colors', 'PMODE 3,1 is 128x192, four colors'])
        if page < 1 or page > 8:
            return self._illegal_function_call(
                f"PMODE start page {page} is outside 1-8",
                ['Use PMODE mode,1 unless you are page-flipping', 'Example: PMODE 4,1'])

        self.emulator.graphics_mode = mode

        return [{'type': 'pmode', 'mode': mode, 'page': page}]
    
    @_graphics_command('SCREEN')
    def execute_screen(self, args):
        """Execute SCREEN command to set screen/color mode"""
        # Parse SCREEN mode[,page] parameters (commas inside an argument
        # expression, e.g. SCREEN X(1,1), don't separate arguments)
        parts = _split_args(args)
        if not parts or len(parts) > 2:
            return self._syntax_error("SCREEN takes a mode and an optional color set",
                                      ['Correct syntax: SCREEN mode[,colorset]',
                                       'Example: SCREEN 1,0',
                                       'Mode 1 is graphics; mode 0 is text'])
        mode = self.emulator.eval_int(parts[0])
        # Color set: as on the CoCo, any nonzero value selects set 1
        page = (1 if self.emulator.eval_int(parts[1]) else 0) if len(parts) > 1 else 1

        if mode < 1 or mode > 2:
            return self._illegal_function_call(
                f"SCREEN mode {mode} is not supported",
                ['SCREEN 1,1 shows the graphics screen', 'SCREEN 1,0 selects the other color set'])

        self.emulator.screen_mode = mode

        return [{'type': 'set_screen', 'mode': mode, 'page': page}]
    
    @_graphics_command('COLOR')
    def execute_color(self, args):
        """Execute COLOR command to set foreground/background colors"""
        parts = _split_args(args, keep_empty=True)
        fg = self.emulator.eval_int(parts[0]) if parts and parts[0] else None
        bg = self.emulator.eval_int(parts[1]) if len(parts) > 1 and parts[1] else None
        for value in (fg, bg):
            if value is not None and not 0 <= value <= 8:
                return self._illegal_function_call(
                    f"color {value} is outside 0-8",
                    ['Colors are 0-8: 0 black, 1 green, 2 yellow, 3 blue, 4 red, ...',
                     'Example: COLOR 4,0'])

        return [{'type': 'set_color', 'fg': fg, 'bg': bg}]
    
    @_graphics_command('PSET', require_graphics=True)
    def execute_pset(self, args):
        """Execute PSET command to set a pixel"""
        result = self._parse_point(args, 'PSET')
        if isinstance(result, list):
            return result
        x, y, extra = result
        color = self._parse_optional_int(extra, 0)
        effective_color = color if color is not None else self.emulator.current_draw_color
        self._plot(x, y, effective_color)
        return [{'type': 'pset', 'x': x, 'y': y, 'color': color}]
    
    @_graphics_command('PRESET', require_graphics=True)
    def execute_preset(self, args):
        """Execute PRESET command to reset a pixel to background color"""
        result = self._parse_point(args, 'PRESET')
        if isinstance(result, list):
            return result
        x, y, _ = result
        self._plot(x, y, self.clear_color)
        return [{'type': 'preset', 'x': x, 'y': y}]
    
    @_graphics_command('LINE', require_graphics=True)
    def execute_line_graphics(self, args):
        """Execute LINE command to draw a line"""

        # Parse LINE (x1,y1)-(x2,y2)[,PSET|PRESET|color][,B|BF],
        # LINE -(x2,y2)[,...] (from the previous LINE's end point),
        # or LINE x1,y1,x2,y2[,color]
        if args.lstrip().startswith(('(', '-')):
            result = self._parse_coord_range(args, 'LINE')
            if isinstance(result, list):
                return result
            x1, y1, x2, y2, parts = result

            mode = 'PSET'
            color = None
            box_type = None

            for part in parts:
                keyword = part.strip().upper()
                if keyword in ('PSET', 'PRESET'):
                    mode = keyword
                elif keyword in ('B', 'BF'):
                    box_type = keyword
                elif keyword:
                    color = self.emulator.eval_int(part)

            self.last_line_end = (x2, y2)
            if mode == 'PRESET':
                pixel_color = self.clear_color
            else:
                pixel_color = color if color is not None else self.emulator.current_draw_color
            if box_type:
                self._record_box(x1, y1, x2, y2, pixel_color, filled=box_type == 'BF')
            else:
                self._record_line(x1, y1, x2, y2, pixel_color)
            return [{'type': 'line', 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                     'color': color, 'mode': mode, 'box_type': box_type}]
        else:
            # Space-separated syntax: LINE x1,y1,x2,y2[,color]
            parts = _split_args(args)
            if len(parts) < 4:
                return self._syntax_error("LINE requires four coordinates", ['Correct syntax: LINE x1,y1,x2,y2 or LINE(x1,y1)-(x2,y2)',
                        'Example: LINE 10,10,100,100',
                        'Specify start and end coordinates'])

            x1 = self.emulator.eval_int(parts[0].strip())
            y1 = self.emulator.eval_int(parts[1].strip())
            x2 = self.emulator.eval_int(parts[2].strip())
            y2 = self.emulator.eval_int(parts[3].strip())

            color = None
            if len(parts) > 4 and parts[4].strip():
                color = self.emulator.eval_int(parts[4].strip())

            return [{'type': 'line', 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'color': color}]
    
    @_graphics_command('CIRCLE', require_graphics=True)
    def execute_circle(self, args):
        """Execute CIRCLE command to draw a circle"""
        # Parse CIRCLE (x,y),radius[,color] or CIRCLE x,y,radius[,color]
        result = self._parse_point(args, 'CIRCLE')
        if isinstance(result, list):
            return result
        x, y, extra = result
        if not extra:
            return self._syntax_error("CIRCLE requires radius",
                ['Correct syntax: CIRCLE(x,y),radius or CIRCLE x,y,radius',
                 'Example: CIRCLE 100,50,25'])
        radius = self.emulator.eval_int(extra[0])
        color = self._parse_optional_int(extra, 1)
        self._record_circle(x, y, radius,
                            color if color is not None else self.emulator.current_draw_color)
        return [{'type': 'circle', 'x': x, 'y': y, 'radius': radius, 'color': color}]
    
    @_graphics_command('PAINT', require_graphics=True)
    def execute_paint(self, args):
        """Execute PAINT command for flood fill"""
        if not (args.startswith('(') and ')' in args):
            return self._syntax_error("Invalid PAINT syntax",
                ['Correct syntax: PAINT(x,y),color or PAINT(x,y),color,boundary',
                 'Example: PAINT(100,50),1',
                 'Coordinates must be enclosed in parentheses'])

        result = self._parse_coord_pair(args, 'PAINT')
        if isinstance(result, list):
            return result
        x, y, remainder = result

        if not remainder.startswith(','):
            return self._syntax_error("PAINT requires color parameter",
                ['Correct syntax: PAINT(x,y),color',
                 'Example: PAINT(100,50),1',
                 'Specify the fill color after coordinates'])

        parts = _split_args(remainder[1:])
        if not parts or not parts[0]:
            return self._syntax_error("PAINT requires color parameter",
                ['Correct syntax: PAINT(x,y),color',
                 'Example: PAINT(100,50),1',
                 'Specify the fill color after coordinates'])

        paint_color = self.emulator.eval_int(parts[0])
        border_color = self._parse_optional_int(parts, 1)
        return [{'type': 'paint', 'x': x, 'y': y, 'fill_color': paint_color, 'boundary_color': border_color}]
    
    @_graphics_command('GPRINT', require_graphics=True)
    def execute_gprint(self, args):
        """Execute GPRINT command to draw text on graphics screen.
        Syntax: GPRINT(x,y),"text"[,color]
        """
        result = self._parse_coord_pair(args, 'GPRINT')
        if isinstance(result, list):
            return result
        x, y, remainder = result

        if not remainder.startswith(','):
            return self._syntax_error("GPRINT requires text after coordinates",
                ['Correct syntax: GPRINT(x,y),"text"',
                 'Example: GPRINT(10,5),"HELLO"',
                 'Optional color: GPRINT(10,5),"HELLO",3'])

        parts = _split_args(remainder[1:])
        if not parts or not parts[0]:
            return self._syntax_error("GPRINT requires text string",
                ['Correct syntax: GPRINT(x,y),"text"',
                 'Example: GPRINT(10,5),"HELLO"'])

        text = self.emulator.evaluate_expression(parts[0])
        if not isinstance(text, str):
            text = format_basic_number(text)
        text = text.upper()  # the GPRINT font, like the CoCo's, has no lowercase

        color = self._parse_optional_int(parts, 1)
        if color is None:
            color = 1  # Default to green (OC)

        return [{'type': 'gtext', 'x': x, 'y': y, 'text': text, 'color': color}]

    @_graphics_command('GET', require_graphics=True)
    def execute_get(self, args):
        """Execute GET command to capture graphics area"""

        # Parse GET (x1,y1)-(x2,y2), array_name [,G]
        result = self._parse_coord_range(args, 'GET') if args.lstrip().startswith('(') else None
        if result is None or isinstance(result, list) or not result[4]:
            return result if isinstance(result, list) else self._syntax_error(
                "Invalid GET syntax",
                ['Correct syntax: GET(x1,y1)-(x2,y2),array_name',
                 'Example: GET(0,0)-(50,50),A',
                 'Specify rectangular area and target array'])
        x1, y1, x2, y2, extra = result
        return [{'type': 'get', 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                 'array': extra[0].strip().upper()}]
    
    @_graphics_command('PUT', require_graphics=True)
    def execute_put(self, args):
        """Execute PUT command to display stored graphics"""

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
            if action not in _PUT_ACTIONS:
                return self._syntax_error(f"Unknown PUT action: {action}",
                    ['PUT actions are PSET, PRESET, AND, OR and NOT',
                     'Example: PUT(100,50),A,PSET'])

            return [{'type': 'put', 'x': x, 'y': y, 'array': array_name, 'action': action}]
        else:
            return self._syntax_error("Invalid PUT syntax", ['Correct syntax: PUT(x,y),array_name or PUT(x,y),array_name,action',
                    'Example: PUT(100,50),A,PSET',
                    'Specify coordinates, array name, and optional action'])
    
    # Direction deltas for DRAW movement commands (dx, dy) in screen coords
    _DRAW_DELTAS = {
        'U': (0, -1), 'D': (0, 1), 'L': (-1, 0), 'R': (1, 0),
        'E': (1, -1), 'F': (1, 1), 'G': (-1, 1), 'H': (-1, -1),
    }

    @_graphics_command('DRAW', require_graphics=True)
    def execute_draw(self, args):
        """Execute DRAW command for turtle graphics"""

        draw_string = self.emulator.evaluate_expression(args)
        if not isinstance(draw_string, str):
            return self._syntax_error('DRAW requires string argument',
                                      ['DRAW takes a string of drawing commands',
                                       'Example: DRAW "U10R10D10L10"'])

        commands = StatementSplitter.parse_draw_commands(draw_string)
        return self._execute_draw_commands(commands)

    def _execute_draw_commands(self, commands, state=None):
        """Execute a list of parsed DRAW commands with shared state."""
        if state is None:
            state = {'blank': False, 'no_update': False, 'scale': 4, 'angle': 0}

        output = []

        for command in commands:
            cmd = command.get('command', '')

            if cmd == 'B':
                state['blank'] = True
                continue
            elif cmd == 'N':
                state['no_update'] = True
                continue
            elif cmd == 'S':
                state['scale'] = command.get('scale', 4)
                continue
            elif cmd == 'C':
                self.emulator.current_draw_color = command.get('color', 1)
                continue
            elif cmd == 'A':
                state['angle'] = command.get('angle', 0) % 4
                continue
            elif cmd == 'X':
                var_name = command.get('variable', '')
                if var_name in self.emulator.variables:
                    sub_string = self.emulator.variables[var_name]
                    if isinstance(sub_string, str):
                        sub_commands = StatementSplitter.parse_draw_commands(sub_string)
                        output.extend(self._execute_draw_commands(sub_commands, state))
                continue

            # Movement command — save position, apply scale and angle, execute
            saved_x = self.emulator.turtle_x
            saved_y = self.emulator.turtle_y
            result = self._execute_move_command(command, state['scale'], state['angle'])

            if state['blank']:
                state['blank'] = False
                # Turtle moved but don't emit draw output
                continue
            for segment in result:
                self._record_line(segment['x1'], segment['y1'], segment['x2'], segment['y2'],
                                  segment['color'])
            output.extend(result)
            if state['no_update']:
                state['no_update'] = False
                # Restore turtle to pre-move position
                self.emulator.turtle_x = saved_x
                self.emulator.turtle_y = saved_y

        return output

    @staticmethod
    def _rotate_delta(dx, dy, angle):
        """Apply angle rotation (0-3) to a direction delta.

        Each unit rotates 90° CCW in screen coordinates (Y-down):
          A0: (dx, dy), A1: (dy, -dx), A2: (-dx, -dy), A3: (-dy, dx)
        """
        for _ in range(angle % 4):
            dx, dy = dy, -dx
        return dx, dy

    def _execute_move_command(self, command, scale, angle=0):
        """Execute a movement DRAW command with scale and angle applied."""
        cmd_type = command.get('command', '')

        if cmd_type in self._DRAW_DELTAS:
            distance = command.get('distance', 1) * scale // 4
            base_dx, base_dy = self._DRAW_DELTAS[cmd_type]
            dx, dy = self._rotate_delta(base_dx * distance, base_dy * distance, angle)

            old_x, old_y = self.emulator.turtle_x, self.emulator.turtle_y
            self.emulator.turtle_x += dx
            self.emulator.turtle_y += dy
            return self._draw_segment(old_x, old_y)

        elif cmd_type == 'M':
            x = command.get('x', self.emulator.turtle_x)
            y = command.get('y', self.emulator.turtle_y)
            relative = command.get('relative', False)

            old_x, old_y = self.emulator.turtle_x, self.emulator.turtle_y
            if relative:
                dx, dy = self._rotate_delta(x * scale // 4, y * scale // 4, angle)
                self.emulator.turtle_x += dx
                self.emulator.turtle_y += dy
            else:
                self.emulator.turtle_x = x
                self.emulator.turtle_y = y
            # M draws a line like the other moves (BM moves without drawing;
            # the caller drops the output for a B-prefixed command)
            return self._draw_segment(old_x, old_y)

        return []

    def _draw_segment(self, old_x, old_y):
        """Line from (old_x, old_y) to the turtle's position, as DRAW output."""
        new_x, new_y = self.emulator.turtle_x, self.emulator.turtle_y
        color = self.emulator.current_draw_color
        return [{'type': 'line', 'x1': old_x, 'y1': old_y, 'x2': new_x, 'y2': new_y,
                 'color': color}]