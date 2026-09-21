"""
FileIOManager for BasiCoCo BASIC Environment

Handles sequential file I/O: OPEN, CLOSE, PRINT#, INPUT#, LINE INPUT.
CoCo BASIC supports file numbers 1-15 with modes I (input), O (output), A (append).
"""

import os

from .ast_nodes import format_print_item
from .error_context import BASIC_RUNTIME_ERRORS, error_response, text_response
from .program_files import FileManager, SandboxError
from .text_utils import StatementSplitter


class FileIOManager:
    """Manages sequential file I/O for the BASIC interpreter."""

    MAX_FILE_NUMBER = 15

    def __init__(self, emulator):
        self.emulator = emulator
        self.open_files = {}  # file_number -> {'filename': str, 'mode': str, 'handle': file_obj}

    def _syntax_error(self, message, suggestions):
        return error_response(self.emulator.error_context.syntax_error(
            message, self.emulator.current_line, suggestions=suggestions))

    def _runtime_error(self, message, suggestions):
        return error_response(self.emulator.error_context.runtime_error(
            message, self.emulator.current_line, suggestions=suggestions))

    # ── Validation helpers ────────────────────────────────────────────

    def _validate_file_number(self, n):
        """Validate file number is in range 1-15. Returns error response or None."""
        if not isinstance(n, int) or n < 1 or n > self.MAX_FILE_NUMBER:
            return self._runtime_error(
                f"FILE NUMBER ERROR: file number must be 1-{self.MAX_FILE_NUMBER}, got {n}",
                [f"Use a file number between 1 and {self.MAX_FILE_NUMBER}",
                 'Example: OPEN "O", #1, "DATA.DAT"'])
        return None

    def _require_open(self, n, required_mode=None):
        """Check file is open (and optionally in the right mode). Returns error response or None."""
        if n not in self.open_files:
            return self._runtime_error(
                f"FILE NOT OPEN: #{n}",
                [f'Open the file first: OPEN "I", #{n}, "filename"',
                 "Check that CLOSE has not already been called"])
        allowed = required_mode if isinstance(required_mode, (list, tuple)) else [required_mode]
        if required_mode and self.open_files[n]['mode'] not in allowed:
            actual = self.open_files[n]['mode']
            # The attempted operation is the one the required mode allows:
            # requiring 'I' means we tried to read; 'O'/'A' means we tried to write.
            attempted = 'read from' if 'I' in allowed else 'write to'
            return self._runtime_error(
                f"FILE MODE ERROR: #{n} is open for {'INPUT' if actual == 'I' else 'OUTPUT' if actual == 'O' else 'APPEND'}, "
                f"cannot {attempted} it",
                ["Close the file and reopen in the correct mode",
                 'Input mode: OPEN "I", #n, "file"',
                 'Output mode: OPEN "O", #n, "file"'])
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
            return None, self._runtime_error(
                f"FILE NUMBER ERROR: invalid file number '{file_num_str}'",
                [f"File number must be 1-{self.MAX_FILE_NUMBER}",
                 'Example: OPEN "O", #1, "DATA.DAT"'])
        err = self._validate_file_number(file_num)
        if err:
            return None, err
        return file_num, None

    def _resolve_filename(self, filename, mode):
        """Resolve a data filename inside the programs sandbox.

        Input mode may also read the bundled programs; output/append only
        ever write to the writable sandbox. Raises SandboxError on escape.
        """
        files = self.emulator.file_manager
        filename = FileManager._strip_quotes(filename)
        if mode == 'I':
            return files.find_readable(filename) or files.resolve_writable(filename)
        return files.resolve_writable(filename)

    # ── OPEN ──────────────────────────────────────────────────────────

    def execute_open(self, args):
        """OPEN mode, #n, filename"""
        parts = StatementSplitter.split_args(args)
        if len(parts) < 3:
            return self._syntax_error(
                "OPEN requires mode, file number, and filename",
                ['Syntax: OPEN "mode", #n, "filename"',
                 'Modes: "I" (input), "O" (output), "A" (append)',
                 'Example: OPEN "O", #1, "DATA.DAT"'])

        # Parse mode — evaluate as expression (supports string variables)
        mode_raw = parts[0].strip()
        try:
            mode_str = str(self.emulator.evaluate_expression(mode_raw)).upper()
        except Exception:
            mode_str = mode_raw.strip('"').strip("'").upper()
        if mode_str not in ('I', 'O', 'A'):
            return self._runtime_error(
                f"FILE MODE ERROR: invalid mode '{mode_str}'",
                ['"I" = input (read)', '"O" = output (write)', '"A" = append'])

        # Parse file number
        file_num, err = self._parse_file_number(parts[1])
        if err:
            return err

        if file_num in self.open_files:
            return self._runtime_error(
                f"FILE ALREADY OPEN: #{file_num}",
                [f"Close file #{file_num} first: CLOSE #{file_num}",
                 "Each file number can only be used for one open file"])

        # Parse filename — evaluate as expression (supports string variables)
        filename_expr = ','.join(parts[2:]).strip()
        try:
            filename = str(self.emulator.evaluate_expression(filename_expr))
        except Exception:
            filename = filename_expr
        try:
            filepath = self._resolve_filename(filename, mode_str)
        except SandboxError as e:
            return self._runtime_error(
                f"OPEN: {e}",
                ['Data files live in the programs directory: OPEN "O", #1, "DATA.DAT"',
                 'Subdirectories inside programs/ are fine: "SAVES/SCORES.DAT"',
                 'Absolute paths, ~ and .. are not allowed'])

        # Open the file
        try:
            if mode_str == 'I':
                handle = open(filepath, 'r')
            else:
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                handle = open(filepath, 'w' if mode_str == 'O' else 'a')
        except FileNotFoundError:
            return self._runtime_error(
                f"FILE NOT FOUND: {os.path.basename(filepath)}",
                ["Check that the file exists",
                 'Use mode "O" to create a new file',
                 'Example: OPEN "O", #1, "NEWFILE.DAT"'])
        except PermissionError:
            return self._runtime_error(
                f"PERMISSION DENIED: {os.path.basename(filepath)}",
                ["Check file permissions",
                 "Choose a different filename",
                 "Close the file in any other program using it"])
        except OSError as e:
            reason = 'IS A DIRECTORY' if isinstance(e, IsADirectoryError) else (e.strerror or str(e)).upper()
            return self._runtime_error(
                f"FILE ERROR: {os.path.basename(filepath) or filename}: {reason}",
                ["Check the filename",
                 'Use a file name, not a directory: OPEN "I", #1, "DATA.DAT"',
                 "Use DIR to see available files"])

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
        # Split off file number (first top-level comma separates file# from expressions)
        comma_pos = self._file_number_comma(args)
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

        # The items parse exactly as PRINT's (the same parser), so adjacent
        # items, separators and expressions follow the same rules
        try:
            node = self.emulator.ast_parser.parse_statement(
                'PRINT ' + expr_part, self.emulator.current_line)
        except ValueError as e:
            return error_response(self.emulator.error_context.wrapped_error(
                "Error in PRINT#: ", e, self.emulator.current_line,
                ["Check expression syntax", "Example: PRINT #1, X, Y"]))

        output_parts = []
        for i, expr in enumerate(node.expressions):
            try:
                value = self.emulator.ast_evaluator.visit(expr)
            except BASIC_RUNTIME_ERRORS as e:
                return error_response(self.emulator.error_context.wrapped_error(
                    "Error evaluating PRINT# expression: ", e, self.emulator.current_line,
                    ["Check expression syntax", "Example: PRINT #1, X, Y"]))
            # Same text PRINT shows, so numbers keep their spaces and
            # INPUT # reads 5;6 back as two numbers
            output_parts.append(format_print_item(value))
            # A comma writes a literal comma (INPUT # reads the items back
            # separately); a semicolon writes nothing
            if i < len(node.separators) and node.separators[i] == ',':
                output_parts.append(',')

        text = ''.join(output_parts)
        if len(node.separators) < len(node.expressions):
            text += '\n'   # no trailing separator: end the line
        handle.write(text)
        handle.flush()
        return []

    # ── INPUT# ────────────────────────────────────────────────────────

    def execute_input_file(self, args):
        """INPUT #n, var1, var2, ...
        args has the # already stripped: "1, A, B$"
        """
        comma_pos = self._file_number_comma(args)
        if comma_pos == -1:
            return self._syntax_error(
                "INPUT# requires file number and at least one variable",
                ["Example: INPUT #1, A$", "Example: INPUT #1, X, Y"])

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
            return self._syntax_error(
                "INPUT# requires at least one variable",
                ["Example: INPUT #1, A$",
                 "Several variables: INPUT #1, NM$, AGE"])

        # Read values from file — values are separated by commas and/or newlines
        for var_str in var_names:
            var_str = var_str.strip()
            if not var_str:
                continue

            # Check for array element: A(1)
            var_desc = self._parse_var_descriptor(var_str)

            value = self._read_next_value(handle, file_num,
                                          numeric=not var_desc['name'].endswith('$'))
            if value is None:
                return self._runtime_error(
                    f"INPUT PAST END OF FILE: #{file_num}",
                    ["Check EOF(n) before reading",
                     "Example: IF EOF(1) THEN GOTO 100"])

            err = self.emulator.store_input_value(var_desc, value)
            if err:
                return self._store_error(err, var_str)

        return []

    def _store_error(self, message, var_str):
        """Report a failed store into an INPUT#/LINE INPUT# target."""
        return self._runtime_error(
            f"{message}: {var_str.strip().upper()}",
            ["Check the array index is within its DIM size",
             "Undimensioned arrays allow indices 0 to 10",
             "Example: DIM A(100) before INPUT #1, A(50)"])

    @staticmethod
    def _file_number_comma(args):
        """Index of the comma ending the file-number expression, or -1.

        Parentheses and quotes are respected, so PRINT #F(1,2),X splits
        after F(1,2), not inside it.
        """
        depth, in_quotes = 0, False
        for i, char in enumerate(args):
            if char == '"':
                in_quotes = not in_quotes
            elif in_quotes:
                continue
            elif char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            elif char == ',' and depth == 0:
                return i
        return -1

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

    def _read_next_value(self, handle, file_num, numeric=False):
        """Read the next comma-or-newline-delimited value from a file.
        Returns the value as a string, or None at EOF.
        Handles quoted strings. A *numeric* item also ends at a space, as in
        Microsoft BASIC, so what PRINT #n,5;6 writes (" 5  6 ") reads back
        as two numbers.
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
            elif numeric:
                # A number ends at a space, comma or end of line; the spaces
                # and one comma after it belong to the separator
                buf = buf.lstrip(' ')
                if not buf:
                    continue   # only blanks left on this line
                end = len(buf)
                for i, ch in enumerate(buf):
                    if ch in ' ,':
                        end = i
                        break
                value = buf[:end]
                buf = buf[end:].lstrip(' ')
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
        comma_pos = self._file_number_comma(args)
        if comma_pos == -1:
            return self._syntax_error(
                "LINE INPUT# requires file number and variable",
                ["Example: LINE INPUT #1, A$",
                 "Put a comma after the file number"])

        file_num_str = args[:comma_pos].strip()
        var_str = args[comma_pos + 1:].strip()

        file_num, err = self._parse_file_number(file_num_str)
        if err:
            return err
        err = self._require_open(file_num, 'I')
        if err:
            return err
        # Check the target before reading, so a refused read takes no line
        var_desc = self._parse_var_descriptor(var_str)
        err = self._require_string_target(var_desc)
        if err:
            return err

        handle = self.open_files[file_num]['handle']
        line = handle.readline()
        if not line:
            return self._runtime_error(
                f"INPUT PAST END OF FILE: #{file_num}",
                ["Check EOF(n) before reading",
                 "Example: WHILE NOT EOF(1): LINE INPUT #1, L$: WEND"])

        value = line.rstrip('\n').rstrip('\r')
        err = self.emulator.store_input_value(var_desc, value)
        if err:
            return self._store_error(err, var_str)
        return []

    def _require_string_target(self, var_desc):
        """LINE INPUT (console or file) reads text: only a string variable
        or string array element can take it."""
        if var_desc['name'].endswith('$'):
            return None
        return self._runtime_error(
            f"TYPE MISMATCH: LINE INPUT needs a string variable, not {var_desc['name']}",
            [f"Use a string variable: LINE INPUT {var_desc['name']}$",
             "Then VAL() it if you need a number"])

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
            return self._syntax_error(
                "LINE INPUT requires a variable name",
                ["Example: LINE INPUT A$",
                 'Example: LINE INPUT "Enter name"; N$'])

        # Set up input state (similar to regular INPUT but with line_input
        # flag); the target may be an array element, LINE INPUT A$(3)
        var_desc = self._parse_var_descriptor(var_str)
        err = self._require_string_target(var_desc)
        if err:
            return err
        self.emulator.input_variables = [var_desc]
        self.emulator.input_prompt = prompt_text
        self.emulator.current_input_index = 0
        self.emulator.waiting_for_input = True
        self.emulator.program_counter = (self.emulator.current_line, self.emulator.current_sub_line)

        return [{'type': 'input_request', 'prompt': prompt_text, 'variable': var_desc['name'],
                 'array': var_desc['array'], 'indices': var_desc.get('indices'),
                 'line_input': True}]

    # ── EOF ───────────────────────────────────────────────────────────

    def eof(self, file_num):
        """EOF(n) — returns -1 at end of file, 0 otherwise."""
        def fail(message, suggestions):
            raise ValueError(self.emulator.error_context.runtime_error(
                message, self.emulator.current_line,
                suggestions=suggestions).format_detailed())

        err = self._validate_file_number(file_num)
        if err:
            fail(f"FILE NUMBER ERROR: file number must be 1-{self.MAX_FILE_NUMBER}",
                 ["Use the number the file was opened with", 'Example: EOF(1) after OPEN "I", #1, "DATA"'])

        if file_num not in self.open_files:
            fail(f"FILE NOT OPEN: #{file_num}",
                 [f'Open it first: OPEN "I", #{file_num}, "FILENAME"',
                  "Check that CLOSE hasn't already run"])

        info = self.open_files[file_num]
        if info['mode'] != 'I':
            fail(f"EOF only valid for input files (#{file_num} is open for output)",
                 [f'Open the file for input: OPEN "I", #{file_num}, "FILENAME"',
                  "EOF tells you when INPUT# has read everything"])

        handle = info['handle']
        # Check read buffer first
        buf = info.get('_read_buffer', '')
        if buf.strip():
            return 0  # Data still in buffer

        # Peek ahead: only blank lines left counts as end of file, because
        # INPUT# skips blank lines (it would fail with INPUT PAST END)
        pos = handle.tell()
        try:
            while True:
                line = handle.readline()
                if not line:
                    return -1
                if line.strip():
                    return 0
        finally:
            handle.seek(pos)

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
