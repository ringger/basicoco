"""
FileIOManager for BasiCoCo BASIC Environment

Handles sequential file I/O: OPEN, CLOSE, PRINT#, INPUT#, LINE INPUT.
CoCo BASIC supports file numbers 1-15 with modes I (input), O (output), A (append).
"""

import os

from .error_context import error_response, text_response
from .program_files import FileManager
from .text_utils import StatementSplitter


class FileIOManager:
    """Manages sequential file I/O for the BASIC interpreter."""

    MAX_FILE_NUMBER = 15

    def __init__(self, emulator):
        self.emulator = emulator
        self.open_files = {}  # file_number -> {'filename': str, 'mode': str, 'handle': file_obj}

    # ── Validation helpers ────────────────────────────────────────────

    def _validate_file_number(self, n):
        """Validate file number is in range 1-15. Returns error response or None."""
        if not isinstance(n, int) or n < 1 or n > self.MAX_FILE_NUMBER:
            error = self.emulator.error_context.runtime_error(
                f"FILE NUMBER ERROR: file number must be 1-{self.MAX_FILE_NUMBER}, got {n}",
                self.emulator.current_line,
                suggestions=[
                    f"Use a file number between 1 and {self.MAX_FILE_NUMBER}",
                    'Example: OPEN "O", #1, "DATA.DAT"'
                ]
            )
            return error_response(error)
        return None

    def _require_open(self, n, required_mode=None):
        """Check file is open (and optionally in the right mode). Returns error response or None."""
        if n not in self.open_files:
            error = self.emulator.error_context.runtime_error(
                f"FILE NOT OPEN: #{n}",
                self.emulator.current_line,
                suggestions=[
                    f'Open the file first: OPEN "I", #{n}, "filename"',
                    "Check that CLOSE has not already been called"
                ]
            )
            return error_response(error)
        if required_mode and self.open_files[n]['mode'] not in (required_mode if isinstance(required_mode, (list, tuple)) else [required_mode]):
            actual = self.open_files[n]['mode']
            error = self.emulator.error_context.runtime_error(
                f"FILE MODE ERROR: #{n} is open for {'INPUT' if actual == 'I' else 'OUTPUT' if actual == 'O' else 'APPEND'}, "
                f"cannot {'write to' if required_mode == 'I' else 'read from'} it",
                self.emulator.current_line,
                suggestions=[
                    "Close the file and reopen in the correct mode",
                    'Input mode: OPEN "I", #n, "file"',
                    'Output mode: OPEN "O", #n, "file"'
                ]
            )
            return error_response(error)
        return None

    def _parse_file_number(self, file_num_str):
        """Parse and validate a file number from a string like '#1' or '1'.
        Returns (file_num, None) on success or (None, error_response) on failure.
        """
        file_num_str = file_num_str.strip()
        if file_num_str.startswith('#'):
            file_num_str = file_num_str[1:]
        try:
            file_num = self.emulator.eval_int(file_num_str)
        except (ValueError, TypeError):
            error = self.emulator.error_context.runtime_error(
                f"FILE NUMBER ERROR: invalid file number '{file_num_str}'",
                self.emulator.current_line,
                suggestions=[
                    f"File number must be 1-{self.MAX_FILE_NUMBER}",
                    'Example: OPEN "O", #1, "DATA.DAT"'
                ]
            )
            return None, error_response(error)
        err = self._validate_file_number(file_num)
        if err:
            return None, err
        return file_num, None

    def _resolve_filename(self, filename):
        """Resolve a filename relative to the programs directory."""
        filename = FileManager._strip_quotes(filename)
        # Resolve relative to programs/ directory
        if not os.path.isabs(filename):
            programs_dir = os.path.join(os.getcwd(), 'programs')
            if os.path.isdir(programs_dir):
                return os.path.join(programs_dir, filename)
        return filename

    # ── OPEN ──────────────────────────────────────────────────────────

    def execute_open(self, args):
        """OPEN mode, #n, filename"""
        parts = StatementSplitter.split_args(args)
        if len(parts) < 3:
            error = self.emulator.error_context.syntax_error(
                "OPEN requires mode, file number, and filename",
                self.emulator.current_line,
                suggestions=[
                    'Syntax: OPEN "mode", #n, "filename"',
                    'Modes: "I" (input), "O" (output), "A" (append)',
                    'Example: OPEN "O", #1, "DATA.DAT"'
                ]
            )
            return error_response(error)

        # Parse mode — evaluate as expression (supports string variables)
        mode_raw = parts[0].strip()
        try:
            mode_str = str(self.emulator.evaluate_expression(mode_raw)).upper()
        except Exception:
            mode_str = mode_raw.strip('"').strip("'").upper()
        if mode_str not in ('I', 'O', 'A'):
            error = self.emulator.error_context.runtime_error(
                f"FILE MODE ERROR: invalid mode '{mode_str}'",
                self.emulator.current_line,
                suggestions=[
                    '"I" = input (read)', '"O" = output (write)', '"A" = append'
                ]
            )
            return error_response(error)

        # Parse file number
        file_num, err = self._parse_file_number(parts[1])
        if err:
            return err

        if file_num in self.open_files:
            error = self.emulator.error_context.runtime_error(
                f"FILE ALREADY OPEN: #{file_num}",
                self.emulator.current_line,
                suggestions=[
                    f"Close file #{file_num} first: CLOSE #{file_num}",
                    "Each file number can only be used for one open file"
                ]
            )
            return error_response(error)

        # Parse filename — evaluate as expression (supports string variables)
        filename_expr = ','.join(parts[2:]).strip()
        try:
            filename = str(self.emulator.evaluate_expression(filename_expr))
        except Exception:
            filename = filename_expr
        filepath = self._resolve_filename(filename)

        # Open the file
        try:
            if mode_str == 'I':
                handle = open(filepath, 'r')
            elif mode_str == 'O':
                os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
                handle = open(filepath, 'w')
            else:  # 'A'
                os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
                handle = open(filepath, 'a')
        except FileNotFoundError:
            error = self.emulator.error_context.runtime_error(
                f"FILE NOT FOUND: {os.path.basename(filepath)}",
                self.emulator.current_line,
                suggestions=[
                    "Check that the file exists",
                    "Use mode \"O\" to create a new file",
                    'Example: OPEN "O", #1, "NEWFILE.DAT"'
                ]
            )
            return error_response(error)
        except PermissionError:
            error = self.emulator.error_context.runtime_error(
                f"PERMISSION DENIED: {os.path.basename(filepath)}",
                self.emulator.current_line,
                suggestions=["Check file permissions"]
            )
            return error_response(error)

        self.open_files[file_num] = {
            'filename': filepath,
            'mode': mode_str,
            'handle': handle,
        }
        return []

    # ── CLOSE ─────────────────────────────────────────────────────────

    def execute_close(self, args):
        """CLOSE [#n] — close specific file or all files."""
        args = args.strip()
        if not args:
            self.close_all()
            return []

        file_num, err = self._parse_file_number(args)
        if err:
            return err

        if file_num in self.open_files:
            try:
                self.open_files[file_num]['handle'].close()
            except Exception:
                pass
            del self.open_files[file_num]
        # Closing an unopened file is not an error (matches real CoCo)
        return []

    def close_all(self):
        """Close all open files."""
        for info in self.open_files.values():
            try:
                info['handle'].close()
            except Exception:
                pass
        self.open_files.clear()

    # ── PRINT# ────────────────────────────────────────────────────────

    def execute_print_file(self, args):
        """PRINT #n, expr [;|,] expr ...
        args has the # already stripped: "1, expr; expr"
        """
        # Split off file number (first comma separates file# from expressions)
        comma_pos = args.find(',')
        if comma_pos == -1:
            # PRINT #n with no expressions — write blank line
            file_num_str = args.strip()
            expr_part = ''
        else:
            file_num_str = args[:comma_pos].strip()
            expr_part = args[comma_pos + 1:]

        file_num, err = self._parse_file_number(file_num_str)
        if err:
            return err
        err = self._require_open(file_num, ('O', 'A'))
        if err:
            return err

        handle = self.open_files[file_num]['handle']

        if not expr_part.strip():
            # PRINT #n — write blank line
            handle.write('\n')
            handle.flush()
            return []

        # Parse and evaluate expressions with separators (;,)
        # Walk through expr_part, splitting on ; and , while respecting quotes and parens
        output_parts = []
        trailing_separator = None

        tokens = self._tokenize_print_args(expr_part)
        for token_type, token_value in tokens:
            if token_type == 'sep':
                if token_value == ',':
                    output_parts.append(',')
                # semicolon = no separator in file output
                trailing_separator = token_value
            elif token_type == 'expr':
                trailing_separator = None
                try:
                    value = self.emulator.evaluate_expression(token_value)
                    if isinstance(value, str):
                        output_parts.append(value)
                    elif isinstance(value, (int, float)):
                        if isinstance(value, float) and value.is_integer():
                            output_parts.append(str(int(value)))
                        else:
                            output_parts.append(str(value))
                    else:
                        output_parts.append(str(value))
                except Exception as e:
                    error = self.emulator.error_context.runtime_error(
                        f"Error evaluating PRINT# expression: {e}",
                        self.emulator.current_line,
                        suggestions=["Check expression syntax", "Example: PRINT #1, X, Y"]
                    )
                    return error_response(error)

        text = ''.join(output_parts)
        if trailing_separator is None:
            text += '\n'
        handle.write(text)
        handle.flush()
        return []

    def _tokenize_print_args(self, text):
        """Split PRINT# arguments into (type, value) pairs.
        type is 'expr' or 'sep'. Respects quotes and parentheses.
        """
        tokens = []
        i = 0
        current_expr = []
        paren_depth = 0

        while i < len(text):
            ch = text[i]
            if ch == '"':
                # Consume quoted string
                current_expr.append(ch)
                i += 1
                while i < len(text) and text[i] != '"':
                    current_expr.append(text[i])
                    i += 1
                if i < len(text):
                    current_expr.append(text[i])
                    i += 1
            elif ch == '(':
                paren_depth += 1
                current_expr.append(ch)
                i += 1
            elif ch == ')':
                paren_depth -= 1
                current_expr.append(ch)
                i += 1
            elif ch in (',', ';') and paren_depth == 0:
                expr_str = ''.join(current_expr).strip()
                if expr_str:
                    tokens.append(('expr', expr_str))
                tokens.append(('sep', ch))
                current_expr = []
                i += 1
            else:
                current_expr.append(ch)
                i += 1

        expr_str = ''.join(current_expr).strip()
        if expr_str:
            tokens.append(('expr', expr_str))

        return tokens

    # ── INPUT# ────────────────────────────────────────────────────────

    def execute_input_file(self, args):
        """INPUT #n, var1, var2, ...
        args has the # already stripped: "1, A, B$"
        """
        comma_pos = args.find(',')
        if comma_pos == -1:
            error = self.emulator.error_context.syntax_error(
                "INPUT# requires file number and at least one variable",
                self.emulator.current_line,
                suggestions=["Example: INPUT #1, A$", "Example: INPUT #1, X, Y"]
            )
            return error_response(error)

        file_num_str = args[:comma_pos].strip()
        var_part = args[comma_pos + 1:]

        file_num, err = self._parse_file_number(file_num_str)
        if err:
            return err
        err = self._require_open(file_num, 'I')
        if err:
            return err

        handle = self.open_files[file_num]['handle']

        # Parse variable names
        var_names = StatementSplitter.split_args(var_part)
        if not var_names:
            error = self.emulator.error_context.syntax_error(
                "INPUT# requires at least one variable",
                self.emulator.current_line,
                suggestions=["Example: INPUT #1, A$"]
            )
            return error_response(error)

        # Read values from file — values are separated by commas and/or newlines
        for var_str in var_names:
            var_str = var_str.strip()
            if not var_str:
                continue

            # Check for array element: A(1)
            var_desc = self._parse_var_descriptor(var_str)

            value = self._read_next_value(handle, file_num)
            if value is None:
                error = self.emulator.error_context.runtime_error(
                    f"INPUT PAST END OF FILE: #{file_num}",
                    self.emulator.current_line,
                    suggestions=[
                        "Check EOF(n) before reading",
                        "Example: IF EOF(1) THEN GOTO 100"
                    ]
                )
                return error_response(error)

            self.emulator.store_input_value(var_desc, value)

        return []

    def _parse_var_descriptor(self, var_str):
        """Parse a variable reference like 'A', 'B$', 'A(1)' into a var_desc dict."""
        var_str = var_str.strip().upper()
        paren_pos = var_str.find('(')
        if paren_pos != -1 and var_str.endswith(')'):
            array_name = var_str[:paren_pos]
            index_str = var_str[paren_pos + 1:-1]
            indices = []
            for idx in StatementSplitter.split_args(index_str):
                indices.append(self.emulator.eval_int(idx))
            return {'name': array_name, 'array': True, 'indices': indices}
        return {'name': var_str, 'array': False}

    def _read_next_value(self, handle, file_num):
        """Read the next comma-or-newline-delimited value from a file.
        Returns the value as a string, or None at EOF.
        Handles quoted strings.
        """
        # Use a per-file read buffer for partial-line reads
        file_info = self.open_files[file_num]
        buf = file_info.get('_read_buffer', '')

        while True:
            # Skip leading whitespace (but not newlines — those are delimiters)
            while buf and buf[0] == ' ':
                buf = buf[1:]

            if not buf:
                line = handle.readline()
                if not line:
                    file_info['_read_buffer'] = ''
                    return None  # EOF
                buf = line.rstrip('\n').rstrip('\r')
                if not buf and line:
                    # Blank line — skip and try next
                    continue

            # Parse a value from buf
            if buf.startswith('"'):
                # Quoted string — find closing quote
                end = buf.find('"', 1)
                if end == -1:
                    value = buf[1:]
                    buf = ''
                else:
                    value = buf[1:end]
                    buf = buf[end + 1:]
                # Skip trailing comma
                buf = buf.lstrip()
                if buf.startswith(','):
                    buf = buf[1:]
            else:
                # Unquoted — read until comma or end
                comma_pos = buf.find(',')
                if comma_pos == -1:
                    value = buf.strip()
                    buf = ''
                else:
                    value = buf[:comma_pos].strip()
                    buf = buf[comma_pos + 1:]

            file_info['_read_buffer'] = buf
            return value

    # ── LINE INPUT ────────────────────────────────────────────────────

    def execute_line_input(self, args):
        """LINE INPUT [#n,] ["prompt";] var$
        args is everything after 'LINE INPUT'.
        """
        args = args.strip()

        if args.startswith('#'):
            # File LINE INPUT#
            return self._line_input_file(args[1:])
        else:
            # Console LINE INPUT
            return self._line_input_console(args)

    def _line_input_file(self, args):
        """LINE INPUT #n, var$"""
        comma_pos = args.find(',')
        if comma_pos == -1:
            error = self.emulator.error_context.syntax_error(
                "LINE INPUT# requires file number and variable",
                self.emulator.current_line,
                suggestions=["Example: LINE INPUT #1, A$"]
            )
            return error_response(error)

        file_num_str = args[:comma_pos].strip()
        var_str = args[comma_pos + 1:].strip()

        file_num, err = self._parse_file_number(file_num_str)
        if err:
            return err
        err = self._require_open(file_num, 'I')
        if err:
            return err

        handle = self.open_files[file_num]['handle']
        line = handle.readline()
        if not line:
            error = self.emulator.error_context.runtime_error(
                f"INPUT PAST END OF FILE: #{file_num}",
                self.emulator.current_line,
                suggestions=["Check EOF(n) before reading"]
            )
            return error_response(error)

        value = line.rstrip('\n').rstrip('\r')
        var_desc = self._parse_var_descriptor(var_str)
        self.emulator.store_input_value(var_desc, value)
        return []

    def _line_input_console(self, args):
        """LINE INPUT ["prompt";] var$"""
        prompt_text = "? "
        var_str = args

        # Check for optional prompt string
        if args.startswith('"'):
            end_quote = args.find('"', 1)
            if end_quote != -1:
                prompt_text = args[1:end_quote]
                rest = args[end_quote + 1:].strip()
                if rest.startswith(';'):
                    rest = rest[1:].strip()
                elif rest.startswith(','):
                    rest = rest[1:].strip()
                var_str = rest

        var_str = var_str.strip()
        if not var_str:
            error = self.emulator.error_context.syntax_error(
                "LINE INPUT requires a variable name",
                self.emulator.current_line,
                suggestions=[
                    "Example: LINE INPUT A$",
                    'Example: LINE INPUT "Enter name"; N$'
                ]
            )
            return error_response(error)

        var_name = var_str.upper()

        # Set up input state (similar to regular INPUT but with line_input flag)
        var_desc = {'name': var_name, 'array': False}
        self.emulator.input_variables = [var_desc]
        self.emulator.input_prompt = prompt_text
        self.emulator.current_input_index = 0
        self.emulator.waiting_for_input = True
        self.emulator.program_counter = (self.emulator.current_line, self.emulator.current_sub_line)

        return [{'type': 'input_request', 'prompt': prompt_text, 'variable': var_name,
                 'array': False, 'indices': None, 'line_input': True}]

    # ── EOF ───────────────────────────────────────────────────────────

    def eof(self, file_num):
        """EOF(n) — returns -1 at end of file, 0 otherwise."""
        err = self._validate_file_number(file_num)
        if err:
            raise ValueError(f"FILE NUMBER ERROR: file number must be 1-{self.MAX_FILE_NUMBER}")

        if file_num not in self.open_files:
            raise ValueError(f"FILE NOT OPEN: #{file_num}")

        info = self.open_files[file_num]
        if info['mode'] != 'I':
            raise ValueError(f"EOF only valid for input files")

        handle = info['handle']
        # Check read buffer first
        buf = info.get('_read_buffer', '')
        if buf.strip():
            return 0  # Data still in buffer

        # Peek at the file
        pos = handle.tell()
        chunk = handle.read(1)
        if not chunk:
            return -1  # EOF
        handle.seek(pos)  # Restore position
        return 0

    # ── Registry integration ──────────────────────────────────────────

    def register_commands(self, registry):
        """Register OPEN and CLOSE as registry commands."""
        registry.register('OPEN', self.execute_open,
                          category='file',
                          description="Open a file for sequential I/O",
                          syntax='OPEN "mode", #n, "filename"',
                          examples=['OPEN "O", #1, "DATA.DAT"',
                                    'OPEN "I", #2, "DATA.DAT"',
                                    'OPEN "A", #1, "LOG.TXT"'])
        registry.register('CLOSE', self.execute_close,
                          category='file',
                          description="Close an open file",
                          syntax="CLOSE [#n]",
                          examples=["CLOSE #1", "CLOSE"])
