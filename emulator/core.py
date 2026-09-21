"""
BasiCoCo - Educational Color Computer BASIC Environment

Main interpreter module. CoCoBasic orchestrates the BASIC environment:
command dispatch, program storage, expression evaluation, and state management.
"""

import logging
import random
import re
import time

logger = logging.getLogger(__name__)
from .text_utils import StatementSplitter
from .graphics import BasicGraphics
from .variables import VariableManager
from .commands import CommandRegistry, CompiledCommand, CompiledMultiLineIf
from .ast_nodes import basic_truthy
from .ast_converter import (expand_statements, starts_control_structure, command_words,
                            find_keyword)
from .function_registry import FunctionRegistry
from .functions import register_all_functions, basic_number_prefix
from .ast_parser import ASTParser
from .ast_evaluator import ASTEvaluator
from .error_context import (ErrorContextManager, error_response, text_response, text_message,
                            BASIC_RUNTIME_ERRORS)
from .program_files import FileManager
from .file_io import FileIOManager
from .program_executor import ProgramExecutor
from .control_flow import ControlFlowCommands
from .data_commands import DataCommands

class CoCoBasic:
    """Main BASIC interpreter for the TRS-80 Color Computer emulator.

    Orchestrates command dispatch, program storage, expression evaluation,
    and state management. Delegates to domain modules for graphics, variables,
    file I/O, control flow, and data commands. See CLAUDE.md for the full
    dispatch order and architectural overview.
    """

    def __init__(self, output_callback=None, debug_mode=False):
        self.program = {}  # Line number -> code (original for LIST display)
        self.expanded_program = {}  # (line_num, sub_index) -> str or ASTNode (for execution)
        self.variables = {}
        self.labels = {}  # label_name -> line_number (for GOTO/GOSUB label support)
        self.data_values = {}  # line_num -> list of parsed values (collected at store-time)
        self.data_statements = []
        self.data_pointer = 0
        self.running = False
        
        self.output_callback = output_callback
        self.current_line = 0
        
        # Initialize error context manager for enhanced error messages
        self.error_context = ErrorContextManager()
        self.current_sub_line = 0
        self.call_stack = []
        self.local_stack = []  # Stack of frames for LOCAL variable save/restore
        self.for_stack = []
        self.if_stack = []
        self.while_stack = []
        self.do_stack = []
        self.graphics_mode = None  # None until PMODE; then 0-4 (PMODE 0 is graphics)
        self.screen_mode = 1    # Screen/color mode
        self.iteration_count = 0  # Safety counter for infinite loops
        self.max_iterations = 50000  # Maximum iterations to prevent infinite loops
        self.max_absolute_iterations = 10000000  # Hard cap even when safety is off
        self.safety_enabled = True  # Enable/disable iteration safety
        self.waiting_for_input = False  # Flag to indicate we're waiting for user input
        self.waiting_for_pause_continuation = False  # Flag for pause continuation
        self._expr_cache = {}  # Cache: expression string -> parsed AST node
        self.program_counter = None  # For resuming execution after input
        self.stopped_position = None  # For CONT command - stores (line, sub_line) where STOP occurred
        self.break_requested = False  # Set by another thread (Ctrl+C); checked each statement

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
        self.rng = random.Random()  # Per-interpreter RNG (RND, RANDOMIZE)
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

        # Initialize file manager, program executor, and command modules
        self.file_manager = FileManager(self)
        self.file_io = FileIOManager(self)
        self.executor = ProgramExecutor(self)
        self.control_flow = ControlFlowCommands(self)
        self.data_commands = DataCommands(self)

        # Initialize command registry and teach parser about registry commands
        self.command_registry = CommandRegistry()
        self._register_all_commands()
        self.ast_parser.registry_commands = set(self.command_registry.commands.keys())
        # Statement-starting words, for telling "THEN A*B" (GOTO) from "THEN CLS"
        self.command_words = command_words(self.ast_parser)
    

    def _remove_expanded_lines(self, line_num):
        """Remove everything compiled from a line: sublines, DATA values, labels."""
        keys = [k for k in self.expanded_program if k[0] == line_num]
        for k in keys:
            del self.expanded_program[k]
        self.data_values.pop(line_num, None)
        for label in [name for name, target in self.labels.items() if target == line_num]:
            del self.labels[label]

    def store_program_line(self, line_num, code):
        """Store, replace or (with empty code) delete a numbered program line.

        The single entry point for program-line edits, so a re-typed line never
        leaves stale sublines, DATA values or labels behind.
        """
        self._remove_expanded_lines(line_num)
        if code:
            self.program[line_num] = code
            self.expand_line_to_sublines(line_num, code)
        else:
            self.program.pop(line_num, None)

    @staticmethod
    def _system_ok():
        """Return a system OK acknowledgment (not user-generated output)."""
        return text_response('OK', source='system')

    def check_reserved_name(self, name):
        """Return error response if name is a reserved function, else None."""
        if self.function_registry.is_function(name):
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
        """Parse a line into (line_number, code) — delegates to StatementSplitter."""
        return StatementSplitter.parse_line(line)
        
    def process_command(self, command):
        if not command:
            return []
            
        command = command.strip()
        
        # Check if this is a numbered line (program line)
        line_num, code = self.parse_line(command)
        if line_num is not None:
            self.store_program_line(line_num, code)
            return self._system_ok()

        # Multi-statement lines go straight to process_line (which splits them)
        call_depth = len(self.call_stack)
        if not StatementSplitter.is_rem_line(command):
            statements = StatementSplitter.split_on_delimiter(command)
            if len(statements) > 1:
                return self._follow_immediate_jump(self.process_line(command), call_depth)

        # LINE INPUT must be intercepted before the registry sees LINE as a graphics command
        m = self._LINE_INPUT_RE.match(command)
        if m:
            return self.file_io.execute_line_input(command[m.end():].lstrip())

        # Try command registry first (plugin-like architecture)
        result = self.command_registry.execute(command)
        if result is not None:
            return result

        # If no command was found, try to execute as a line of code
        return self._follow_immediate_jump(self.process_line(command), call_depth)

    def _follow_immediate_jump(self, result, call_depth):
        """GOTO/GOSUB typed at the prompt (GOTO 100, A=1: GOSUB 500) runs the
        stored program from that line without clearing variables, as on the
        CoCo, instead of returning a raw jump directive to the caller.

        A GOSUB's return point is set past the last line, so its RETURN
        comes back to the prompt rather than falling into the program.
        """
        jump = next((item for item in result
                     if isinstance(item, dict) and item.get('type') == 'jump'), None)
        if jump is None:
            return result
        before = [item for item in result if item is not jump]
        if jump['line'] not in self.program:
            del self.call_stack[call_depth:]  # drop an immediate GOSUB's frame
            return before + error_response(self.error_context.runtime_error(
                f"UNDEFINED LINE {jump['line']}", self.current_line,
                suggestions=['Check the line number exists: LIST',
                             'Enter the line first, e.g. 100 PRINT "HERE"',
                             'Labels must be defined on their own line']))
        if len(self.call_stack) > call_depth:
            self.call_stack[-1] = (float('inf'),) + tuple(self.call_stack[-1][1:])
        return before + self.executor.run_program_from_line(jump['line'], clear_variables=False)
    
    def list_program(self):
        output = []
        for line_num in sorted(self.program.keys()):
            if line_num >= 0:  # skip a pending immediate-mode line (-1)
                output.append(text_message(f'{line_num} {self.program[line_num]}'))
        return output
    
    def clear_variables(self, args):
        """BASIC CLEAR command - clears variables, optionally sets string space"""
        # Parse optional string space argument
        args = args.strip()
        if args:
            try:
                # The string-space size is validated but otherwise ignored
                self.eval_int(args)
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
        self.variable_manager.clear_variables()
        # Silent inside a running program; acknowledged at the prompt
        return [] if self.running else self._system_ok()
    
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

    def process_kill_confirmation(self, response, filename=None):
        return self.file_manager.process_kill_confirmation(response, filename)

    def merge_program(self, filename):
        return self.file_manager.merge_program(filename)

    def chain_program(self, args):
        return self.file_manager.chain_program(args)

    def change_directory(self, path):
        return self.file_manager.change_directory(path)
    
    _LABEL_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*$')

    def resolve_label(self, name):
        """Look up a label name and return its line number, or None."""
        return self.labels.get(name.upper())

    def expand_line_to_sublines(self, line_num, code):
        """Compile a stored line into sublines (see ast_converter.expand_statements)."""
        # Detect label definition (e.g. "CalcAvg:") before any splitting
        m = self._LABEL_RE.match(code.strip())
        if m:
            label_name = m.group(1).upper()
            self.labels[label_name] = line_num
            # Store as a no-op so the line exists in expanded_program
            self.expanded_program[(line_num, 0)] = self._COMMENT
            return

        # Comment lines (REM or ') are never split; stored as a no-op
        if StatementSplitter.is_rem_line(code):
            self.expanded_program[(line_num, 0)] = self._COMMENT
            return

        # Split on colons, expanding a one-line IF (wherever it starts) into
        # block sublines; each subline is then pre-compiled by _store_subline
        for i, subline in enumerate(expand_statements(code, self.command_words)):
            self._store_subline(line_num, i, subline)

    # Structural markers that skip methods inspect as text — never pre-parse these
    # Compiled no-op for comment sublines (REM ..., ' ...)
    _COMMENT = CompiledCommand(lambda args: [], '', keyword='REM')

    def _store_subline(self, line_num, sub_index, stmt):
        """Store a subline, pre-parsing to AST node or CompiledCommand."""
        if StatementSplitter.is_rem_line(stmt):
            self.expanded_program[(line_num, sub_index)] = self._COMMENT
            return
        upper = stmt.upper().strip()
        # Collect DATA values before compiling (DATA handler is a no-op at runtime)
        if self._DATA_RE.match(upper):
            from .data_commands import DataCommands
            args = stmt.strip()[4:]  # DATA"A" (crunched) works too
            values = DataCommands.parse_data_values(args)
            if values:
                self.data_values.setdefault(line_num, []).extend(values)
        # Multi-line IF: pre-parse the condition expression
        if upper.startswith('IF ') and upper.endswith('THEN'):
            condition_str = stmt.strip()[3:]  # Remove 'IF '
            condition_str = condition_str[:condition_str.upper().rfind('THEN')].strip()
            if condition_str:
                try:
                    condition_ast = self.ast_parser.parse_expression(condition_str)
                    self.expanded_program[(line_num, sub_index)] = CompiledMultiLineIf(condition_ast)
                    return
                except (ValueError, IndexError, KeyError, AttributeError):
                    pass  # Fall through to store as string
            self.expanded_program[(line_num, sub_index)] = stmt
            return
        # File I/O must stay as text — AST parser silently drops '#'
        if self._is_file_io(upper):
            self.expanded_program[(line_num, sub_index)] = stmt
            return
        # Try to pre-parse as AST; returns None for registry commands,
        # unknown identifiers, and anything else the parser can't handle
        node = self.ast_parser.try_parse_statement(stmt)
        if node is not None:
            self.expanded_program[(line_num, sub_index)] = node
            return
        # Try to pre-compile as a registry command
        compiled = self._try_compile_command(stmt, upper)
        self.expanded_program[(line_num, sub_index)] = compiled if compiled else stmt

    # PRINT#/INPUT# with any whitespace before the '#' (a '#' inside a
    # quoted string, as in PRINT "#", is not a file number)
    _FILE_IO_RE = re.compile(r'^(?:PRINT|INPUT)\s*#')
    # LINE INPUT with any spacing between the two words
    _LINE_INPUT_RE = re.compile(r'^\s*LINE\s+INPUT(?![A-Z0-9_$])', re.IGNORECASE)
    # DATA as a whole keyword (also crunched: DATA"A",1)
    _DATA_RE = re.compile(r'^DATA(?![A-Z0-9_$])', re.IGNORECASE)

    @classmethod
    def _is_file_io(cls, upper):
        """Check if a statement is a file I/O command that must bypass AST."""
        return bool(cls._LINE_INPUT_RE.match(upper) or cls._FILE_IO_RE.match(upper))

    def _try_compile_command(self, stmt, upper=None):
        """Pre-resolve a statement to a CompiledCommand, or return None."""
        if upper is None:
            upper = stmt.upper().strip()
        # File I/O intercepts must go through process_statement
        if self._is_file_io(upper):
            return None
        tokens = CommandRegistry.tokenize_command(stmt.strip())
        if not tokens:
            return None
        cmd_name = tokens[0].upper()
        handler = self.command_registry.get_handler(cmd_name)
        if handler:
            args = stmt.strip()[len(tokens[0]):].strip()
            return CompiledCommand(handler, args, keyword=cmd_name)
        return None

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
        if StatementSplitter.is_rem_line(code):
            return self.process_statement(code)

        # Lines containing control structures (IF/FOR/WHILE/DO anywhere) run
        # as a temporary one-line program so loops and IF blocks work
        statements = expand_statements(code, self.command_words)
        if any(starts_control_structure(s) for s in statements):
            if len(statements) > 1:
                return self._execute_converted_as_temporary_program(statements)
            return self.process_statement(statements[0])

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

    # Line number used for an immediate-mode line that needs the executor
    IMMEDIATE_LINE = -1

    def _execute_converted_as_temporary_program(self, converted_statements):
        """Run an immediate-mode line that contains control structures.

        Its statements are added to the program as line -1 (which sorts
        before every real line), followed by END, and run in place. So a
        jump into the program works (GOTO 100 or IF X THEN GOTO 100 from
        the prompt continues the stored program at line 100, as on the
        CoCo), and a pending INPUT can be resumed. Line -1 is removed as
        soon as execution finishes (see finish_immediate_line).
        """
        if not converted_statements:
            return []

        self.store_program_line(self.IMMEDIATE_LINE, '')
        self.program[self.IMMEDIATE_LINE] = ': '.join(converted_statements)
        for i, statement in enumerate(list(converted_statements) + ['END']):
            self._store_subline(self.IMMEDIATE_LINE, i, statement.strip())
        self.for_stack.clear()
        self.call_stack.clear()

        results = self.executor.run_program_from_line(self.IMMEDIATE_LINE, clear_variables=False)
        self.finish_immediate_line()
        return [item for item in results
                if not (isinstance(item, dict)
                        and (item.get('source') == 'system'
                             or item.get('type') in ('program_end', 'program_start')))]

    def finish_immediate_line(self):
        """Remove the temporary immediate-mode line once nothing is pending."""
        if (self.IMMEDIATE_LINE in self.program and not self.waiting_for_input
                and not self.waiting_for_pause_continuation):
            self.store_program_line(self.IMMEDIATE_LINE, '')

    def _try_ast_execute(self, code):
        """Try to execute a statement via AST. Returns None if not handled."""
        code_stripped = code.strip()
        if not code_stripped:
            return None

        code_upper = code_stripped.upper()
        parts = code_upper.split(None, 1)
        first_word = parts[0] if parts else ''

        # Validate IF statements require a THEN (or GOTO) keyword — outside
        # quotes: IF A$="THEN" is still missing one
        if (first_word == 'IF' and find_keyword(code_stripped, 'THEN') < 0
                and find_keyword(code_stripped, 'GOTO') < 0):
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

        from .ast_parser import RegistryCommandError
        try:
            ast_node = self.ast_parser.parse_statement(code_stripped, self.current_line)
        except RegistryCommandError:
            return None  # Not an AST-handled statement
        except (ValueError, IndexError, KeyError, AttributeError) as e:
            # Genuine parse error in an AST-handled statement
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
            return None

        try:
            result = self.ast_evaluator.visit(ast_node)
            # Ensure result is a list (statement results must be List[Dict])
            if not isinstance(result, list):
                return None
            return result
        except BASIC_RUNTIME_ERRORS as e:
            # A runtime error (BAD SUBSCRIPT, TYPE MISMATCH, ...), not a syntax error
            if str(e):
                error = self.error_context.wrapped_error(
                    "", e, self.current_line,
                    suggestions=[
                        f'Check the values used in {first_word}',
                        'Use HELP to see command syntax',
                    ]
                )
                return error_response(error)
            return None

    def process_statement(self, code):
        """Execute a single BASIC statement. Dispatch order:

        1. Multi-line IF (bare 'IF cond THEN') — can't be AST-parsed
        2. File I/O intercepts (PRINT#, INPUT#, LINE INPUT) — AST doesn't handle '#'
        3. AST execution — everything not in the CommandRegistry
        4. CommandRegistry — NEXT, WEND, LOOP, DIM, SOUND, etc.
        """
        if not code.strip() or StatementSplitter.is_rem_line(code):
            return []

        # Handle multi-line IF (bare "IF condition THEN" without action)
        code_upper = code.strip().upper()
        if code_upper.startswith('IF ') and code_upper.endswith('THEN'):
            condition = code.strip()[3:]  # Remove 'IF '
            condition = condition[:condition.upper().rfind('THEN')].strip()
            if condition:
                try:
                    condition_result = self.evaluate_condition(condition)
                except (ValueError, IndexError, KeyError, AttributeError, TypeError) as e:
                    return error_response(self.error_context.syntax_error(
                        f"Invalid IF condition: {condition} ({e})",
                        self.current_line,
                        suggestions=['Example: IF X = 5 THEN',
                                     'Conditions compare two values: =, <>, <, >, <=, >=',
                                     'Check for a missing operand after the operator']))
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
        m = self._LINE_INPUT_RE.match(code.strip())
        if m:
            return self.file_io.execute_line_input(code.strip()[m.end():].lstrip())
        if self._FILE_IO_RE.match(code_upper):
            rest = code.strip()[5:].lstrip()[1:]  # drop keyword and '#'
            if code_upper.startswith('PRINT'):
                return self.file_io.execute_print_file(rest)
            return self.file_io.execute_input_file(rest)

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
        """Evaluate a BASIC expression string using the AST parser.
        Caches parsed AST nodes so repeated expressions (e.g. in loops)
        skip the tokenizer and parser on subsequent calls."""
        expr = expr.strip()
        if not expr:
            error = self.error_context.syntax_error("Empty expression", line or self.current_line)
            raise ValueError(error.format_message())
        try:
            ast_node = self._expr_cache.get(expr)
            if ast_node is None:
                ast_node = self.ast_parser.parse_expression(expr, line or self.current_line)
                self._expr_cache[expr] = ast_node
            return self.ast_evaluator.visit(ast_node)
        except ValueError:
            raise
        except BASIC_RUNTIME_ERRORS as e:
            raise ValueError(str(e))

    def eval_int(self, expr, line=None):
        """Evaluate an expression and return an integer (TYPE MISMATCH for a string)."""
        value = self.evaluate_expression(expr, line)
        if isinstance(value, str):
            raise ValueError(f"TYPE MISMATCH: {expr.strip()} is a string; a number is needed here")
        return int(value)

    def read_array_element(self, array_name, indices):
        """Read an array element given already-evaluated integer indices."""
        value, error_msg = self.variable_manager.get_array_element(array_name, indices)
        if error_msg:
            error = self.error_context.runtime_error(
                error_msg,
                suggestions=["Check that array indices are within bounds",
                             "Arrays used without DIM hold indices 0-10"]
            )
            raise ValueError(error.format_detailed())

        return value

    def evaluate_condition(self, condition):
        """Evaluate a condition string using the AST parser.

        Parse and runtime errors propagate to the caller: a malformed or
        failing condition must be reported, never silently read as false.
        """
        condition = condition.strip()
        ast_node = self._expr_cache.get(condition)
        if ast_node is None:
            ast_node = self.ast_parser.parse_expression(condition, self.current_line)
            self._expr_cache[condition] = ast_node
        return basic_truthy(self.ast_evaluator.visit(ast_node))
    
    def execute_sound(self, args):
        # SOUND frequency,duration
        self.error_context.set_context(self.current_line, f"SOUND {args}")
        
        parts = StatementSplitter.split_args(args)
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
            error = self.error_context.wrapped_error(
                "Invalid SOUND parameters: ", e,
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
                self.rng.seed(seed)
            except (ValueError, TypeError) as e:
                error = self.error_context.wrapped_error(
                    "Invalid RANDOMIZE seed: ", e,
                    self.current_line,
                    suggestions=["RANDOMIZE requires a numeric seed",
                                 "Example: RANDOMIZE 42"])
                return error_response(error)
        else:
            self.rng.seed()
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
                
            # Inside a program, the executor's pause handler saves the resume
            # point and sets waiting_for_pause_continuation.
            return [{'type': 'pause', 'duration': pause_time}]
            
        except (ValueError, TypeError) as e:
            # Return proper error without masking the exception
            error = self.error_context.wrapped_error(
                "PAUSE command error: ", e,
                self.current_line,
                suggestions=["PAUSE requires a numeric duration",
                             "Example: PAUSE 1000"])
            return error_response(error)
    
    def store_input_value(self, var_desc, value):
        """Store a user-entered value into the appropriate variable or array element.

        var_desc is a dict with 'name', 'array', and optionally 'indices'.
        For backwards compatibility, var_desc may also be a plain string (variable name).

        Returns None on success, or an error message (e.g. "BAD SUBSCRIPT")
        that the caller must report.
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

        # Convert value to appropriate type (numbers parse like VAL)
        if var_name.endswith('$'):
            typed_value = str(value)
        else:
            try:
                typed_value = basic_number_prefix(str(value))
            except OverflowError:
                typed_value = 0

        if is_array and indices is not None:
            return self.variable_manager.set_array_element(var_name, indices, typed_value)
        self.variables[var_name] = typed_value
        return None

    def clear_all_stacks(self):
        """Clear all control-flow stacks."""
        self.for_stack.clear()
        self.call_stack.clear()
        self.local_stack.clear()
        self.if_stack.clear()
        self.while_stack.clear()
        self.do_stack.clear()

    def clear_input_state(self):
        """Clear multi-variable INPUT state."""
        self.input_variables = None
        self.input_prompt = None
        self.current_input_index = 0

    def clear_interpreter_state(self, clear_program=True):
        """Clear interpreter state - shared function for NEW, LOAD, and other commands"""
        if clear_program:
            self.program.clear()
            self.expanded_program.clear()
            self.data_values.clear()
            self.labels.clear()

        self.variables.clear()
        self.arrays.clear()  # Clear all dimensioned arrays
        self.clear_all_stacks()
        self.data_statements.clear()
        self.data_pointer = 0
        self.running = False
        self.waiting_for_input = False
        self.waiting_for_pause_continuation = False
        self.program_counter = None
        self.graphics.clear_pixel_buffer()
        self.stopped_position = None  # Clear stopped position
        self.break_requested = False

        # Reset TIMER (trace_mode intentionally NOT reset — persists across RUN like real CoCo)
        self.timer_epoch = time.time()

        # Clear ON ERROR GOTO state
        self.on_error_goto_line = None
        self.error_number = 0
        self.error_line = 0
        self.error_resume_position = None
        self.in_error_handler = False

        # Clear multi-variable INPUT state
        self.clear_input_state()
        self.current_line = 0
        self.current_sub_line = 0
        self.iteration_count = 0
        self.keyboard_buffer.clear()
        self.graphics_mode = None  # No PMODE yet: graphics off
        self.screen_mode = 1  # Reset screen/color mode
        self.current_draw_color = 1  # Reset drawing color
        self.turtle_x = 64  # Reset turtle to center
        self.turtle_y = 48
        self.print_column = 0  # Reset print cursor

    def execute_new(self):
        """NEW command - clear program and variables"""
        self.clear_interpreter_state(clear_program=True)
        self.file_io.close_all()
        self.trace_mode = False
        return text_response('READY')
    
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

    def _register_all_commands(self):
        """Register all BASIC commands by delegating to each module."""
        self.graphics.register_commands(self.command_registry)
        self.variable_manager.register_commands(self.command_registry)
        self.file_io.register_commands(self.command_registry)
        self.control_flow.register_commands(self.command_registry)
        self.data_commands.register_commands(self.command_registry)

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
                                     syntax="RENUM [new_start],[old_start],[increment]",
                                     examples=["RENUM", "RENUM 100", "RENUM 1000,500", "RENUM 100,,5"])
        
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
        
        self.command_registry.register('MERGE', self.merge_program,
                                     category='system',
                                     description="Merge program lines from a file into current program",
                                     syntax='MERGE "filename"',
                                     examples=['MERGE "SUBS"', 'MERGE "library.bas"'])

        self.command_registry.register('CHAIN', self.chain_program,
                                     category='system',
                                     description="Load and run another program",
                                     syntax='CHAIN "filename" [, ALL] [, line_number]',
                                     examples=['CHAIN "GAME"', 'CHAIN "PART2", ALL',
                                               'CHAIN "MAIN", ALL, 1000'])

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
            output.append(text_message(line))
        
        return output
    

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
                        self.store_program_line(line_num, '')
                        lines_deleted += 1
                
                if lines_deleted == 0:
                    return text_response('NO LINES DELETED')
                else:
                    return text_response(f'DELETED {lines_deleted} LINE(S)')
                    
            else:
                # Single line format: DELETE line_number
                line_num = int(args)
                
                if line_num in self.program:
                    self.store_program_line(line_num, '')
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
                suggestions=["Check that the specified line numbers exist",
                             "Example: DELETE 100-200"])
            return error_response(error)

    def execute_renum(self, args):
        """RENUM statement - renumber program lines"""
        # Extended Color BASIC order: RENUM [new_start],[old_start],[increment]
        # Defaults: new_start=10, old_start=first line, increment=10

        new_start = 10
        increment = 10
        old_start = None

        if args.strip():
            parts = [p.strip() for p in StatementSplitter.split_args(args, keep_empty=True)]
            try:
                if len(parts) > 3:
                    raise ValueError('too many arguments')
                if parts[0]:
                    new_start = int(parts[0])
                if len(parts) >= 2 and parts[1]:
                    old_start = int(parts[1])
                if len(parts) >= 3 and parts[2]:
                    increment = int(parts[2])
            except ValueError:
                error = self.error_context.syntax_error(
                    "Invalid line number in RENUM command",
                    self.current_line,
                    suggestions=[
                        'RENUM new_start,old_start,increment (any may be left empty)',
                        'Example: RENUM 100,,10',
                        'Line numbers must be integers'
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
                    'Example: RENUM 10,,10 (increment of 10)',
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
            line_mapping[old_line] = current_new
            current_new += increment

        # Check for conflicts with existing lines not being renumbered
        unchanged_lines = set(self.program.keys()) - set(old_lines)
        new_lines = set(line_mapping.values())
        conflicts = unchanged_lines & new_lines
        # Renumbering must not change the order in which lines run
        order_before = sorted(self.program.keys())
        order_after = sorted(order_before, key=lambda n: line_mapping.get(n, n))
        if not conflicts and order_after != order_before:
            error = self.error_context.runtime_error(
                "RENUM WOULD REORDER PROGRAM LINES",
                self.current_line,
                suggestions=["Choose a new start line above the last unchanged line",
                             "Renumber the whole program with RENUM new,increment",
                             "Example: RENUM 100,10"])
            return error_response(error)
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
        
        # Replace the program and recompile it from scratch (sublines,
        # DATA values and labels are all keyed by line number)
        self.program = {}
        self.expanded_program = {}
        self.data_values = {}
        self.labels = {}
        for line_num in sorted(new_program):
            self.store_program_line(line_num, new_program[line_num])
        
        return text_response(f'RENUMBERED {len(line_mapping)} LINES')

    # A jump keyword and the line number(s) after it. GOTO/GOSUB may take a
    # comma list (ON X GOTO 10,20,30); the others take one number.
    _LINE_REF_RE = re.compile(r'(GOTO|GOSUB|THEN|ELSE|RESTORE|RESUME)(\s*)(\d+(?:\s*,\s*\d+)*)',
                              re.IGNORECASE)

    @classmethod
    def _update_line_references(cls, code, line_mapping):
        """Renumber line-number targets in one line of code.

        Scans the text so that quoted strings and comments are never
        touched (PRINT "GOTO 10" stays as it is), and crunched targets
        (GOTO10, IFX=1THEN20) are handled.
        """
        def renumber(match):
            return str(line_mapping.get(int(match.group(0)), int(match.group(0))))

        out = []
        i, in_quotes, statement_start = 0, False, True
        while i < len(code):
            char = code[i]
            if char == '"':
                in_quotes = not in_quotes
                statement_start = False
            elif not in_quotes:
                if char == "'" or (statement_start and code[i:i + 3].upper() == 'REM'):
                    out.append(code[i:])  # the rest of the line is a comment
                    break
                if char == ':':
                    statement_start = True
                elif not char.isspace():
                    statement_start = False
                    match = None if i and code[i - 1].isalpha() else cls._LINE_REF_RE.match(code, i)
                    if match:
                        keyword, space, numbers = match.groups()
                        if keyword.upper() not in ('GOTO', 'GOSUB'):
                            numbers = re.match(r'\d+', numbers).group(0)
                        out.append(keyword + space + re.sub(r'\d+', renumber, numbers))
                        i = match.start() + len(keyword) + len(space) + len(numbers)
                        continue
            out.append(char)
            i += 1
        return ''.join(out)

    def execute_safety(self, args):
        """SAFETY statement - enable or disable iteration safety limits"""
        args = args.strip().upper()
        
        if not args:
            # Show current status
            status = "ON" if self.safety_enabled else "OFF"
            return text_response(f'SAFETY IS {status}')
        
        if args == 'ON':
            self.safety_enabled = True
            logger.info('SAFETY ON - iteration limits enabled')
            return text_response('SAFETY ON - ITERATION LIMITS ENABLED')
        elif args == 'OFF':
            self.safety_enabled = False
            logger.info('SAFETY OFF - iteration limits disabled (hard cap: %s)',
                        f'{self.max_absolute_iterations:,}')
            return [text_message('SAFETY OFF - ITERATION LIMITS DISABLED'),
                    text_message(f'(HARD CAP AT {self.max_absolute_iterations:,} ITERATIONS STILL ACTIVE)')]
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

