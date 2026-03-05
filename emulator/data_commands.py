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
            error = em.error_context.syntax_error(
                "READ requires variable names",
                em.current_line,
                suggestions=[
                    "Specify variables to read data into",
                    "Example: READ A, B$, C",
                    "Variables must match DATA statement types"
                ]
            )
            return error_response(error)

        var_names = StatementSplitter.split_args(args)

        for var_name in var_names:
            if em.data_pointer >= len(em.data_statements):
                error = em.error_context.runtime_error(
                    "OUT OF DATA",
                    em.current_line,
                    suggestions=[
                        "Add more DATA statements to your program",
                        "Use RESTORE to reset data pointer to beginning",
                        "Check that READ statements match available DATA"
                    ]
                )
                return error_response(error)

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
            error = em.error_context.syntax_error(
                "Invalid array syntax in DATA statement",
                em.current_line,
                suggestions=[
                    'Array syntax: A(1,2) or B$(5)',
                    'Check array name and index format',
                    'Ensure parentheses are properly matched'
                ]
            )
            return error_response(error)

        array_name = var_name[:paren_pos]
        indices_str = var_name[paren_pos + 1:-1]

        try:
            indices = [em.eval_int(idx) for idx in StatementSplitter.split_args(indices_str)]

            err_msg = em.variable_manager.set_array_element(array_name.upper(), indices, value)
            if err_msg:
                error = em.error_context.runtime_error(
                    err_msg, em.current_line,
                    suggestions=["Check array dimensions with DIM",
                                 "Array indices must be within bounds"])
                return error_response(error)
            return None

        except ValueError:
            error = em.error_context.syntax_error(
                "Invalid line number format",
                em.current_line,
                suggestions=[
                    'Line numbers must be integers',
                    'Example: 10, 20, 100',
                    'Check that the line number is valid'
                ]
            )
            return error_response(error)
        except (IndexError, TypeError, KeyError):
            error = em.error_context.runtime_error(
                "Array index out of bounds",
                suggestions=[
                    'Check that array indices are within valid range',
                    'Arrays are 0-indexed: DIM A(10) creates indices 0-10',
                    'Use valid positive integer indices'
                ]
            )
            return error_response(error)

    def execute_restore(self, args):
        """RESTORE command - reset data pointer to beginning."""
        self.emulator.data_pointer = 0
        return []
