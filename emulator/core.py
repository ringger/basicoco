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
        self.graphics_mode = 0  # 0 = text mode, 1-4 = PMODE graphics
        self.screen_mode = 1    # Screen/color mode
        self.iteration_count = 0  # Safety counter for infinite loops
        self.max_iterations = 50000  # Maximum iterations to prevent infinite loops
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
        
    def execute_command(self, command):
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
        return self.execute_line(command)
    
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
                string_space = int(args)
                # In TRS-80 BASIC, this would set string space
                # For our implementation, we'll just acknowledge it
                self.variable_manager.clear_variables()
                return [{'type': 'text', 'text': f'OK'}]
            except ValueError:
                return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
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
            
            # Clear current program
            self.program.clear()
            self.expanded_program.clear()
            
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
    
    def list_files(self, args=None):
        """List available BASIC program files"""
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
        """Expand line using BasicParser"""
        return BasicParser.expand_line_to_sublines(line_num, code, self.expanded_program)
        
    def run_program(self):
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
        
        output = []
        self.running = True
        self.iteration_count = 0
        
        # Pre-process DATA statements - collect all DATA from program lines
        self.data_statements.clear()
        self.data_pointer = 0
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
            result = self.execute_single_statement(statement)
            
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
            return [{'type': 'error', 'message': 'NO PROGRAM TO CONTINUE'}]
        
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
            result = self.execute_single_statement(statement)
            
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
        """Split a line into statements on colons, but respect quoted strings and IF/THEN constructs"""
        statements = []
        current_statement = ""
        in_quotes = False
        
        # Check if this line contains an IF/THEN construct that starts the line
        code_upper = code.upper().strip()
        if_pos = code_upper.find('IF ')
        then_pos = code_upper.find(' THEN ')
        
        # If this line STARTS with an IF/THEN statement, don't split after THEN
        if if_pos == 0 and then_pos > if_pos:
            # This line starts with IF/THEN - treat the whole thing as one statement
            statements.append(code.strip())
            return statements
        
        # Normal colon splitting for other statements (including FOR loops)
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
    
    
    def execute_line(self, code):
        # Handle multi-statement lines separated by colons
        statements = self.split_statements(code)
        if len(statements) > 1:
            # Execute each statement and collect results
            all_results = []
            for statement in statements:
                result = self.execute_single_statement(statement)
                if result:
                    all_results.extend(result)
                    # Handle jumps in multi-statement lines
                    for item in result:
                        if item.get('type') == 'jump':
                            return all_results  # Return all accumulated results including jump
            return all_results
        else:
            # Single statement
            return self.execute_single_statement(code)
    
    def execute_single_statement(self, code):
        if not code.strip():
            return []
        
        # Try the command registry first
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
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        else:
            # Program execution context
            return [{'type': 'error', 'message': f'SYNTAX ERROR IN {self.current_line}'}]
    
    
    
    
    
    
    
    
    
    # All function evaluation now handled by ExpressionEvaluator
    # Old function methods removed - see expressions.py and functions.py
    
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
        # FOR I=1 TO 10 [STEP 1] - handle colons properly
        args = args.split(':')[0].strip()  # Remove colon and everything after
        
        # Set error context for FOR command
        self.error_context.set_context(self.current_line, f"FOR {args}")
        
        # Better pattern that looks for the word TO, not individual letters
        match = re.match(r'(\w+)\s*=\s*(.+?)\s+TO\s+(.+?)(?:\s+STEP\s+(.+?))?$', args, re.IGNORECASE)
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
        # IF condition THEN [action | multi-line]
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
        
        # Initialize IF stack if needed
        if not hasattr(self, 'if_stack'):
            self.if_stack = []
        
        condition_result = self.evaluate_condition(condition.strip())
        
        # Check if it's a single-line IF or multi-line IF
        if then_part == '' or then_part.upper() == 'THEN':
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
        else:
            # Single-line IF - existing behavior
            if condition_result:
                if then_part.isdigit():
                    # GOTO line number
                    return [{'type': 'jump', 'line': int(then_part)}]
                else:
                    # Execute command
                    return self.execute_line(then_part)
            
            return []
    
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
        except Exception as e:
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
    
    def execute_gosub(self, args):
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
        except Exception as e:
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
        except Exception as e:
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
            
        except Exception as e:
            # Return proper error without masking the exception
            return [{'type': 'error', 'message': f'PAUSE command error: {type(e).__name__}: {e}'}]
    
    def execute_new(self):
        # NEW command - clear program and variables
        self.program.clear()
        self.expanded_program.clear()
        self.variables.clear()
        self.arrays.clear()  # Clear all dimensioned arrays
        self.for_stack.clear()
        self.call_stack.clear()
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
        self.keyboard_buffer.clear()  # Clear keyboard buffer
        self.graphics_mode = 0  # Reset to text mode
        return [{'type': 'text', 'text': 'READY'}]
    
    def execute_end(self, args):
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
            return [{'type': 'error', 'message': 'CAN\'T CONTINUE'}]
        
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
            result = self.execute_single_statement(statement)
            
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
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
            
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
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        except Exception:
            return [{'type': 'error', 'message': 'BAD SUBSCRIPT'}]
    
    def execute_restore(self, args):
        # RESTORE command - reset data pointer to beginning
        self.data_pointer = 0
        return []
    
    def execute_on(self, args):
        # ON variable GOTO/GOSUB line1,line2,line3...
        # ON X GOTO 100,200,300
        # ON Y GOSUB 1000,2000,3000
        args = args.strip()
        
        # Parse: ON variable GOTO/GOSUB lines
        match = re.match(r'ON\s+(\w+)\s+(GOTO|GOSUB)\s+(.+)', args)
        if not match:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        
        var_name = match.group(1)
        command = match.group(2)
        line_list = match.group(3)
        
        # Get variable value
        if var_name not in self.variables:
            return [{'type': 'error', 'message': 'UNDEFINED VARIABLE'}]
        
        var_value = int(self.variables[var_name])
        
        # Parse line numbers
        line_numbers = [int(line.strip()) for line in line_list.split(',')]
        
        # Check if variable value is within range (1-based indexing)
        if var_value < 1 or var_value > len(line_numbers):
            # If out of range, continue to next statement (don't jump)
            return []
        
        # Get the target line number (1-based indexing)
        target_line = line_numbers[var_value - 1]
        
        if command == 'GOTO':
            return [{'type': 'jump', 'line': target_line}]
        elif command == 'GOSUB':
            # Push current position to call stack
            self.call_stack.append((self.current_line, self.current_sub_line))
            return [{'type': 'jump', 'line': target_line}]
        
        return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
    
    def execute_dim(self, args):
        # DIM A(10), B$(5,10), C(20)
        if not args:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        
        # Parse comma-separated array declarations, but be careful with parentheses
        array_defs = []
        current_def = ""
        paren_count = 0
        
        for char in args:
            current_def += char
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            elif char == ',' and paren_count == 0:
                array_defs.append(current_def[:-1].strip())  # Exclude the comma
                current_def = ""
        
        if current_def.strip():
            array_defs.append(current_def.strip())
        
        for array_def in array_defs:
            array_def = array_def.strip()
            
            # Parse array_name(dimensions)
            match = re.match(r'(\w+\$?)\(([^)]+)\)', array_def)
            if not match:
                return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
            
            array_name = match.group(1)
            dimensions_str = match.group(2)
            
            # Check if array name conflicts with reserved function names
            if array_name in self.get_reserved_function_names():
                return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
            
            # Parse dimensions (comma-separated numbers)
            try:
                dimensions = [int(dim.strip()) for dim in dimensions_str.split(',')]
                
                # Validate dimensions (must be positive)
                for dim in dimensions:
                    if dim <= 0:
                        return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
                
                # Check if array is already dimensioned (after syntax validation)
                if array_name in self.arrays:
                    return [{'type': 'error', 'message': 'REDIM\'D ARRAY'}]
                
                # Create multi-dimensional array initialized to 0 or ""
                # Note: Color Computer BASIC arrays - DIM A(10) creates indices 0-10 (11 elements)
                # Each dimension N creates N+1 elements with indices 0 to N
                
                if array_name.endswith('$'):
                    # String array
                    self.arrays[array_name] = self.create_multidim_array(dimensions, "")
                else:
                    # Numeric array
                    self.arrays[array_name] = self.create_multidim_array(dimensions, 0)
                    
            except ValueError:
                return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        
        return []  # DIM doesn't produce output
    
    def create_multidim_array(self, dimensions, init_value):
        # Create nested lists for multi-dimensional array
        if len(dimensions) == 1:
            return [init_value] * (dimensions[0] + 1)  # DIM A(10) creates 11 elements (0-10)
        else:
            return [self.create_multidim_array(dimensions[1:], init_value) for _ in range(dimensions[0] + 1)]
    
    def evaluate_inkey_function(self, expr):
        # INKEY$ - return next key from keyboard buffer or empty string
        # INKEY$ doesn't take parameters, but might be called as INKEY$ or INKEY$(empty)
        if expr == 'INKEY$':
            # Simple INKEY$ call
            pass
        else:
            # Check for INKEY$() format
            if not re.match(r'INKEY\$\(\s*\)', expr):
                raise ValueError(f"Invalid INKEY$ function: {expr}")
        
        # Return the next character from keyboard buffer or empty string
        if self.keyboard_buffer:
            return self.keyboard_buffer.pop(0)
        else:
            return ""
    
    def add_key_to_buffer(self, key):
        # Add a key to the keyboard buffer for INKEY$ to retrieve
        self.keyboard_buffer.append(key)
    
    
    
    
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
        
        self.command_registry.register('FILES', self.list_files,
                                     category='system',
                                     description="List available BASIC program files",
                                     syntax="FILES",
                                     examples=["FILES"])
        
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
    
    def execute_assignment(self, args):
        """Handle variable assignment through LET or direct assignment"""
        return self.execute_line_assignment(args)

    # Phase 3: Enhanced Control Flow Methods
    def execute_while(self, args):
        """WHILE statement - begin conditional loop"""
        # For now, implement legacy-style WHILE tracking
        # Later we can enhance with AST parsing for multi-line support
        if not hasattr(self, 'while_stack'):
            self.while_stack = []
        
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
        if not hasattr(self, 'while_stack') or not self.while_stack:
            return [{'type': 'error', 'message': 'WEND WITHOUT WHILE'}]
        
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
                return [{'type': 'error', 'message': 'EXIT FOR WITHOUT FOR'}]
        else:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
    
    def execute_do(self, args):
        """DO statement - begin DO/LOOP block"""
        if not hasattr(self, 'do_stack'):
            self.do_stack = []
        
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
        if not hasattr(self, 'do_stack') or not self.do_stack:
            return [{'type': 'error', 'message': 'LOOP WITHOUT DO'}]
        
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
        if not hasattr(self, 'if_stack') or not self.if_stack:
            return [{'type': 'error', 'message': 'ELSE WITHOUT IF'}]
        
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
        if not hasattr(self, 'if_stack') or not self.if_stack:
            return [{'type': 'error', 'message': 'ENDIF WITHOUT IF'}]
        
        # Pop the current IF from the stack
        self.if_stack.pop()
        return []

# Global BASIC interpreter instance
basic = CoCoBasic()

