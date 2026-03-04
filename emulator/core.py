"""
BasiCoCo - Educational Color Computer BASIC Environment

This module contains the main CoCoBasic class that implements the BASIC interpreter.
The class has been extracted from the monolithic app.py file to improve maintainability.
"""

import random
import re
import time
from .parser import BasicParser
from .graphics import BasicGraphics
from .variables import VariableManager
from .commands import CommandRegistry
from .expressions import FunctionRegistry
from .functions import register_all_functions
from .ast_nodes import basic_truthy
from .ast_parser import ASTParser
from .ast_evaluator import ASTEvaluator
from .output_manager import StreamingOutputManager, LegacyOutputAdapter
from .error_context import ErrorContextManager, error_response, text_response
from .file_manager import FileManager
from .file_io import FileIOManager
from .program_executor import ProgramExecutor

class CoCoBasic:
    def __init__(self, output_callback=None, debug_mode=False):
        self.program = {}  # Line number -> code (original for LIST display)
        self.expanded_program = {}  # (line_num, sub_index) -> str or ASTNode (for execution)
        self.variables = {}
        self.data_statements = []
        self.data_pointer = 0
        self.running = False
        
        # Initialize enhanced output management system
        self.output_manager = StreamingOutputManager(debug_mode=debug_mode)
        self.legacy_adapter = LegacyOutputAdapter(self.output_manager)
        
        # Set up legacy compatibility
        if output_callback:
            self.legacy_adapter.set_output_callback(output_callback)
        
        # Legacy property for backward compatibility
        self.output_callback = output_callback
        self.current_line = 0
        
        # Initialize error context manager for enhanced error messages
        self.error_context = ErrorContextManager()
        self.current_sub_line = 0
        self.call_stack = []
        self.for_stack = []
        self.if_stack = []
        self.while_stack = []
        self.do_stack = []
        self.graphics_mode = 0  # 0 = text mode, 1-4 = PMODE graphics
        self.screen_mode = 1    # Screen/color mode
        self.iteration_count = 0  # Safety counter for infinite loops
        self.max_iterations = 50000  # Maximum iterations to prevent infinite loops
        self.max_absolute_iterations = 10000000  # Hard cap even when safety is off
        self.safety_enabled = True  # Enable/disable iteration safety
        self.waiting_for_input = False  # Flag to indicate we're waiting for user input
        self.waiting_for_pause_continuation = False  # Flag for pause continuation
        self.pause_duration = 0  # Duration of current pause
        self.program_counter = None  # For resuming execution after input
        self.stopped_position = None  # For CONT command - stores (line, sub_line) where STOP occurred

        # TIMER pseudo-variable (increments at 60 Hz like real CoCo)
        self.timer_epoch = time.time()
        self.trace_mode = False  # TRON/TROFF trace mode

        # ON ERROR GOTO state
        self.on_error_goto_line = None    # Handler line number, or None
        self.error_number = 0             # ERR pseudo-variable
        self.error_line = 0               # ERL pseudo-variable
        self.error_resume_position = None # (line_num, sub_index) of error site
        self.in_error_handler = False     # Prevents recursive error handling

        # Multi-variable INPUT state
        self.input_variables = None  # List of variables waiting for input
        self.input_prompt = None     # Prompt text for multi-variable input
        self.current_input_index = 0 # Current variable index being input
        self.arrays = {}  # Storage for dimensioned arrays
        self.keyboard_buffer = []  # Buffer for INKEY$ function
        self.print_column = 0  # Current PRINT cursor column (for comma zones)
        self.last_rnd = 0.0  # Last value returned by RND (for RND(0))
        self.current_draw_color = 1  # Default drawing color
        self.turtle_x = 64  # Turtle graphics X position (center of default screen)
        self.turtle_y = 48  # Turtle graphics Y position (center of default screen)
        
        # Initialize graphics, variables, and I/O modules
        self.graphics = BasicGraphics(self)
        self.variable_manager = VariableManager(self)
        
        # Initialize AST parser/evaluator and function registry
        self.function_registry = FunctionRegistry()
        register_all_functions(self.function_registry)
        self.ast_parser = ASTParser(known_functions=set(self.function_registry.list_functions()))
        self.ast_evaluator = ASTEvaluator(self)

        # Initialize file manager and program executor
        self.file_manager = FileManager(self)
        self.file_io = FileIOManager(self)
        self.executor = ProgramExecutor(self)

        # Initialize command registry and teach parser about registry commands
        self.command_registry = CommandRegistry()
        self._register_all_commands()
        self.ast_parser.registry_commands = set(self.command_registry.commands.keys())
    
    def emit_output(self, output):
        """
        Emit output using the StreamingOutputManager.
        
        Maintains backward compatibility while using the enhanced output system.
        """
        return self.legacy_adapter.emit_output(output)
    
    def emit_text(self, text: str, source: str = None):
        """Emit text output using the new system"""
        self.output_manager.text(text, source=source, line_number=self.current_line)
    
    def emit_error(self, message: str, source: str = None):
        """Emit error output using the new system"""
        self.output_manager.error(message, source=source, line_number=self.current_line)
    
    def emit_debug(self, message: str, source: str = None):
        """Emit debug output using the new system"""
        self.output_manager.debug(message, source=source, line_number=self.current_line)
    

    def _remove_expanded_lines(self, line_num):
        """Remove all expanded_program entries for a given line number."""
        keys = [k for k in self.expanded_program if k[0] == line_num]
        for k in keys:
            del self.expanded_program[k]

    @staticmethod
    def _system_ok():
        """Return a system OK acknowledgment (not user-generated output)."""
        return [{'type': 'text', 'text': 'OK', 'source': 'system'}]

    def get_reserved_function_names(self):
        """Return list of reserved function names that cannot be used as variable/array names"""
        return ['LEFT$', 'RIGHT$', 'MID$', 'LEN', 'ABS', 'INT', 'RND', 'SQR',
                'SIN', 'COS', 'TAN', 'ATN', 'EXP', 'LOG', 'CHR$', 'ASC', 'STR$', 'VAL',
                'INKEY$', 'HEX$', 'OCT$', 'MEM', 'FRE']

    def check_reserved_name(self, name):
        """Return error response if name is a reserved function, else None."""
        if name in self.get_reserved_function_names():
            error = self.error_context.syntax_error(
                f"Cannot use reserved function name: {name}",
                self.current_line,
                suggestions=[
                    'Choose a different variable name',
                    'Reserved names include built-in functions like SIN, COS, etc.',
                    'Example: Use DATA instead of SIN'
                ]
            )
            return error_response(error)
        return None

    def _require_stack(self, stack, keyword, matching, example):
        """Return error response if stack is empty (keyword without matching opener), else None."""
        if not stack:
            error = self.error_context.syntax_error(
                f"{keyword} without matching {matching}",
                self.current_line,
                suggestions=[
                    f'Every {keyword} must have a matching {matching}',
                    f'Check that {matching} blocks are properly nested',
                    f'Example: {example}'
                ]
            )
            return error_response(error)
        return None

    def parse_line(self, line):
        """Parse a line using the BasicParser - kept for backward compatibility"""
        return BasicParser.parse_line(line)
        
    def process_command(self, command):
        if not command:
            return []
            
        command = command.strip()
        
        # Check if this is a numbered line (program line)
        line_num, code = self.parse_line(command)
        if line_num is not None:
            # This is a program line - add it to the program
            if code:  # Non-empty code
                self.program[line_num] = code
                self.expand_line_to_sublines(line_num, code)
            else:  # Empty code - delete the line
                if line_num in self.program:
                    del self.program[line_num]
                self._remove_expanded_lines(line_num)
            return self._system_ok()

        # Multi-statement lines go straight to process_line (which splits them)
        if not BasicParser.is_rem_line(command):
            statements = BasicParser.split_on_delimiter(command)
            if len(statements) > 1:
                return self.process_line(command)

        # LINE INPUT must be intercepted before the registry sees LINE as a graphics command
        if command.upper().startswith('LINE INPUT'):
            return self.file_io.execute_line_input(command[10:].lstrip())

        # Try command registry first (plugin-like architecture)
        result = self.command_registry.execute(command)
        if result is not None:
            return result

        # If no command was found, try to execute as a line of code
        return self.process_line(command)
    
    def list_program(self):
        output = []
        for line_num in sorted(self.program.keys()):
            output.append({'type': 'text', 'text': f'{line_num} {self.program[line_num]}'})
        return output
    
    def clear_program(self):
        self.program.clear()
        self.expanded_program.clear()
        self.variable_manager.clear_variables()
        return self._system_ok()
    
    def clear_variables(self, args):
        """BASIC CLEAR command - clears variables, optionally sets string space"""
        # Parse optional string space argument
        args = args.strip()
        if args:
            try:
                string_space = self.eval_int(args)
                # In TRS-80 BASIC, this would set string space
                # For our implementation, we'll just acknowledge it
                self.variable_manager.clear_variables()
                return text_response('OK')
            except ValueError:
                error = self.error_context.syntax_error(
                    "Invalid number in CLEAR command",
                    self.current_line,
                    suggestions=[
                        'CLEAR takes an optional numeric argument',
                        'Example: CLEAR 1000',
                        'Check that the number is valid'
                    ]
                )
                return error_response(error)
        else:
            # CLEAR with no arguments - just clear variables
            self.variable_manager.clear_variables()
            return self._system_ok()
    
    # File operations — delegated to FileManager
    def load_program(self, filename):
        return self.file_manager.load_program(filename)

    def save_program(self, filename):
        return self.file_manager.save_program(filename)

    def dir_command(self, args=None):
        return self.file_manager.dir_command(args)

    def files_command(self, args=None):
        return self.file_manager.files_command(args)

    def drive_command(self, args=None):
        return self.file_manager.drive_command(args)

    def kill_file(self, filename):
        return self.file_manager.kill_file(filename)

    def process_kill_confirmation(self, response, filename):
        return self.file_manager.process_kill_confirmation(response, filename)

    def change_directory(self, path):
        return self.file_manager.change_directory(path)
    
    def expand_line_to_sublines(self, line_num, code):
        """Expand line using BasicParser or AST converter for single-line control structures"""
        # REM lines should never be split or AST-converted
        if BasicParser.is_rem_line(code):
            self.expanded_program[(line_num, 0)] = code.strip()
            return

        # Use AST conversion for control structures with colons OR IF statements (even without colons)
        has_control = BasicParser.has_control_keyword(code)
        has_colons = ':' in code
        is_if_statement = code.upper().strip().startswith('IF ')

        if (has_control and has_colons) or is_if_statement:
            # Try AST conversion for single-line control structures
            try:
                from .ast_converter import parse_and_convert_single_line
                converted = parse_and_convert_single_line(code, self.ast_parser)

                if converted:
                    # Add converted statements as sublines, pre-parsing body to AST
                    for i, statement in enumerate(converted):
                        stmt = statement.strip()
                        if stmt:
                            self._store_subline(line_num, i, stmt)
                    return
            except (ValueError, IndexError, KeyError, AttributeError):
                # Fall back to BasicParser if AST conversion fails
                pass

        # Use BasicParser for normal statements
        return BasicParser.expand_line_to_sublines(line_num, code, self.expanded_program)

    # Structural markers that skip methods inspect as text — never pre-parse these
    _STRUCTURAL_MARKERS = frozenset({'ELSE', 'ENDIF'})
    _STRUCTURAL_PREFIXES = ('IF ', 'NEXT ', 'NEXT', 'WEND', 'LOOP')

    def _store_subline(self, line_num, sub_index, stmt):
        """Store a subline, pre-parsing to AST node if eligible."""
        upper = stmt.upper().strip()
        # Structural markers must stay as text for skip methods
        if upper in self._STRUCTURAL_MARKERS or (
                upper.startswith('IF ') and upper.endswith('THEN')) or (
                any(upper.startswith(p) for p in self._STRUCTURAL_PREFIXES)):
            self.expanded_program[(line_num, sub_index)] = stmt
            return
        # Only try to parse statements that start with a letter (commands/assignments).
        # Bare numbers like '50' (implicit GOTO) must stay as text for process_statement.
        first_char = upper[0] if upper else ''
        if not first_char.isalpha():
            self.expanded_program[(line_num, sub_index)] = stmt
            return
        # Try to pre-parse as AST; parser raises RegistryCommandError for
        # commands it can't handle, so no need to check a migrated-commands set
        try:
            from .ast_nodes import VariableNode, LiteralNode
            node = self.ast_parser.parse_statement(stmt)
            # Bare expressions (variable refs, literals) aren't valid statements —
            # keep as text so process_statement can route them properly
            if isinstance(node, (VariableNode, LiteralNode)):
                self.expanded_program[(line_num, sub_index)] = stmt
            else:
                self.expanded_program[(line_num, sub_index)] = node
        except Exception:
            self.expanded_program[(line_num, sub_index)] = stmt

    # ------------------------------------------------------------------
    # Shared execution engine
    # ------------------------------------------------------------------

    # Program execution — delegated to ProgramExecutor
    def run_program(self, clear_variables=True):
        return self.executor.run_program(clear_variables)

    def continue_program_execution(self):
        return self.executor.continue_program_execution()

    def process_line(self, code):
        """
        Process a line of BASIC code. Multi-statement lines (colons) and
        single-line control structures are expanded into temporary sublines
        and executed via run_program, just like stored program lines.
        """
        # REM lines are never split
        if BasicParser.is_rem_line(code):
            return self.process_statement(code)

        # Try AST conversion for single-line control structures
        has_control = BasicParser.has_control_keyword(code)
        has_colons = ':' in code
        is_if_statement = code.upper().strip().startswith('IF ')

        if (has_control and has_colons) or is_if_statement:
            try:
                from .ast_converter import parse_and_convert_single_line
                converted = parse_and_convert_single_line(code, self.ast_parser)
                if converted:
                    return self._execute_converted_as_temporary_program(converted)
            except (ValueError, IndexError, KeyError, AttributeError) as e:
                if hasattr(self, 'emit_debug'):
                    self.emit_debug(f"AST conversion failed for '{code}': {str(e)}")

        # Split on colons; single statements go straight to process_statement
        statements = BasicParser.split_on_delimiter(code)
        if len(statements) <= 1:
            return self.process_statement(code)

        # Multi-statement immediate mode: execute each statement sequentially.
        # Unlike control structures, plain multi-statement lines must surface
        # jump directives and errors to the caller rather than consuming them
        # internally via run_program().
        all_results = []
        for stmt in statements:
            result = self.process_statement(stmt)
            if result:
                all_results.extend(result)
                # Stop on jump directives or errors (like real CoCo BASIC)
                for item in result:
                    if isinstance(item, dict) and item.get('type') in ('jump', 'error'):
                        return all_results
        return all_results

    def _execute_converted_as_temporary_program(self, converted_statements):
        """
        Execute AST-converted statements by creating a temporary program entry
        and using the existing run_program infrastructure completely.
        """
        if not converted_statements:
            return []

        # Use a temporary line number for immediate mode (negative to avoid conflicts)
        temp_line_num = -1

        saved_state = self.save_execution_state()

        try:
            # Clear program and set up temporary program
            self.program = {temp_line_num: '# AST Converted statements'}  # Placeholder only
            self.expanded_program = {}

            self.for_stack.clear()
            self.call_stack.clear()

            # Add AST-converted statements directly as sublines, pre-parsing to AST
            for i, statement in enumerate(converted_statements):
                if statement.strip():
                    self._store_subline(temp_line_num, i, statement.strip())

            # Use the actual run_program method - it has all the sophisticated control flow logic
            # Don't clear variables since we want to preserve the current variable state
            results = self.run_program(clear_variables=False)

            # Filter out system OK messages and other program-mode artifacts
            filtered_results = []
            for item in results:
                if isinstance(item, dict):
                    if item.get('source') == 'system':
                        continue  # Skip system messages
                    elif item.get('type') in ['program_end', 'program_start']:
                        continue  # Skip program control messages

                filtered_results.append(item)

            return filtered_results

        finally:
            self.restore_execution_state(saved_state)

    def _try_ast_execute(self, code):
        """Try to execute a statement via AST. Returns None if not handled."""
        from .ast_parser import RegistryCommandError

        code_stripped = code.strip()
        code_upper = code_stripped.upper()
        parts = code_upper.split(None, 1)
        first_word = parts[0] if parts else ''

        # Registry commands skip AST parsing (cheap early-out)
        if first_word in self.ast_parser.registry_commands:
            return None

        # Must start with a letter to be a valid statement
        if not code_stripped or not code_stripped[0].isalpha():
            return None

        # Validate IF statements require THEN keyword
        if first_word == 'IF' and 'THEN' not in code_upper:
            error = self.error_context.syntax_error(
                "Missing THEN in IF statement",
                self.current_line,
                suggestions=[
                    "Correct syntax: IF condition THEN action",
                    'Example: IF A > 5 THEN PRINT "BIG"',
                    "IF statements must include THEN keyword"
                ]
            )
            return error_response(error)

        try:
            ast_node = self.ast_parser.parse_statement(code_stripped)
            result = self.ast_evaluator.visit(ast_node)
            # Ensure result is a list (statement results must be List[Dict])
            if not isinstance(result, list):
                return None  # Not a valid statement result, fall back
            return result
        except RegistryCommandError:
            return None  # Fall through to registry
        except (ValueError, IndexError, KeyError, AttributeError, TypeError, ZeroDivisionError) as e:
            error_msg = str(e)
            if error_msg:
                error = self.error_context.syntax_error(
                    error_msg,
                    self.current_line,
                    suggestions=[
                        f'Check {first_word} syntax',
                        'Use HELP to see command syntax',
                        'Check BASIC reference for proper syntax'
                    ]
                )
                return error_response(error)
            return None  # Fall back to registry

    def process_statement(self, code):
        if not code.strip():
            return []

        # Handle multi-line IF (bare "IF condition THEN" without action)
        code_upper = code.strip().upper()
        if code_upper.startswith('IF ') and code_upper.endswith('THEN'):
            condition = code.strip()[3:]  # Remove 'IF '
            condition = condition[:condition.upper().rfind('THEN')].strip()
            if condition:
                condition_result = self.evaluate_condition(condition)
                if_info = {
                    'condition_met': condition_result,
                    'line': self.current_line,
                    'sub_line': self.current_sub_line,
                    'in_else': False
                }
                self.if_stack.append(if_info)
                if not condition_result:
                    return [{'type': 'skip_if_block'}]
                else:
                    return []

        # File I/O: PRINT#, INPUT#, LINE INPUT# intercepted before AST
        if code_upper.startswith('LINE INPUT'):
            return self.file_io.execute_line_input(code.strip()[10:].lstrip())
        if code_upper.startswith('PRINT') and '#' in code_upper[:10]:
            rest = code.strip()[5:].lstrip()
            if rest.startswith('#'):
                return self.file_io.execute_print_file(rest[1:])
        if code_upper.startswith('INPUT') and '#' in code_upper[:10]:
            rest = code.strip()[5:].lstrip()
            if rest.startswith('#'):
                return self.file_io.execute_input_file(rest[1:])

        # Try AST execution for migrated commands
        ast_result = self._try_ast_execute(code)
        if ast_result is not None:
            return ast_result

        # Try the command registry
        result = self.command_registry.execute(code.strip())
        if result is not None:
            return result
        
        # If nothing matches, it's a syntax error
        line = self.current_line if (self.current_line != 0 and self.running) else None
        error = self.error_context.syntax_error(
            "Unrecognized command or syntax",
            line,
            suggestions=[
                'Check command spelling and syntax',
                'Use HELP to see available commands',
                'Check BASIC reference for proper syntax'
            ]
        )
        return error_response(error)

    def evaluate_expression(self, expr, line=None):
        """Evaluate a BASIC expression string using the AST parser."""
        expr = expr.strip()
        if not expr:
            error = self.error_context.syntax_error("Empty expression", line or self.current_line)
            raise ValueError(error.format_message())
        try:
            ast_node = self.ast_parser.parse_expression(expr, line or self.current_line)
            return self.ast_evaluator.visit(ast_node)
        except ValueError:
            raise
        except (IndexError, KeyError, AttributeError, TypeError, ZeroDivisionError) as e:
            raise ValueError(str(e))

    def eval_int(self, expr, line=None):
        """Evaluate an expression and return an integer."""
        return int(self.evaluate_expression(expr, line))

    def execute_next(self, args):
        if not self.for_stack:
            error = self.error_context.runtime_error(
                "NEXT WITHOUT FOR",
                self.current_line,
                suggestions=[
                    "NEXT must be preceded by a FOR statement",
                    "Example: FOR I = 1 TO 10: ... : NEXT I",
                    "Check that FOR and NEXT statements are properly paired"
                ]
            )
            return error_response(error)
        
        for_info = self.for_stack[-1]
        var_name = for_info['var']
        
        # Increment the loop variable
        self.variables[var_name] += for_info['step']
        
        # Ensure numeric types for comparison
        current_val = self.variables[var_name]
        end_val = for_info['end']
        step_val = for_info['step']
        
        # Check if loop should continue
        if ((step_val > 0 and current_val <= end_val) or
            (step_val < 0 and current_val >= end_val)):
            # Continue loop - jump to the line AFTER the FOR line
            # This prevents FOR from reinitializing the loop variable
            return [{'type': 'jump_after_for', 'for_line': for_info['line'], 'for_sub_line': for_info['sub_line']}]
        else:
            # End loop
            self.for_stack.pop()
            return []
    
    def _evaluate_array_access(self, array_name, indices_str):
        """Evaluate array element access."""
        if array_name not in self.arrays:
            error = self.error_context.reference_error(
                array_name,
                "UNDIM'D ARRAY",
                suggestions=[
                    f"Declare the array first: DIM {array_name}(size)",
                    "Check the array name spelling"
                ]
            )
            raise ValueError(error.format_message())

        indices = []
        try:
            for idx in indices_str.split(','):
                indices.append(self.eval_int(idx))
        except ValueError as e:
            error = self.error_context.type_error(
                "Invalid array index",
                "integer",
                "non-numeric expression"
            )
            raise ValueError(error.format_message()) from e

        value, error_msg = self.variable_manager.get_array_element(array_name, indices)
        if error_msg:
            error = self.error_context.runtime_error(
                error_msg,
                suggestions=["Check that array indices are within bounds"]
            )
            raise ValueError(error.format_message())

        return value

    def evaluate_condition(self, condition):
        """Evaluate a condition string using the AST parser."""
        try:
            ast_node = self.ast_parser.parse_expression(condition, self.current_line)
            return bool(self.ast_evaluator.visit(ast_node))
        except (ValueError, IndexError, KeyError, AttributeError, TypeError, ZeroDivisionError):
            return False
    
    def execute_sound(self, args):
        # SOUND frequency,duration
        self.error_context.set_context(self.current_line, f"SOUND {args}")
        
        parts = BasicParser.split_args(args)
        if len(parts) != 2:
            error = self.error_context.syntax_error(
                "SOUND requires two parameters",
                self.current_line,
                suggestions=[
                    "Correct syntax: SOUND frequency, duration",
                    "Example: SOUND 440, 100 (plays A note for 100 ticks)",
                    "Both frequency and duration are required"
                ]
            )
            return error_response(error)

        try:
            frequency = self.eval_int(parts[0], self.current_line)
            duration = self.eval_int(parts[1], self.current_line)
            
            if frequency < 1 or frequency > 4095:
                error = self.error_context.runtime_error(
                    f"Frequency {frequency} out of range",
                    self.current_line,
                    suggestions=[
                        "Frequency must be between 1 and 4095 Hz",
                        "Common frequencies: 440 (A note), 262 (C note), 1000 (1kHz tone)",
                        "Lower numbers = deeper tones, higher numbers = higher pitch"
                    ]
                )
                return error_response(error)
                
            if duration < 1 or duration > 255:
                error = self.error_context.runtime_error(
                    f"Duration {duration} out of range", 
                    self.current_line,
                    suggestions=[
                        "Duration must be between 1 and 255 ticks",
                        "Shorter duration = brief sound, longer duration = sustained sound",
                        "Try values like 50 (short beep) or 100 (medium beep)"
                    ]
                )
                return error_response(error)
            
            return [{'type': 'sound', 'frequency': frequency, 'duration': duration}]
            
        except (ValueError, TypeError) as e:
            error = self.error_context.runtime_error(
                f"Invalid SOUND parameters: {e}",
                self.current_line,
                suggestions=[
                    "Both frequency and duration must be numeric",
                    "Example: SOUND 440, 100",
                    "Check that expressions evaluate to integers"
                ]
            )
            return error_response(error)
    
    def execute_randomize(self, args):
        """RANDOMIZE [seed] - seed the random number generator"""
        args = args.strip()
        if args:
            try:
                seed = self.eval_int(args, self.current_line)
                random.seed(seed)
            except (ValueError, TypeError) as e:
                error = self.error_context.runtime_error(
                    f"Invalid RANDOMIZE seed: {e}",
                    self.current_line,
                    suggestions=["RANDOMIZE requires a numeric seed",
                                 "Example: RANDOMIZE 42"])
                return error_response(error)
        else:
            random.seed()
        return self._system_ok()

    def execute_pause(self, args):
        """Execute PAUSE command - pause execution for specified time"""
        try:
            if not args.strip():
                # Default pause of 1 second
                pause_time = 1.0
            else:
                # Evaluate the pause time argument
                pause_time = float(self.evaluate_expression(args.strip()))
                
            # Limit pause time for safety (max 10 seconds)
            if pause_time < 0:
                pause_time = 0
            elif pause_time > 10:
                pause_time = 10
                
            # For program execution, pause and wait for continuation
            if hasattr(self, 'program_counter') and self.program_counter is not None:
                # We're in program execution - save state and pause
                self.waiting_for_pause_continuation = True
                self.pause_duration = pause_time
                # Find the next position to continue from
                all_positions = sorted(self.expanded_program.keys())
                try:
                    current_pos_index = all_positions.index(self.program_counter)
                    if current_pos_index < len(all_positions) - 1:
                        self.program_counter = all_positions[current_pos_index + 1]
                    else:
                        # End of program
                        self.program_counter = None
                except ValueError:
                    # Current position not found, end program
                    self.program_counter = None
                
                return [{'type': 'pause', 'duration': pause_time}]
            else:
                # Direct command execution - just return pause instruction
                return [{'type': 'pause', 'duration': pause_time}]
            
        except (ValueError, TypeError) as e:
            # Return proper error without masking the exception
            error = self.error_context.runtime_error(
                f"PAUSE command error: {e}",
                self.current_line,
                suggestions=["PAUSE requires a numeric duration",
                             "Example: PAUSE 1000"])
            return error_response(error)
    
    def store_input_value(self, var_desc, value):
        """Store a user-entered value into the appropriate variable or array element.

        var_desc is a dict with 'name', 'array', and optionally 'indices'.
        For backwards compatibility, var_desc may also be a plain string (variable name).
        """
        if isinstance(var_desc, str):
            # Legacy: plain variable name string
            var_name = var_desc
            is_array = False
            indices = None
        else:
            var_name = var_desc['name']
            is_array = var_desc.get('array', False)
            indices = var_desc.get('indices')

        # Convert value to appropriate type
        if var_name.endswith('$'):
            typed_value = str(value)
        else:
            try:
                if '.' in str(value) or 'E' in str(value).upper():
                    typed_value = float(value)
                else:
                    typed_value = int(value)
            except (ValueError, TypeError):
                typed_value = 0

        if is_array and indices is not None:
            self.variable_manager.set_array_element(var_name, indices, typed_value)
        else:
            self.variables[var_name] = typed_value

    def clear_all_stacks(self):
        """Clear all control-flow stacks."""
        self.for_stack.clear()
        self.call_stack.clear()
        self.if_stack.clear()
        self.while_stack.clear()
        self.do_stack.clear()

    def save_execution_state(self):
        """Snapshot program and execution state for later restoration."""
        return {
            'program': self.program.copy(),
            'expanded_program': self.expanded_program.copy(),
            'running': self.running,
            'current_line': self.current_line,
            'current_sub_line': self.current_sub_line,
            'for_stack': self.for_stack.copy(),
            'call_stack': self.call_stack.copy(),
        }

    def restore_execution_state(self, state):
        """Restore a previously saved execution state snapshot."""
        self.program = state['program']
        self.expanded_program = state['expanded_program']
        self.running = state['running']
        self.current_line = state['current_line']
        self.current_sub_line = state['current_sub_line']
        self.for_stack = state['for_stack']
        self.call_stack = state['call_stack']

    def clear_interpreter_state(self, clear_program=True):
        """Clear interpreter state - shared function for NEW, LOAD, and other commands"""
        if clear_program:
            self.program.clear()
            self.expanded_program.clear()
        
        self.variables.clear()
        self.arrays.clear()  # Clear all dimensioned arrays
        self.clear_all_stacks()
        self.data_statements.clear()
        self.data_pointer = 0
        self.running = False
        self.waiting_for_input = False
        self.waiting_for_pause_continuation = False
        self.pause_duration = 0
        self.program_counter = None
        self.graphics.clear_pixel_buffer()
        self.stopped_position = None  # Clear stopped position

        # Reset TIMER (trace_mode intentionally NOT reset — persists across RUN like real CoCo)
        self.timer_epoch = time.time()

        # Clear ON ERROR GOTO state
        self.on_error_goto_line = None
        self.error_number = 0
        self.error_line = 0
        self.error_resume_position = None
        self.in_error_handler = False

        # Clear multi-variable INPUT state
        self.input_variables = None
        self.input_prompt = None
        self.current_input_index = 0
        self.current_line = 0
        self.current_sub_line = 0
        self.iteration_count = 0
        # Don't clear keyboard buffer - preserve keys for INKEY$
        self.graphics_mode = 0  # Reset to text mode
        self.screen_mode = 1  # Reset screen/color mode
        self.current_draw_color = 1  # Reset drawing color
        self.turtle_x = 64  # Reset turtle to center
        self.turtle_y = 48
        self.print_column = 0  # Reset print cursor
        self.last_rnd = 0.0  # Reset last RND value

    def execute_new(self):
        """NEW command - clear program and variables"""
        self.clear_interpreter_state(clear_program=True)
        self.file_io.close_all()
        self.trace_mode = False
        return text_response('READY')
    
    def execute_stop(self, args):
        # STOP command - stop program execution with message (allows CONT)
        self.running = False
        # Store position for CONT command
        self.stopped_position = (self.current_line, self.current_sub_line)
        return text_response('BREAK IN ' + str(self.current_line))
    
    def execute_cont(self, args):
        return self.executor.execute_cont(args)

    def _execute_cls(self):
        """CLS — clear screen and reset print column."""
        self.print_column = 0
        return [{'type': 'clear_screen'}]

    def _execute_tron(self):
        """TRON — enable trace mode."""
        self.trace_mode = True
        return []

    def _execute_troff(self):
        """TROFF — disable trace mode."""
        self.trace_mode = False
        return []

    def execute_resume(self, args):
        """RESUME [NEXT | line] — resume after ON ERROR GOTO handler."""
        if not self.in_error_handler:
            error = self.error_context.runtime_error(
                "RESUME WITHOUT ERROR",
                suggestions=["RESUME can only be used inside an ON ERROR GOTO handler",
                             "Use ON ERROR GOTO line to set up an error handler first"])
            return error_response(error)
        self.in_error_handler = False
        args = args.strip().upper()
        if args == '' or args == '0':
            return [{'type': 'resume', 'position': self.error_resume_position}]
        elif args == 'NEXT':
            return [{'type': 'resume_next', 'position': self.error_resume_position}]
        else:
            try:
                line = self.eval_int(args, self.current_line)
            except (ValueError, TypeError):
                error = self.error_context.syntax_error(
                    f"Invalid RESUME target: {args}",
                    self.current_line,
                    suggestions=["Use RESUME, RESUME NEXT, or RESUME line"])
                return error_response(error)
            return [{'type': 'jump', 'line': line}]

    def execute_data(self, args):
        # DATA command - store data values in program
        # DATA 10,20,"HELLO",30.5
        if not args:
            return []
        
        # During program execution, DATA statements should be skipped
        # (they were already preprocessed in run_program)
        if self.running:
            return []
        
        # Parse comma-separated values, respecting quotes
        data_items = []
        items = BasicParser.split_on_delimiter(args, delimiter=',')
        
        for item in items:
            item = item.strip()
            if item.startswith('"') and item.endswith('"'):
                # String literal
                data_items.append(item[1:-1])
            else:
                # Try to parse as number: int first, then float, else string
                try:
                    data_items.append(int(item))
                except ValueError:
                    try:
                        data_items.append(float(item))
                    except ValueError:
                        data_items.append(item)
        
        # Store data items with current line number for organization
        self.data_statements.extend([(self.current_line, item) for item in data_items])
        
        return []  # DATA commands don't produce output
    
    def execute_read(self, args):
        # READ command - read data into variables
        # READ A,B$,C
        if not args:
            error = self.error_context.syntax_error(
                "READ requires variable names",
                self.current_line,
                suggestions=[
                    "Specify variables to read data into",
                    "Example: READ A, B$, C",
                    "Variables must match DATA statement types"
                ]
            )
            return error_response(error)
        
        # Parse variable names (parenthesis-aware for multi-dim arrays)
        var_names = BasicParser.split_args(args)
        
        for var_name in var_names:
            if self.data_pointer >= len(self.data_statements):
                error = self.error_context.runtime_error(
                    "OUT OF DATA",
                    self.current_line,
                    suggestions=[
                        "Add more DATA statements to your program",
                        "Use RESTORE to reset data pointer to beginning",
                        "Check that READ statements match available DATA"
                    ]
                )
                return error_response(error)
            
            # Get the next data item
            line_num, data_value = self.data_statements[self.data_pointer]
            self.data_pointer += 1
            
            # Check if this is an array element assignment
            if '(' in var_name and ')' in var_name:
                # Handle array element assignment
                result = self.assign_array_element(var_name, data_value)
                if result:  # If there was an error
                    return result
            else:
                # Store in variable
                self.variables[var_name] = data_value
        
        return []  # READ commands don't produce output unless there's an error
    
    def assign_array_element(self, var_name, value):
        """Assign a value to an array element, return error result if there's an issue"""
        # Extract array name and index contents, handling nested parentheses
        paren_pos = var_name.find('(')
        if paren_pos == -1 or not var_name.rstrip().endswith(')'):
            error = self.error_context.syntax_error(
                "Invalid array syntax in DATA statement",
                self.current_line,
                suggestions=[
                    'Array syntax: A(1,2) or B$(5)',
                    'Check array name and index format',
                    'Ensure parentheses are properly matched'
                ]
            )
            return error_response(error)

        array_name = var_name[:paren_pos]
        indices_str = var_name[paren_pos + 1:-1]  # contents between outer parens

        # Parse indices using parenthesis-aware split
        try:
            indices = [self.eval_int(idx) for idx in BasicParser.split_args(indices_str)]
            
            # Use VariableManager to set array element
            err_msg = self.variable_manager.set_array_element(array_name.upper(), indices, value)
            if err_msg:
                error = self.error_context.runtime_error(
                    err_msg, self.current_line,
                    suggestions=["Check array dimensions with DIM",
                                 "Array indices must be within bounds"])
                return error_response(error)
            return None  # No error
            
        except ValueError:
            error = self.error_context.syntax_error(
                "Invalid line number format",
                self.current_line,
                suggestions=[
                    'Line numbers must be integers',
                    'Example: 10, 20, 100',
                    'Check that the line number is valid'
                ]
            )
            return error_response(error)
        except (IndexError, TypeError, KeyError):
            error = self.error_context.runtime_error(
                "Array index out of bounds",
                suggestions=[
                    'Check that array indices are within valid range',
                    'Arrays are 0-indexed: DIM A(10) creates indices 0-10',
                    'Use valid positive integer indices'
                ]
            )
            return error_response(error)

    def execute_restore(self, args):
        # RESTORE command - reset data pointer to beginning
        self.data_pointer = 0
        return []
    
    # ON GOTO/GOSUB and ON ERROR GOTO migrated to AST (ast_evaluator.py)
    # INKEY$ functionality moved to functions.py function registry
    # Keyboard buffer management now handled by function registry
    
    
    
    
    def _register_all_commands(self):
        """Register all BASIC commands by delegating to each module"""
        # Let each module register its own commands
        self.graphics.register_commands(self.command_registry)
        self.variable_manager.register_commands(self.command_registry)
        self.file_io.register_commands(self.command_registry)
        # Core commands - control flow
        # Note: IF, GOTO, GOSUB, RETURN, FOR, WHILE, EXIT, DO, END are handled by AST execution

        self.command_registry.register('NEXT', self.execute_next,
                                     category='control',
                                     description="End FOR loop and increment counter",
                                     syntax="NEXT [variable]",
                                     examples=["NEXT", "NEXT I", "NEXT X"])

        self.command_registry.register('WEND', self.execute_wend,
                                     category='control',
                                     description="End WHILE loop",
                                     syntax="WEND",
                                     examples=["WEND"])

        self.command_registry.register('LOOP', self.execute_loop,
                                     category='control',
                                     description="End DO loop block",
                                     syntax="LOOP [WHILE condition | UNTIL condition]",
                                     examples=["LOOP", "LOOP WHILE X > 0", "LOOP UNTIL Y = 10"])

        self.command_registry.register('ELSE', self.execute_else,
                                     category='control',
                                     description="Alternative branch in IF statement",
                                     syntax="ELSE",
                                     examples=["ELSE"])
        
        self.command_registry.register('ENDIF', self.execute_endif,
                                     category='control',
                                     description="End multi-line IF block",
                                     syntax="ENDIF",
                                     examples=["ENDIF"])
        
        self.command_registry.register('STOP', self.execute_stop,
                                     category='control',
                                     description="Stop program execution",
                                     syntax="STOP",
                                     examples=["STOP"])
        
        self.command_registry.register('CONT', self.execute_cont,
                                     category='system',
                                     description="Continue program after STOP",
                                     syntax="CONT",
                                     examples=["CONT"])

        self.command_registry.register('TRON', lambda args: self._execute_tron(),
                                     category='system',
                                     description="Enable trace mode (print line numbers during execution)",
                                     syntax="TRON",
                                     examples=["TRON"])

        self.command_registry.register('TROFF', lambda args: self._execute_troff(),
                                     category='system',
                                     description="Disable trace mode",
                                     syntax="TROFF",
                                     examples=["TROFF"])

        self.command_registry.register('RESUME', self.execute_resume,
                                     category='flow',
                                     description="Resume execution after ON ERROR GOTO handler",
                                     syntax="RESUME [NEXT | line]",
                                     examples=["RESUME", "RESUME NEXT", "RESUME 100"])

        # Data commands
        self.command_registry.register('DATA', self.execute_data,
                                     category='data',
                                     description="Define data values for READ statements",
                                     syntax="DATA value1, value2, ...",
                                     examples=["DATA 10, 20, 30", "DATA \"HELLO\", \"WORLD\""])
        
        self.command_registry.register('READ', self.execute_read,
                                     category='data', 
                                     description="Read data values into variables",
                                     syntax="READ variable1, variable2, ...",
                                     examples=["READ A, B, C", "read NAME$, AGE"])
        
        self.command_registry.register('RESTORE', self.execute_restore,
                                     category='data',
                                     description="Reset DATA pointer to beginning",
                                     syntax="RESTORE",
                                     examples=["RESTORE"])
        
        # System commands
        self.command_registry.register('CLS', lambda args: self._execute_cls(),
                                     category='system',
                                     description="Clear the screen",
                                     syntax="CLS",
                                     examples=["CLS"])
        
        self.command_registry.register('NEW', lambda args: self.execute_new(),
                                     category='system',
                                     description="Clear program and variables",
                                     syntax="NEW",
                                     examples=["NEW"])
        
        self.command_registry.register('SOUND', self.execute_sound,
                                     category='system',
                                     description="Generate sound tones",
                                     syntax="SOUND tone, duration",
                                     examples=["SOUND 440, 100", "SOUND 220, 50"])
        
        self.command_registry.register('RANDOMIZE', self.execute_randomize,
                                     category='system',
                                     description="Seed the random number generator",
                                     syntax="RANDOMIZE [seed]",
                                     examples=["RANDOMIZE", "RANDOMIZE 42"])

        self.command_registry.register('PAUSE', self.execute_pause,
                                     category='system',
                                     description="Pause execution for specified time",
                                     syntax="PAUSE duration",
                                     examples=["PAUSE 1000", "PAUSE 500"])
        
        # Program management commands
        self.command_registry.register('LIST', lambda args: self.list_program(),
                                     category='system',
                                     description="List program lines",
                                     syntax="LIST",
                                     examples=["LIST"])
        
        self.command_registry.register('RUN', lambda args: self.run_program(),
                                     category='system',
                                     description="Execute the program",
                                     syntax="RUN",
                                     examples=["RUN"])
        
        self.command_registry.register('CLEAR', self.clear_variables,
                                     category='system',
                                     description="Clear variables and optionally set string space",
                                     syntax="CLEAR [string_space]",
                                     examples=["CLEAR", "CLEAR 1000"])
        
        self.command_registry.register('DELETE', self.execute_delete,
                                     category='system',
                                     description="Delete program lines or line ranges",
                                     syntax="DELETE line_number | DELETE start-end",
                                     examples=["DELETE 100", "DELETE 10-50", "DELETE 200-300"])
        
        self.command_registry.register('RENUM', self.execute_renum,
                                     category='system',
                                     description="Renumber program lines",
                                     syntax="RENUM [new_start],[increment],[old_start]",
                                     examples=["RENUM", "RENUM 100", "RENUM 100,10", "RENUM 100,10,50"])
        
        self.command_registry.register('SAFETY', self.execute_safety,
                                     category='system',
                                     description="Enable or disable iteration safety limits",
                                     syntax="SAFETY ON | SAFETY OFF",
                                     examples=["SAFETY ON", "SAFETY OFF"])
        
        self.command_registry.register('LOAD', self.load_program,
                                     category='system',
                                     description="Load program from file",
                                     syntax="LOAD \"filename\"",
                                     examples=["LOAD \"DEMO.BAS\"", "LOAD \"programs/game.bas\""])
        
        self.command_registry.register('SAVE', self.save_program,
                                     category='system',
                                     description="Save program to file",
                                     syntax="SAVE \"filename\"",
                                     examples=["SAVE \"MYGAME\"", "SAVE \"programs/utility.bas\""])
        
        self.command_registry.register('CSAVE', self.save_program,
                                     category='system',
                                     description="Save program (cassette version, redirects to SAVE)",
                                     syntax="CSAVE \"filename\"",
                                     examples=["CSAVE \"MYGAME\""])
        
        self.command_registry.register('CLOAD', self.load_program,
                                     category='system',
                                     description="Load program (cassette version, redirects to LOAD)",
                                     syntax="CLOAD \"filename\"",
                                     examples=["CLOAD \"DEMO.BAS\""])
        
        self.command_registry.register('DIR', self.dir_command,
                                     category='system',
                                     description="List available BASIC program files",
                                     syntax="DIR [drive]",
                                     examples=["DIR", "DIR 0"])
        
        self.command_registry.register('FILES', self.files_command,
                                     category='system',
                                     description="Reserve file buffers (no-op in this implementation)",
                                     syntax="FILES max_files[,buffer_size]",
                                     examples=["FILES 4", "FILES 8,256"])
        
        self.command_registry.register('DRIVE', self.drive_command,
                                     category='system',
                                     description="Set default drive (no-op in this implementation)",
                                     syntax="DRIVE drive_number",
                                     examples=["DRIVE 0", "DRIVE 1"])
        
        self.command_registry.register('KILL', self.kill_file,
                                     category='system',
                                     description="Delete a BASIC program file",
                                     syntax="KILL \"filename\"",
                                     examples=["KILL \"OLDGAME\"", "KILL \"programs/test.bas\""])
        
        self.command_registry.register('CD', self.change_directory,
                                     category='system',
                                     description="Change current working directory",
                                     syntax="CD [\"path\"]",
                                     examples=["CD", "CD \"programs\"", "CD \"..\"", "CD \"~\""])
        
        # Comments
        self.command_registry.register('REM', lambda args: [],
                                     category='system',
                                     description="Add remark/comment (ignored)",
                                     syntax="REM comment text",
                                     examples=["REM This is a comment", "REM TODO: Fix this later"])
        
        self.command_registry.register("'", lambda args: [],
                                     category='system',
                                     description="Add remark/comment (short form)",
                                     syntax="' comment text", 
                                     examples=["' This is a comment", "' Variables: A=5, B=10"])
        
        # Help system
        self.command_registry.register('HELP', self.execute_help,
                                     category='system',
                                     description="Show help for commands",
                                     syntax="HELP [command]",
                                     examples=["HELP", "HELP PRINT", "HELP FOR"])
    
    def execute_help(self, args):
        """Execute HELP command to show command information"""
        args = args.strip()
        
        # Generate help using the command registry
        help_lines = self.command_registry.generate_help(args if args else None)
        
        # Convert to output format
        output = []
        for line in help_lines:
            output.append({'type': 'text', 'text': line})
        
        return output
    

    # Enhanced Control Flow Methods
    def execute_wend(self, args):
        """WEND statement - end WHILE loop"""
        err = self._require_stack(self.while_stack, 'WEND', 'WHILE', 'WHILE condition ... WEND')
        if err:
            return err
        
        # Get the current WHILE loop
        while_info = self.while_stack[-1]

        # Re-evaluate the condition using stored AST node
        result = self.ast_evaluator.visit(while_info['condition_ast'])
        condition_true = basic_truthy(result)
        if condition_true:
            # Continue loop - jump back to after the WHILE statement
            return [{'type': 'jump_after_while', 
                    'while_line': while_info['line'],
                    'while_sub_line': while_info['sub_line']}]
        else:
            # Exit loop
            self.while_stack.pop()
            return []
    
    def execute_loop(self, args):
        """LOOP statement - end DO/LOOP block"""
        err = self._require_stack(self.do_stack, 'LOOP', 'DO', 'DO ... LOOP or DO ... LOOP WHILE condition')
        if err:
            return err
        
        # Get current DO loop
        do_info = self.do_stack[-1]

        # Parse LOOP [WHILE condition | UNTIL condition]
        args = args.strip()
        condition = do_info.get('condition')
        condition_ast = do_info.get('condition_ast')
        condition_type = do_info.get('condition_type')

        # Check for condition at LOOP (overrides DO condition)
        for keyword in ('WHILE', 'UNTIL'):
            prefix = keyword + ' '
            if args.upper().startswith(prefix):
                condition_str = args[len(prefix):].strip()
                condition_type = keyword
                if 'loop_condition_ast' not in do_info or do_info.get('loop_condition_str') != condition_str:
                    try:
                        do_info['loop_condition_ast'] = self.ast_parser.parse_expression(condition_str, self.current_line)
                        do_info['loop_condition_str'] = condition_str
                    except (ValueError, IndexError, KeyError, AttributeError):
                        do_info['loop_condition_ast'] = None
                condition_ast = do_info.get('loop_condition_ast')
                condition = condition_str if condition_ast is None else None
                break

        # Evaluate loop continuation
        should_continue = False
        if condition_ast is not None:
            # AST-based condition evaluation (condition from DO statement)
            result = self.ast_evaluator.visit(condition_ast)
            condition_true = basic_truthy(result)
            if condition_type == 'WHILE':
                should_continue = condition_true
            elif condition_type == 'UNTIL':
                should_continue = not condition_true
        elif condition:
            # String-based condition (from LOOP WHILE/UNTIL syntax)
            if condition_type == 'WHILE':
                should_continue = self.evaluate_condition(condition)
            elif condition_type == 'UNTIL':
                should_continue = not self.evaluate_condition(condition)
        else:
            # Infinite loop without condition
            should_continue = True
        
        if should_continue:
            # Continue loop - jump back to after DO
            return [{'type': 'jump_after_do',
                    'do_line': do_info['line'],
                    'do_sub_line': do_info['sub_line']}]
        else:
            # Exit loop
            self.do_stack.pop()
            return []

    def execute_else(self, args):
        """ELSE statement - alternative branch in multi-line IF"""
        err = self._require_stack(self.if_stack, 'ELSE', 'IF', 'IF condition ... ELSE ... ENDIF')
        if err:
            return err
        
        # Get current IF info
        if_info = self.if_stack[-1]
        
        # If we were in the THEN part and condition was true, skip to ENDIF
        if if_info['condition_met'] and not if_info['in_else']:
            if_info['in_else'] = True
            return [{'type': 'skip_else_block'}]
        
        # If we're already in ELSE or condition was false, continue with ELSE
        if_info['in_else'] = True
        return []
    
    def execute_endif(self, args):
        """ENDIF statement - end multi-line IF block"""
        err = self._require_stack(self.if_stack, 'ENDIF', 'IF', 'IF condition ... ENDIF')
        if err:
            return err
        
        # Pop the current IF from the stack
        self.if_stack.pop()
        return []
    
    def execute_delete(self, args):
        """DELETE statement - delete program lines or line ranges"""
        args = args.strip()
        if not args:
            error = self.error_context.syntax_error(
                "DELETE requires line number(s)",
                self.current_line,
                suggestions=[
                    'Correct syntax: DELETE line_number or DELETE start-end',
                    'Example: DELETE 100 or DELETE 100-200',
                    'Specify which lines to delete'
                ]
            )
            return error_response(error)
        
        try:
            # Parse the argument - can be single line or range
            if '-' in args:
                # Range format: DELETE start-end
                parts = args.split('-', 1)
                if len(parts) != 2:
                    error = self.error_context.syntax_error(
                        "Invalid range format in DELETE",
                        self.current_line,
                        suggestions=[
                            'Correct syntax: DELETE start-end',
                            'Example: DELETE 100-200',
                            'Use hyphen to separate start and end line numbers'
                        ]
                    )
                    return error_response(error)
                
                start_str = parts[0].strip()
                end_str = parts[1].strip()
                
                if not start_str or not end_str:
                    error = self.error_context.syntax_error(
                        "Invalid range format in DELETE",
                        self.current_line,
                        suggestions=[
                            'Both start and end line numbers are required',
                            'Example: DELETE 100-200',
                            'Cannot have empty line numbers in range'
                        ]
                    )
                    return error_response(error)
                
                start_line = int(start_str)
                end_line = int(end_str)
                
                if start_line > end_line:
                    error = self.error_context.syntax_error(
                        "Start line must be less than or equal to end line",
                        self.current_line,
                        suggestions=[
                            'Example: DELETE 100-200 not DELETE 200-100',
                            'Start line number must be <= end line number',
                            'Check the range specification'
                        ]
                    )
                    return error_response(error)
                
                # Delete all lines in the range
                lines_deleted = 0
                for line_num in list(self.program.keys()):
                    if start_line <= line_num <= end_line:
                        del self.program[line_num]
                        self._remove_expanded_lines(line_num)
                        lines_deleted += 1
                
                if lines_deleted == 0:
                    return text_response('NO LINES DELETED')
                else:
                    return text_response(f'DELETED {lines_deleted} LINE(S)')
                    
            else:
                # Single line format: DELETE line_number
                line_num = int(args)
                
                if line_num in self.program:
                    del self.program[line_num]
                    self._remove_expanded_lines(line_num)
                    return text_response(f'DELETED LINE {line_num}')
                else:
                    return text_response(f'LINE {line_num} NOT FOUND')
                    
        except ValueError:
            error = self.error_context.syntax_error(
                "Invalid line number in DELETE command",
                self.current_line,
                suggestions=[
                    'Line numbers must be integers',
                    'Example: DELETE 100 or DELETE 100-200',
                    'Check that line numbers are valid'
                ]
            )
            return error_response(error)
        except (TypeError, KeyError) as e:
            error = self.error_context.runtime_error(
                f"DELETE error: {e}",
                self.current_line,
                suggestions=["Check that the specified line numbers exist"])
            return error_response(error)

    def execute_renum(self, args):
        """RENUM statement - renumber program lines"""
        # Parse arguments: RENUM [new_start],[increment],[old_start]
        # Defaults: new_start=10, increment=10, old_start=first line
        
        new_start = 10
        increment = 10
        old_start = None
        
        if args:
            args = args.strip()
            parts = args.split(',')
            
            try:
                if len(parts) >= 1 and parts[0].strip():
                    new_start = int(parts[0].strip())
                if len(parts) >= 2 and parts[1].strip():
                    increment = int(parts[1].strip())
                if len(parts) >= 3 and parts[2].strip():
                    old_start = int(parts[2].strip())
            except ValueError:
                error = self.error_context.syntax_error(
                    "Invalid line number in RENUM command",
                    self.current_line,
                    suggestions=[
                        'Line numbers must be integers',
                        'Example: RENUM 10,10',
                        'Check that line numbers are valid'
                    ]
                )
                return error_response(error)
        
        if new_start < 1 or new_start > 65535:
            error = self.error_context.syntax_error(
                "Line number out of range",
                self.current_line,
                suggestions=[
                    'Line numbers must be between 1 and 65535',
                    'Example: RENUM 10,10',
                    'Use valid line number range'
                ]
            )
            return error_response(error)
        if increment < 1:
            error = self.error_context.syntax_error(
                "Increment must be positive",
                self.current_line,
                suggestions=[
                    'Increment must be greater than 0',
                    'Example: RENUM 10,10 (increment of 10)',
                    'Use positive increment value'
                ]
            )
            return error_response(error)
        
        # Get sorted list of existing line numbers
        old_lines = sorted(self.program.keys())
        if not old_lines:
            return text_response('NO PROGRAM TO RENUMBER')
        
        # Determine which lines to renumber
        if old_start is not None:
            old_lines = [line for line in old_lines if line >= old_start]
            if not old_lines:
                return text_response('NO LINES TO RENUMBER')
        
        # Create mapping of old to new line numbers
        line_mapping = {}
        current_new = new_start
        for old_line in old_lines:
            line_mapping[old_line] = current_new
            current_new += increment
            if current_new > 65535:
                error = self.error_context.runtime_error(
                    "New line numbers exceed maximum value",
                    suggestions=[
                        'Line numbers must be between 1 and 65535',
                        'Use smaller increment or fewer lines to renumber',
                        'Consider renumbering in smaller batches'
                    ]
                )
                return error_response(error)
        
        # Check for conflicts with existing lines not being renumbered
        unchanged_lines = set(self.program.keys()) - set(old_lines)
        new_lines = set(line_mapping.values())
        conflicts = unchanged_lines & new_lines
        if conflicts:
            error = self.error_context.runtime_error(
                f"NEW LINE {min(conflicts)} CONFLICTS WITH EXISTING LINE",
                self.current_line,
                suggestions=["Choose different RENUM parameters to avoid conflicts",
                             "Delete conflicting lines first"])
            return error_response(error)
        
        # Update program with new line numbers
        new_program = {}
        
        # Keep unchanged lines
        for line_num in unchanged_lines:
            new_program[line_num] = self.program[line_num]
        
        # Add renumbered lines with updated GOTO/GOSUB/THEN targets
        for old_line, new_line in line_mapping.items():
            new_program[new_line] = self._update_line_references(
                self.program[old_line], line_mapping)
        
        # Replace the program
        self.program = new_program
        
        # Rebuild expanded program
        self.expanded_program = {}
        for line_num in sorted(self.program.keys()):
            self.expand_line_to_sublines(line_num, self.program[line_num])
        
        return text_response(f'RENUMBERED {len(line_mapping)} LINES')

    @staticmethod
    def _update_line_references(code, line_mapping):
        """Update GOTO/GOSUB/THEN line number targets in a line of code."""
        pattern = r'\b(GOTO|GOSUB|THEN)\s+(\d+)\b'

        def replace_line_ref(match):
            keyword = match.group(1)
            target = int(match.group(2))
            if target in line_mapping:
                return f'{keyword} {line_mapping[target]}'
            return match.group(0)

        updated = re.sub(pattern, replace_line_ref, code, flags=re.IGNORECASE)

        # Also handle ON...GOTO and ON...GOSUB with comma-separated line numbers
        on_pattern = r'\b(ON\s+.*?\s+(?:GOTO|GOSUB))\s+([\d,\s]+)\b'

        def replace_on_refs(match):
            prefix = match.group(1)
            targets = match.group(2)
            parts = []
            for part in targets.split(','):
                part = part.strip()
                if part.isdigit():
                    target = int(part)
                    if target in line_mapping:
                        parts.append(str(line_mapping[target]))
                    else:
                        parts.append(part)
                else:
                    parts.append(part)
            return f'{prefix} {",".join(parts)}'

        return re.sub(on_pattern, replace_on_refs, updated, flags=re.IGNORECASE)

    def execute_safety(self, args):
        """SAFETY statement - enable or disable iteration safety limits"""
        args = args.strip().upper()
        
        if not args:
            # Show current status
            status = "ON" if self.safety_enabled else "OFF"
            return text_response(f'SAFETY IS {status}')
        
        if args == 'ON':
            self.safety_enabled = True
            return text_response('SAFETY ON - ITERATION LIMITS ENABLED')
        elif args == 'OFF':
            self.safety_enabled = False
            return [{'type': 'text', 'text': 'SAFETY OFF - ITERATION LIMITS DISABLED'},
                    {'type': 'text', 'text': f'(HARD CAP AT {self.max_absolute_iterations:,} ITERATIONS STILL ACTIVE)'}]
        else:
            error = self.error_context.syntax_error(
                "Invalid SAFETY command syntax",
                self.current_line,
                suggestions=[
                    'Correct syntax: SAFETY ON or SAFETY OFF',
                    'Example: SAFETY ON',
                    'Use ON or OFF after SAFETY'
                ]
            )
            return error_response(error)

