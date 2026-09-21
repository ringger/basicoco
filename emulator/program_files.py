"""
Program File Operations for BasiCoCo BASIC Environment

Handles program file management: LOAD, SAVE, DIR, KILL, CD, FILES, DRIVE.
For sequential data I/O (OPEN, CLOSE, PRINT#, INPUT#), see file_io.py.
"""

import glob
import os
import re
import time

from .error_context import error_response, text_response, text_message

# Bundled example programs shipped with the project (read-only fallback for
# LOAD / MERGE / CHAIN / OPEN "I")
PROJECT_PROGRAMS_DIR = os.path.realpath(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'programs'))


class SandboxError(ValueError):
    """A filename that would reach outside the programs sandbox."""


class FileManager:
    """Manages file operations for the BASIC interpreter.

    Takes a reference to the emulator so it can access program state,
    error_context, parse_line, etc.

    Filesystem sandbox: every file a BASIC program names is confined to the
    ``programs/`` directory under the current working directory (the
    *writable root*), optionally inside a per-session virtual subdirectory set
    by CD. Absolute paths, ``~`` and ``..`` are refused, and symlinks that
    resolve outside the root are rejected. The project's bundled programs are
    a read-only fallback for loading. Nothing here ever calls os.chdir, so one
    session's CD cannot affect another's.
    """

    def __init__(self, emulator):
        self.emulator = emulator
        self.subdir = ''          # virtual CD directory, relative to the root
        self.pending_kill = None  # path awaiting KILL confirmation

    # ── Sandbox ──────────────────────────────────────────────────────

    @staticmethod
    def writable_root():
        """The sandbox root: programs/ under the current working directory."""
        return os.path.realpath(os.path.join(os.getcwd(), 'programs'))

    def _confine(self, name, root, subdir=''):
        """Resolve *name* inside *root*/*subdir*, or raise SandboxError."""
        name = name.strip()
        if (os.path.isabs(name) or name.startswith('~')
                or re.match(r'^[A-Za-z]:', name)):
            raise SandboxError(f"ABSOLUTE PATHS NOT ALLOWED: {name}")
        if '..' in re.split(r'[\\/]', name):
            raise SandboxError(f"PATH OUTSIDE PROGRAMS DIRECTORY: {name}")
        path = os.path.realpath(os.path.join(root, subdir, name))
        if os.path.commonpath([path, root]) != root:
            raise SandboxError(f"PATH OUTSIDE PROGRAMS DIRECTORY: {name}")
        return path

    def resolve_writable(self, name):
        """Path for creating, writing or deleting *name* (writable root only)."""
        return self._confine(name, self.writable_root(), self.subdir)

    def find_readable(self, name):
        """Existing path for reading *name*: the writable root (current CD
        directory) first, then the bundled programs. None if not found."""
        candidates = [self.resolve_writable(name)]
        if os.path.isdir(PROJECT_PROGRAMS_DIR):
            candidates.append(self._confine(name, PROJECT_PROGRAMS_DIR))
        return next((p for p in candidates if os.path.isfile(p)), None)

    def _sandbox_error(self, err, command):
        return error_response(self.emulator.error_context.runtime_error(
            f"{command}: {err}", self.emulator.current_line,
            suggestions=['Files live in the programs directory; use a plain name like "MYFILE"',
                         'Subdirectories inside programs/ are fine: "GAMES/PONG"',
                         'Absolute paths, ~ and .. are not allowed']))

    def filename_argument(self, raw):
        """The filename a command names: a quoted literal, or a string
        expression such as F$ or "GAME"+N$ (evaluated)."""
        raw = raw.strip()
        if raw[:1] in ('"', "'"):
            quote = raw[0]
            end = raw.find(quote, 1)
            if end == -1 or end == len(raw) - 1:
                return raw[1:end] if end != -1 else raw[1:]
        try:
            value = self.emulator.evaluate_expression(raw)
        except Exception:
            return self._strip_quotes(raw)
        return value if isinstance(value, str) else self._strip_quotes(raw)

    def _syntax_error(self, message, suggestions):
        return error_response(self.emulator.error_context.syntax_error(
            message, self.emulator.current_line, suggestions=suggestions))

    def _runtime_error(self, message, suggestions):
        return error_response(self.emulator.error_context.runtime_error(
            message, self.emulator.current_line, suggestions=suggestions))

    @staticmethod
    def _strip_quotes(s):
        """Strip surrounding single or double quotes from a string."""
        s = s.strip()
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            return s[1:-1]
        return s

    def _require_filename(self, filename, verb, example):
        """Return error response if filename is empty, else None."""
        if not filename:
            return self._syntax_error("Filename required", [
                f"Provide a filename to {verb}",
                f'Example: {example}',
                'File extension .bas will be added automatically'
            ])
        return None

    @staticmethod
    def _ensure_bas_extension(filename):
        """Add .bas extension if not already present."""
        if not filename.lower().endswith('.bas'):
            filename += '.bas'
        return filename

    def _find_program_file(self, filename):
        """Find a .bas file inside the sandbox. Returns path or None; raises
        SandboxError for names that would escape it."""
        return self.find_readable(filename)

    def _next_auto_line(self, emu):
        """Return the next auto-generated line number (max existing + 10, rounded up to next 10)."""
        if emu.program:
            highest = max(emu.program.keys())
            return ((highest // 10) + 1) * 10
        return 10

    def _load_lines(self, filepath, emu):
        """Read a .bas file and store its lines, auto-numbering unnumbered lines.

        Returns the count of lines loaded.
        """
        lines_loaded = 0
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                line_num, code = emu.parse_line(line)
                if line_num is None:
                    # Unnumbered line — auto-assign
                    code = line  # entire line is code
                    line_num = self._next_auto_line(emu)
                if code:
                    emu.store_program_line(line_num, code)
                    lines_loaded += 1
        return lines_loaded

    def _file_error(self, message, filename, command):
        """Return a formatted file error response list."""
        error = self.emulator.error_context.file_error(message, filename, command)
        return error_response(error)

    def load_program(self, filename):
        """Load a BASIC program from a file"""
        emu = self.emulator
        filename = self.filename_argument(filename)

        err = self._require_filename(filename, 'load', 'LOAD "MYGAME"')
        if err:
            return err

        filename = self._ensure_bas_extension(filename)

        try:
            found_file = self._find_program_file(filename)
        except SandboxError as e:
            return self._sandbox_error(e, 'LOAD')

        try:

            if not found_file:
                return self._file_error(f"FILE NOT FOUND: {os.path.basename(filename)}", filename, "LOAD")

            # Clear current program and interpreter state
            emu.clear_interpreter_state(clear_program=True)

            lines_loaded = self._load_lines(found_file, emu)

            return text_response(f'LOADED {lines_loaded} LINES FROM {os.path.basename(found_file)}')

        except FileNotFoundError:
            return self._file_error(f"FILE NOT FOUND: {os.path.basename(filename)}", filename, "LOAD")
        except PermissionError:
            return self._file_error(f"PERMISSION DENIED: {os.path.basename(filename)}", filename, "LOAD")
        except Exception as e:
            return self._file_error(f"LOAD ERROR: {str(e)}", filename, "LOAD")

    def save_program(self, filename):
        """Save the current BASIC program to a file"""
        emu = self.emulator
        filename = self.filename_argument(filename)

        err = self._require_filename(filename, 'save', 'SAVE "MYGAME"')
        if err:
            return err

        if not emu.program:
            return self._runtime_error("NO PROGRAM TO SAVE", [
                "Enter a program first using line numbers",
                'Example: 10 PRINT "HELLO"',
                'Use LIST command to see current program'
            ])

        filename = self._ensure_bas_extension(filename)

        try:
            filename = self.resolve_writable(filename)
        except SandboxError as e:
            return self._sandbox_error(e, 'SAVE')

        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            # (negative = a pending immediate-mode line, never saved)
            sorted_lines = [(n, code) for n, code in sorted(emu.program.items()) if n >= 0]

            with open(filename, 'w') as f:
                for line_num, code in sorted_lines:
                    f.write(f"{line_num} {code}\n")

            lines_saved = len(sorted_lines)
            return text_response(f'SAVED {lines_saved} LINES TO {os.path.basename(filename)}')

        except PermissionError:
            return self._file_error(f"PERMISSION DENIED: {os.path.basename(filename)}", filename, "SAVE")
        except (OSError, Exception) as e:
            return self._file_error(f"SAVE ERROR: {str(e)}", filename, "SAVE")

    def dir_command(self, args=None):
        """DIR command - List BASIC program files in the sandbox: the current
        CD directory, then the bundled (read-only) programs."""
        current_dir = os.path.join(self.writable_root(), self.subdir)
        search_dirs = [(current_dir, self._display_dir())]
        if (os.path.isdir(PROJECT_PROGRAMS_DIR)
                and os.path.realpath(current_dir) != PROJECT_PROGRAMS_DIR):
            search_dirs.append((PROJECT_PROGRAMS_DIR, 'PROJECT PROGRAMS/ (READ-ONLY)'))

        output = []
        output.append(text_message('BASIC PROGRAM FILES:'))
        output.append(text_message('=' * 40))

        total_files = 0

        for directory, dir_name in search_dirs:
            if not os.path.isdir(directory):
                continue

            files = glob.glob(os.path.join(directory, "*.bas"))

            if files:
                output.append(text_message(f"\n{dir_name}:"))

                # Sort files and display
                files.sort()
                for file_path in files:
                    filename = os.path.basename(file_path)
                    try:
                        # Get file size
                        size = os.path.getsize(file_path)
                        size_str = f"{size:>6} bytes"

                        mtime = os.path.getmtime(file_path)
                        time_str = time.strftime("%m/%d/%y %H:%M", time.localtime(mtime))

                        output.append(text_message(f"  {filename:<20} {size_str} {time_str}"))
                        total_files += 1
                    except OSError:
                        # If we can't get file info, just show the name
                        output.append(text_message(f"  {filename}"))
                        total_files += 1

        if total_files == 0:
            output.append(text_message('\nNO .BAS FILES FOUND'))
            output.append(text_message('Use SAVE "filename" to create programs'))
        else:
            output.append(text_message(f'\nTOTAL: {total_files} FILE(S)'))
            output.append(text_message('Use LOAD "filename" to load a program'))

        # Add empty line so prompt appears on new line
        output.append(text_message(''))

        return output

    def files_command(self, args=None):
        """FILES command - Reserve file buffers (no-op in modern implementation)"""
        return self.emulator._system_ok()

    def drive_command(self, args=None):
        """DRIVE command - Set default drive (no-op in modern implementation)"""
        return self.emulator._system_ok()

    def kill_file(self, filename):
        """Delete a BASIC program file with confirmation"""
        filename = self.filename_argument(filename)

        err = self._require_filename(filename, 'delete', 'KILL "OLDGAME"')
        if err:
            return err

        filename = self._ensure_bas_extension(filename)

        # Only files in the writable sandbox can be deleted (never the
        # bundled read-only programs)
        try:
            target = self.resolve_writable(filename)
        except SandboxError as e:
            return self._sandbox_error(e, 'KILL')
        if not os.path.isfile(target):
            return self._file_error(f"FILE NOT FOUND: {os.path.basename(filename)}", filename, "KILL")

        # The path stays on the server; the client only answers Y/N
        self.pending_kill = target
        return [
            text_message(f'DELETE {os.path.basename(target)}? (Y/N)'),
            {'type': 'input_request', 'prompt': '? ', 'variable': '_kill_confirm'},
        ]

    def process_kill_confirmation(self, response, filename=None):
        """Process the Y/N answer to a pending KILL.

        The file deleted is the one KILL recorded server-side; *filename*
        (still sent by older clients) is ignored, so a client can never
        choose what gets deleted.
        """
        target, self.pending_kill = self.pending_kill, None
        if target is None:
            return self._runtime_error("NO KILL PENDING", [
                'Use KILL "filename" first; it asks for confirmation',
                'Answer Y to delete or N to cancel'])

        if response.strip().upper() in ['Y', 'YES']:
            try:
                os.remove(target)
                return text_response(f'DELETED {os.path.basename(target)}')
            except PermissionError:
                return self._file_error(f"PERMISSION DENIED: {os.path.basename(target)}", target, "KILL")
            except OSError as e:
                return self._file_error(f"DELETE ERROR: {str(e)}", target, "KILL")
        return text_response('DELETE CANCELLED')

    def merge_program(self, filename):
        """MERGE - merge lines from a file into the current program in memory.

        Lines with matching numbers replace existing lines; new line numbers
        are inserted in order.  Unlike LOAD, the current program is NOT
        cleared first.
        """
        emu = self.emulator
        filename = self.filename_argument(filename)

        err = self._require_filename(filename, 'merge', 'MERGE "SUBS"')
        if err:
            return err

        filename = self._ensure_bas_extension(filename)

        try:
            found_file = self._find_program_file(filename)
        except SandboxError as e:
            return self._sandbox_error(e, 'MERGE')

        try:
            if not found_file:
                return self._file_error(
                    f"FILE NOT FOUND: {os.path.basename(filename)}",
                    filename, "MERGE")

            lines_merged = self._load_lines(found_file, emu)

            result = text_response(
                f'MERGED {lines_merged} LINES FROM {os.path.basename(found_file)}')
            # Signal executor to rebuild position list if running
            if emu.running:
                result.append({'type': 'program_modified'})
            return result

        except PermissionError:
            return self._file_error(
                f"PERMISSION DENIED: {os.path.basename(filename)}",
                filename, "MERGE")
        except Exception as e:
            return self._file_error(
                f"MERGE ERROR: {str(e)}", filename, "MERGE")

    def chain_program(self, args):
        """CHAIN - load and run another program.

        Syntax:
            CHAIN "filename"              - load & run, clearing variables
            CHAIN "filename", ALL         - load & run, preserving variables
            CHAIN "filename", line_num    - load & run starting at line_num
            CHAIN "filename", ALL, line_num - preserve variables, start at line_num

        On the real CoCo, CHAIN loaded from tape/disk and immediately ran.
        """
        emu = self.emulator

        if not args or not args.strip():
            return self._syntax_error("Filename required", [
                'Provide a filename to chain',
                'Example: CHAIN "UTILS"',
                'Use CHAIN "file", ALL to keep variables'
            ])

        # Parse arguments: "filename" [, ALL] [, line_number]
        from .text_utils import StatementSplitter
        parts = StatementSplitter.split_args(args)

        filename = self.filename_argument(parts[0])
        preserve_vars = False
        start_line = None
        start_label = None

        for part in parts[1:]:
            stripped = part.strip()
            if stripped.upper() == 'ALL':
                preserve_vars = True
            else:
                try:
                    start_line = int(stripped)
                except ValueError:
                    # Might be a label name
                    if re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', stripped):
                        start_label = stripped.upper()
                    else:
                        return self._syntax_error(f"Invalid CHAIN argument: {stripped}", [
                            'Use ALL to preserve variables',
                            'Use a line number or label to start at a specific point',
                            'Example: CHAIN "GAME", ALL, 1000'
                        ])

        filename = self._ensure_bas_extension(filename)

        try:
            found_file = self._find_program_file(filename)
        except SandboxError as e:
            return self._sandbox_error(e, 'CHAIN')

        try:
            if not found_file:
                return self._file_error(
                    f"FILE NOT FOUND: {os.path.basename(filename)}",
                    filename, "CHAIN")

            # CHAIN from a running program hands control back to the executor
            # loop (see the 'chain' directive) instead of starting a nested run
            called_from_program = emu.running

            # Save variables/arrays if requested
            saved_vars = None
            saved_arrays = None
            if preserve_vars:
                saved_vars = dict(emu.variables)
                saved_arrays = dict(emu.arrays)

            # Clear state and load the new program
            emu.clear_interpreter_state(clear_program=True)

            self._load_lines(found_file, emu)

            # Restore variables if ALL was specified
            if saved_vars is not None:
                emu.variables = saved_vars
            if saved_arrays is not None:
                emu.arrays = saved_arrays

            # Resolve label to line number if needed
            if start_label is not None:
                resolved = emu.resolve_label(start_label)
                if resolved is None:
                    return self._file_error(
                        f"UNDEFINED LABEL: {start_label}",
                        os.path.basename(found_file), "CHAIN")
                start_line = resolved

            if called_from_program:
                emu.running = True
                return [{'type': 'chain', 'start_line': start_line}]

            # Run the loaded program (CHAIN typed as an immediate command)
            if start_line is not None:
                return emu.executor.run_program_from_line(
                    start_line, clear_variables=False)
            else:
                return emu.run_program(clear_variables=False)

        except PermissionError:
            return self._file_error(
                f"PERMISSION DENIED: {os.path.basename(filename)}",
                filename, "CHAIN")
        except Exception as e:
            return self._file_error(
                f"CHAIN ERROR: {str(e)}", filename, "CHAIN")

    def _display_dir(self, subdir=None):
        """How a sandbox directory is shown to the user, e.g. PROGRAMS/GAMES."""
        subdir = self.subdir if subdir is None else subdir
        return 'PROGRAMS/' + subdir.replace(os.sep, '/') if subdir else 'PROGRAMS/'

    def change_directory(self, path):
        """CD - change this session's directory inside the programs sandbox.

        The directory is virtual (per interpreter); the process working
        directory is never changed. "/" or "~" returns to the programs root;
        ".." goes up but never above it.
        """
        path = self.filename_argument(path) if path.strip() else ''

        if not path:
            return text_response(f'CURRENT DIRECTORY: {self._display_dir()}')

        old_display = self._display_dir()
        if path in ('/', '~', '\\'):
            new_subdir = ''
        elif path == '..':
            new_subdir = os.path.dirname(self.subdir)
        else:
            try:
                target = self.resolve_writable(path)
            except SandboxError as e:
                return self._sandbox_error(e, 'CD')
            if not os.path.isdir(target):
                return self._file_error(f"DIRECTORY NOT FOUND: {path}", path, "CD")
            new_subdir = os.path.relpath(target, self.writable_root())
            if new_subdir == '.':
                new_subdir = ''

        self.subdir = new_subdir
        return [text_message(f'CHANGED FROM {old_display}'),
                text_message(f'TO {self._display_dir()}')]
