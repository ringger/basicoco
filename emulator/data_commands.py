"""
DATA/READ/RESTORE Commands for BasiCoCo BASIC Environment

Handles DATA storage, READ into variables, and RESTORE of the data pointer.
"""

from .text_utils import StatementSplitter
from .error_context import error_response


class DataCommands:
    """Handler for DATA, READ, and RESTORE commands."""

    def __init__(self, emulator):
        self.emulator = emulator

    def _syntax_error(self, message, suggestions):
        em = self.emulator
        return error_response(em.error_context.syntax_error(
            message, em.current_line, suggestions=suggestions))

    def _runtime_error(self, message, suggestions):
        em = self.emulator
        return error_response(em.error_context.runtime_error(
            message, em.current_line, suggestions=suggestions))

    def register_commands(self, registry):
        """Register data commands with the command registry."""
        registry.register('DATA', self.execute_data,
                         category='data',
                         description="Define data values for READ statements",
                         syntax="DATA value1, value2, ...",
                         examples=["DATA 10, 20, 30", "DATA \"HELLO\", \"WORLD\""])

        registry.register('READ', self.execute_read,
                         category='data',
                         description="Read data values into variables",
                         syntax="READ variable1, variable2, ...",
                         examples=["READ A, B, C", "read NAME$, AGE"])

        registry.register('RESTORE', self.execute_restore,
                         category='data',
                         description="Reset DATA pointer to beginning",
                         syntax="RESTORE",
                         examples=["RESTORE"])

    @staticmethod
    def parse_data_values(args):
        """Parse DATA argument string into a list of typed values."""
        items = StatementSplitter.split_on_delimiter(args, delimiter=',')
        data_items = []
        for item in items:
            item = item.strip()
            if item.startswith('"') and item.endswith('"'):
                data_items.append(item[1:-1])
            else:
                try:
                    data_items.append(int(item))
                except ValueError:
                    try:
                        data_items.append(float(item))
                    except ValueError:
                        data_items.append(item)
        return data_items

    def execute_data(self, args):
        """DATA command - store data values in program."""
        em = self.emulator
        if not args:
            return []

        # During program execution, DATA statements are skipped
        # (they were already collected at store-time)
        if em.running:
            return []

        # Immediate mode: parse and append directly
        data_items = self.parse_data_values(args)
        em.data_statements.extend([(em.current_line, item) for item in data_items])
        return []

    def execute_read(self, args):
        """READ command - read data into variables."""
        em = self.emulator
        if not args:
            return self._syntax_error("READ requires variable names", [
                "Specify variables to read data into",
                "Example: READ A, B$, C",
                "Variables must match DATA statement types"
            ])

        var_names = StatementSplitter.split_args(args)

        for var_name in var_names:
            if em.data_pointer >= len(em.data_statements):
                return self._runtime_error("OUT OF DATA", [
                    "Add more DATA statements to your program",
                    "Use RESTORE to reset data pointer to beginning",
                    "Check that READ statements match available DATA"
                ])

            line_num, data_value = em.data_statements[em.data_pointer]
            em.data_pointer += 1

            if '(' in var_name and ')' in var_name:
                result = self.assign_array_element(var_name, data_value)
                if result:
                    return result
            else:
                em.variables[var_name] = data_value

        return []

    def assign_array_element(self, var_name, value):
        """Assign a value to an array element, return error result if there's an issue."""
        em = self.emulator
        paren_pos = var_name.find('(')
        if paren_pos == -1 or not var_name.rstrip().endswith(')'):
            return self._syntax_error("Invalid array syntax in DATA statement", [
                'Array syntax: A(1,2) or B$(5)',
                'Check array name and index format',
                'Ensure parentheses are properly matched'
            ])

        array_name = var_name[:paren_pos]
        indices_str = var_name[paren_pos + 1:-1]

        try:
            indices = [em.eval_int(idx) for idx in StatementSplitter.split_args(indices_str)]

            err_msg = em.variable_manager.set_array_element(array_name.upper(), indices, value)
            if err_msg:
                return self._runtime_error(err_msg, [
                    "Check array dimensions with DIM",
                    "Array indices must be within bounds"
                ])
            return None

        except ValueError:
            return self._syntax_error("Invalid line number format", [
                'Line numbers must be integers',
                'Example: 10, 20, 100',
                'Check that the line number is valid'
            ])
        except (IndexError, TypeError, KeyError):
            return self._runtime_error("Array index out of bounds", [
                'Check that array indices are within valid range',
                'Arrays are 0-indexed: DIM A(10) creates indices 0-10',
                'Use valid positive integer indices'
            ])

    def execute_restore(self, args):
        """RESTORE [line | label] - reset data pointer.

        No argument: reset to beginning of all DATA.
        With line number: reset to first DATA at or after that line.
        With label name: resolve label to line number, then same.
        """
        em = self.emulator
        args = args.strip() if args else ''
        if not args:
            em.data_pointer = 0
            return []

        # Resolve label or line number
        target_line = em.resolve_label(args.upper())
        if target_line is None:
            try:
                target_line = em.eval_int(args, em.current_line)
            except (ValueError, TypeError):
                return self._syntax_error(f"Invalid RESTORE target: {args}", [
                    "Use RESTORE, RESTORE line_number, or RESTORE label",
                    "Example: RESTORE 1000 or RESTORE MyData"
                ])

        # Find first data entry at or after target line
        for i, (line_num, value) in enumerate(em.data_statements):
            if line_num >= target_line:
                em.data_pointer = i
                return []

        # No DATA at or after target — point past end (next READ will get OUT OF DATA)
        em.data_pointer = len(em.data_statements)
        return []
