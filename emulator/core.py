"""
Core TRS-80 Color Computer BASIC Emulator

This module contains the main CoCoBasic class that implements the BASIC interpreter.
The class has been extracted from the monolithic app.py file to improve maintainability.
"""

import re
from .parser import BasicParser
from .graphics import BasicGraphics
from .variables import VariableManager
from .io import IOHandler
from .commands import CommandRegistry
from .expressions import ExpressionEvaluator
from .output_manager import StreamingOutputManager, LegacyOutputAdapter, OutputType
from .error_context import ErrorContextManager

class CoCoBasic:
    def __init__(self, output_callback=None, debug_mode=False):
        self.program = {}  # Line number -> code (original for LIST display)
        self.expanded_program = {}  # (line_num, sub_index) -> statement (for execution)
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
        self.safety_enabled = True  # Enable/disable iteration safety
        self.waiting_for_input = False  # Flag to indicate we're waiting for user input
        self.waiting_for_pause_continuation = False  # Flag for pause continuation
        self.pause_duration = 0  # Duration of current pause
        self.program_counter = None  # For resuming execution after input
        self.stopped_position = None  # For CONT command - stores (line, sub_line) where STOP occurred
        
        # Multi-variable INPUT state
        self.input_variables = None  # List of variables waiting for input
        self.input_prompt = None     # Prompt text for multi-variable input
        self.current_input_index = 0 # Current variable index being input
        self.arrays = {}  # Storage for dimensioned arrays
        self.keyboard_buffer = []  # Buffer for INKEY$ function
        self.current_draw_color = 1  # Default drawing color
        self.turtle_x = 64  # Turtle graphics X position (center of default screen)
        self.turtle_y = 48  # Turtle graphics Y position (center of default screen)
        
        # Initialize graphics, variables, and I/O modules
        self.graphics = BasicGraphics(self)
        self.variable_manager = VariableManager(self)
        self.io_handler = IOHandler(self)
        
        # Initialize expression evaluator
        self.expression_evaluator = ExpressionEvaluator(self)

        # AST-based execution: commands in this set use AST parse+visit instead of registry
        self._ast_migrated_commands = {'END', 'GOTO', 'LET', 'PRINT', 'GOSUB', 'RETURN'}
        self._ast_evaluator = None  # Lazy-initialized ASTEvaluator

        # Initialize command registry
        self.command_registry = CommandRegistry()
        self._register_all_commands()
    
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
    
    @property 
    def key_buffer(self):
        """Compatibility property for tests"""
        return self.keyboard_buffer
    
    @key_buffer.setter
    def key_buffer(self, value):
        """Compatibility property for tests"""
        self.keyboard_buffer = value
        
    def get_reserved_function_names(self):
        """Return list of reserved function names that cannot be used as variable/array names"""
        return ['LEFT$', 'RIGHT$', 'MID$', 'LEN', 'ABS', 'INT', 'RND', 'SQR', 
                'SIN', 'COS', 'TAN', 'ATN', 'EXP', 'LOG', 'CHR$', 'ASC', 'STR$', 'VAL', 'INKEY$']
        
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
                # Remove from expanded program
                keys_to_remove = [key for key in self.expanded_program.keys() if key[0] == line_num]
                for key in keys_to_remove:
                    del self.expanded_program[key]
            return [{'type': 'text', 'text': 'OK'}]
        
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
        return [{'type': 'text', 'text': 'OK'}]
    
    def clear_variables(self, args):
        """BASIC CLEAR command - clears variables, optionally sets string space"""
        # Parse optional string space argument
        args = args.strip()
        if args:
            try:
                string_space = int(self.evaluate_expression(args))
                # In TRS-80 BASIC, this would set string space
                # For our implementation, we'll just acknowledge it
                self.variable_manager.clear_variables()
                return [{'type': 'text', 'text': f'OK'}]
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
                return [{'type': 'error', 'message': error.format_detailed()}]
        else:
            # CLEAR with no arguments - just clear variables
            self.variable_manager.clear_variables()
            return [{'type': 'text', 'text': 'OK'}]
    
    def load_program(self, filename):
        """Load a BASIC program from a file"""
        import os
        
        # Parse filename - handle quotes
        filename = filename.strip()
        if filename.startswith('"') and filename.endswith('"'):
            filename = filename[1:-1]
        elif filename.startswith("'") and filename.endswith("'"):
            filename = filename[1:-1]
        
        if not filename:
            error = self.error_context.syntax_error(
                "SYNTAX ERROR: Filename required",
                self.current_line,
                suggestions=[
                    "Provide a filename to load",
                    'Example: LOAD "MYGAME"', 
                    'File extension .bas will be added automatically'
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
        
        # Add .bas extension if not present
        if not filename.lower().endswith('.bas'):
            filename += '.bas'
        
        try:
            original_filename = filename
            
            # Search order: current dir -> programs/ -> project root
            search_paths = [
                filename,  # Current directory
                os.path.join('programs', filename),  # programs subdirectory
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), filename),  # project root
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'programs', filename)  # project root/programs
            ]
            
            found_file = None
            for path in search_paths:
                if os.path.exists(path):
                    found_file = path
                    break
            
            if not found_file:
                error = self.error_context.file_error(
                    f"FILE NOT FOUND: {os.path.basename(original_filename)}",
                    original_filename,
                    "LOAD"
                )
                return [{'type': 'error', 'message': error.format_detailed()}]
            
            filename = found_file
            
            # Clear current program and interpreter state
            self.clear_interpreter_state(clear_program=True)
            
            # Load and parse the file
            with open(filename, 'r') as f:
                lines_loaded = 0
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):  # Skip empty lines and comments
                        # Parse each line as if it were entered directly
                        line_num, code = self.parse_line(line)
                        if line_num is not None:
                            if code:
                                self.program[line_num] = code
                                self.expand_line_to_sublines(line_num, code)
                                lines_loaded += 1
                            # Skip lines that are just line numbers with no code
                        else:
                            # Handle lines without line numbers - treat as comments or ignore
                            pass
            
            return [{'type': 'text', 'text': f'LOADED {lines_loaded} LINES FROM {os.path.basename(filename)}'}]
            
        except FileNotFoundError:
            error = self.error_context.file_error(
                f"FILE NOT FOUND: {os.path.basename(filename)}",
                filename,
                "LOAD"
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
        except PermissionError:
            error = self.error_context.file_error(
                f"PERMISSION DENIED: {os.path.basename(filename)}",
                filename, 
                "LOAD"
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
        except Exception as e:
            error = self.error_context.file_error(
                f"LOAD ERROR: {str(e)}",
                filename,
                "LOAD"
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
    
    def save_program(self, filename):
        """Save the current BASIC program to a file"""
        import os
        
        # Parse filename - handle quotes
        filename = filename.strip()
        if filename.startswith('"') and filename.endswith('"'):
            filename = filename[1:-1]
        elif filename.startswith("'") and filename.endswith("'"):
            filename = filename[1:-1]
        
        if not filename:
            error = self.error_context.syntax_error(
                "SYNTAX ERROR: Filename required",
                self.current_line,
                suggestions=[
                    "Provide a filename to save",
                    'Example: SAVE "MYGAME"', 
                    'File extension .bas will be added automatically'
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
        
        # Check if there's a program to save
        if not self.program:
            error = self.error_context.runtime_error(
                "NO PROGRAM TO SAVE",
                suggestions=[
                    "Enter a program first using line numbers",
                    'Example: 10 PRINT "HELLO"',
                    'Use LIST command to see current program'
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
        
        # Add .bas extension if not present
        if not filename.lower().endswith('.bas'):
            filename += '.bas'
        
        try:
            # Create programs directory if it doesn't exist
            os.makedirs('programs', exist_ok=True)
            
            # Default save location is programs directory
            if not os.path.dirname(filename):
                filename = os.path.join('programs', filename)
            
            # Sort program lines by line number for proper output
            sorted_lines = sorted(self.program.items())
            
            # Write program to file
            with open(filename, 'w') as f:
                for line_num, code in sorted_lines:
                    f.write(f"{line_num} {code}\n")
            
            lines_saved = len(sorted_lines)
            return [{'type': 'text', 'text': f'SAVED {lines_saved} LINES TO {os.path.basename(filename)}'}]
            
        except PermissionError:
            error = self.error_context.file_error(
                f"PERMISSION DENIED: {os.path.basename(filename)}",
                filename,
                "SAVE"
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
        except OSError as e:
            error = self.error_context.file_error(
                f"SAVE ERROR: {str(e)}",
                filename,
                "SAVE"
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
        except Exception as e:
            error = self.error_context.file_error(
                f"SAVE ERROR: {str(e)}",
                filename,
                "SAVE"
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
    
    def dir_command(self, args=None):
        """DIR command - List available BASIC program files"""
        import os
        import glob
        
        # Get project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Search directories - use absolute paths to avoid duplicates
        search_dirs = [
            os.getcwd(),                           # Current directory
            os.path.join(os.getcwd(), 'programs')  # Programs subdirectory from current dir
        ]
        
        # Add project programs directory if different from above
        project_programs = os.path.join(project_root, 'programs')
        
        # Convert to absolute paths and remove duplicates
        search_dirs = list(dict.fromkeys([os.path.abspath(d) for d in search_dirs + [project_programs] if os.path.exists(d)]))
        
        output = []
        output.append({'type': 'text', 'text': 'BASIC PROGRAM FILES:'})
        output.append({'type': 'text', 'text': '=' * 40})
        
        total_files = 0
        
        for directory in search_dirs:
            if not os.path.exists(directory):
                continue
                
            # Find .bas files in this directory
            pattern = os.path.join(directory, "*.bas")
            files = glob.glob(pattern)
            
            if files:
                # Display directory header based on absolute path
                cwd = os.getcwd()
                if directory == cwd:
                    dir_name = "CURRENT DIRECTORY"
                elif directory == os.path.join(cwd, 'programs'):
                    dir_name = "PROGRAMS/"
                elif directory.endswith('programs'):
                    # This is a programs directory from elsewhere (like project root)
                    if directory != os.path.join(cwd, 'programs'):
                        dir_name = "PROJECT PROGRAMS/"
                    else:
                        dir_name = "PROGRAMS/"
                else:
                    dir_name = f"{os.path.basename(directory)}/"
                    
                output.append({'type': 'text', 'text': f"\n{dir_name}:"})
                
                # Sort files and display
                files.sort()
                for file_path in files:
                    filename = os.path.basename(file_path)
                    try:
                        # Get file size
                        size = os.path.getsize(file_path)
                        size_str = f"{size:>6} bytes"
                        
                        # Get modification time
                        import time
                        mtime = os.path.getmtime(file_path)
                        time_str = time.strftime("%m/%d/%y %H:%M", time.localtime(mtime))
                        
                        output.append({'type': 'text', 'text': f"  {filename:<20} {size_str} {time_str}"})
                        total_files += 1
                    except OSError:
                        # If we can't get file info, just show the name
                        output.append({'type': 'text', 'text': f"  {filename}"})
                        total_files += 1
        
        if total_files == 0:
            output.append({'type': 'text', 'text': '\nNO .BAS FILES FOUND'})
            output.append({'type': 'text', 'text': 'Use SAVE "filename" to create programs'})
        else:
            output.append({'type': 'text', 'text': f'\nTOTAL: {total_files} FILE(S)'})
            output.append({'type': 'text', 'text': 'Use LOAD "filename" to load a program'})
        
        # Add empty line so prompt appears on new line
        output.append({'type': 'text', 'text': ''})
        
        return output
    
    def files_command(self, args=None):
        """FILES command - Reserve file buffers (no-op in modern implementation)"""
        # In authentic Disk BASIC, FILES reserved memory for file buffers
        # With our modern backend, this is unnecessary
        # We accept the command for compatibility but do nothing
        
        # Parse arguments if provided (e.g., FILES 4 or FILES 8,256)
        # but ignore them since we don't need to reserve buffers
        
        return [{'type': 'text', 'text': 'OK'}]
    
    def drive_command(self, args=None):
        """DRIVE command - Set default drive (no-op in modern implementation)"""
        # In authentic Disk BASIC, DRIVE set the default drive number (0-3)
        # With our modern filesystem backend, this is unnecessary
        # We accept the command for compatibility but do nothing
        
        # Parse drive number if provided (e.g., DRIVE 0)
        # but ignore it since we use filesystem paths directly
        
        return [{'type': 'text', 'text': 'OK'}]
    
    def kill_file(self, filename):
        """Delete a BASIC program file with confirmation"""
        import os
        
        # Parse filename - handle quotes
        filename = filename.strip()
        if filename.startswith('"') and filename.endswith('"'):
            filename = filename[1:-1]
        elif filename.startswith("'") and filename.endswith("'"):
            filename = filename[1:-1]
        
        if not filename:
            error = self.error_context.syntax_error(
                "SYNTAX ERROR: Filename required",
                self.current_line,
                suggestions=[
                    "Provide a filename to delete",
                    'Example: KILL "OLDGAME"', 
                    'File extension .bas will be added automatically'
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
        
        # Add .bas extension if not present
        if not filename.lower().endswith('.bas'):
            filename += '.bas'
        
        try:
            # Search for the file in the same locations as LOAD
            search_paths = [
                filename,  # Current directory
                os.path.join('programs', filename),  # programs subdirectory
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), filename),  # project root
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'programs', filename)  # project root/programs
            ]
            
            found_file = None
            for path in search_paths:
                if os.path.exists(path):
                    found_file = path
                    break
            
            if not found_file:
                error = self.error_context.file_error(
                    f"FILE NOT FOUND: {os.path.basename(filename)}",
                    filename,
                    "KILL"
                )
                return [{'type': 'error', 'message': error.format_detailed()}]
            
            # For safety, we'll implement a simple confirmation through the CLI
            # The CLI client will handle the confirmation prompt
            output = []
            output.append({'type': 'text', 'text': f'DELETE {os.path.basename(found_file)}? (Y/N)'})
            output.append({'type': 'input_request', 'prompt': '? ', 'variable': '_kill_confirm', 'filename': found_file})
            
            return output
            
        except Exception as e:
            error = self.error_context.file_error(
                f"KILL ERROR: {str(e)}",
                filename,
                "KILL"
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
    
    def process_kill_confirmation(self, response, filename):
        """Process the confirmation response for KILL command"""
        import os
        
        response = response.strip().upper()
        
        if response in ['Y', 'YES']:
            try:
                os.remove(filename)
                return [{'type': 'text', 'text': f'DELETED {os.path.basename(filename)}'}]
            except PermissionError:
                error = self.error_context.file_error(
                    f"PERMISSION DENIED: {os.path.basename(filename)}",
                    filename,
                    "KILL"
                )
                return [{'type': 'error', 'message': error.format_detailed()}]
            except Exception as e:
                error = self.error_context.file_error(
                    f"DELETE ERROR: {str(e)}",
                    filename,
                    "KILL"
                )
                return [{'type': 'error', 'message': error.format_detailed()}]
        else:
            return [{'type': 'text', 'text': 'DELETE CANCELLED'}]
    
    def change_directory(self, path):
        """Change current working directory"""
        import os
        
        # Parse path - handle quotes
        path = path.strip()
        if path.startswith('"') and path.endswith('"'):
            path = path[1:-1]
        elif path.startswith("'") and path.endswith("'"):
            path = path[1:-1]
        
        # If no path provided, show current directory
        if not path:
            current_dir = os.getcwd()
            return [{'type': 'text', 'text': f'CURRENT DIRECTORY: {current_dir}'}]
        
        try:
            # Special handling for common shortcuts
            if path == "..":
                path = os.path.dirname(os.getcwd())
            elif path == "~":
                path = os.path.expanduser("~")
            elif path == "/":
                path = "/"
            elif path.startswith("~/"):
                path = os.path.expanduser(path)
            
            # Change to the directory
            old_dir = os.getcwd()
            os.chdir(path)
            new_dir = os.getcwd()
            
            return [{'type': 'text', 'text': f'CHANGED FROM {old_dir}'}] + \
                   [{'type': 'text', 'text': f'TO {new_dir}'}]
            
        except FileNotFoundError:
            error = self.error_context.file_error(
                f"DIRECTORY NOT FOUND: {path}",
                path,
                "CD"
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
        except PermissionError:
            error = self.error_context.file_error(
                f"PERMISSION DENIED: {path}",
                path,
                "CD"
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
        except OSError as e:
            error = self.error_context.file_error(
                f"CD ERROR: {str(e)}",
                path,
                "CD"
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
        except Exception as e:
            error = self.error_context.file_error(
                f"CD ERROR: {str(e)}",
                path,
                "CD"
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
    
    def expand_line_to_sublines(self, line_num, code):
        """Expand line using BasicParser or AST converter for single-line control structures"""
        # Check if this is a single-line control structure that should use AST conversion
        control_keywords = ['IF', 'FOR', 'WHILE', 'DO']
        has_control = any(keyword in code.upper() for keyword in control_keywords)
        has_colons = ':' in code
        is_if_statement = code.upper().strip().startswith('IF ')

        # Use AST conversion for control structures with colons OR IF statements (even without colons)
        if (has_control and has_colons) or is_if_statement:
            # Try AST conversion for single-line control structures
            try:
                from .ast_converter import parse_and_convert_single_line
                converted = parse_and_convert_single_line(code, self.expression_evaluator.ast_parser)

                if converted:
                    # Add converted statements as sublines
                    for i, statement in enumerate(converted):
                        if statement.strip():
                            self.expanded_program[(line_num, i)] = statement.strip()
                    return
            except Exception:
                # Fall back to BasicParser if AST conversion fails
                pass

        # Use BasicParser for normal statements
        return BasicParser.expand_line_to_sublines(line_num, code, self.expanded_program)

    def run_program(self, clear_variables=True):
        if not self.program:
            error = self.error_context.runtime_error(
                "NO PROGRAM",
                suggestions=[
                    "Enter a program first using line numbers",
                    'Example: 10 PRINT "HELLO"',
                    'Use LOAD "filename" to load a program from disk'
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]

        # Clear variables and arrays but keep program (like authentic BASIC)
        # For temporary execution, we may want to preserve variables
        if clear_variables:
            self.clear_interpreter_state(clear_program=False)

        output = []
        self.running = True

        # Pre-process DATA statements (already cleared by clear_interpreter_state above)
        preprocessing_running = self.running
        self.running = False  # Temporarily disable running flag for preprocessing
        for line_num in sorted(self.program.keys()):
            # Check if this line contains DATA statements
            line_code = self.program[line_num].strip().upper()
            if line_code.startswith('DATA '):
                # Process the DATA statement
                data_args = self.program[line_num][4:].strip()  # Remove 'DATA'
                self.current_line = line_num
                self.execute_data(data_args)
        self.running = preprocessing_running  # Restore running flag
        
        # Get all sub-line positions sorted by (line_num, sub_index)
        all_positions = sorted(self.expanded_program.keys())
        current_pos_index = 0
        
        while current_pos_index < len(all_positions) and self.running:
            # Safety check for infinite loops
            if self.safety_enabled:
                self.iteration_count += 1
                if self.iteration_count > self.max_iterations:
                    output.append({'type': 'error', 'message': 'PROGRAM STOPPED - TOO MANY ITERATIONS'})
                    self.running = False
                    break
            
            # Get current position and statement
            line_num, sub_index = all_positions[current_pos_index]
            self.current_line = line_num
            self.current_sub_line = sub_index
            statement = self.expanded_program[(line_num, sub_index)]
            
            # Execute the single statement (not multi-statement since we've already expanded)
            result = self.process_statement(statement)
            
            if result:
                # Check for INPUT and PAUSE requests first
                for item in result:
                    if item.get('type') == 'input_request':
                        # Save our position so we can resume
                        if current_pos_index + 1 < len(all_positions):
                            self.program_counter = all_positions[current_pos_index + 1]
                        else:
                            self.program_counter = None
                        self.waiting_for_input = True
                        self.running = False  # Pause execution
                        output.append(item)
                        return output  # Return immediately with input request
                    elif item.get('type') == 'pause':
                        # Save our position so we can resume after pause
                        if current_pos_index + 1 < len(all_positions):
                            self.program_counter = all_positions[current_pos_index + 1]
                        else:
                            self.program_counter = None
                        self.waiting_for_pause_continuation = True
                        self.running = False  # Pause execution
                        output.append(item)
                        return output  # Return immediately with pause request
                
                # Handle jump commands
                jumped = False
                for item in result:
                    if item.get('type') == 'jump':
                        target_line = item['line']
                        # Find the first sub-line of the target line
                        target_positions = [(ln, si) for ln, si in all_positions if ln == target_line]
                        if target_positions:
                            current_pos_index = all_positions.index(target_positions[0])
                            jumped = True
                            break
                        else:
                            output.append({'type': 'error', 'message': f'UNDEFINED LINE {target_line}'})
                            self.running = False
                            break
                    elif item.get('type') == 'jump_after_for':
                        # Jump to the sub-line after the FOR sub-line
                        for_line = item['for_line']
                        for_sub_line = item.get('for_sub_line', 0)
                        
                        # Find the exact FOR position using both line and sub_line
                        for_position = (for_line, for_sub_line)
                        if for_position in all_positions:
                            for_index = all_positions.index(for_position)
                            # Jump to the next sub-line (after the FOR)
                            current_pos_index = for_index + 1
                            jumped = True
                            break
                        else:
                            output.append({'type': 'error', 'message': f'UNDEFINED FOR LINE {for_line}'})
                            self.running = False
                            break
                    elif item.get('type') == 'jump_return':
                        # RETURN from GOSUB - jump to specific sub-line position
                        return_line = item['line']
                        return_sub_line = item['sub_line']
                        
                        # Find the position after the GOSUB call
                        return_positions = [(ln, si) for ln, si in all_positions if ln == return_line]
                        if return_positions:
                            # Find the sub-line that matches or is after the return_sub_line
                            for pos in return_positions:
                                if pos[1] > return_sub_line:
                                    current_pos_index = all_positions.index(pos)
                                    jumped = True
                                    break
                            else:
                                # If no later sub-line found, jump to next line
                                next_line_positions = [(ln, si) for ln, si in all_positions if ln > return_line]
                                if next_line_positions:
                                    current_pos_index = all_positions.index(next_line_positions[0])
                                    jumped = True
                        
                        if not jumped:
                            # If can't find return position, just continue
                            current_pos_index += 1
                            jumped = True
                        break
                    elif item.get('type') == 'skip_for_loop':
                        # Skip to after the matching NEXT for this variable
                        var_name = item['var']
                        # Find the matching NEXT statement
                        for pos_idx in range(current_pos_index + 1, len(all_positions)):
                            check_line, check_sub = all_positions[pos_idx]
                            check_statement = self.expanded_program.get((check_line, check_sub), '')
                            if check_statement.strip().startswith('NEXT'):
                                # Check if it's the matching NEXT (same variable or no variable)
                                next_parts = check_statement.strip().split()
                                if len(next_parts) == 1 or next_parts[1] == var_name:
                                    # Jump to the position after this NEXT
                                    current_pos_index = pos_idx + 1
                                    jumped = True
                                    break
                        if not jumped:
                            output.append({'type': 'error', 'message': f'FOR WITHOUT NEXT'})
                            self.running = False
                            break
                        break
                    elif item.get('type') == 'skip_while_loop':
                        # Skip to matching WEND
                        for pos_idx in range(current_pos_index + 1, len(all_positions)):
                            check_line, check_sub = all_positions[pos_idx]
                            check_statement = self.expanded_program.get((check_line, check_sub), '')
                            if check_statement.strip().upper().startswith('WEND'):
                                current_pos_index = pos_idx + 1
                                jumped = True
                                break
                        if not jumped:
                            output.append({'type': 'error', 'message': 'WHILE WITHOUT WEND'})
                            self.running = False
                            break
                        break
                    elif item.get('type') == 'jump_after_while':
                        # Jump back to after WHILE statement
                        while_line = item['while_line']
                        while_sub_line = item['while_sub_line']
                        while_position = (while_line, while_sub_line)
                        if while_position in all_positions:
                            while_index = all_positions.index(while_position)
                            current_pos_index = while_index + 1
                            jumped = True
                        break
                    elif item.get('type') == 'skip_do_loop':
                        # Skip to matching LOOP
                        for pos_idx in range(current_pos_index + 1, len(all_positions)):
                            check_line, check_sub = all_positions[pos_idx]
                            check_statement = self.expanded_program.get((check_line, check_sub), '')
                            if check_statement.strip().upper().startswith('LOOP'):
                                current_pos_index = pos_idx + 1
                                jumped = True
                                break
                        if not jumped:
                            output.append({'type': 'error', 'message': 'DO WITHOUT LOOP'})
                            self.running = False
                            break
                        break
                    elif item.get('type') == 'jump_after_do':
                        # Jump back to after DO statement
                        do_line = item['do_line']
                        do_sub_line = item['do_sub_line']
                        do_position = (do_line, do_sub_line)
                        if do_position in all_positions:
                            do_index = all_positions.index(do_position)
                            current_pos_index = do_index + 1
                            jumped = True
                        break
                    elif item.get('type') == 'exit_for_loop':
                        # Exit FOR loop - skip to after matching NEXT
                        if self.for_stack:
                            var_name = self.for_stack[-1]['var']
                            # First pop the for_stack since we're exiting
                            self.for_stack.pop()
                            for pos_idx in range(current_pos_index + 1, len(all_positions)):
                                check_line, check_sub = all_positions[pos_idx]
                                check_statement = self.expanded_program.get((check_line, check_sub), '')
                                if check_statement.strip().startswith('NEXT'):
                                    next_parts = check_statement.strip().split()
                                    if len(next_parts) == 1 or (len(next_parts) > 1 and next_parts[1] == var_name):
                                        current_pos_index = pos_idx + 1
                                        jumped = True
                                        break
                            if not jumped:
                                # Continue execution after current position
                                current_pos_index += 1
                                jumped = True
                        break
                    elif item.get('type') == 'skip_if_block':
                        # Skip to matching ELSE or ENDIF (handle nesting)
                        nest_level = 0
                        for pos_idx in range(current_pos_index + 1, len(all_positions)):
                            check_line, check_sub = all_positions[pos_idx]
                            check_statement = self.expanded_program.get((check_line, check_sub), '')
                            statement_upper = check_statement.strip().upper()
                            
                            if 'IF' in statement_upper and 'THEN' in statement_upper:
                                nest_level += 1
                            elif statement_upper.startswith('ELSE') and nest_level == 0:
                                current_pos_index = pos_idx
                                jumped = True
                                break
                            elif statement_upper.startswith('ENDIF'):
                                if nest_level == 0:
                                    current_pos_index = pos_idx + 1
                                    jumped = True
                                    break
                                else:
                                    nest_level -= 1
                        if not jumped:
                            output.append({'type': 'error', 'message': 'IF WITHOUT ENDIF'})
                            self.running = False
                            break
                        break
                    elif item.get('type') == 'skip_else_block':
                        # Skip to matching ENDIF (handle nesting)
                        nest_level = 0
                        for pos_idx in range(current_pos_index + 1, len(all_positions)):
                            check_line, check_sub = all_positions[pos_idx]
                            check_statement = self.expanded_program.get((check_line, check_sub), '')
                            statement_upper = check_statement.strip().upper()
                            
                            if 'IF' in statement_upper and 'THEN' in statement_upper:
                                nest_level += 1
                            elif statement_upper.startswith('ENDIF'):
                                if nest_level == 0:
                                    current_pos_index = pos_idx
                                    jumped = True
                                    break
                                else:
                                    nest_level -= 1
                        if not jumped:
                            output.append({'type': 'error', 'message': 'ELSE WITHOUT ENDIF'})
                            self.running = False
                            break
                        break
                    elif item.get('type') != 'input_request':  # Skip input_request as we handled it above
                        # During program execution, filter out "OK" messages
                        if not (item.get('type') == 'text' and item.get('text') == 'OK'):
                            output.append(item)
                            # Emit output immediately for real-time streaming
                            self.emit_output([item])
                        # Check if this is an error that should halt execution
                        if item.get('type') == 'error':
                            self.running = False
                            self.call_stack.clear()  # Clear call stack on error
                            self.for_stack.clear()   # Clear FOR stack on error
                            break
                
                if not jumped:
                    current_pos_index += 1
            else:
                current_pos_index += 1
        
        self.running = False
        return output
    
    def continue_program_execution(self):
        # Resume program execution after INPUT or PAUSE
        if not hasattr(self, 'program_counter') or self.program_counter is None:
            error = self.error_context.runtime_error(
                "No program to continue",
                suggestions=[
                    'A program must be running to use CONT',
                    'Run a program first with RUN',
                    'Use CONT only after STOP or error interruption'
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
        
        # Clear pause continuation state if that's why we're continuing
        if hasattr(self, 'waiting_for_pause_continuation') and self.waiting_for_pause_continuation:
            self.waiting_for_pause_continuation = False
        
        output = []
        self.running = True
        
        # Get all sub-line positions sorted by (line_num, sub_index)
        all_positions = sorted(self.expanded_program.keys())
        
        # Find the index of the current program counter position
        try:
            current_pos_index = all_positions.index(self.program_counter)
        except ValueError:
            # Current position not found, end program
            self.running = False
            self.program_counter = None
            return []
        
        while current_pos_index < len(all_positions) and self.running:
            # Safety check for infinite loops
            if self.safety_enabled:
                self.iteration_count += 1
                if self.iteration_count > self.max_iterations:
                    output.append({'type': 'error', 'message': 'PROGRAM STOPPED - TOO MANY ITERATIONS'})
                    self.running = False
                    break
            
            # Get current position and statement
            line_num, sub_index = all_positions[current_pos_index]
            self.current_line = line_num
            self.current_sub_line = sub_index
            statement = self.expanded_program[(line_num, sub_index)]
            
            # Execute the single statement
            result = self.process_statement(statement)
            
            if result:
                # Check for INPUT and PAUSE requests first
                for item in result:
                    if item.get('type') == 'input_request':
                        # Save our position so we can resume
                        if current_pos_index + 1 < len(all_positions):
                            self.program_counter = all_positions[current_pos_index + 1]
                        else:
                            self.program_counter = None
                        self.waiting_for_input = True
                        self.running = False  # Pause execution
                        output.append(item)
                        return output  # Return immediately with input request
                    elif item.get('type') == 'pause':
                        # Save our position so we can resume after pause
                        if current_pos_index + 1 < len(all_positions):
                            self.program_counter = all_positions[current_pos_index + 1]
                        else:
                            self.program_counter = None
                        self.waiting_for_pause_continuation = True
                        self.running = False  # Pause execution
                        output.append(item)
                        return output  # Return immediately with pause request
                
                # Handle jump commands (same logic as run_program)
                jumped = False
                for item in result:
                    if item.get('type') == 'jump':
                        target_line = item['line']
                        target_positions = [(ln, si) for ln, si in all_positions if ln == target_line]
                        if target_positions:
                            current_pos_index = all_positions.index(target_positions[0])
                            jumped = True
                            break
                        else:
                            output.append({'type': 'error', 'message': f'UNDEFINED LINE {target_line}'})
                            self.running = False
                            break
                    elif item.get('type') == 'jump_after_for':
                        for_line = item['for_line']
                        for_positions = [(ln, si) for ln, si in all_positions if ln == for_line]
                        if for_positions:
                            for_pos = for_positions[0]
                            for_index = all_positions.index(for_pos)
                            current_pos_index = for_index + 1
                            jumped = True
                            break
                        else:
                            output.append({'type': 'error', 'message': f'UNDEFINED FOR LINE {for_line}'})
                            self.running = False
                            break
                    elif item.get('type') == 'jump_return':
                        # RETURN from GOSUB - jump to specific sub-line position
                        return_line = item['line']
                        return_sub_line = item['sub_line']
                        
                        # Find the position after the GOSUB call
                        return_positions = [(ln, si) for ln, si in all_positions if ln == return_line]
                        if return_positions:
                            # Find the sub-line that matches or is after the return_sub_line
                            for pos in return_positions:
                                if pos[1] > return_sub_line:
                                    current_pos_index = all_positions.index(pos)
                                    jumped = True
                                    break
                            else:
                                # If no later sub-line found, jump to next line
                                next_line_positions = [(ln, si) for ln, si in all_positions if ln > return_line]
                                if next_line_positions:
                                    current_pos_index = all_positions.index(next_line_positions[0])
                                    jumped = True
                        
                        if not jumped:
                            # If can't find return position, just continue
                            current_pos_index += 1
                            jumped = True
                        break
                    elif item.get('type') != 'input_request':
                        # During program execution, filter out "OK" messages
                        if not (item.get('type') == 'text' and item.get('text') == 'OK'):
                            output.append(item)
                            # Emit output immediately for real-time streaming
                            self.emit_output([item])
                        # Check if this is an error that should halt execution
                        if item.get('type') == 'error':
                            self.running = False
                            self.call_stack.clear()  # Clear call stack on error
                            self.for_stack.clear()   # Clear FOR stack on error
                            break
                
                if not jumped:
                    current_pos_index += 1
            else:
                current_pos_index += 1
        
        self.running = False
        self.program_counter = None
        return output
    
    def split_statements(self, code):
        """Split a line into statements on colons, but respect quoted strings"""
        statements = []
        current_statement = ""
        in_quotes = False

        # Simple colon splitting that respects quoted strings
        # Control structure handling is now done by AST converter
        for char in code:
            if char == '"':
                in_quotes = not in_quotes
                current_statement += char
            elif char == ':' and not in_quotes:
                if current_statement.strip():
                    statements.append(current_statement.strip())
                current_statement = ""
            else:
                current_statement += char

        if current_statement.strip():
            statements.append(current_statement.strip())

        return statements
    
    
    def process_line(self, code):
        """
        Process a line of BASIC code, converting single-line control structures
        to multi-line equivalents using the AST parser infrastructure.
        """
        # First, check if this is a single-line control structure that needs conversion
        code_upper = code.upper().strip()

        # Enhanced detection of control structures with colons (single-line format)
        control_keywords = ['IF ', 'FOR ', 'WHILE ', 'DO:', 'DO ']
        has_control = any(code_upper.startswith(kw) for kw in control_keywords)
        has_colons = ':' in code

        if has_control and has_colons:
            # Try to convert single-line control structure to multi-line using AST parser
            try:
                from .ast_converter import parse_and_convert_single_line
                converted = parse_and_convert_single_line(code, self.expression_evaluator.ast_parser)

                if converted:
                    # For immediate mode, create a temporary program entry and reuse run_program logic
                    return self._execute_converted_as_temporary_program(converted)
            except Exception as e:
                # Log debug info for AST conversion failures but continue with fallback
                if hasattr(self, 'emit_debug'):
                    self.emit_debug(f"AST conversion failed for '{code}': {str(e)}")
                # Fall back to original processing

        # Original processing for non-control structures or if AST conversion failed
        statements = self.split_statements(code)
        if len(statements) > 1:
            # Execute each statement and collect results
            all_results = []
            for statement in statements:
                if statement.strip():  # Skip empty statements
                    result = self.process_statement(statement)
                    if result:
                        all_results.extend(result)
                        # Handle jumps in multi-statement lines
                        for item in result:
                            if isinstance(item, dict) and item.get('type') in ['jump', 'jump_return']:
                                return all_results  # Return all accumulated results including jump
            return all_results
        else:
            # Single statement
            return self.process_statement(code)

    def _execute_converted_as_temporary_program(self, converted_statements):
        """
        Execute AST-converted statements by creating a temporary program entry
        and using the existing run_program infrastructure completely.
        """
        if not converted_statements:
            return []

        # Use a temporary line number for immediate mode (negative to avoid conflicts)
        temp_line_num = -1

        # Save current program state completely
        old_program = self.program.copy()
        old_expanded_program = self.expanded_program.copy()
        old_running = self.running
        old_current_line = self.current_line
        old_current_sub_line = self.current_sub_line
        old_for_stack = getattr(self, 'for_stack', []).copy()
        old_call_stack = getattr(self, 'call_stack', []).copy()

        try:
            # Clear program and set up temporary program
            self.program = {temp_line_num: '# AST Converted statements'}  # Placeholder only
            self.expanded_program = {}

            self.for_stack.clear()
            self.call_stack.clear()

            # Add AST-converted statements directly as sublines - no rejoining needed!
            for i, statement in enumerate(converted_statements):
                if statement.strip():
                    self.expanded_program[(temp_line_num, i)] = statement.strip()

            # Use the actual run_program method - it has all the sophisticated control flow logic
            # Don't clear variables since we want to preserve the current variable state
            results = self.run_program(clear_variables=False)

            # Filter out any "OK" messages and other program-mode artifacts
            filtered_results = []
            for item in results:
                if isinstance(item, dict):
                    if item.get('type') == 'text' and item.get('text') == 'OK':
                        continue  # Skip OK messages
                    elif item.get('type') in ['program_end', 'program_start']:
                        continue  # Skip program control messages

                filtered_results.append(item)

            return filtered_results

        finally:
            # Restore complete program state
            self.program = old_program
            self.expanded_program = old_expanded_program
            self.running = old_running
            self.current_line = old_current_line
            self.current_sub_line = old_current_sub_line
            self.for_stack = old_for_stack
            self.call_stack = old_call_stack

    def _try_ast_execute(self, code):
        """Try to execute a statement via AST. Returns None if not migrated."""
        if not self._ast_migrated_commands:
            return None

        code_stripped = code.strip()
        code_upper = code_stripped.upper()
        parts = code_upper.split(None, 1)
        first_word = parts[0] if parts else ''

        if first_word not in self._ast_migrated_commands:
            # Check for implicit assignment (no LET keyword)
            if 'LET' in self._ast_migrated_commands and '=' in code_stripped:
                # Avoid misidentifying comparisons (IF X=5, etc.)
                lhs = code_stripped.split('=', 1)[0]
                if not any(op in lhs for op in ['<', '>', '!']):
                    # Don't treat keyword statements as assignments
                    # (e.g., FOR I = 1 TO 10 contains '=' but isn't assignment)
                    if first_word in self.command_registry.commands or first_word in self.command_registry.aliases:
                        return None
                    # First token must start with a letter to be a variable name
                    lhs_stripped = lhs.strip()
                    if not lhs_stripped or not lhs_stripped[0].isalpha():
                        return None
                    first_word = 'LET'
                else:
                    return None
            else:
                return None

        try:
            ast_node = self.expression_evaluator.ast_parser.parse_statement(code_stripped)
            if self._ast_evaluator is None:
                from .ast_parser import ASTEvaluator
                self._ast_evaluator = ASTEvaluator(self)
            result = self._ast_evaluator.visit(ast_node)
            # Ensure result is a list (statement results must be List[Dict])
            if not isinstance(result, list):
                return None  # Not a valid statement result, fall back
            return result
        except Exception:
            return None  # Fall back to registry

    def process_statement(self, code):
        if not code.strip():
            return []

        # Try AST execution for migrated commands
        ast_result = self._try_ast_execute(code)
        if ast_result is not None:
            return ast_result

        # Try the command registry
        result = self.command_registry.execute(code.strip())
        if result is not None:
            return result
        
        # Fallback: check for variable assignment
        if '=' in code and not any(op in code.split('=')[0] for op in ['<', '>', '!', '=']):
            # Variable assignment without LET - delegate to VariableManager
            return self.variable_manager.execute_let(code)
        
        # If nothing matches, it's a syntax error
        if self.current_line == 0 or not self.running:
            # Direct command or not in program execution
            error = self.error_context.syntax_error(
                "Unrecognized command or syntax",
                suggestions=[
                    'Check command spelling and syntax',
                    'Use HELP to see available commands',
                    'Check BASIC reference for proper syntax'
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
        else:
            # Program execution context
            error = self.error_context.syntax_error(
                "Unrecognized command or syntax",
                self.current_line,
                suggestions=[
                    'Check command spelling and syntax',
                    'Use HELP to see available commands',
                    'Check BASIC reference for proper syntax'
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
    
    
    
    
    
    
    
    
    
    def evaluate_expression(self, expr, line=None):
        """Delegate expression evaluation to the ExpressionEvaluator"""
        try:
            return self.expression_evaluator.evaluate(expr, line or self.current_line)
        except ValueError as e:
            # Preserve enhanced error messages by re-raising as-is
            raise e
        except Exception as e:
            # For other exceptions, convert to ValueError for backward compatibility
            raise ValueError(str(e))

    def execute_for(self, args):
        """Execute FOR loop statement"""
        # FOR I=1 TO 10 [STEP 1] - handle multi-line FOR loops
        # Single-line FOR loops are now handled by AST converter
        for_part = args.strip()

        # Set error context for FOR command
        self.error_context.set_context(self.current_line, f"FOR {for_part}")

        # Better pattern that looks for the word TO, not individual letters
        match = re.match(r'(\w+)\s*=\s*(.+?)\s+TO\s+(.+?)(?:\s+STEP\s+(.+?))?$', for_part, re.IGNORECASE)
        if not match:
            error = self.error_context.syntax_error(
                "SYNTAX ERROR: Invalid FOR statement",
                self.current_line,
                suggestions=[
                    "Correct syntax: FOR variable = start TO end [STEP increment]",
                    "Example: FOR I = 1 TO 10 or FOR X = 0 TO 100 STEP 5",
                    "Variable name must be a single letter or word"
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]

        var_name = match.group(1).strip()

        # Evaluate expressions with enhanced error handling
        try:
            start_val = self.evaluate_expression(match.group(2).strip(), self.current_line)
            end_val = self.evaluate_expression(match.group(3).strip(), self.current_line)
            step_val = self.evaluate_expression(match.group(4).strip(), self.current_line) if match.group(4) else 1
        except ValueError as e:
            # Enhanced error already formatted, just pass it through
            return [{'type': 'error', 'message': str(e)}]

        # Ensure numeric values for comparison
        try:
            start_val = float(start_val) if isinstance(start_val, str) else start_val
            end_val = float(end_val) if isinstance(end_val, str) else end_val
            step_val = float(step_val) if isinstance(step_val, str) else step_val
        except (ValueError, TypeError):
            error = self.error_context.type_error(
                "FOR loop values must be numeric",
                "number",
                "non-numeric expression",
                suggestions=[
                    "Use numeric expressions: FOR I = 1 TO 10",
                    "Variables must contain numbers: LET N = 5; FOR I = 1 TO N",
                    "Check that all expressions evaluate to numbers"
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]

        # Check if loop should execute at all
        if ((step_val > 0 and start_val > end_val) or
            (step_val < 0 and start_val < end_val)):
            # Skip the loop entirely - jump to NEXT and pop it
            self.variables[var_name] = start_val  # Still set the variable
            # Return a jump to find and skip past the matching NEXT
            return [{'type': 'skip_for_loop', 'var': var_name}]

        self.variables[var_name] = start_val
        self.for_stack.append({
            'var': var_name,
            'end': end_val,
            'step': step_val,
            'line': self.current_line,
            'sub_line': self.current_sub_line
        })

        return []
    
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
            return [{'type': 'error', 'message': error.format_detailed()}]
        
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
    
    def execute_if(self, args):
        """Execute IF/THEN/ELSE statement"""
        # IF condition THEN [action | multi-line] - now using AST parser
        if 'THEN' not in args.upper():
            error = self.error_context.syntax_error(
                "SYNTAX ERROR: Missing THEN in IF statement",
                self.current_line,
                suggestions=[
                    "Correct syntax: IF condition THEN action",
                    'Example: IF A > 5 THEN PRINT "BIG"',
                    "IF statements must include THEN keyword"
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]

        # Find THEN (case-insensitive)
        then_pos = args.upper().find('THEN')
        condition = args[:then_pos].strip()
        then_part = args[then_pos + 4:].strip()  # Skip 'THEN'
        
        # Check for empty condition
        if not condition:
            error = self.error_context.syntax_error(
                "SYNTAX ERROR: Empty condition in IF statement",
                self.current_line,
                suggestions=[
                    "Provide a condition to test",
                    'Example: IF A = 5 THEN PRINT "EQUAL"',
                    "Condition can use operators: =, <>, <, >, <=, >="
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
        
        condition_result = self.evaluate_condition(condition.strip())
        
        # Handle both single-line and multi-line IF statements
        # Complex single-line IF statements (with colons) are handled by AST converter in process_line()
        # Simple single-line IF statements (without colons) are handled here
        if then_part and then_part.upper() != 'THEN':
            # Single-line IF with action in THEN clause
            if ':' in then_part:
                # Complex single-line IF with multiple statements - should be handled by AST converter
                # If we get here, it means the AST converter didn't catch it, so provide fallback
                return self.process_line(then_part)
            else:
                # Simple single-line IF - handle directly
                if condition_result:
                    # Handle THEN clause - check if it's a line number or statement
                    then_upper = then_part.upper().strip()

                    # Check if it starts with a BASIC keyword
                    basic_keywords = ['PRINT', 'LET', 'GOTO', 'GOSUB', 'RETURN', 'END', 'STOP',
                                    'IF', 'FOR', 'NEXT', 'DIM', 'INPUT', 'READ', 'DATA',
                                    'RESTORE', 'ON', 'DEF', 'PAUSE', 'NEW', 'LIST', 'RUN',
                                    'EXIT', 'DO', 'LOOP', 'WHILE', 'WEND', 'ELSE', 'ENDIF']

                    starts_with_keyword = any(then_upper.startswith(keyword) for keyword in basic_keywords)

                    # Check if it looks like an assignment
                    is_assignment = ('=' in then_part and
                                   not any(op in then_part for op in ['>=', '<=', '<>', '==']) and
                                   not then_part.strip().startswith('='))

                    if starts_with_keyword or is_assignment:
                        # Execute as statement
                        return self.process_line(then_part)
                    else:
                        # Try to parse as line number - use GOTO
                        try:
                            int(self.evaluate_expression(then_part))
                            return self.execute_goto(then_part)
                        except (ValueError, TypeError):
                            # If not a number, treat as statement
                            return self.process_line(then_part)
                else:
                    # Condition false - do nothing
                    return []

        # Multi-line IF - push to stack
        if_info = {
            'condition_met': condition_result,
            'line': self.current_line,
            'sub_line': self.current_sub_line,
            'in_else': False
        }
        self.if_stack.append(if_info)

        # If condition is false, skip to ELSE or ENDIF
        if not condition_result:
            return [{'type': 'skip_if_block'}]
        else:
            return []  # Continue with THEN block
    
    def evaluate_condition(self, condition):
        # Simple condition evaluation
        operators = ['>=', '<=', '<>', '=', '>', '<']
        for op in operators:
            if op in condition:
                left, right = condition.split(op, 1)
                left_val = self.evaluate_expression(left.strip())
                right_val = self.evaluate_expression(right.strip())
                
                if op == '=':
                    return left_val == right_val
                elif op == '<>':
                    return left_val != right_val
                elif op == '<':
                    return left_val < right_val
                elif op == '>':
                    return left_val > right_val
                elif op == '<=':
                    return left_val <= right_val
                elif op == '>=':
                    return left_val >= right_val
        
        return False
    
    def execute_goto(self, args):
        """Execute GOTO statement"""
        self.error_context.set_context(self.current_line, f"GOTO {args}")

        if not args.strip():
            error = self.error_context.syntax_error(
                "SYNTAX ERROR: Missing line number",
                self.current_line,
                suggestions=[
                    "Correct syntax: GOTO line_number",
                    "Example: GOTO 100",
                    "Specify the line number to jump to"
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]

        try:
            line_num = int(self.evaluate_expression(args.strip(), self.current_line))
            if line_num <= 0:
                error = self.error_context.runtime_error(
                    f"Invalid line number {line_num}",
                    self.current_line,
                    suggestions=[
                        "Line numbers must be positive integers",
                        "Use line numbers that exist in your program",
                        "Check with LIST command to see available lines"
                    ]
                )
                return [{'type': 'error', 'message': error.format_detailed()}]
            return [{'type': 'jump', 'line': line_num}]
        except ValueError as e:
            # Enhanced error from expression evaluation
            return [{'type': 'error', 'message': str(e)}]
        except (TypeError, KeyError) as e:
            error = self.error_context.syntax_error(
                "SYNTAX ERROR: Invalid GOTO target",
                self.current_line,
                suggestions=[
                    "Correct syntax: GOTO line_number",
                    "Example: GOTO 100 or GOTO L where L is a numeric variable",
                    "Line number must be a positive integer"
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]

    def _execute_via_ast(self, statement: str):
        """Execute a statement using AST parser and visitor"""
        try:
            # Parse statement using AST parser
            ast_node = self.expression_evaluator.ast_parser.parse_statement(statement)

            # Evaluate using AST visitor
            from .ast_parser import ASTEvaluator
            evaluator = ASTEvaluator(self)
            return evaluator.visit(ast_node)

        except Exception as e:
            # Return error if AST execution fails
            return [{'type': 'error', 'message': str(e)}]

    def execute_gosub(self, args):
        """Execute GOSUB statement"""
        self.error_context.set_context(self.current_line, f"GOSUB {args}")

        if not args.strip():
            error = self.error_context.syntax_error(
                "SYNTAX ERROR: Missing line number",
                self.current_line,
                suggestions=[
                    "Correct syntax: GOSUB line_number",
                    "Example: GOSUB 1000",
                    "Specify the line number of the subroutine to call"
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]

        try:
            line_num = int(self.evaluate_expression(args.strip(), self.current_line))
            if line_num <= 0:
                error = self.error_context.runtime_error(
                    f"Invalid subroutine line number {line_num}",
                    self.current_line,
                    suggestions=[
                        "Line numbers must be positive integers",
                        "Use line numbers that exist in your program",
                        "Subroutine should end with RETURN statement"
                    ]
                )
                return [{'type': 'error', 'message': error.format_detailed()}]
            self.call_stack.append((self.current_line, self.current_sub_line))
            return [{'type': 'jump', 'line': line_num}]
        except ValueError as e:
            # Enhanced error from expression evaluation
            return [{'type': 'error', 'message': str(e)}]
        except (TypeError, KeyError) as e:
            error = self.error_context.syntax_error(
                "SYNTAX ERROR: Invalid GOSUB target",
                self.current_line,
                suggestions=[
                    "Correct syntax: GOSUB line_number",
                    "Example: GOSUB 1000 or GOSUB SUB_LINE where SUB_LINE is a variable",
                    "Make sure target line contains a subroutine that ends with RETURN"
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
    
    def execute_return(self, args):
        """Execute RETURN statement"""
        if not self.call_stack:
            error = self.error_context.runtime_error(
                "RETURN WITHOUT GOSUB",
                self.current_line,
                suggestions=[
                    "RETURN must be preceded by a GOSUB statement",
                    "Example: GOSUB 1000: ... : 1000 RETURN",
                    "Check that subroutines are called with GOSUB before RETURN"
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]

        return_line, return_sub_line = self.call_stack.pop()

        # Return to the sub-line after the GOSUB call
        return [{'type': 'jump_return', 'line': return_line, 'sub_line': return_sub_line}]
    
    
    
    
    
    
    
    def execute_sound(self, args):
        # SOUND frequency,duration
        self.error_context.set_context(self.current_line, f"SOUND {args}")
        
        parts = args.split(',')
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
            return [{'type': 'error', 'message': error.format_detailed()}]
        
        try:
            frequency = int(self.evaluate_expression(parts[0].strip(), self.current_line))
            duration = int(self.evaluate_expression(parts[1].strip(), self.current_line))
            
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
                return [{'type': 'error', 'message': error.format_detailed()}]
                
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
                return [{'type': 'error', 'message': error.format_detailed()}]
            
            return [{'type': 'sound', 'frequency': frequency, 'duration': duration}]
            
        except ValueError as e:
            # Enhanced error from expression evaluation
            return [{'type': 'error', 'message': str(e)}]
        except TypeError as e:
            error = self.error_context.runtime_error(
                "Invalid SOUND parameters",
                self.current_line,
                details=str(e),
                suggestions=[
                    "Both frequency and duration must be numeric",
                    "Example: SOUND 440, 100",
                    "Check that expressions evaluate to integers"
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
    
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
            return [{'type': 'error', 'message': f'PAUSE command error: {type(e).__name__}: {e}'}]
    
    def clear_interpreter_state(self, clear_program=True):
        """Clear interpreter state - shared function for NEW, LOAD, and other commands"""
        if clear_program:
            self.program.clear()
            self.expanded_program.clear()
        
        self.variables.clear()
        self.arrays.clear()  # Clear all dimensioned arrays
        self.for_stack.clear()
        self.call_stack.clear()
        self.if_stack.clear()
        self.while_stack.clear()
        self.do_stack.clear()
        self.data_statements.clear()
        self.data_pointer = 0
        self.running = False
        self.waiting_for_input = False
        self.waiting_for_pause_continuation = False
        self.pause_duration = 0
        self.program_counter = None
        self.stopped_position = None  # Clear stopped position
        
        # Clear multi-variable INPUT state
        self.input_variables = None
        self.input_prompt = None
        self.current_input_index = 0
        self.current_line = 0
        self.current_sub_line = 0
        self.iteration_count = 0
        # Don't clear keyboard buffer - preserve keys for INKEY$
        self.graphics_mode = 0  # Reset to text mode

    def execute_new(self):
        """NEW command - clear program and variables"""
        self.clear_interpreter_state(clear_program=True)
        return [{'type': 'text', 'text': 'READY'}]
    
    def execute_end(self, args):
        """Execute END statement"""
        # END command - end program execution silently
        self.running = False
        # Clear stopped position since END terminates completely
        self.stopped_position = None
        return []  # No output for END
    
    def execute_stop(self, args):
        # STOP command - stop program execution with message (allows CONT)
        self.running = False
        # Store position for CONT command
        self.stopped_position = (self.current_line, self.current_sub_line)
        return [{'type': 'text', 'text': 'BREAK IN ' + str(self.current_line)}]
    
    def execute_cont(self, args):
        # CONT command - continue execution after STOP
        if self.stopped_position is None:
            error = self.error_context.runtime_error(
                "Cannot continue - no program was stopped",
                suggestions=[
                    'Use CONT only after a program has been stopped',
                    'Program must be paused with STOP or Ctrl+C',
                    'Run a new program with RUN command'
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
        
        # Resume from the line after where we stopped
        self.stopped_line, self.stopped_sub_line = self.stopped_position
        
        # Reset state for continuation
        self.running = True
        output = []
        
        # Get all sub-line positions sorted by (line_num, sub_index)
        all_positions = sorted(self.expanded_program.keys())
        
        # Find the position after where we stopped
        continue_pos = None
        for i, (line_num, sub_index) in enumerate(all_positions):
            if line_num == self.stopped_line and sub_index > self.stopped_sub_line:
                continue_pos = i
                break
            elif line_num > self.stopped_line:
                continue_pos = i
                break
        
        if continue_pos is None:
            # No more lines to execute
            self.running = False
            return [{'type': 'text', 'text': 'READY'}]
        
        # Continue execution from the found position
        current_pos_index = continue_pos
        
        while current_pos_index < len(all_positions) and self.running:
            # Safety check for infinite loops
            if self.safety_enabled:
                self.iteration_count += 1
                if self.iteration_count > self.max_iterations:
                    output.append({'type': 'error', 'message': 'PROGRAM STOPPED - TOO MANY ITERATIONS'})
                    self.running = False
                    break
            
            # Get current position and statement
            line_num, sub_index = all_positions[current_pos_index]
            self.current_line = line_num
            self.current_sub_line = sub_index
            statement = self.expanded_program[(line_num, sub_index)]
            
            # Execute the single statement
            result = self.process_statement(statement)
            
            if result:
                # Handle input requests
                for item in result:
                    if item.get('type') == 'input_request':
                        if current_pos_index + 1 < len(all_positions):
                            self.program_counter = all_positions[current_pos_index + 1]
                        else:
                            self.program_counter = None
                        self.waiting_for_input = True
                        self.running = False
                        output.append(item)
                        return output
                
                # Handle jump commands
                jumped = False
                for item in result:
                    if item.get('type') == 'jump':
                        target_line = item['line']
                        target_positions = [(ln, si) for ln, si in all_positions if ln == target_line]
                        if target_positions:
                            current_pos_index = all_positions.index(target_positions[0])
                            jumped = True
                            break
                        else:
                            output.append({'type': 'error', 'message': f'UNDEFINED LINE {target_line}'})
                            self.running = False
                            break
                    elif item.get('type') == 'jump_after_for':
                        for_line = item['for_line']
                        for_positions = [(ln, si) for ln, si in all_positions if ln == for_line]
                        if for_positions:
                            for_pos = for_positions[0]
                            for_index = all_positions.index(for_pos)
                            current_pos_index = for_index + 1
                            jumped = True
                            break
                        else:
                            output.append({'type': 'error', 'message': f'UNDEFINED FOR LINE {for_line}'})
                            self.running = False
                            break
                    elif item.get('type') == 'jump_return':
                        return_line = item['line']
                        return_sub_line = item['sub_line']
                        return_positions = [(ln, si) for ln, si in all_positions if ln == return_line]
                        if return_positions:
                            for pos in return_positions:
                                if pos[1] > return_sub_line:
                                    current_pos_index = all_positions.index(pos)
                                    jumped = True
                                    break
                            else:
                                next_line_positions = [(ln, si) for ln, si in all_positions if ln > return_line]
                                if next_line_positions:
                                    current_pos_index = all_positions.index(next_line_positions[0])
                                    jumped = True
                        
                        if not jumped:
                            current_pos_index += 1
                            jumped = True
                        break
                    elif item.get('type') != 'input_request':
                        # During program execution, filter out "OK" messages
                        if not (item.get('type') == 'text' and item.get('text') == 'OK'):
                            output.append(item)
                            # Emit output immediately for real-time streaming
                            self.emit_output([item])
                        # Check if this is an error that should halt execution
                        if item.get('type') == 'error':
                            self.running = False
                            self.call_stack.clear()  # Clear call stack on error
                            self.for_stack.clear()   # Clear FOR stack on error
                            break
                
                if not jumped:
                    current_pos_index += 1
            else:
                current_pos_index += 1
        
        self.running = False
        self.stopped_position = None  # Clear stopped position after successful continuation
        return output
    
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
        items = self.split_data_args(args)
        
        for item in items:
            item = item.strip()
            if item.startswith('"') and item.endswith('"'):
                # String literal
                data_items.append(item[1:-1])
            else:
                # Try to parse as number
                try:
                    if '.' in item:
                        data_items.append(float(item))
                    else:
                        data_items.append(int(item))
                except ValueError:
                    # Store as string if not a valid number
                    data_items.append(item)
        
        # Store data items with current line number for organization
        self.data_statements.extend([(self.current_line, item) for item in data_items])
        
        return []  # DATA commands don't produce output
    
    def split_data_args(self, args):
        """Split DATA arguments on commas, but respect quoted strings"""
        items = []
        current_item = ""
        in_quotes = False
        
        for char in args:
            if char == '"':
                in_quotes = not in_quotes
                current_item += char
            elif char == ',' and not in_quotes:
                # Comma outside quotes - split here
                items.append(current_item.strip())
                current_item = ""
            else:
                current_item += char
        
        # Add the last item
        if current_item.strip():
            items.append(current_item.strip())
        
        return items
    
    def execute_read(self, args):
        # READ command - read data into variables
        # READ A,B$,C
        if not args:
            error = self.error_context.syntax_error(
                "SYNTAX ERROR: READ requires variable names",
                self.current_line,
                suggestions=[
                    "Specify variables to read data into",
                    "Example: READ A, B$, C",
                    "Variables must match DATA statement types"
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
        
        # Parse variable names
        var_names = [name.strip() for name in args.split(',')]
        
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
                return [{'type': 'error', 'message': error.format_detailed()}]
            
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
        # Check if this is an array assignment (A(5) = 10)
        array_match = re.match(r'(\w+\$?)\(([^)]+)\)', var_name)
        if not array_match:
            error = self.error_context.syntax_error(
                "Invalid array syntax in DATA statement",
                self.current_line,
                suggestions=[
                    'Array syntax: A(1,2) or B$(5)',
                    'Check array name and index format',
                    'Ensure parentheses are properly matched'
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
            
        # Array assignment
        array_name = array_match.group(1)
        indices_str = array_match.group(2)
        
        # Parse indices and use VariableManager
        try:
            indices = [int(self.evaluate_expression(idx.strip())) for idx in indices_str.split(',')]
            
            # Use VariableManager to set array element
            error = self.variable_manager.set_array_element(array_name.upper(), indices, value)
            if error:
                return [{'type': 'error', 'message': error}]
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
            return [{'type': 'error', 'message': error.format_detailed()}]
        except (IndexError, TypeError, KeyError):
            error = self.error_context.runtime_error(
                "Array index out of bounds",
                suggestions=[
                    'Check that array indices are within valid range',
                    'Arrays are 0-indexed: DIM A(10) creates indices 0-10',
                    'Use valid positive integer indices'
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]

    def execute_restore(self, args):
        # RESTORE command - reset data pointer to beginning
        self.data_pointer = 0
        return []
    
    def execute_on(self, args):
        """ON expression GOTO/GOSUB line1,line2,line3..."""
        args = args.strip()
        
        # Parse: ON expression GOTO/GOSUB lines
        # First find GOTO or GOSUB keyword
        goto_pos = args.upper().find(' GOTO ')
        gosub_pos = args.upper().find(' GOSUB ')
        
        if goto_pos == -1 and gosub_pos == -1:
            error = self.error_context.syntax_error(
                "SYNTAX ERROR: ON requires GOTO or GOSUB",
                self.current_line,
                suggestions=["Use ON expression GOTO line1,line2,...",
                           "Use ON expression GOSUB line1,line2,..."]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
        
        # Determine which command and split
        if goto_pos != -1 and (gosub_pos == -1 or goto_pos < gosub_pos):
            command = 'GOTO'
            expr_part = args[:goto_pos].strip()
            line_part = args[goto_pos + 6:].strip()  # Skip ' GOTO '
        else:
            command = 'GOSUB'
            expr_part = args[:gosub_pos].strip()
            line_part = args[gosub_pos + 7:].strip()  # Skip ' GOSUB '
        
        # Remove leading 'ON' if present
        if expr_part.upper().startswith('ON '):
            expr_part = expr_part[3:].strip()
        elif expr_part.upper() == 'ON':
            error = self.error_context.syntax_error(
                "SYNTAX ERROR: ON requires an expression",
                self.current_line,
                suggestions=["Provide a numeric expression after ON"]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
        
        # Evaluate the expression
        try:
            value = self.evaluate_expression(expr_part, self.current_line)
            # Convert to integer and ensure it's 1-based
            index = int(value)
        except (ValueError, TypeError) as e:
            error = self.error_context.runtime_error(
                f"ON expression error: {str(e)}",
                suggestions=["Ensure the expression evaluates to a number",
                           "Check variable values"]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
        
        # Parse line numbers using expression evaluation
        try:
            line_parts = [part.strip() for part in line_part.split(',')]
            line_numbers = []
            for part in line_parts:
                if part:
                    line_numbers.append(int(self.evaluate_expression(part, self.current_line)))
        except (ValueError, TypeError) as e:
            error = self.error_context.syntax_error(
                f"INVALID line numbers in ON statement: {str(e)}",
                self.current_line,
                suggestions=["Use comma-separated line numbers or expressions",
                           "Example: ON X GOTO 100,200,300",
                           "Example: ON X GOTO START,LOOP,END"]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
        
        # Check if index is within range (1-based indexing)
        if index < 1 or index > len(line_numbers):
            # If out of range, continue to next statement (standard BASIC behavior)
            return []
        
        # Get the target line number (1-based indexing)
        target_line = line_numbers[index - 1]
        
        # Set context for error reporting
        self.error_context.set_context(self.current_line, f"ON {expr_part} {command} {line_part}")
        
        # Use command registry dispatch instead of hardcoded logic
        if command == 'GOTO':
            return self.command_registry.execute(f"GOTO {target_line}")
        elif command == 'GOSUB':
            return self.command_registry.execute(f"GOSUB {target_line}")
        
        error = self.error_context.syntax_error(
            "Invalid ON statement syntax", 
            self.current_line,
            suggestions=[
                'Correct syntax: ON expression GOTO line1,line2,... or ON expression GOSUB line1,line2,...',
                'Example: ON X GOTO 100,200,300',
                'Expression must evaluate to a number'
            ]
        )
        return [{'type': 'error', 'message': error.format_detailed()}]
    
    # INKEY$ functionality moved to functions.py function registry
    # Keyboard buffer management now handled by function registry
    
    
    
    
    def _register_all_commands(self):
        """Register all BASIC commands by delegating to each module"""
        # Let each module register its own commands
        self.graphics.register_commands(self.command_registry)  
        self.variable_manager.register_commands(self.command_registry)
        self.io_handler.register_commands(self.command_registry)
        
        # Core commands - control flow
        self.command_registry.register('IF', self.execute_if, 
                                     category='control',
                                     description="Conditional execution of statements",
                                     syntax="IF condition THEN statement [ELSE statement]",
                                     examples=["IF A > 5 THEN PRINT \"BIG\"", "IF X = 0 THEN GOTO 100 ELSE PRINT X"])
        
        self.command_registry.register('GOTO', self.execute_goto,
                                     category='control', 
                                     description="Jump to specified line number",
                                     syntax="GOTO line_number",
                                     examples=["GOTO 100", "GOTO START_LINE"])
        
        self.command_registry.register('GOSUB', self.execute_gosub,
                                     category='control',
                                     description="Call subroutine at specified line",
                                     syntax="GOSUB line_number", 
                                     examples=["GOSUB 1000", "GOSUB SUBROUTINE_LINE"])
        
        self.command_registry.register('ON', self.execute_on,
                                     category='control',
                                     description="Multi-way branch based on expression value",
                                     syntax="ON expression GOTO/GOSUB line1,line2,...",
                                     examples=["ON X GOTO 100,200,300", "ON A+1 GOSUB 1000,2000,3000"])
        
        self.command_registry.register('RETURN', self.execute_return,
                                     category='control',
                                     description="Return from subroutine",
                                     syntax="RETURN",
                                     examples=["RETURN"])
        
        self.command_registry.register('FOR', self.execute_for,
                                     category='control',
                                     description="Begin FOR loop with counter variable",
                                     syntax="FOR variable = start TO end [STEP increment]",
                                     examples=["FOR I = 1 TO 10", "FOR X = 0 TO 100 STEP 5"])
        
        self.command_registry.register('NEXT', self.execute_next,
                                     category='control', 
                                     description="End FOR loop and increment counter",
                                     syntax="NEXT [variable]",
                                     examples=["NEXT", "NEXT I", "NEXT X"])
        
        # Phase 3: Enhanced Control Flow Commands
        self.command_registry.register('WHILE', self.execute_while,
                                     category='control',
                                     description="Begin WHILE loop with condition",
                                     syntax="WHILE condition",
                                     examples=["WHILE X > 0", "WHILE A$ <> \"QUIT\""])
        
        self.command_registry.register('WEND', self.execute_wend,
                                     category='control',
                                     description="End WHILE loop",
                                     syntax="WEND",
                                     examples=["WEND"])
        
        self.command_registry.register('EXIT', self.execute_exit,
                                     category='control',
                                     description="Exit from current loop early",
                                     syntax="EXIT FOR",
                                     examples=["EXIT FOR"])
        
        self.command_registry.register('DO', self.execute_do,
                                     category='control',
                                     description="Begin DO loop block",
                                     syntax="DO [WHILE condition | UNTIL condition]",
                                     examples=["DO", "DO WHILE X > 0", "DO UNTIL Y = 10"])
        
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
        
        self.command_registry.register('END', self.execute_end,
                                     category='control',
                                     description="End program execution", 
                                     syntax="END",
                                     examples=["END"])
        
        self.command_registry.register('CONT', self.execute_cont,
                                     category='system',
                                     description="Continue program after STOP",
                                     syntax="CONT",
                                     examples=["CONT"])
        
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
        self.command_registry.register('CLS', lambda args: [{'type': 'clear_screen'}],
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
    

    # Phase 3: Enhanced Control Flow Methods
    def execute_while(self, args):
        """WHILE statement - begin conditional loop"""
        # For now, implement legacy-style WHILE tracking
        condition = args.strip()
        if self.evaluate_condition(condition):
            # Store the while condition and current position for loop jumping
            self.while_stack.append({
                'condition': condition,
                'line': self.current_line,
                'sub_line': self.current_sub_line
            })
            return []  # Continue with next statement
        else:
            # Skip to matching WEND
            return [{'type': 'skip_while_loop'}]
    
    def execute_wend(self, args):
        """WEND statement - end WHILE loop"""
        if not self.while_stack:
            error = self.error_context.syntax_error(
                "WEND without matching WHILE",
                self.current_line,
                suggestions=[
                    'Every WEND must have a matching WHILE',
                    'Check that WHILE loops are properly nested',
                    'Example: WHILE condition ... WEND'
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
        
        # Get the current WHILE loop
        while_info = self.while_stack[-1]
        
        # Re-evaluate the condition
        if self.evaluate_condition(while_info['condition']):
            # Continue loop - jump back to after the WHILE statement
            return [{'type': 'jump_after_while', 
                    'while_line': while_info['line'],
                    'while_sub_line': while_info['sub_line']}]
        else:
            # Exit loop
            self.while_stack.pop()
            return []
    
    def execute_exit(self, args):
        """EXIT statement - exit from current loop"""
        args = args.strip().upper()
        if args == 'FOR':
            # Exit current FOR loop - don't pop here, do it in the jump handler
            if self.for_stack:
                return [{'type': 'exit_for_loop'}]
            else:
                error = self.error_context.syntax_error(
                    "EXIT FOR without matching FOR",
                    self.current_line,
                    suggestions=[
                        'EXIT FOR can only be used inside a FOR loop',
                        'Check that FOR loops are properly nested',
                        'Example: FOR I=1 TO 10 ... EXIT FOR ... NEXT I'
                    ]
                )
                return [{'type': 'error', 'message': error.format_detailed()}]
        else:
            error = self.error_context.syntax_error(
                "Invalid EXIT statement", 
                self.current_line,
                suggestions=[
                    'Correct syntax: EXIT FOR',
                    'EXIT can only be used to exit FOR loops',
                    'Use RETURN to exit subroutines or END to stop program'
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
    
    def execute_do(self, args):
        """DO statement - begin DO/LOOP block"""
        # Parse DO [WHILE condition | UNTIL condition]
        args = args.strip()
        condition = None
        condition_type = None
        
        if args.upper().startswith('WHILE '):
            condition = args[6:].strip()
            condition_type = 'WHILE'
            # Evaluate condition at top
            if not self.evaluate_condition(condition):
                return [{'type': 'skip_do_loop'}]
        elif args.upper().startswith('UNTIL '):
            condition = args[6:].strip()
            condition_type = 'UNTIL'
            # Evaluate condition at top
            if self.evaluate_condition(condition):
                return [{'type': 'skip_do_loop'}]
        
        # Store DO loop info
        self.do_stack.append({
            'condition': condition,
            'condition_type': condition_type,
            'line': self.current_line,
            'sub_line': self.current_sub_line
        })
        
        return []
    
    def execute_loop(self, args):
        """LOOP statement - end DO/LOOP block"""
        if not self.do_stack:
            error = self.error_context.syntax_error(
                "LOOP without matching DO",
                self.current_line,
                suggestions=[
                    'Every LOOP must have a matching DO',
                    'Check that DO loops are properly nested',
                    'Example: DO ... LOOP or DO ... LOOP WHILE condition'
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
        
        # Get current DO loop
        do_info = self.do_stack[-1]
        
        # Parse LOOP [WHILE condition | UNTIL condition]
        args = args.strip()
        condition = do_info['condition']
        condition_type = do_info['condition_type']
        
        # Check for condition at LOOP
        if args.upper().startswith('WHILE '):
            condition = args[6:].strip()
            condition_type = 'WHILE'
        elif args.upper().startswith('UNTIL '):
            condition = args[6:].strip()
            condition_type = 'UNTIL'
        
        # Evaluate loop continuation
        should_continue = False
        if condition:
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
        if not self.if_stack:
            error = self.error_context.syntax_error(
                "ELSE without matching IF",
                self.current_line,
                suggestions=[
                    'Every ELSE must have a matching IF',
                    'Check that IF blocks are properly structured',
                    'Example: IF condition ... ELSE ... ENDIF'
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
        
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
        if not self.if_stack:
            error = self.error_context.syntax_error(
                "ENDIF without matching IF",
                self.current_line,
                suggestions=[
                    'Every ENDIF must have a matching IF',
                    'Check that IF blocks are properly structured',
                    'Example: IF condition ... ENDIF'
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]
        
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
            return [{'type': 'error', 'message': error.format_detailed()}]
        
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
                    return [{'type': 'error', 'message': error.format_detailed()}]
                
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
                    return [{'type': 'error', 'message': error.format_detailed()}]
                
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
                    return [{'type': 'error', 'message': error.format_detailed()}]
                
                # Delete all lines in the range
                lines_deleted = 0
                for line_num in list(self.program.keys()):
                    if start_line <= line_num <= end_line:
                        del self.program[line_num]
                        # Remove from expanded program
                        keys_to_remove = [key for key in self.expanded_program.keys() if key[0] == line_num]
                        for key in keys_to_remove:
                            del self.expanded_program[key]
                        lines_deleted += 1
                
                if lines_deleted == 0:
                    return [{'type': 'text', 'text': 'NO LINES DELETED'}]
                else:
                    return [{'type': 'text', 'text': f'DELETED {lines_deleted} LINE(S)'}]
                    
            else:
                # Single line format: DELETE line_number
                line_num = int(args)
                
                if line_num in self.program:
                    del self.program[line_num]
                    # Remove from expanded program
                    keys_to_remove = [key for key in self.expanded_program.keys() if key[0] == line_num]
                    for key in keys_to_remove:
                        del self.expanded_program[key]
                    return [{'type': 'text', 'text': f'DELETED LINE {line_num}'}]
                else:
                    return [{'type': 'text', 'text': f'LINE {line_num} NOT FOUND'}]
                    
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
            return [{'type': 'error', 'message': error.format_detailed()}]
        except (TypeError, KeyError) as e:
            return [{'type': 'error', 'message': f'DELETE ERROR: {str(e)}'}]

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
                return [{'type': 'error', 'message': error.format_detailed()}]
        
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
            return [{'type': 'error', 'message': error.format_detailed()}]
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
            return [{'type': 'error', 'message': error.format_detailed()}]
        
        # Get sorted list of existing line numbers
        old_lines = sorted(self.program.keys())
        if not old_lines:
            return [{'type': 'text', 'text': 'NO PROGRAM TO RENUMBER'}]
        
        # Determine which lines to renumber
        if old_start is not None:
            old_lines = [line for line in old_lines if line >= old_start]
            if not old_lines:
                return [{'type': 'text', 'text': 'NO LINES TO RENUMBER'}]
        
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
                return [{'type': 'error', 'message': error.format_detailed()}]
        
        # Check for conflicts with existing lines not being renumbered
        unchanged_lines = set(self.program.keys()) - set(old_lines)
        new_lines = set(line_mapping.values())
        conflicts = unchanged_lines & new_lines
        if conflicts:
            return [{'type': 'error', 'message': f'ERROR - NEW LINE {min(conflicts)} CONFLICTS WITH EXISTING LINE'}]
        
        # Update program with new line numbers
        new_program = {}
        
        # Keep unchanged lines
        for line_num in unchanged_lines:
            new_program[line_num] = self.program[line_num]
        
        # Add renumbered lines with updated GOTO/GOSUB/THEN targets
        for old_line, new_line in line_mapping.items():
            code = self.program[old_line]
            
            # Update GOTO, GOSUB, and THEN line references in the code
            # This is a simple implementation - more sophisticated parsing would be better
            import re
            
            # Pattern to match GOTO, GOSUB, THEN followed by a line number
            pattern = r'\b(GOTO|GOSUB|THEN)\s+(\d+)\b'
            
            def replace_line_ref(match):
                keyword = match.group(1)
                target = int(match.group(2))
                if target in line_mapping:
                    return f'{keyword} {line_mapping[target]}'
                return match.group(0)
            
            updated_code = re.sub(pattern, replace_line_ref, code, flags=re.IGNORECASE)
            
            # Also handle ON...GOTO and ON...GOSUB with comma-separated line numbers
            on_pattern = r'\b(ON\s+.*?\s+(?:GOTO|GOSUB))\s+([\d,\s]+)\b'
            
            def replace_on_refs(match):
                prefix = match.group(1)
                targets = match.group(2)
                # Split by comma and update each line number
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
            
            updated_code = re.sub(on_pattern, replace_on_refs, updated_code, flags=re.IGNORECASE)
            
            new_program[new_line] = updated_code
        
        # Replace the program
        self.program = new_program
        
        # Rebuild expanded program
        self.expanded_program = {}
        for line_num in sorted(self.program.keys()):
            self.expand_line_to_sublines(line_num, self.program[line_num])
        
        return [{'type': 'text', 'text': f'RENUMBERED {len(line_mapping)} LINES'}]
    
    def execute_safety(self, args):
        """SAFETY statement - enable or disable iteration safety limits"""
        args = args.strip().upper()
        
        if not args:
            # Show current status
            status = "ON" if self.safety_enabled else "OFF"
            return [{'type': 'text', 'text': f'SAFETY IS {status}'}]
        
        if args == 'ON':
            self.safety_enabled = True
            return [{'type': 'text', 'text': 'SAFETY ON - ITERATION LIMITS ENABLED'}]
        elif args == 'OFF':
            self.safety_enabled = False
            return [{'type': 'text', 'text': 'SAFETY OFF - ITERATION LIMITS DISABLED'}]
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
            return [{'type': 'error', 'message': error.format_detailed()}]

