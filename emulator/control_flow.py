"""
Control Flow Commands for BasiCoCo BASIC Environment

Loop-closing commands (NEXT, WEND, LOOP), IF block management (ELSE, ENDIF),
and execution control (STOP, CONT, RESUME).

Opening commands (FOR, WHILE, DO, IF, GOTO, GOSUB, RETURN) are handled by
the AST evaluator in ast_evaluator.py.
"""

from .ast_nodes import basic_truthy
from .error_context import error_response, text_response


class ControlFlowCommands:
    """Handler for control-flow closing commands and execution control."""

    def __init__(self, emulator):
        self.emulator = emulator

    def register_commands(self, registry):
        """Register control-flow commands with the command registry."""
        em = self.emulator

        registry.register('NEXT', self.execute_next,
                         category='control',
                         description="End FOR loop and increment counter",
                         syntax="NEXT [variable]",
                         examples=["NEXT", "NEXT I", "NEXT X"])

        registry.register('WEND', self.execute_wend,
                         category='control',
                         description="End WHILE loop",
                         syntax="WEND",
                         examples=["WEND"])

        registry.register('LOOP', self.execute_loop,
                         category='control',
                         description="End DO loop block",
                         syntax="LOOP [WHILE condition | UNTIL condition]",
                         examples=["LOOP", "LOOP WHILE X > 0", "LOOP UNTIL Y = 10"])

        registry.register('ELSE', self.execute_else,
                         category='control',
                         description="Alternative branch in IF statement",
                         syntax="ELSE",
                         examples=["ELSE"])

        registry.register('ENDIF', self.execute_endif,
                         category='control',
                         description="End multi-line IF block",
                         syntax="ENDIF",
                         examples=["ENDIF"])

        registry.register('LOCAL', self.execute_local,
                         category='control',
                         description="Save variables for restoration on RETURN",
                         syntax="LOCAL var1, var2, ...",
                         examples=["LOCAL IX, IY", "LOCAL N$, I"])

        registry.register('STOP', self.execute_stop,
                         category='control',
                         description="Stop program execution",
                         syntax="STOP",
                         examples=["STOP"])

        registry.register('CONT', lambda args: em.executor.execute_cont(args),
                         category='system',
                         description="Continue program after STOP",
                         syntax="CONT",
                         examples=["CONT"])

        registry.register('RESUME', self.execute_resume,
                         category='flow',
                         description="Resume execution after ON ERROR GOTO handler",
                         syntax="RESUME [NEXT | line]",
                         examples=["RESUME", "RESUME NEXT", "RESUME 100"])

    def execute_next(self, args):
        em = self.emulator
        if not em.for_stack:
            error = em.error_context.runtime_error(
                "NEXT WITHOUT FOR",
                em.current_line,
                suggestions=[
                    "NEXT must be preceded by a FOR statement",
                    "Example: FOR I = 1 TO 10: ... : NEXT I",
                    "Check that FOR and NEXT statements are properly paired"
                ]
            )
            return error_response(error)

        for_info = em.for_stack[-1]
        var_name = for_info['var']

        # Increment the loop variable
        em.variables[var_name] += for_info['step']

        # Check if loop should continue
        current_val = em.variables[var_name]
        end_val = for_info['end']
        step_val = for_info['step']

        if ((step_val > 0 and current_val <= end_val) or
            (step_val < 0 and current_val >= end_val)):
            return [{'type': 'jump_after_for', 'for_line': for_info['line'], 'for_sub_line': for_info['sub_line']}]
        else:
            em.for_stack.pop()
            return []

    def execute_wend(self, args):
        """WEND statement - end WHILE loop"""
        em = self.emulator
        err = em._require_stack(em.while_stack, 'WEND', 'WHILE', 'WHILE condition ... WEND')
        if err:
            return err

        while_info = em.while_stack[-1]

        # Re-evaluate the condition using stored AST node
        result = em.ast_evaluator.visit(while_info['condition_ast'])
        condition_true = basic_truthy(result)
        if condition_true:
            return [{'type': 'jump_after_while',
                    'while_line': while_info['line'],
                    'while_sub_line': while_info['sub_line']}]
        else:
            em.while_stack.pop()
            return []

    def execute_loop(self, args):
        """LOOP statement - end DO/LOOP block"""
        em = self.emulator
        err = em._require_stack(em.do_stack, 'LOOP', 'DO', 'DO ... LOOP or DO ... LOOP WHILE condition')
        if err:
            return err

        do_info = em.do_stack[-1]

        # Parse LOOP [WHILE condition | UNTIL condition]
        args = args.strip()
        condition = do_info.get('condition')
        condition_ast = do_info.get('condition_ast')
        condition_type = do_info.get('condition_type')

        # Check for condition at LOOP (overrides DO condition)
        for keyword in ('WHILE', 'UNTIL'):
            prefix = keyword + ' '
            if args.upper().startswith(prefix):
                condition_str = args[len(prefix):].strip()
                condition_type = keyword
                if 'loop_condition_ast' not in do_info or do_info.get('loop_condition_str') != condition_str:
                    try:
                        do_info['loop_condition_ast'] = em.ast_parser.parse_expression(condition_str, em.current_line)
                        do_info['loop_condition_str'] = condition_str
                    except (ValueError, IndexError, KeyError, AttributeError):
                        do_info['loop_condition_ast'] = None
                condition_ast = do_info.get('loop_condition_ast')
                condition = condition_str if condition_ast is None else None
                break

        # Evaluate loop continuation
        should_continue = False
        if condition_ast is not None:
            result = em.ast_evaluator.visit(condition_ast)
            condition_true = basic_truthy(result)
            if condition_type == 'WHILE':
                should_continue = condition_true
            elif condition_type == 'UNTIL':
                should_continue = not condition_true
        elif condition:
            if condition_type == 'WHILE':
                should_continue = em.evaluate_condition(condition)
            elif condition_type == 'UNTIL':
                should_continue = not em.evaluate_condition(condition)
        else:
            should_continue = True

        if should_continue:
            return [{'type': 'jump_after_do',
                    'do_line': do_info['line'],
                    'do_sub_line': do_info['sub_line']}]
        else:
            em.do_stack.pop()
            return []

    def execute_else(self, args):
        """ELSE statement - alternative branch in multi-line IF"""
        em = self.emulator
        err = em._require_stack(em.if_stack, 'ELSE', 'IF', 'IF condition ... ELSE ... ENDIF')
        if err:
            return err

        if_info = em.if_stack[-1]

        if if_info['condition_met'] and not if_info['in_else']:
            if_info['in_else'] = True
            return [{'type': 'skip_else_block'}]

        if_info['in_else'] = True
        return []

    def execute_endif(self, args):
        """ENDIF statement - end multi-line IF block"""
        em = self.emulator
        err = em._require_stack(em.if_stack, 'ENDIF', 'IF', 'IF condition ... ENDIF')
        if err:
            return err

        em.if_stack.pop()
        return []

    def execute_local(self, args):
        """LOCAL var1, var2, ... — save variable values for restoration on RETURN.

        Must be inside a GOSUB call. Each listed variable's current value is
        saved onto the local_stack frame. On RETURN, saved values are restored.
        """
        em = self.emulator
        if not em.local_stack:
            error = em.error_context.runtime_error(
                "LOCAL WITHOUT GOSUB",
                em.current_line,
                suggestions=[
                    "LOCAL can only be used inside a subroutine called with GOSUB",
                    "Example: GOSUB MySub: ... : MySub: LOCAL I, J",
                    "LOCAL saves variables so RETURN restores them"
                ]
            )
            return error_response(error)

        if not args:
            error = em.error_context.syntax_error(
                "LOCAL requires variable names",
                em.current_line,
                suggestions=[
                    "Correct syntax: LOCAL var1, var2, ...",
                    "Example: LOCAL IX, IY, N$",
                    "Variables are saved and restored on RETURN"
                ]
            )
            return error_response(error)

        from .text_utils import StatementSplitter
        var_names = StatementSplitter.split_args(args)
        frame = em.local_stack[-1]
        for var_name in var_names:
            name = var_name.strip().upper()
            if not name:
                continue
            saved_value = em.variables.get(name, None)
            frame.append((name, saved_value))
        return []

    def execute_stop(self, args):
        """STOP command - stop program execution with message (allows CONT)"""
        em = self.emulator
        em.running = False
        em.stopped_position = (em.current_line, em.current_sub_line)
        return text_response('BREAK IN ' + str(em.current_line))

    def execute_resume(self, args):
        """RESUME [NEXT | line] - resume after ON ERROR GOTO handler."""
        em = self.emulator
        if not em.in_error_handler:
            error = em.error_context.runtime_error(
                "RESUME WITHOUT ERROR",
                suggestions=["RESUME can only be used inside an ON ERROR GOTO handler",
                             "Use ON ERROR GOTO line to set up an error handler first"])
            return error_response(error)
        em.in_error_handler = False
        args = args.strip().upper()
        if args == '' or args == '0':
            return [{'type': 'resume', 'position': em.error_resume_position}]
        elif args == 'NEXT':
            return [{'type': 'resume_next', 'position': em.error_resume_position}]
        else:
            try:
                line = em.eval_int(args, em.current_line)
            except (ValueError, TypeError):
                error = em.error_context.syntax_error(
                    f"Invalid RESUME target: {args}",
                    em.current_line,
                    suggestions=["Use RESUME, RESUME NEXT, or RESUME line"])
                return error_response(error)
            return [{'type': 'jump', 'line': line}]
