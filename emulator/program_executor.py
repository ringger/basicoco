"""
ProgramExecutor for BasiCoCo BASIC Environment

Drives program execution: RUN, CONT, continue after INPUT/PAUSE.
Handles the main execution loop, flow-control directives, and ON ERROR GOTO.
"""

import logging
import re

from .ast_nodes import basic_truthy
from .commands import CompiledCommand, CompiledMultiLineIf
from .error_context import error_response, text_response, error_message, text_message

logger = logging.getLogger(__name__)


def _classify_error(message: str) -> int:
    """Map an error message to a CoCo-style numeric error code."""
    msg = message.upper()
    if 'DIVISION BY ZERO' in msg or 'DIVIDE BY ZERO' in msg:
        return 99
    if 'SYNTAX' in msg:
        return 1
    if 'UNDEFINED LINE' in msg:
        return 7
    if 'TYPE MISMATCH' in msg:
        return 13
    if 'OVERFLOW' in msg:
        return 6
    if 'OUT OF DATA' in msg:
        return 4
    if 'ILLEGAL FUNCTION' in msg or 'ILLEGAL QUANTITY' in msg:
        return 5
    if 'STRING TOO LONG' in msg:
        return 14
    if re.search(r'SUBSCRIPT|OUT OF RANGE|DIMENSION', msg):
        return 9
    return 0


class ProgramExecutor:
    """Drives BASIC program execution: RUN, CONT, continue after INPUT/PAUSE.

    Takes a reference to the emulator so it can access program state,
    stacks, process_statement(), etc.
    """

    def __init__(self, emulator):
        self.emulator = emulator

    # ------------------------------------------------------------------
    # Position helpers (pure lookups on expanded_program)
    # ------------------------------------------------------------------

    def _save_resume_point(self, current_pos_index, all_positions):
        """Save the program counter to the next position for later resumption."""
        emu = self.emulator
        if current_pos_index + 1 < len(all_positions):
            emu.program_counter = all_positions[current_pos_index + 1]
        else:
            emu.program_counter = None

    def _find_position_index(self, pos, all_positions):
        """Find the index of an exact (line, sub_line) position, or None."""
        try:
            return all_positions.index(pos)
        except ValueError:
            return None

    def _find_line_position(self, target_line, all_positions):
        """Find the first sub-line position for a given line number.

        Returns the index into *all_positions*, or ``None`` if not found.
        """
        for i, (ln, _si) in enumerate(all_positions):
            if ln == target_line:
                return i
        return None

    @staticmethod
    def _get_keyword(entry):
        """Return the command keyword for a program entry (string or CompiledCommand)."""
        if isinstance(entry, CompiledCommand):
            return entry.keyword
        if isinstance(entry, str):
            return entry.strip().split(None, 1)[0].upper() if entry.strip() else ''
        return ''

    def _skip_to_keyword(self, keyword, current_pos_index, all_positions):
        """Search forward for a statement starting with *keyword*.

        Returns the index of the matching position, or ``None``.
        """
        emu = self.emulator
        keyword_upper = keyword.upper()
        for pos_idx in range(current_pos_index + 1, len(all_positions)):
            entry = emu.expanded_program.get(all_positions[pos_idx], '')
            if self._get_keyword(entry) == keyword_upper:
                return pos_idx
        return None

    def _skip_to_next(self, var_name, current_pos_index, all_positions):
        """Search forward for a matching NEXT statement.

        Returns the index of the matching NEXT, or ``None``.
        """
        emu = self.emulator
        for pos_idx in range(current_pos_index + 1, len(all_positions)):
            entry = emu.expanded_program.get(all_positions[pos_idx], '')
            if isinstance(entry, CompiledCommand):
                if entry.keyword == 'NEXT':
                    if not entry.args or entry.args == var_name:
                        return pos_idx
            elif isinstance(entry, str):
                stmt = entry.strip()
                if stmt.startswith('NEXT'):
                    parts = stmt.split()
                    if len(parts) == 1 or (len(parts) > 1 and parts[1] == var_name):
                        return pos_idx
        return None

    def _skip_if_or_else_block(self, current_pos_index, all_positions, stop_at_else):
        """Skip forward through nested IF blocks.

        If *stop_at_else* is True, stop at a matching ELSE or ENDIF.
        If False, stop only at a matching ENDIF.

        Returns (new_pos_index, jumped).
        """
        emu = self.emulator
        nest_level = 0
        for pos_idx in range(current_pos_index + 1, len(all_positions)):
            entry = emu.expanded_program.get(all_positions[pos_idx], '')
            if isinstance(entry, CompiledMultiLineIf):
                nest_level += 1
            elif isinstance(entry, CompiledCommand):
                kw = entry.keyword
                if stop_at_else and kw == 'ELSE' and nest_level == 0:
                    return pos_idx, True
                elif kw == 'ENDIF':
                    if nest_level == 0:
                        return pos_idx, True
                    else:
                        nest_level -= 1
            elif isinstance(entry, str):
                stmt = entry.strip().upper()
                if stmt.startswith('IF ') and 'THEN' in stmt:
                    nest_level += 1
                elif stop_at_else and stmt.startswith('ELSE') and nest_level == 0:
                    return pos_idx, True
                elif stmt.startswith('ENDIF'):
                    if nest_level == 0:
                        return pos_idx, True
                    else:
                        nest_level -= 1
        return current_pos_index, False

    # ------------------------------------------------------------------
    # Flow control dispatcher
    # ------------------------------------------------------------------

    def _handle_flow_control(self, result, current_pos_index, all_positions, output):
        """Process flow-control items from a statement result.

        Returns ``(new_pos_index, action)`` where *action* is:
        - ``'next'``   -- advance to *new_pos_index* normally
        - ``'jumped'`` -- jump to *new_pos_index* (don't increment)
        - ``'return'`` -- return *output* immediately (INPUT / PAUSE pause)
        - ``'stop'``   -- stop execution
        """
        emu = self.emulator

        # --- INPUT / PAUSE: return immediately so caller can yield control ---
        for item in result:
            if item.get('type') == 'input_request':
                self._save_resume_point(current_pos_index, all_positions)
                emu.waiting_for_input = True
                emu.running = False
                output.append(item)
                return current_pos_index, 'return'
            if item.get('type') == 'pause':
                self._save_resume_point(current_pos_index, all_positions)
                emu.waiting_for_pause_continuation = True
                emu.running = False
                output.append(item)
                return current_pos_index, 'return'

        # --- Jump / flow-control directives ---
        for item in result:
            item_type = item.get('type')

            if item_type == 'jump':
                idx = self._find_line_position(item['line'], all_positions)
                if idx is not None:
                    return idx, 'jumped'
                output.append(error_message(f"UNDEFINED LINE {item['line']}"))
                return current_pos_index, 'stop'

            elif item_type == 'jump_after_for':
                for_pos = (item['for_line'], item.get('for_sub_line', 0))
                idx = self._find_position_index(for_pos, all_positions)
                if idx is not None:
                    return idx + 1, 'jumped'
                output.append(error_message(f"UNDEFINED FOR LINE {item['for_line']}"))
                return current_pos_index, 'stop'

            elif item_type == 'jump_return':
                return_line = item['line']
                return_sub_line = item['sub_line']
                # Find first sub-line after the GOSUB call
                for i, (ln, si) in enumerate(all_positions):
                    if ln == return_line and si > return_sub_line:
                        return i, 'jumped'
                # Try next line
                for i, (ln, _si) in enumerate(all_positions):
                    if ln > return_line:
                        return i, 'jumped'
                return current_pos_index + 1, 'jumped'

            elif item_type == 'skip_for_loop':
                idx = self._skip_to_next(item['var'], current_pos_index, all_positions)
                if idx is not None:
                    return idx + 1, 'jumped'
                output.append(error_message('FOR WITHOUT NEXT'))
                return current_pos_index, 'stop'

            elif item_type == 'skip_while_loop':
                idx = self._skip_to_keyword('WEND', current_pos_index, all_positions)
                if idx is not None:
                    return idx + 1, 'jumped'
                output.append(error_message('WHILE WITHOUT WEND'))
                return current_pos_index, 'stop'

            elif item_type == 'jump_after_while':
                pos = (item['while_line'], item['while_sub_line'])
                idx = self._find_position_index(pos, all_positions)
                if idx is not None:
                    return idx + 1, 'jumped'
                return current_pos_index + 1, 'next'

            elif item_type == 'skip_do_loop':
                idx = self._skip_to_keyword('LOOP', current_pos_index, all_positions)
                if idx is not None:
                    return idx + 1, 'jumped'
                output.append(error_message('DO WITHOUT LOOP'))
                return current_pos_index, 'stop'

            elif item_type == 'jump_after_do':
                pos = (item['do_line'], item['do_sub_line'])
                idx = self._find_position_index(pos, all_positions)
                if idx is not None:
                    return idx + 1, 'jumped'
                return current_pos_index + 1, 'next'

            elif item_type == 'exit_for_loop':
                if emu.for_stack:
                    var_name = emu.for_stack[-1]['var']
                    emu.for_stack.pop()
                    idx = self._skip_to_next(var_name, current_pos_index, all_positions)
                    if idx is not None:
                        return idx + 1, 'jumped'
                return current_pos_index + 1, 'jumped'

            elif item_type == 'skip_if_block':
                new_idx, found = self._skip_if_or_else_block(
                    current_pos_index, all_positions, stop_at_else=True)
                if found:
                    return new_idx, 'jumped'
                output.append(error_message('IF WITHOUT ENDIF'))
                return current_pos_index, 'stop'

            elif item_type == 'skip_else_block':
                new_idx, found = self._skip_if_or_else_block(
                    current_pos_index, all_positions, stop_at_else=False)
                if found:
                    return new_idx, 'jumped'
                output.append(error_message('ELSE WITHOUT ENDIF'))
                return current_pos_index, 'stop'

            elif item_type == 'resume':
                idx = self._find_position_index(item['position'], all_positions)
                if idx is not None:
                    return idx, 'jumped'
                return current_pos_index + 1, 'next'

            elif item_type == 'program_modified':
                # MERGE changed expanded_program; rebuild all_positions
                return current_pos_index, 'rebuild'

            elif item_type == 'resume_next':
                idx = self._find_position_index(item['position'], all_positions)
                if idx is not None:
                    return idx + 1, 'next'
                return current_pos_index + 1, 'next'

            elif item_type != 'input_request':
                if item.get('type') == 'error':
                    # ON ERROR GOTO handler intercept — suppress error output
                    if (emu.on_error_goto_line is not None
                            and not emu.in_error_handler):
                        line_num, sub_index = all_positions[current_pos_index]
                        emu.error_line = line_num
                        emu.error_number = _classify_error(
                            item.get('message', ''))
                        emu.error_resume_position = (line_num, sub_index)
                        emu.in_error_handler = True
                        handler_idx = self._find_line_position(
                            emu.on_error_goto_line, all_positions)
                        if handler_idx is not None:
                            return handler_idx, 'jumped'
                    # No handler or handler line not found
                    logger.warning('Runtime error at line %d: %s',
                                   all_positions[current_pos_index][0],
                                   item.get('message', '(unknown)'))
                    output.append(item)
                    emu.emit_output([item])
                    emu.running = False
                    emu.clear_all_stacks()
                    return current_pos_index, 'stop'
                # Regular output -- filter system OK messages
                if not item.get('source') == 'system':
                    output.append(item)
                    emu.emit_output([item])

        return current_pos_index + 1, 'next'

    # ------------------------------------------------------------------
    # Main execution loop
    # ------------------------------------------------------------------

    def _execute_statements_loop(self, all_positions, start_index):
        """Shared execution loop used by run_program, continue_program_execution,
        and execute_cont.  Returns the accumulated output list."""
        emu = self.emulator
        output = []
        has_graphics = False
        current_pos_index = start_index

        while current_pos_index < len(all_positions) and emu.running:
            # Safety check
            emu.iteration_count += 1
            if emu.safety_enabled and emu.iteration_count > emu.max_iterations:
                logger.warning('Program stopped: too many iterations (%d > %d)',
                               emu.iteration_count, emu.max_iterations)
                output.append(error_message('PROGRAM STOPPED - TOO MANY ITERATIONS'))
                emu.running = False
                break
            if emu.iteration_count > emu.max_absolute_iterations:
                logger.warning('Program stopped: absolute iteration limit reached (%d)',
                               emu.max_absolute_iterations)
                output.append(error_message('PROGRAM STOPPED - ABSOLUTE ITERATION LIMIT REACHED'))
                emu.running = False
                break

            line_num, sub_index = all_positions[current_pos_index]
            emu.current_line = line_num
            emu.current_sub_line = sub_index
            statement = emu.expanded_program[(line_num, sub_index)]

            if emu.trace_mode and sub_index == 0:
                output.append(text_message(f'[{line_num}]'))

            # Dispatch: CompiledMultiLineIf → condition eval + if_stack,
            # CompiledCommand → direct call, AST node → visitor,
            # string → full process_statement (file I/O, DATA)
            if isinstance(statement, CompiledMultiLineIf):
                condition_result = basic_truthy(emu.ast_evaluator.visit(statement.condition_ast))
                if_info = {
                    'condition_met': condition_result,
                    'line': line_num,
                    'sub_line': sub_index,
                    'in_else': False
                }
                emu.if_stack.append(if_info)
                result = [{'type': 'skip_if_block'}] if not condition_result else []
            elif isinstance(statement, CompiledCommand):
                result = statement.handler(statement.args)
            elif isinstance(statement, str):
                result = emu.process_statement(statement)
            else:
                try:
                    result = emu.ast_evaluator.visit(statement)
                    if not isinstance(result, list):
                        result = None
                except (ValueError, IndexError, KeyError, AttributeError,
                        TypeError, ZeroDivisionError) as e:
                    error_msg = str(e) if str(e) else f"{type(e).__name__}"
                    result = error_response(
                        emu.error_context.runtime_error(error_msg, line_num)
                    )

            if result:
                # Auto-yield on PCLS: when a screen clear arrives after
                # graphics output, flush the completed frame to the
                # client and resume at the PCLS itself.
                if has_graphics:
                    for item in result:
                        if item.get('type') == 'pcls':
                            emu.program_counter = all_positions[current_pos_index]
                            emu.waiting_for_pause_continuation = True
                            emu.running = False
                            output.append({'type': 'pause', 'duration': 0.05})
                            return output

                new_pos, action = self._handle_flow_control(
                    result, current_pos_index, all_positions, output)
                if action == 'return':
                    return output
                elif action == 'stop':
                    emu.running = False
                    break
                elif action == 'rebuild':
                    # MERGE modified the program — rebuild position list and data
                    cur_key = all_positions[current_pos_index]
                    all_positions = sorted(emu.expanded_program.keys())
                    # Rebuild data_statements from merged data_values
                    emu.data_statements = []
                    for line_num in sorted(emu.data_values.keys()):
                        emu.data_statements.extend(
                            [(line_num, v) for v in emu.data_values[line_num]]
                        )
                    # Advance past the current (MERGE) statement
                    idx = self._find_position_index(cur_key, all_positions)
                    current_pos_index = (idx + 1) if idx is not None else 0
                elif action == 'jumped':
                    current_pos_index = new_pos
                else:  # 'next'
                    current_pos_index = new_pos

                for item in result:
                    if item.get('type') in ('line', 'paint', 'pset',
                                            'circle', 'draw'):
                        has_graphics = True
            else:
                current_pos_index += 1

        return output

    # ------------------------------------------------------------------
    # Public execution entry points
    # ------------------------------------------------------------------

    def run_program(self, clear_variables=True):
        emu = self.emulator
        if not emu.program:
            error = emu.error_context.runtime_error(
                "NO PROGRAM",
                suggestions=[
                    "Enter a program first using line numbers",
                    'Example: 10 PRINT "HELLO"',
                    'Use LOAD "filename" to load a program from disk'
                ]
            )
            return error_response(error)

        # Clear variables and arrays but keep program (like authentic BASIC)
        if clear_variables:
            emu.clear_interpreter_state(clear_program=False)

        emu.running = True

        # Build data_statements from pre-collected data_values (parsed at store-time)
        for line_num in sorted(emu.data_values.keys()):
            emu.data_statements.extend(
                [(line_num, v) for v in emu.data_values[line_num]]
            )

        all_positions = sorted(emu.expanded_program.keys())
        output = self._execute_statements_loop(all_positions, 0)
        if not emu.waiting_for_input and not emu.waiting_for_pause_continuation:
            emu.running = False
        return output

    def run_program_from_line(self, start_line, clear_variables=True):
        """Run the program starting at a specific line number.

        Used by CHAIN "file", line_num to begin execution at an arbitrary line.
        """
        emu = self.emulator
        if not emu.program:
            error = emu.error_context.runtime_error(
                "NO PROGRAM",
                suggestions=[
                    "Enter a program first using line numbers",
                    'Example: 10 PRINT "HELLO"',
                    'Use LOAD "filename" to load a program from disk'
                ]
            )
            return error_response(error)

        if clear_variables:
            emu.clear_interpreter_state(clear_program=False)

        emu.running = True

        # Build data_statements
        for line_num in sorted(emu.data_values.keys()):
            emu.data_statements.extend(
                [(line_num, v) for v in emu.data_values[line_num]]
            )

        all_positions = sorted(emu.expanded_program.keys())

        # Find the starting position for the requested line
        start_index = self._find_line_position(start_line, all_positions)
        if start_index is None:
            emu.running = False
            error = emu.error_context.runtime_error(
                f"UNDEFINED LINE NUMBER: {start_line}",
                suggestions=[
                    'Check that the target line exists in the chained program',
                    'Use LIST to view the program after loading'
                ]
            )
            return error_response(error)

        output = self._execute_statements_loop(all_positions, start_index)
        if not emu.waiting_for_input and not emu.waiting_for_pause_continuation:
            emu.running = False
        return output

    def continue_program_execution(self):
        """Resume program execution after INPUT or PAUSE."""
        emu = self.emulator
        if not hasattr(emu, 'program_counter') or emu.program_counter is None:
            error = emu.error_context.runtime_error(
                "No program to continue",
                suggestions=[
                    'A program must be running to use CONT',
                    'Run a program first with RUN',
                    'Use CONT only after STOP or error interruption'
                ]
            )
            return error_response(error)

        # Clear pause continuation state if that's why we're continuing
        if hasattr(emu, 'waiting_for_pause_continuation') and emu.waiting_for_pause_continuation:
            emu.waiting_for_pause_continuation = False

        emu.running = True
        all_positions = sorted(emu.expanded_program.keys())

        try:
            start_index = all_positions.index(emu.program_counter)
        except ValueError:
            emu.running = False
            emu.program_counter = None
            error = emu.error_context.runtime_error(
                "Cannot resume - program has been modified",
                suggestions=[
                    'The program was changed while paused',
                    'Use RUN to start the program from the beginning'
                ]
            )
            return error_response(error)

        output = self._execute_statements_loop(all_positions, start_index)
        if not emu.waiting_for_input and not emu.waiting_for_pause_continuation:
            emu.running = False
            emu.program_counter = None
        return output

    def execute_cont(self, args):
        """CONT command -- continue execution after STOP."""
        emu = self.emulator
        if emu.stopped_position is None:
            error = emu.error_context.runtime_error(
                "Cannot continue - no program was stopped",
                suggestions=[
                    'Use CONT only after a program has been stopped',
                    'Program must be paused with STOP or Ctrl+C',
                    'Run a new program with RUN command'
                ]
            )
            return error_response(error)

        stopped_line, stopped_sub_line = emu.stopped_position

        emu.running = True
        all_positions = sorted(emu.expanded_program.keys())

        # Find the position after where we stopped
        continue_pos = None
        for i, (ln, si) in enumerate(all_positions):
            if (ln == stopped_line and si > stopped_sub_line) or ln > stopped_line:
                continue_pos = i
                break

        if continue_pos is None:
            emu.running = False
            return text_response('READY')

        output = self._execute_statements_loop(all_positions, continue_pos)
        emu.running = False
        emu.stopped_position = None
        return output
