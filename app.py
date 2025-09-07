from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import re
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'trs80-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

class CoCoBasic:
    def __init__(self):
        self.program = {}  # Line number -> code (original for LIST display)
        self.expanded_program = {}  # (line_num, sub_index) -> statement (for execution)
        self.variables = {}
        self.data_statements = []
        self.data_pointer = 0
        self.running = False
        self.current_line = 0
        self.current_sub_line = 0
        self.call_stack = []
        self.for_stack = []
        self.graphics_mode = 0  # 0 = text mode, 1-4 = PMODE graphics
        self.screen_mode = 1    # Screen/color mode
        self.iteration_count = 0  # Safety counter for infinite loops
        self.max_iterations = 10000  # Maximum iterations to prevent infinite loops
        self.waiting_for_input = False  # Flag to indicate we're waiting for user input
        self.program_counter = None  # For resuming execution after input
        self.stopped_position = None  # For CONT command - stores (line, sub_line) where STOP occurred
        self.arrays = {}  # Storage for dimensioned arrays
        self.keyboard_buffer = []  # Buffer for INKEY$ function
        self.current_draw_color = 1  # Default drawing color
        self.turtle_x = 64  # Turtle graphics X position (center of default screen)
        self.turtle_y = 48  # Turtle graphics Y position (center of default screen)
    
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
        line = line.strip().upper()
        if not line:
            return None, None
            
        # Check if line starts with a number
        match = re.match(r'^(\d+)\s+(.*)', line)
        if match:
            line_num = int(match.group(1))
            code = match.group(2)
            return line_num, code
        else:
            # Direct command (no line number)
            return None, line
    
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
        
        # Handle immediate commands
        if command.upper() == 'LIST':
            return self.list_program()
        elif command.upper() == 'RUN':
            return self.run_program()
        elif command.upper() == 'CLEAR':
            return self.clear_program()
        elif command.upper() == 'CLS':
            return [{'type': 'clear_screen'}]
        else:
            # Try to execute as a line of code
            return self.execute_line(command)
    
    def list_program(self):
        output = []
        for line_num in sorted(self.program.keys()):
            output.append({'type': 'text', 'text': f'{line_num} {self.program[line_num]}'})
        return output
    
    def clear_program(self):
        self.program.clear()
        self.expanded_program.clear()
        self.variables.clear()
        return [{'type': 'text', 'text': 'OK'}]
    
    def expand_line_to_sublines(self, line_num, code):
        """Expand a multi-statement line into virtual sub-lines"""
        statements = self.split_statements(code)
        
        # Clear any existing sub-lines for this line number
        keys_to_remove = [key for key in self.expanded_program.keys() if key[0] == line_num]
        for key in keys_to_remove:
            del self.expanded_program[key]
        
        # Create sub-lines
        for sub_index, statement in enumerate(statements):
            self.expanded_program[(line_num, sub_index)] = statement
    
    def run_program(self):
        if not self.program:
            return [{'type': 'error', 'message': 'NO PROGRAM'}]
        
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
                # Check for INPUT requests first
                for item in result:
                    if item.get('type') == 'input_request':
                        # Save our position so we can resume
                        self.program_counter = current_pos_index + 1
                        self.waiting_for_input = True
                        self.running = False  # Pause execution
                        output.append(item)
                        return output  # Return immediately with input request
                
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
                    elif item.get('type') != 'input_request':  # Skip input_request as we handled it above
                        output.append(item)
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
        # Resume program execution after INPUT
        if not hasattr(self, 'program_counter') or self.program_counter is None:
            return [{'type': 'error', 'message': 'NO PROGRAM TO CONTINUE'}]
        
        output = []
        self.running = True
        
        # Get all sub-line positions sorted by (line_num, sub_index)
        all_positions = sorted(self.expanded_program.keys())
        current_pos_index = self.program_counter
        
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
                # Check for INPUT requests first
                for item in result:
                    if item.get('type') == 'input_request':
                        # Save our position so we can resume
                        self.program_counter = current_pos_index + 1
                        self.waiting_for_input = True
                        self.running = False  # Pause execution
                        output.append(item)
                        return output  # Return immediately with input request
                
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
                        output.append(item)
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
    
    def format_number_for_output(self, value):
        """Format a number for BASIC output - integers should not show decimal"""
        if isinstance(value, (int, float)):
            if isinstance(value, float) and value.is_integer():
                return str(int(value))
            else:
                return str(value)
        return str(value)
    
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
        parts = code.split()
        if not parts:
            return []
            
        first_part = parts[0]
        
        # Handle commands with parentheses (graphics commands) - case insensitive
        first_part_upper = first_part.upper()
        if first_part_upper.startswith('PSET('):
            paren_pos = first_part.find('(')
            # Reconstruct the full arguments from all parts
            args = first_part[paren_pos:] + (' ' + ' '.join(parts[1:]) if len(parts) > 1 else '')
            return self.execute_pset(args)
        elif first_part_upper.startswith('PRESET('):
            paren_pos = first_part.find('(')
            args = first_part[paren_pos:] + (' ' + ' '.join(parts[1:]) if len(parts) > 1 else '')
            return self.execute_preset(args)
        elif first_part_upper.startswith('CIRCLE('):
            paren_pos = first_part.find('(')
            args = first_part[paren_pos:] + (' ' + ' '.join(parts[1:]) if len(parts) > 1 else '')
            return self.execute_circle(args)
        elif first_part_upper.startswith('LINE('):
            paren_pos = first_part.find('(')
            args = first_part[paren_pos:] + (' ' + ' '.join(parts[1:]) if len(parts) > 1 else '')
            return self.execute_line_graphics(args)
        
        # Regular command parsing (case insensitive)
        command = first_part.upper()
        
        if command == 'PRINT':
            return self.execute_print(' '.join(parts[1:]))
        elif command == 'INPUT':
            return self.execute_input(' '.join(parts[1:]))
        elif command == 'CLS':
            return [{'type': 'clear_screen'}]
        elif command == 'LET':
            return self.execute_let(' '.join(parts[1:]))
        elif command == 'FOR':
            return self.execute_for(' '.join(parts[1:]))
        elif command == 'NEXT':
            return self.execute_next(' '.join(parts[1:]))
        elif command == 'IF':
            return self.execute_if(' '.join(parts[1:]))
        elif command == 'GOTO':
            return self.execute_goto(' '.join(parts[1:]))
        elif command == 'GOSUB':
            return self.execute_gosub(' '.join(parts[1:]))
        elif command == 'RETURN':
            return self.execute_return()
        elif command == 'PMODE':
            return self.execute_pmode(' '.join(parts[1:]))
        elif command == 'SCREEN':
            return self.execute_screen(' '.join(parts[1:]))
        elif command == 'PCLS':
            return [{'type': 'pcls'}]
        elif command == 'COLOR':
            return self.execute_color(' '.join(parts[1:]))
        elif command == 'PSET':
            return self.execute_pset(' '.join(parts[1:]))
        elif command == 'PRESET':
            return self.execute_preset(' '.join(parts[1:]))
        elif command == 'CIRCLE':
            return self.execute_circle(' '.join(parts[1:]))
        elif command == 'LINE':
            return self.execute_line_graphics(' '.join(parts[1:]))
        elif command == 'SOUND':
            return self.execute_sound(' '.join(parts[1:]))
        elif command == 'REM':
            # Comments - do nothing, just return empty
            return []
        elif command == 'NEW':
            return self.execute_new()
        elif command == 'END' or command == 'STOP':
            return self.execute_end()
        elif command == 'CONT':
            return self.execute_cont()
        elif command == 'DATA':
            return self.execute_data(' '.join(parts[1:]))
        elif command == 'READ':
            return self.execute_read(' '.join(parts[1:]))
        elif command == 'RESTORE':
            return self.execute_restore()
        elif command.startswith('ON'):
            return self.execute_on(' '.join(parts))
        elif command == 'DIM':
            return self.execute_dim(' '.join(parts[1:]))
        elif command == 'GET':
            return self.execute_get(' '.join(parts[1:]))
        elif command == 'PUT':
            return self.execute_put(' '.join(parts[1:]))
        elif command == 'DRAW':
            return self.execute_draw(' '.join(parts[1:]))
        elif first_part_upper.startswith('PAINT('):
            paren_pos = first_part.find('(')
            return self.execute_paint(first_part[paren_pos:])
        elif '=' in code:
            # Variable assignment without LET
            return self.execute_let(code)
        else:
            return [{'type': 'error', 'message': f'SYNTAX ERROR IN {self.current_line}'}]
    
    def execute_print(self, args):
        if not args:
            return [{'type': 'text', 'text': ''}]
        
        # Handle multiple print items separated by semicolons and commas
        items_with_separators = self.split_print_args_with_separators(args)
        output_parts = []
        
        for i, (item, separator) in enumerate(items_with_separators):
            item = item.strip()
            if not item and i == 0:  # Skip empty first item
                continue
                
            try:
                # Try to evaluate the expression
                value = self.evaluate_expression(item)
                formatted_value = self.format_number_for_output(value)
            except ValueError as e:
                # Check for specific BASIC errors that should be propagated
                error_msg = str(e)
                if "UNDIM'D ARRAY" in error_msg or "BAD SUBSCRIPT" in error_msg:
                    return [{'type': 'error', 'message': error_msg.split(':')[0] if ':' in error_msg else error_msg}]
                # If evaluation fails, try simple cases
                if item.startswith('"') and item.endswith('"'):
                    formatted_value = item[1:-1]
                elif item in self.variables:
                    formatted_value = self.format_number_for_output(self.variables[item])
                elif item.replace('.', '').replace('-', '').isdigit():
                    formatted_value = item
                else:
                    formatted_value = item  # Print as-is
            except Exception as e:
                # For other exceptions, try simple cases
                if item.startswith('"') and item.endswith('"'):
                    formatted_value = item[1:-1]
                elif item in self.variables:
                    formatted_value = self.format_number_for_output(self.variables[item])
                elif item.replace('.', '').replace('-', '').isdigit():
                    formatted_value = item
                else:
                    formatted_value = item  # Print as-is
            
            # Add the formatted value
            if formatted_value or i == 0:  # Always add first item, even if empty
                output_parts.append(formatted_value)
                
                # Add separator if not the last item
                if i < len(items_with_separators) - 1:
                    if separator == ';':
                        # Semicolon: no extra space
                        pass
                    elif separator == ',':
                        # Comma: add spacing (tab stop simulation)
                        output_parts.append('    ')  # 4 spaces for tab stop
                    else:
                        # Default: single space
                        output_parts.append(' ')
        
        text = ''.join(output_parts)
        return [{'type': 'text', 'text': text}]
    
    def split_print_args(self, args):
        # Split on semicolons and commas, but respect function parentheses
        items = []
        current_item = ""
        paren_depth = 0
        
        for char in args:
            if char == '(':
                paren_depth += 1
                current_item += char
            elif char == ')':
                paren_depth -= 1
                current_item += char
            elif char in [';', ','] and paren_depth == 0:
                if current_item.strip():
                    items.append(current_item.strip())
                current_item = ""
            else:
                current_item += char
        
        if current_item.strip():
            items.append(current_item.strip())
        
        return items
    
    def split_print_args_with_separators(self, args):
        # Split on semicolons and commas, but respect function parentheses and quoted strings
        # Return list of (item, separator) tuples
        items = []
        current_item = ""
        paren_depth = 0
        in_quote = False
        
        for i, char in enumerate(args):
            if char == '"' and not in_quote:
                in_quote = True
                current_item += char
            elif char == '"' and in_quote:
                in_quote = False
                current_item += char
            elif char == '(' and not in_quote:
                paren_depth += 1
                current_item += char
            elif char == ')' and not in_quote:
                paren_depth -= 1
                current_item += char
            elif char in [';', ','] and paren_depth == 0 and not in_quote:
                # Found separator at top level (not inside quotes or parentheses)
                separator = char
                if current_item.strip():
                    items.append((current_item.strip(), separator))
                else:
                    items.append(('', separator))
                current_item = ""
            else:
                current_item += char
        
        # Add the last item (no separator after the last item)
        if current_item.strip():
            items.append((current_item.strip(), None))
        elif items:  # If we have items but last is empty, still add it
            items.append(('', None))
        
        return items
    
    def find_matching_paren(self, text, start_pos=0):
        """Find the position of the matching closing parenthesis"""
        paren_count = 0
        for i in range(start_pos, len(text)):
            if text[i] == '(':
                paren_count += 1
            elif text[i] == ')':
                paren_count -= 1
                if paren_count == 0:
                    return i
        return -1  # No matching parenthesis found
    
    def split_args_respecting_parentheses(self, args):
        """Split arguments on commas while respecting parentheses"""
        items = []
        current_item = ""
        paren_depth = 0
        
        for char in args:
            if char == '(':
                paren_depth += 1
                current_item += char
            elif char == ')':
                paren_depth -= 1
                current_item += char
            elif char == ',' and paren_depth == 0:
                # Found separator at top level
                items.append(current_item.strip())
                current_item = ""
            else:
                current_item += char
        
        # Add the last item
        if current_item.strip():
            items.append(current_item.strip())
        
        return items
    
    def execute_input(self, args):
        # Handle INPUT with optional prompt
        # INPUT "PROMPT"; VAR or INPUT VAR1, VAR2, VAR3
        prompt = ""
        var_names = []
        
        if '"' in args:
            # Find the string literal prompt
            match = re.match(r'"([^"]*)"[;,]?\s*(.*)', args)
            if match:
                prompt = match.group(1)
                vars_part = match.group(2).strip()
            else:
                return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        else:
            # Simple INPUT VAR1, VAR2, etc.
            vars_part = args.strip()
            prompt = "? "
        
        # Parse variable names (comma-separated)
        if vars_part:
            var_names = [var.strip() for var in vars_part.split(',')]
        
        if not var_names:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        
        # Validate first variable name (allow array notation like A$(1))
        first_var = var_names[0]
        if not first_var:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        
        # Check if it's a valid variable name or array element
        # Valid: A, A$, A(1), A$(1), etc.
        if not (re.match(r'^[A-Za-z]\w*\$?$', first_var) or 
                re.match(r'^[A-Za-z]\w*\$?\([^)]+\)$', first_var)):
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        
        # Return an input request for the first variable (simplified implementation)
        # In a full implementation, this would handle multiple variables sequentially
        return [{'type': 'input_request', 'prompt': prompt, 'variable': first_var}]
    
    def execute_let(self, args):
        if '=' not in args:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        
        parts = args.split('=', 1)
        var_name = parts[0].strip()
        expression = parts[1].strip()
        
        # Validate variable name
        if not var_name:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        
        # Normalize variable name to uppercase for case insensitivity
        var_name = var_name.upper()
        
        # Check if this is an array assignment (A(5) = 10) and validate reserved names
        array_match = re.match(r'(\w+\$?)\(([^)]+)\)', var_name)
        base_var_name = array_match.group(1) if array_match else var_name
        
        # Check if variable name conflicts with reserved function names
        if base_var_name in self.get_reserved_function_names():
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        if array_match:
            # Array assignment
            array_name = array_match.group(1)
            indices_str = array_match.group(2)
            
            # Check if array exists
            if array_name not in self.arrays:
                return [{'type': 'error', 'message': 'UNDIM\'D ARRAY'}]
            
            # Parse indices
            try:
                indices = [int(self.evaluate_expression(idx.strip())) for idx in indices_str.split(',')]
                
                # Evaluate the expression value
                if expression.startswith('"') and expression.endswith('"'):
                    value = expression[1:-1]  # String value
                else:
                    value = self.evaluate_expression(expression)
                
                # Set array element
                current = self.arrays[array_name]
                for i, idx in enumerate(indices[:-1]):
                    if idx < 0 or idx >= len(current):
                        return [{'type': 'error', 'message': 'BAD SUBSCRIPT'}]
                    current = current[idx]
                
                # Set the final element
                final_idx = indices[-1]
                if final_idx < 0 or final_idx >= len(current):
                    return [{'type': 'error', 'message': 'BAD SUBSCRIPT'}]
                
                current[final_idx] = value
                
            except ValueError:
                return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
            except Exception:
                return [{'type': 'error', 'message': 'BAD SUBSCRIPT'}]
        else:
            # Regular variable assignment
            try:
                if expression.startswith('"') and expression.endswith('"'):
                    # String value
                    self.variables[var_name] = expression[1:-1]
                elif expression.replace('.', '').replace('-', '').isdigit():
                    # Numeric value
                    self.variables[var_name] = float(expression) if '.' in expression else int(expression)
                elif expression in self.variables:
                    # Copy from another variable
                    self.variables[var_name] = self.variables[expression]
                else:
                    # Try to evaluate as a simple math expression
                    self.variables[var_name] = self.evaluate_expression(expression)
            except:
                return [{'type': 'error', 'message': 'TYPE MISMATCH'}]
        
        return [{'type': 'text', 'text': 'OK'}]
    
    def evaluate_single_function(self, expr):
        """Handle single function calls (when entire expression is one function)"""
        expr = expr.strip()
        
        # Check if this is truly a single function call by verifying that it starts with
        # a function name, has matching parentheses, and doesn't have extra content after
        function_names = ['LEFT$', 'RIGHT$', 'MID$', 'LEN', 'ABS', 'INT', 'RND', 'SQR',
                         'SIN', 'COS', 'TAN', 'ATN', 'EXP', 'LOG', 'CHR$', 'ASC', 'STR$', 'VAL']
        
        for func_name in function_names:
            if expr.startswith(func_name + '('):
                # Extract the full function call to see if it matches the entire expression
                args_str = self.extract_function_args(expr, func_name)
                if args_str is not None:
                    # Reconstruct the expected function call
                    expected = f"{func_name}({args_str})"
                    if expr == expected:
                        # This is indeed a single function call
                        if func_name == 'LEFT$':
                            return self.evaluate_left_function(expr)
                        elif func_name == 'RIGHT$':
                            return self.evaluate_right_function(expr)
                        elif func_name == 'MID$':
                            return self.evaluate_mid_function(expr)
                        elif func_name == 'LEN':
                            return self.evaluate_len_function(expr)
                        elif func_name == 'ABS':
                            return self.evaluate_abs_function(expr)
                        elif func_name == 'INT':
                            return self.evaluate_int_function(expr)
                        elif func_name == 'RND':
                            return self.evaluate_rnd_function(expr)
                        elif func_name == 'SQR':
                            return self.evaluate_sqr_function(expr)
                        elif func_name == 'SIN':
                            return self.evaluate_sin_function(expr)
                        elif func_name == 'COS':
                            return self.evaluate_cos_function(expr)
                        elif func_name == 'TAN':
                            return self.evaluate_tan_function(expr)
                        elif func_name == 'ATN':
                            return self.evaluate_atn_function(expr)
                        elif func_name == 'EXP':
                            return self.evaluate_exp_function(expr)
                        elif func_name == 'LOG':
                            return self.evaluate_log_function(expr)
                        elif func_name == 'CHR$':
                            return self.evaluate_chr_function(expr)
                        elif func_name == 'ASC':
                            return self.evaluate_asc_function(expr)
                        elif func_name == 'STR$':
                            return self.evaluate_str_function(expr)
                        elif func_name == 'VAL':
                            return self.evaluate_val_function(expr)
        
        # Special case for INKEY$ (with or without parentheses)
        if expr == 'INKEY$' or re.match(r'INKEY\$\(\s*\)', expr):
            return self.evaluate_inkey_function(expr)
        
        return None  # No single function match
    
    def substitute_basic_functions(self, expr):
        """Substitute BASIC function calls with their evaluated results"""
        original_expr = expr
        
        # List of functions to substitute
        functions = ['LEFT$', 'RIGHT$', 'MID$', 'LEN', 'ABS', 'INT', 'RND', 'SQR', 
                    'SIN', 'COS', 'TAN', 'ATN', 'EXP', 'LOG', 'CHR$', 'ASC', 'STR$', 'VAL']
        
        # Keep substituting until no more functions found
        changed = True
        while changed:
            changed = False
            for func_name in functions:
                # Find function calls and replace them
                search_pattern = f'{func_name}('
                pos = 0
                while pos < len(expr):
                    pos = expr.find(search_pattern, pos)
                    if pos == -1:
                        break
                    
                    # Find the matching closing parenthesis
                    paren_count = 0
                    start_pos = pos + len(search_pattern) - 1  # Position of opening parenthesis
                    end_pos = -1
                    
                    for i in range(start_pos, len(expr)):
                        if expr[i] == '(':
                            paren_count += 1
                        elif expr[i] == ')':
                            paren_count -= 1
                            if paren_count == 0:
                                end_pos = i
                                break
                    
                    if end_pos != -1:
                        # Extract the complete function call
                        func_call = expr[pos:end_pos + 1]
                        try:
                            # Evaluate the function call
                            result = self.evaluate_single_function(func_call)
                            if result is not None:
                                # Replace the function call with its result
                                if isinstance(result, str):
                                    # For string results, wrap in quotes for eval
                                    replacement = '"' + result.replace('"', '\\"') + '"'
                                else:
                                    replacement = str(result)
                                expr = expr[:pos] + replacement + expr[end_pos + 1:]
                                changed = True
                                # Don't increment pos, re-scan from current position
                                continue
                        except:
                            pass  # If function evaluation fails, leave it as-is
                    
                    pos += len(search_pattern)
        
        return expr
    
    def evaluate_expression(self, expr):
        expr = expr.strip()
        original_expr = expr
        
        # First, check if the entire expression is a single function call
        single_func_result = self.evaluate_single_function(expr)
        if single_func_result is not None:
            return single_func_result
        
        # For complex expressions, substitute BASIC functions first
        expr = self.substitute_basic_functions(expr)
        
        # Check for simple array access only (entire expression is just array access)
        array_match = re.match(r'^(\w+\$?)\(([^)]+)\)$', expr)
        if array_match:
            array_name = array_match.group(1)
            indices_str = array_match.group(2)
            
            # Check if array exists
            if array_name not in self.arrays:
                raise ValueError(f"UNDIM'D ARRAY: {array_name}")
            
            # Parse indices
            try:
                indices = [int(self.evaluate_simple_expression(idx.strip())) for idx in indices_str.split(',')]
                
                # Get array element
                current = self.arrays[array_name]
                for idx in indices[:-1]:
                    if idx < 0 or idx >= len(current):
                        raise ValueError("BAD SUBSCRIPT")
                    current = current[idx]
                
                # Get the final element
                final_idx = indices[-1]
                if final_idx < 0 or final_idx >= len(current):
                    raise ValueError("BAD SUBSCRIPT")
                
                return current[final_idx]
                
            except ValueError as ve:
                if "BAD SUBSCRIPT" in str(ve) or "UNDIM'D ARRAY" in str(ve):
                    raise ve
                raise ValueError("SYNTAX ERROR")
        
        # Handle string literals
        if expr.startswith('"') and expr.endswith('"'):
            return expr[1:-1]  # Return string without quotes
        
        # Check if this is a simple variable reference (case insensitive)
        if re.match(r'^\w+\$?$', expr):
            expr_upper = expr.upper()
            if expr_upper in self.variables:
                return self.variables[expr_upper]
        
        # Replace array accesses with their values for complex expressions
        array_pattern = r'(\w+\$?)\(([^)]+)\)'
        def replace_array_access(match):
            array_name = match.group(1)
            indices_str = match.group(2)
            
            # Check if array exists
            if array_name not in self.arrays:
                raise ValueError(f"UNDIM'D ARRAY: {array_name}")
            
            # Parse indices
            try:
                indices = [int(self.evaluate_simple_expression(idx.strip())) for idx in indices_str.split(',')]
                
                # Get array element
                current = self.arrays[array_name]
                for idx in indices[:-1]:
                    if idx < 0 or idx >= len(current):
                        raise ValueError("BAD SUBSCRIPT")
                    current = current[idx]
                
                # Get the final element
                final_idx = indices[-1]
                if final_idx < 0 or final_idx >= len(current):
                    raise ValueError("BAD SUBSCRIPT")
                
                # Return the value, wrapped in quotes if it's a string
                value = current[final_idx]
                if isinstance(value, str):
                    return '"' + value.replace('"', '\\"') + '"'
                else:
                    return str(value)
                
            except ValueError as ve:
                if "BAD SUBSCRIPT" in str(ve) or "UNDIM'D ARRAY" in str(ve):
                    raise ve
                raise ValueError("SYNTAX ERROR")
        
        # Apply array access replacement
        original_expr = expr
        expr = re.sub(array_pattern, replace_array_access, expr)
        
        # Replace variables with their values for complex expressions (case insensitive)
        for var, val in self.variables.items():
            # Use word boundary for variables, but handle $ specially
            if var.endswith('$'):
                # For string variables ending in $, match word boundary before and non-alphanumeric after
                pattern = r'\b' + re.escape(var) + r'(?![A-Za-z0-9_$])'
            else:
                # For numeric variables, use standard word boundaries
                pattern = r'\b' + re.escape(var) + r'\b'
            if re.search(pattern, expr, re.IGNORECASE):
                if isinstance(val, str):
                    # For string values, wrap in quotes for eval
                    replacement = '"' + val.replace('"', '\\"') + '"'
                else:
                    replacement = str(val)
                expr = re.sub(pattern, replacement, expr, flags=re.IGNORECASE)
        
        # Simple evaluation (dangerous in real code, but OK for demo)
        try:
            result = eval(expr)
            return result
        except ZeroDivisionError:
            # Handle division by zero - in BASIC, this produces infinity and continues execution
            return float('inf')  # Return positive infinity and continue execution
        except Exception as e:
            raise ValueError(f"Invalid expression '{original_expr}': {e}")
    
    def evaluate_left_function(self, expr):
        # LEFT$(string, n) - get leftmost n characters
        args_str = self.extract_function_args(expr, 'LEFT$')
        if args_str is None:
            raise ValueError(f"Invalid LEFT$ function: {expr}")
        
        # Parse the comma-separated arguments with proper parentheses handling
        args = self.parse_function_arguments(args_str, 2)
        if len(args) != 2:
            raise ValueError(f"LEFT$ requires exactly 2 arguments: {expr}")
        
        string_expr, n_expr = args
        
        # Evaluate the string and number parts
        string_val = self.evaluate_expression(string_expr)
        n_val = int(self.evaluate_expression(n_expr))
        
        result = str(string_val)[:n_val]
        return result
    
    def evaluate_right_function(self, expr):
        # RIGHT$(string, n) - get rightmost n characters
        args_str = self.extract_function_args(expr, 'RIGHT$')
        if args_str is None:
            raise ValueError(f"Invalid RIGHT$ function: {expr}")
        
        # Parse the comma-separated arguments with proper parentheses handling
        args = self.parse_function_arguments(args_str, 2)
        if len(args) != 2:
            raise ValueError(f"RIGHT$ requires exactly 2 arguments: {expr}")
        
        string_expr, n_expr = args
        
        # Evaluate the string and number parts
        string_val = self.evaluate_expression(string_expr)
        n_val = int(self.evaluate_expression(n_expr))
        
        result = str(string_val)[-n_val:] if n_val > 0 else ""
        return result
    
    def evaluate_mid_function(self, expr):
        # MID$(string, start, length) - get substring
        args_str = self.extract_function_args(expr, 'MID$')
        if args_str is None:
            raise ValueError(f"Invalid MID$ function: {expr}")
        
        # Parse the comma-separated arguments with proper parentheses handling
        args = self.parse_function_arguments(args_str, 3)
        if len(args) < 2 or len(args) > 3:
            raise ValueError(f"MID$ requires 2 or 3 arguments: {expr}")
        
        string_expr = args[0]
        start_expr = args[1]
        length_expr = args[2] if len(args) == 3 else None
        
        # Evaluate the parts
        string_val = str(self.evaluate_expression(string_expr))
        start_val = int(self.evaluate_expression(start_expr)) - 1  # BASIC is 1-based, Python is 0-based
        
        if length_expr:
            length_val = int(self.evaluate_expression(length_expr))
            result = string_val[start_val:start_val + length_val]
        else:
            result = string_val[start_val:]
        
        return result
    
    def extract_function_args(self, expr, func_name):
        """Extract function arguments handling nested parentheses properly"""
        prefix = f"{func_name}("
        if not expr.startswith(prefix):
            return None
        
        # Find the matching closing parenthesis
        paren_count = 0
        start_pos = len(prefix) - 1  # Start at the opening parenthesis
        
        for i, char in enumerate(expr[start_pos:], start_pos):
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
                if paren_count == 0:
                    # Found the matching closing parenthesis
                    args_str = expr[len(prefix):i]
                    return args_str.strip()
        
        return None  # No matching parenthesis found
    
    def parse_function_arguments(self, args_str, expected_count):
        """Parse comma-separated function arguments handling nested parentheses"""
        if not args_str.strip():
            return []
        
        args = []
        current_arg = ""
        paren_count = 0
        
        for char in args_str:
            if char == ',' and paren_count == 0:
                # Found argument separator at top level
                args.append(current_arg.strip())
                current_arg = ""
            else:
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                current_arg += char
        
        # Add the last argument
        if current_arg.strip():
            args.append(current_arg.strip())
        
        return args
    
    def evaluate_len_function(self, expr):
        # LEN(string) - get length of string
        args_str = self.extract_function_args(expr, 'LEN')
        if args_str is None:
            raise ValueError(f"Invalid LEN function: {expr}")
        
        string_val = str(self.evaluate_expression(args_str))
        return len(string_val)
    
    def evaluate_abs_function(self, expr):
        # ABS(number) - absolute value
        args_str = self.extract_function_args(expr, 'ABS')
        if args_str is None:
            raise ValueError(f"Invalid ABS function: {expr}")
        
        num_val = float(self.evaluate_expression(args_str))
        return abs(num_val)
    
    def evaluate_int_function(self, expr):
        # INT(number) - integer part (floor)
        args_str = self.extract_function_args(expr, 'INT')
        if args_str is None:
            raise ValueError(f"Invalid INT function: {expr}")
        
        num_val = float(self.evaluate_expression(args_str))
        return int(num_val)
    
    def evaluate_rnd_function(self, expr):
        # RND(n) - random number
        import random
        args_str = self.extract_function_args(expr, 'RND')
        if args_str is None:
            raise ValueError(f"Invalid RND function: {expr}")
        
        num_val = float(self.evaluate_expression(args_str))
        
        if num_val > 0:
            return random.random()  # 0 to 1
        elif num_val == 0:
            return random.random()  # same as positive
        else:
            # Negative repeats last random number (simplified)
            return random.random()
    
    def evaluate_sqr_function(self, expr):
        # SQR(number) - square root
        import math
        args_str = self.extract_function_args(expr, 'SQR')
        if args_str is None:
            raise ValueError(f"Invalid SQR function: {expr}")
        
        num_val = float(self.evaluate_expression(args_str))
        
        if num_val < 0:
            raise ValueError("SQR of negative number")
        
        return math.sqrt(num_val)
    
    def evaluate_sin_function(self, expr):
        # SIN(radians) - sine
        import math
        args_str = self.extract_function_args(expr, 'SIN')
        if args_str is None:
            raise ValueError(f"Invalid SIN function: {expr}")
        
        num_val = float(self.evaluate_expression(args_str))
        return math.sin(num_val)
    
    def evaluate_cos_function(self, expr):
        # COS(radians) - cosine
        import math
        args_str = self.extract_function_args(expr, 'COS')
        if args_str is None:
            raise ValueError(f"Invalid COS function: {expr}")
        
        num_val = float(self.evaluate_expression(args_str))
        return math.cos(num_val)
    
    def evaluate_tan_function(self, expr):
        # TAN(radians) - tangent
        import math
        args_str = self.extract_function_args(expr, 'TAN')
        if args_str is None:
            raise ValueError(f"Invalid TAN function: {expr}")
        
        num_val = float(self.evaluate_expression(args_str))
        return math.tan(num_val)
    
    def evaluate_atn_function(self, expr):
        # ATN(number) - arctangent
        import math
        args_str = self.extract_function_args(expr, 'ATN')
        if args_str is None:
            raise ValueError(f"Invalid ATN function: {expr}")
        
        num_val = float(self.evaluate_expression(args_str))
        return math.atan(num_val)
    
    def evaluate_exp_function(self, expr):
        # EXP(number) - e raised to the power
        import math
        args_str = self.extract_function_args(expr, 'EXP')
        if args_str is None:
            raise ValueError(f"Invalid EXP function: {expr}")
        
        num_val = float(self.evaluate_expression(args_str))
        return math.exp(num_val)
    
    def evaluate_log_function(self, expr):
        # LOG(number) - natural logarithm
        import math
        args_str = self.extract_function_args(expr, 'LOG')
        if args_str is None:
            raise ValueError(f"Invalid LOG function: {expr}")
        
        num_val = float(self.evaluate_expression(args_str))
        
        if num_val <= 0:
            raise ValueError("LOG of zero or negative number")
        
        return math.log(num_val)
    
    def evaluate_chr_function(self, expr):
        # CHR$(n) - character from ASCII code
        args_str = self.extract_function_args(expr, 'CHR$')
        if args_str is None:
            raise ValueError(f"Invalid CHR$ function: {expr}")
        
        num_val = int(self.evaluate_expression(args_str))
        
        if num_val < 0 or num_val > 255:
            raise ValueError("CHR$ argument out of range")
        
        return chr(num_val)
    
    def evaluate_asc_function(self, expr):
        # ASC(string) - ASCII code of first character
        args_str = self.extract_function_args(expr, 'ASC')
        if args_str is None:
            raise ValueError(f"Invalid ASC function: {expr}")
        
        string_val = str(self.evaluate_expression(args_str))
        
        if len(string_val) == 0:
            raise ValueError("ASC of empty string")
        
        return ord(string_val[0])
    
    def evaluate_str_function(self, expr):
        # STR$(number) - convert number to string
        args_str = self.extract_function_args(expr, 'STR$')
        if args_str is None:
            raise ValueError(f"Invalid STR$ function: {expr}")
        
        num_val = self.evaluate_expression(args_str)
        
        # Format like BASIC does - with leading space for positive numbers
        if isinstance(num_val, int):
            return f" {num_val}" if num_val >= 0 else str(num_val)
        else:
            return f" {num_val}" if num_val >= 0 else str(num_val)
    
    def evaluate_val_function(self, expr):
        # VAL(string) - convert string to number
        args_str = self.extract_function_args(expr, 'VAL')
        if args_str is None:
            raise ValueError(f"Invalid VAL function: {expr}")
        
        string_val = str(self.evaluate_expression(args_str)).strip()
        
        try:
            # Try to parse as integer first, then float
            if '.' in string_val or 'E' in string_val.upper():
                return float(string_val)
            else:
                return int(string_val)
        except ValueError:
            # Return 0 if cannot parse (BASIC behavior)
            return 0
    
    def evaluate_simple_expression(self, expr):
        # Simple expression evaluation without recursion into string functions
        expr = expr.strip()
        
        # Handle string literals
        if expr.startswith('"') and expr.endswith('"'):
            return expr[1:-1]  # Return string without quotes
        
        # Check for array access (A(5) or B$(2,3))
        array_match = re.match(r'(\w+\$?)\(([^)]+)\)', expr)
        if array_match:
            array_name = array_match.group(1)
            indices_str = array_match.group(2)
            
            # Check if array exists
            if array_name not in self.arrays:
                raise ValueError(f"UNDIM'D ARRAY: {array_name}")
            
            # Parse indices
            try:
                indices = [int(self.evaluate_simple_expression(idx.strip())) for idx in indices_str.split(',')]
                
                # Get array element
                current = self.arrays[array_name]
                for idx in indices[:-1]:
                    if idx < 0 or idx >= len(current):
                        raise ValueError("BAD SUBSCRIPT")
                    current = current[idx]
                
                # Get the final element
                final_idx = indices[-1]
                if final_idx < 0 or final_idx >= len(current):
                    raise ValueError("BAD SUBSCRIPT")
                
                return current[final_idx]
                
            except ValueError as ve:
                if "BAD SUBSCRIPT" in str(ve) or "UNDIM'D ARRAY" in str(ve):
                    raise ve
                raise ValueError("SYNTAX ERROR")
        
        # Handle variables
        if expr in self.variables:
            return self.variables[expr]
        
        # Handle numbers
        try:
            if '.' in expr:
                return float(expr)
            else:
                return int(expr)
        except ValueError:
            pass
        
        # Replace variables with their values for mathematical expressions
        original_expr = expr
        for var, val in self.variables.items():
            if var in expr:
                expr = re.sub(r'\b' + re.escape(var) + r'\b', str(val), expr)
        
        # Evaluate mathematical expressions
        try:
            result = eval(expr)
            return result
        except ZeroDivisionError:
            # Handle division by zero - in BASIC, this produces infinity and continues execution
            # We need to signal this error while allowing execution to continue
            # For now, return infinity - the calling context should handle the error display
            return float('inf')  # Return positive infinity and continue execution
        except Exception as e:
            raise ValueError(f"Invalid simple expression '{original_expr}': {e}")
    
    def execute_for(self, args):
        # FOR I=1 TO 10 [STEP 1] - handle colons properly
        args = args.split(':')[0].strip()  # Remove colon and everything after
        
        match = re.match(r'(\w+)\s*=\s*([^TO\s]+)\s+TO\s+([^STEP\s:]+)(?:\s+STEP\s+([^:\s]+))?', args)
        if not match:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        
        var_name = match.group(1).strip()
        start_val = self.evaluate_expression(match.group(2).strip())
        end_val = self.evaluate_expression(match.group(3).strip())
        step_val = self.evaluate_expression(match.group(4).strip()) if match.group(4) else 1
        
        # Ensure numeric values for comparison
        try:
            start_val = float(start_val) if isinstance(start_val, str) else start_val
            end_val = float(end_val) if isinstance(end_val, str) else end_val
            step_val = float(step_val) if isinstance(step_val, str) else step_val
        except (ValueError, TypeError):
            return [{'type': 'error', 'message': 'TYPE MISMATCH'}]
        
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
            return [{'type': 'error', 'message': 'NEXT WITHOUT FOR'}]
        
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
        # IF condition THEN action
        if ' THEN ' not in args:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        
        condition, action = args.split(' THEN ', 1)
        
        if self.evaluate_condition(condition.strip()):
            if action.strip().isdigit():
                # GOTO line number
                return [{'type': 'jump', 'line': int(action.strip())}]
            else:
                # Execute command
                return self.execute_line(action.strip())
        
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
        try:
            line_num = int(args.strip())
            return [{'type': 'jump', 'line': line_num}]
        except:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
    
    def execute_gosub(self, args):
        try:
            line_num = int(args.strip())
            self.call_stack.append((self.current_line, self.current_sub_line))
            return [{'type': 'jump', 'line': line_num}]
        except:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
    
    def execute_return(self):
        if not self.call_stack:
            return [{'type': 'error', 'message': 'RETURN WITHOUT GOSUB'}]
        
        return_line, return_sub_line = self.call_stack.pop()
        
        # Return to the sub-line after the GOSUB call
        return [{'type': 'jump_return', 'line': return_line, 'sub_line': return_sub_line}]
    
    def execute_pmode(self, args):
        parts = args.split(',')
        if len(parts) < 1:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        
        try:
            mode = int(parts[0].strip())
            if mode < 0 or mode > 4:
                return [{'type': 'error', 'message': 'ILLEGAL FUNCTION CALL'}]
            
            self.graphics_mode = mode
            page = int(parts[1].strip()) if len(parts) > 1 else 1
            
            return [{'type': 'pmode', 'mode': mode, 'page': page}]
        except:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
    
    def execute_screen(self, args):
        try:
            # SCREEN can take 1 or 2 parameters: SCREEN mode or SCREEN fg,bg
            parts = args.split(',')
            screen_mode = int(parts[0].strip())
            
            if screen_mode < 1 or screen_mode > 8:
                return [{'type': 'error', 'message': 'ILLEGAL FUNCTION CALL'}]
            
            self.screen_mode = screen_mode
            
            # Handle optional background color parameter
            bg_color = None
            if len(parts) > 1:
                bg_color = int(parts[1].strip())
            
            return [{'type': 'set_screen', 'mode': screen_mode, 'bg': bg_color}]
        except:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
    
    def execute_pset(self, args):
        # PSET(x,y) or PSET(x,y,color) or PSET x,y or PSET x,y,color
        args = args.strip()
        
        # Handle parentheses format: PSET(x,y) or PSET(x,y,color)
        if args.startswith('(') and ')' in args:
            # Extract content between matching parentheses
            close_paren_pos = self.find_matching_paren(args)
            if close_paren_pos == -1:
                return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
            paren_content = args[1:close_paren_pos]
            coords = self.split_args_respecting_parentheses(paren_content)
        else:
            # Handle space-separated format: PSET x,y or PSET x,y,color
            coords = self.split_args_respecting_parentheses(args)
        
        if len(coords) < 2:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        
        try:
            x = int(float(self.evaluate_expression(coords[0].strip())))
            y = int(float(self.evaluate_expression(coords[1].strip())))
            color = int(float(self.evaluate_expression(coords[2].strip()))) if len(coords) > 2 else None
            
            return [{'type': 'pset', 'x': x, 'y': y, 'color': color}]
        except Exception as e:
            return [{'type': 'error', 'message': f'PSET ERROR: {str(e)}'}]
    
    def execute_preset(self, args):
        # PRESET(x,y) or PRESET x,y
        args = args.strip()
        
        # Handle parentheses format: PRESET(x,y)
        if args.startswith('(') and ')' in args:
            close_paren_pos = self.find_matching_paren(args)
            if close_paren_pos == -1:
                return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
            paren_content = args[1:close_paren_pos]
            coords = self.split_args_respecting_parentheses(paren_content)
        else:
            # Handle space-separated format: PRESET x,y
            coords = self.split_args_respecting_parentheses(args)
            
        if len(coords) < 2:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        
        try:
            x = int(self.evaluate_expression(coords[0].strip()))
            y = int(self.evaluate_expression(coords[1].strip()))
            
            return [{'type': 'preset', 'x': x, 'y': y}]
        except:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
    
    def execute_line_graphics(self, args):
        # LINE(x1,y1)-(x2,y2) or LINE(x1,y1)-(x2,y2),color or LINE x1,y1,x2,y2 or LINE x1,y1,x2,y2,color
        args = args.strip()
        
        # Handle parentheses format: LINE(x1,y1)-(x2,y2)
        if ')-(' in args:
            parts = args.split(')-(',1)
            if len(parts) != 2:
                return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
            
            # Parse first coordinate
            start_coords = parts[0].strip()
            if not start_coords.startswith('('):
                return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
            start_paren_content = start_coords[1:]
            start_coords = self.split_args_respecting_parentheses(start_paren_content)
            
            # Parse second coordinate and optional color
            end_part = parts[1].strip()
            if ')' not in end_part:
                return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
            
            close_paren = end_part.index(')')
            end_paren_content = end_part[:close_paren]
            end_coords = self.split_args_respecting_parentheses(end_paren_content)
            color_part = end_part[close_paren+1:].strip()
            
            try:
                x1 = int(self.evaluate_expression(start_coords[0].strip()))
                y1 = int(self.evaluate_expression(start_coords[1].strip()))
                x2 = int(self.evaluate_expression(end_coords[0].strip()))
                y2 = int(self.evaluate_expression(end_coords[1].strip()))
                
                color = None
                if color_part.startswith(','):
                    color = int(self.evaluate_expression(color_part[1:].strip()))
                
                return [{'type': 'line', 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'color': color}]
            except:
                return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        else:
            # Handle space-separated format: LINE x1,y1,x2,y2 or LINE x1,y1,x2,y2,color
            coords = self.split_args_respecting_parentheses(args)
            if len(coords) < 4:
                return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
            
            try:
                x1 = int(self.evaluate_expression(coords[0].strip()))
                y1 = int(self.evaluate_expression(coords[1].strip()))
                x2 = int(self.evaluate_expression(coords[2].strip()))
                y2 = int(self.evaluate_expression(coords[3].strip()))
                color = int(self.evaluate_expression(coords[4].strip())) if len(coords) > 4 else None
                
                return [{'type': 'line', 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'color': color}]
            except:
                return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
    
    def execute_circle(self, args):
        # CIRCLE(x,y),radius or CIRCLE(x,y),radius,color or CIRCLE x,y,radius or CIRCLE x,y,radius,color
        args = args.strip()
        
        # Handle parentheses format: CIRCLE(x,y),radius
        if args.startswith('(') and ')' in args:
            close_paren = self.find_matching_paren(args)
            if close_paren == -1:
                return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
            paren_content = args[1:close_paren]
            coords = self.split_args_respecting_parentheses(paren_content)
            rest = args[close_paren+1:].strip()
            
            if not rest.startswith(','):
                return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
            
            params = self.split_args_respecting_parentheses(rest[1:])
            
            if len(coords) < 2 or len(params) < 1:
                return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
            
            try:
                x = int(self.evaluate_expression(coords[0].strip()))
                y = int(self.evaluate_expression(coords[1].strip()))
                radius = int(self.evaluate_expression(params[0].strip()))
                color = int(self.evaluate_expression(params[1].strip())) if len(params) > 1 else None
                
                return [{'type': 'circle', 'x': x, 'y': y, 'radius': radius, 'color': color}]
            except:
                return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        else:
            # Handle space-separated format: CIRCLE x,y,radius or CIRCLE x,y,radius,color
            params = self.split_args_respecting_parentheses(args)
            
            if len(params) < 3:
                return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
            
            try:
                x = int(self.evaluate_expression(params[0].strip()))
                y = int(self.evaluate_expression(params[1].strip()))
                radius = int(self.evaluate_expression(params[2].strip()))
                color = int(self.evaluate_expression(params[3].strip())) if len(params) > 3 else None
                
                return [{'type': 'circle', 'x': x, 'y': y, 'radius': radius, 'color': color}]
            except:
                return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
    
    def execute_paint(self, args):
        # PAINT(x,y),color or PAINT(x,y),color,boundary_color
        if not args.startswith('(') or ')' not in args:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        
        # Check if we're in graphics mode
        if self.graphics_mode == 0:
            return [{'type': 'error', 'message': 'ILLEGAL FUNCTION CALL'}]
        
        close_paren = args.index(')')
        coords = args[1:close_paren].split(',')
        rest = args[close_paren+1:].strip()
        
        if len(coords) != 2:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        
        if not rest.startswith(','):
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        
        params = rest[1:].split(',')
        if len(params) < 1:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        
        try:
            x = int(float(self.evaluate_expression(coords[0].strip())))
            y = int(float(self.evaluate_expression(coords[1].strip())))
            fill_color = int(float(self.evaluate_expression(params[0].strip())))
            boundary_color = int(float(self.evaluate_expression(params[1].strip()))) if len(params) > 1 else None
            
            return [{'type': 'paint', 'x': x, 'y': y, 'fill_color': fill_color, 'boundary_color': boundary_color}]
        except (ValueError, TypeError):
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
    
    def execute_color(self, args):
        # COLOR fg,bg
        parts = args.split(',')
        try:
            fg = int(self.evaluate_expression(parts[0].strip())) if parts[0].strip() else None
            bg = int(self.evaluate_expression(parts[1].strip())) if len(parts) > 1 and parts[1].strip() else None
            
            return [{'type': 'set_color', 'fg': fg, 'bg': bg}]
        except:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
    
    def execute_sound(self, args):
        # SOUND frequency,duration
        parts = args.split(',')
        if len(parts) != 2:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        
        try:
            frequency = int(self.evaluate_expression(parts[0].strip()))
            duration = int(self.evaluate_expression(parts[1].strip()))
            
            if frequency < 1 or frequency > 4095:
                return [{'type': 'error', 'message': 'ILLEGAL FUNCTION CALL'}]
            if duration < 1 or duration > 255:
                return [{'type': 'error', 'message': 'ILLEGAL FUNCTION CALL'}]
            
            return [{'type': 'sound', 'frequency': frequency, 'duration': duration}]
        except:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
    
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
        self.program_counter = None
        self.stopped_position = None  # Clear stopped position
        self.current_line = 0
        self.current_sub_line = 0
        self.iteration_count = 0
        self.keyboard_buffer.clear()  # Clear keyboard buffer
        self.graphics_mode = 0  # Reset to text mode
        return [{'type': 'text', 'text': 'READY'}]
    
    def execute_end(self):
        # END/STOP command - stop program execution
        self.running = False
        # Store position for CONT command
        self.stopped_position = (self.current_line, self.current_sub_line)
        return [{'type': 'text', 'text': 'BREAK IN ' + str(self.current_line)}]
    
    def execute_cont(self):
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
                        self.program_counter = current_pos_index + 1
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
                        output.append(item)
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
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        
        # Parse variable names
        var_names = [name.strip() for name in args.split(',')]
        
        for var_name in var_names:
            if self.data_pointer >= len(self.data_statements):
                return [{'type': 'error', 'message': 'OUT OF DATA'}]
            
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
        
        # Check if array exists
        if array_name not in self.arrays:
            return [{'type': 'error', 'message': 'UNDIM\'D ARRAY'}]
        
        # Parse indices
        try:
            indices = [int(self.evaluate_expression(idx.strip())) for idx in indices_str.split(',')]
            
            # Set array element
            current = self.arrays[array_name]
            for i, idx in enumerate(indices[:-1]):
                if idx < 0 or idx >= len(current):
                    return [{'type': 'error', 'message': 'BAD SUBSCRIPT'}]
                current = current[idx]
            
            # Set the final element
            final_idx = indices[-1]
            if final_idx < 0 or final_idx >= len(current):
                return [{'type': 'error', 'message': 'BAD SUBSCRIPT'}]
            
            current[final_idx] = value
            return None  # No error
            
        except ValueError:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        except Exception:
            return [{'type': 'error', 'message': 'BAD SUBSCRIPT'}]
    
    def execute_restore(self):
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
    
    def execute_get(self, args):
        # GET (x1,y1)-(x2,y2), array_name
        # Save rectangular graphics area to an array
        if not args:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        
        # Parse the coordinates and array name
        # Format: (x1,y1)-(x2,y2), array_name
        match = re.match(r'\(([^,]+),([^)]+)\)-\(([^,]+),([^)]+)\),\s*(\w+\$?)', args)
        if not match:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        
        try:
            x1 = int(self.evaluate_expression(match.group(1).strip()))
            y1 = int(self.evaluate_expression(match.group(2).strip()))
            x2 = int(self.evaluate_expression(match.group(3).strip()))
            y2 = int(self.evaluate_expression(match.group(4).strip()))
            array_name = match.group(5).strip()
            
            # Check if we're in graphics mode
            if self.graphics_mode == 0:
                return [{'type': 'error', 'message': 'ILLEGAL FUNCTION CALL'}]
            
            # Get the dimensions
            width = abs(x2 - x1) + 1
            height = abs(y2 - y1) + 1
            
            # Create array to store the graphics data
            # In real Color Computer, this would store actual pixel data
            # For our simulation, we'll store coordinate and color information
            graphics_data = []
            for y in range(min(y1, y2), max(y1, y2) + 1):
                row = []
                for x in range(min(x1, x2), max(x1, x2) + 1):
                    # For simulation purposes, store coordinate info
                    # In real implementation, this would be actual pixel data
                    row.append({'x': x, 'y': y, 'color': self.current_draw_color})
                graphics_data.append(row)
            
            # Store in arrays with special GET prefix to distinguish from regular DIM arrays
            self.arrays[array_name] = graphics_data
            
            return [{'type': 'get', 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'array': array_name}]
            
        except (ValueError, TypeError):
            return [{'type': 'error', 'message': 'TYPE MISMATCH'}]
    
    def execute_put(self, args):
        # PUT (x,y), array_name [,action]
        # Display graphics array at position
        if not args:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        
        # Parse the coordinates and array name carefully, respecting parentheses
        # Format: (x,y), array_name [,PSET|PRESET|OR|AND|XOR]
        parts = []
        current_part = ""
        paren_count = 0
        
        for char in args:
            if char == '(':
                paren_count += 1
                current_part += char
            elif char == ')':
                paren_count -= 1
                current_part += char
            elif char == ',' and paren_count == 0:
                parts.append(current_part.strip())
                current_part = ""
            else:
                current_part += char
        
        if current_part.strip():
            parts.append(current_part.strip())
        
        if len(parts) < 2:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        
        # Parse coordinates
        coord_match = re.match(r'\(([^,]+),([^)]+)\)', parts[0].strip())
        if not coord_match:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        
        try:
            x = int(self.evaluate_expression(coord_match.group(1).strip()))
            y = int(self.evaluate_expression(coord_match.group(2).strip()))
            array_name = parts[1].strip()
            action = parts[2].strip() if len(parts) > 2 else 'PSET'
            
            # Check if we're in graphics mode
            if self.graphics_mode == 0:
                return [{'type': 'error', 'message': 'ILLEGAL FUNCTION CALL'}]
            
            # Check if array exists
            if array_name not in self.arrays:
                return [{'type': 'error', 'message': 'UNDIM\'D ARRAY'}]
            
            graphics_data = self.arrays[array_name]
            
            # Send PUT command to frontend for graphics rendering
            return [{'type': 'put', 'x': x, 'y': y, 'array': array_name, 'action': action, 'data': graphics_data}]
            
        except (ValueError, TypeError):
            return [{'type': 'error', 'message': 'TYPE MISMATCH'}]
    
    def execute_draw(self, args):
        # DRAW string - Logo-style turtle graphics
        if not args:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        
        # Check if we're in graphics mode
        if self.graphics_mode == 0:
            return [{'type': 'error', 'message': 'ILLEGAL FUNCTION CALL'}]
        
        # Evaluate the draw string expression
        try:
            draw_string = self.evaluate_expression(args.strip())
            if not isinstance(draw_string, str):
                return [{'type': 'error', 'message': 'TYPE MISMATCH'}]
            
            # Parse and execute DRAW commands
            return self.parse_draw_commands(draw_string.upper())
            
        except (ValueError, TypeError):
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
    
    def parse_draw_commands(self, draw_string):
        # Parse DRAW command string like "U10R20D10L20" or "BU5BR10"
        commands = []
        i = 0
        
        while i < len(draw_string):
            char = draw_string[i]
            
            # Skip spaces
            if char == ' ':
                i += 1
                continue
            
            # Handle B (blank/move) command - can be followed by direction
            blank_move = False
            if char == 'B':
                blank_move = True
                i += 1
                if i < len(draw_string):
                    char = draw_string[i]  # Get the direction after B
                else:
                    continue  # Skip if B is at end of string
            
            # Parse number following the command
            number = ""
            j = i + 1
            while j < len(draw_string) and draw_string[j].isdigit():
                number += draw_string[j]
                j += 1
            
            distance = int(number) if number else 1
            
            # Execute the draw command
            result = self.execute_draw_command(char, distance, blank_move)
            if result and result[0].get('type') == 'error':
                return result
            elif result:
                commands.extend(result)
            
            i = j
        
        return commands
    
    def execute_draw_command(self, command, distance, blank_move=False):
        # Execute individual DRAW commands
        old_x, old_y = self.turtle_x, self.turtle_y
        new_x, new_y = old_x, old_y
        
        # Calculate new position based on command
        if command == 'U':  # Up
            new_y = old_y - distance
        elif command == 'D':  # Down
            new_y = old_y + distance
        elif command == 'L':  # Left
            new_x = old_x - distance
        elif command == 'R':  # Right
            new_x = old_x + distance
        elif command == 'E':  # Up-Right diagonal
            new_x = old_x + distance
            new_y = old_y - distance
        elif command == 'F':  # Down-Right diagonal
            new_x = old_x + distance
            new_y = old_y + distance
        elif command == 'G':  # Down-Left diagonal
            new_x = old_x - distance
            new_y = old_y + distance
        elif command == 'H':  # Up-Left diagonal
            new_x = old_x - distance
            new_y = old_y - distance
        else:
            return [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        
        # Update turtle position
        self.turtle_x = new_x
        self.turtle_y = new_y
        
        # If blank_move is True, move without drawing
        if blank_move:
            return []  # Return empty list - no line drawn
        else:
            # Draw line from old position to new position
            return [{'type': 'line', 'x1': old_x, 'y1': old_y, 'x2': new_x, 'y2': new_y, 'color': self.current_draw_color}]

# Global BASIC interpreter instance
basic = CoCoBasic()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('execute_command')
def handle_command(data):
    command = data.get('command', '')
    line_num, code = basic.parse_line(command)
    
    if line_num is not None:
        # Store program line
        if code:
            basic.program[line_num] = code
            # Also expand into sub-lines for execution
            basic.expand_line_to_sublines(line_num, code)
        else:
            # Delete line if no code
            basic.program.pop(line_num, None)
            # Also remove from expanded program
            keys_to_remove = [key for key in basic.expanded_program.keys() if key[0] == line_num]
            for key in keys_to_remove:
                del basic.expanded_program[key]
        emit('output', [{'type': 'text', 'text': 'OK'}])
    else:
        # Execute immediate command
        result = basic.execute_command(code)
        emit('output', result)

@socketio.on('input_response')
def handle_input_response(data):
    var_name = data.get('variable', '')
    user_input = data.get('value', '')
    
    # Store the input value in the variable
    # Try to convert to number if possible, otherwise store as string
    try:
        if '.' in user_input:
            basic.variables[var_name] = float(user_input)
        else:
            basic.variables[var_name] = int(user_input)
    except ValueError:
        basic.variables[var_name] = user_input
    
    # Continue program execution if we were in the middle of running a program
    if hasattr(basic, 'waiting_for_input') and basic.waiting_for_input:
        basic.waiting_for_input = False
        # Resume program execution from where we left off
        result = basic.continue_program_execution()
        emit('output', result)
    else:
        # Just acknowledge the input
        emit('output', [{'type': 'text', 'text': 'OK'}])

@socketio.on('keypress')
def handle_keypress(data):
    key = data.get('key', '')
    if key:
        basic.add_key_to_buffer(key)

@socketio.on('connect')
def on_connect():
    emit('output', [{'type': 'text', 'text': 'COLOR COMPUTER BASIC V1.0\nREADY'}])

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)