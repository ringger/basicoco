"""
FileManager for BasiCoCo BASIC Environment

Handles all file I/O operations: LOAD, SAVE, DIR, KILL, CD, FILES, DRIVE.
Extracted from core.py to reduce its size.
"""

import glob
import os
import time

from .error_context import error_response, text_response


class FileManager:
    """Manages file operations for the BASIC interpreter.

    Takes a reference to the emulator so it can access program state,
    error_context, parse_line, etc.
    """

    def __init__(self, emulator):
        self.emulator = emulator

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
            error = self.emulator.error_context.syntax_error(
                "Filename required",
                self.emulator.current_line,
                suggestions=[
                    f"Provide a filename to {verb}",
                    f'Example: {example}',
                    'File extension .bas will be added automatically'
                ]
            )
            return error_response(error)
        return None

    @staticmethod
    def _ensure_bas_extension(filename):
        """Add .bas extension if not already present."""
        if not filename.lower().endswith('.bas'):
            filename += '.bas'
        return filename

    def _find_program_file(self, filename):
        """Search for a .bas file in standard locations. Returns path or None."""
        search_paths = [
            filename,
            os.path.join('programs', filename),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), filename),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'programs', filename),
        ]
        for path in search_paths:
            if os.path.exists(path):
                return path
        return None

    def _file_error(self, message, filename, command):
        """Return a formatted file error response list."""
        error = self.emulator.error_context.file_error(message, filename, command)
        return error_response(error)

    def load_program(self, filename):
        """Load a BASIC program from a file"""
        emu = self.emulator
        filename = self._strip_quotes(filename)

        err = self._require_filename(filename, 'load', 'LOAD "MYGAME"')
        if err:
            return err

        filename = self._ensure_bas_extension(filename)

        try:
            found_file = self._find_program_file(filename)

            if not found_file:
                return self._file_error(f"FILE NOT FOUND: {os.path.basename(filename)}", filename, "LOAD")

            # Clear current program and interpreter state
            emu.clear_interpreter_state(clear_program=True)

            # Load and parse the file
            with open(found_file, 'r') as f:
                lines_loaded = 0
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):  # Skip empty lines and comments
                        line_num, code = emu.parse_line(line)
                        if line_num is not None:
                            if code:
                                emu.program[line_num] = code
                                emu.expand_line_to_sublines(line_num, code)
                                lines_loaded += 1

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
        filename = self._strip_quotes(filename)

        err = self._require_filename(filename, 'save', 'SAVE "MYGAME"')
        if err:
            return err

        if not emu.program:
            error = emu.error_context.runtime_error(
                "NO PROGRAM TO SAVE",
                suggestions=[
                    "Enter a program first using line numbers",
                    'Example: 10 PRINT "HELLO"',
                    'Use LIST command to see current program'
                ]
            )
            return error_response(error)

        filename = self._ensure_bas_extension(filename)

        try:
            os.makedirs('programs', exist_ok=True)

            if not os.path.dirname(filename):
                filename = os.path.join('programs', filename)

            sorted_lines = sorted(emu.program.items())

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
        """DIR command - List available BASIC program files"""
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
        return self.emulator._system_ok()

    def drive_command(self, args=None):
        """DRIVE command - Set default drive (no-op in modern implementation)"""
        return self.emulator._system_ok()

    def kill_file(self, filename):
        """Delete a BASIC program file with confirmation"""
        emu = self.emulator
        filename = self._strip_quotes(filename)

        err = self._require_filename(filename, 'delete', 'KILL "OLDGAME"')
        if err:
            return err

        filename = self._ensure_bas_extension(filename)

        try:
            found_file = self._find_program_file(filename)

            if not found_file:
                return self._file_error(f"FILE NOT FOUND: {os.path.basename(filename)}", filename, "KILL")

            return [
                {'type': 'text', 'text': f'DELETE {os.path.basename(found_file)}? (Y/N)'},
                {'type': 'input_request', 'prompt': '? ', 'variable': '_kill_confirm', 'filename': found_file},
            ]

        except Exception as e:
            return self._file_error(f"KILL ERROR: {str(e)}", filename, "KILL")

    def process_kill_confirmation(self, response, filename):
        """Process the confirmation response for KILL command"""
        response = response.strip().upper()

        if response in ['Y', 'YES']:
            try:
                os.remove(filename)
                return text_response(f'DELETED {os.path.basename(filename)}')
            except PermissionError:
                return self._file_error(f"PERMISSION DENIED: {os.path.basename(filename)}", filename, "KILL")
            except Exception as e:
                return self._file_error(f"DELETE ERROR: {str(e)}", filename, "KILL")
        else:
            return text_response('DELETE CANCELLED')

    def change_directory(self, path):
        """Change current working directory"""
        path = self._strip_quotes(path)

        if not path:
            current_dir = os.getcwd()
            return text_response(f'CURRENT DIRECTORY: {current_dir}')

        try:
            if path == "..":
                path = os.path.dirname(os.getcwd())
            elif path == "~":
                path = os.path.expanduser("~")
            elif path == "/":
                path = "/"
            elif path.startswith("~/"):
                path = os.path.expanduser(path)

            old_dir = os.getcwd()
            os.chdir(path)
            new_dir = os.getcwd()

            return [{'type': 'text', 'text': f'CHANGED FROM {old_dir}'},
                    {'type': 'text', 'text': f'TO {new_dir}'}]

        except FileNotFoundError:
            return self._file_error(f"DIRECTORY NOT FOUND: {path}", path, "CD")
        except PermissionError:
            return self._file_error(f"PERMISSION DENIED: {path}", path, "CD")
        except (OSError, Exception) as e:
            return self._file_error(f"CD ERROR: {str(e)}", path, "CD")
