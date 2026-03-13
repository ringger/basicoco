"""
AST Evaluator for TRS-80 Color Computer BASIC Emulator

This module evaluates AST nodes produced by the parser, executing BASIC
statements and expressions at runtime.
"""

import time
from typing import Any, Union

from .ast_nodes import (
    ASTNode, ASTVisitor, LiteralNode, VariableNode, BinaryOpNode, UnaryOpNode,
    FunctionCallNode, ArrayAccessNode, AssignmentNode, IfStatementNode,
    ForStatementNode, WhileStatementNode, DoLoopStatementNode,
    ExitForStatementNode, EndStatementNode, GotoStatementNode,
    PrintStatementNode, GosubStatementNode, ReturnStatementNode,
    InputStatementNode, OnBranchStatementNode, OnErrorGotoNode,
    ProgramNode, BlockNode,
    Operator, basic_truthy
)
from .error_context import error_response, text_message, error_message


class ASTEvaluator(ASTVisitor):
    """Evaluator that executes AST nodes"""

    def __init__(self, emulator):
        self.emulator = emulator

    @staticmethod
    def _to_basic_int(val):
        """Convert a value to a BASIC integer for bitwise operations.

        Python booleans (from comparisons) map to -1 (True) / 0 (False)
        matching CoCo BASIC convention. Numbers are truncated to int.
        """
        if isinstance(val, bool):
            return -1 if val else 0
        return int(val)

    @staticmethod
    def _format_print_value(value):
        """Format a value for PRINT output.

        CoCo BASIC numeric formatting: a leading space for the sign position
        (positive numbers get a space, negative get '-') and a trailing space.
        """
        if isinstance(value, str):
            return value
        elif isinstance(value, (int, float)):
            if isinstance(value, float) and value.is_integer():
                num_str = str(int(value))
            else:
                num_str = str(value)
            if value < 0:
                return num_str + ' '
            else:
                return ' ' + num_str + ' '
        else:
            return str(value)

    def visit_number(self, node: LiteralNode) -> Union[int, float]:
        """Visit number literal"""
        return node.value

    def visit_string(self, node: LiteralNode) -> str:
        """Visit string literal"""
        return node.value

    def visit_variable(self, node: VariableNode) -> Any:
        """Visit variable reference"""
        var_name = node.name.upper()
        if var_name == 'ERR':
            return self.emulator.error_number
        if var_name == 'ERL':
            return self.emulator.error_line
        if var_name == 'TIMER':
            return int((time.time() - self.emulator.timer_epoch) * 60)
        if var_name in self.emulator.variables:
            return self.emulator.variables[var_name]
        return 0 if not var_name.endswith('$') else ""

    def visit_binary_op(self, node: BinaryOpNode) -> Any:
        """Visit binary operation"""
        left_val = self.visit(node.left)
        right_val = self.visit(node.right)

        if node.operator == Operator.ADD:
            return left_val + right_val
        elif node.operator == Operator.SUBTRACT:
            return left_val - right_val
        elif node.operator == Operator.MULTIPLY:
            return left_val * right_val
        elif node.operator == Operator.DIVIDE:
            if right_val == 0:
                raise ZeroDivisionError("Division by zero")
            return left_val / right_val
        elif node.operator == Operator.POWER:
            return left_val ** right_val
        elif node.operator == Operator.EQUAL:
            return -1 if left_val == right_val else 0
        elif node.operator == Operator.NOT_EQUAL:
            return -1 if left_val != right_val else 0
        elif node.operator == Operator.LESS_THAN:
            return -1 if left_val < right_val else 0
        elif node.operator == Operator.GREATER_THAN:
            return -1 if left_val > right_val else 0
        elif node.operator == Operator.LESS_EQUAL:
            return -1 if left_val <= right_val else 0
        elif node.operator == Operator.GREATER_EQUAL:
            return -1 if left_val >= right_val else 0
        elif node.operator == Operator.AND:
            return self._to_basic_int(left_val) & self._to_basic_int(right_val)
        elif node.operator == Operator.OR:
            return self._to_basic_int(left_val) | self._to_basic_int(right_val)
        elif node.operator == Operator.MOD:
            # Modulo operation
            if right_val == 0:
                raise ZeroDivisionError("Modulo by zero")
            return left_val % right_val
        else:
            error = self.emulator.error_context.runtime_error(
                f"Unknown binary operator: {node.operator}",
                suggestions=[
                    "Supported operators: +, -, *, /, ^, MOD, =, <>, <, >, <=, >=, AND, OR",
                    "Check operator spelling and spacing"
                ]
            )
            raise ValueError(error.format_message())

    def visit_unary_op(self, node: UnaryOpNode) -> Any:
        """Visit unary operation"""
        operand_val = self.visit(node.operand)

        if node.operator == Operator.SUBTRACT:
            return -operand_val
        elif node.operator == Operator.ADD:
            return +operand_val
        elif node.operator == Operator.NOT:
            return ~self._to_basic_int(operand_val)
        else:
            error = self.emulator.error_context.runtime_error(
                f"Unknown unary operator: {node.operator}",
                suggestions=[
                    "Supported unary operators: -, +, NOT",
                    "Check operator spelling"
                ]
            )
            raise ValueError(error.format_message())

    def visit_function_call(self, node: FunctionCallNode) -> Any:
        """Visit function call"""
        # Delegate to the expression evaluator's function registry
        func_name = node.function_name.upper()

        # Evaluate arguments to their actual values
        arg_values = []
        for arg in node.arguments:
            arg_values.append(self.visit(arg))

        # Check if it's a function first
        handler = self.emulator.function_registry.get_handler(func_name)
        if handler:
            return handler(self.emulator, arg_values)

        # If not a function, check if it's an array access (dimensioned or not).
        # Array access uses the same syntax as function calls — both are parsed
        # as FunctionCallNode and distinguished here at evaluation time.
        if len(arg_values) > 0:  # Has arguments, likely array access
            # Convert arguments to indices and delegate to array access
            indices = [int(val) for val in arg_values]
            return self.emulator._evaluate_array_access(func_name, ','.join(map(str, indices)))

        # Neither function nor array access
        available_functions = list(self.emulator.function_registry.list_functions()[:10])
        error = self.emulator.error_context.reference_error(
            func_name,
            "UNDEFINED FUNCTION",
            suggestions=[
                f"Available functions: {', '.join(available_functions[:5])}",
                "Check function name spelling",
                f"Use DIM {func_name}() to create an array instead"
            ]
        )
        raise ValueError(error.format_message())

    def visit_array_access(self, node: ArrayAccessNode) -> Any:
        """Visit array access"""
        array_name = node.array_name.upper()

        # Evaluate indices
        indices = []
        for index_node in node.indices:
            indices.append(int(self.visit(index_node)))

        # Get array element
        value, error = self.emulator.variable_manager.get_array_element(array_name, indices)
        if error:
            raise ValueError(error)

        return value

    def visit_while_statement(self, node: WhileStatementNode) -> Any:
        """Visit WHILE statement - evaluate condition, push to stack or skip"""
        condition_result = self.visit(node.condition)
        condition_true = basic_truthy(condition_result)

        if condition_true:
            self.emulator.while_stack.append({
                'condition_ast': node.condition,
                'line': self.emulator.current_line,
                'sub_line': self.emulator.current_sub_line
            })
            return []
        else:
            return [{'type': 'skip_while_loop'}]

    def visit_do_loop_statement(self, node: DoLoopStatementNode) -> Any:
        """Visit DO statement - evaluate top condition if present, push to stack"""
        if node.condition and node.condition_position == 'TOP':
            condition_result = self.visit(node.condition)
            condition_true = basic_truthy(condition_result)

            if node.condition_type == 'WHILE' and not condition_true:
                return [{'type': 'skip_do_loop'}]
            elif node.condition_type == 'UNTIL' and condition_true:
                return [{'type': 'skip_do_loop'}]

        self.emulator.do_stack.append({
            'condition_ast': node.condition,
            'condition_type': node.condition_type,
            'line': self.emulator.current_line,
            'sub_line': self.emulator.current_sub_line
        })
        return []

    def visit_exit_for_statement(self, node: ExitForStatementNode) -> Any:
        """Visit EXIT FOR statement - signal to exit current FOR loop"""
        if not self.emulator.for_stack:
            error = self.emulator.error_context.syntax_error(
                "EXIT FOR without matching FOR",
                self.emulator.current_line,
                suggestions=[
                    'EXIT FOR can only be used inside a FOR loop',
                    'Check that FOR loops are properly nested',
                    'Example: FOR I=1 TO 10 ... EXIT FOR ... NEXT I'
                ]
            )
            return error_response(error)
        return [{'type': 'exit_for_loop'}]

    def visit_if_statement(self, node: IfStatementNode) -> Any:
        """Visit IF statement - evaluate condition and execute appropriate branch"""
        condition_result = self.visit(node.condition)

        condition_true = basic_truthy(condition_result)

        if condition_true:
            result = self.visit(node.then_branch)
            # THEN with number = GOTO
            if isinstance(result, (int, float)) and not isinstance(result, bool):
                line_num = int(result)
                err = self._validate_line_number(line_num)
                if err:
                    return err
                return [{'type': 'jump', 'line': line_num}]
            # None means visitor couldn't handle it — fall back to registry
            if result is None:
                return None
            return result if isinstance(result, list) else []
        elif node.else_branch:
            result = self.visit(node.else_branch)
            if isinstance(result, (int, float)) and not isinstance(result, bool):
                return [{'type': 'jump', 'line': int(result)}]
            if result is None:
                return None
            return result if isinstance(result, list) else []
        else:
            return []

    def visit_block(self, node: BlockNode) -> Any:
        """Visit block statement - execute all statements in sequence"""
        results = []

        for statement in node.statements:
            result = self.visit(statement)
            if result:
                if isinstance(result, list):
                    results.extend(result)
                else:
                    results.append(result)

                # Check for control flow signals
                for item in (result if isinstance(result, list) else [result]):
                    if isinstance(item, dict) and item.get('type') in ['exit_for', 'jump', 'jump_return']:
                        return results  # Exit block early on control flow

        return results

    def visit_program(self, node: ProgramNode) -> Any:
        """Visit PROGRAM node - execute all statements in sequence"""
        results = []
        for statement in node.statements:
            try:
                result = self.visit(statement)
                if isinstance(result, list):
                    results.extend(result)
                elif result is not None:
                    results.append(result)

                # Check for control flow that should exit program
                for item in (result if isinstance(result, list) else [result]):
                    if isinstance(item, dict) and item.get('type') in ['jump', 'jump_return', 'end']:
                        return results  # Exit program on control flow
            except (ValueError, IndexError, KeyError, AttributeError, TypeError, ZeroDivisionError) as e:
                err = self.emulator.error_context.runtime_error(
                    str(e), self.emulator.current_line)
                results.append(error_message(err.format_message()))

        return results

    def visit_print_statement(self, node: PrintStatementNode) -> Any:
        """Visit PRINT statement"""
        ZONE_WIDTH = 16  # CoCo uses 16-column comma zones

        # Handle empty PRINT (blank line)
        if not node.expressions:
            self.emulator.print_column = 0
            return [text_message('')]

        # Build output from expressions and separators
        output_parts = []
        col = self.emulator.print_column

        for i, expr in enumerate(node.expressions):
            # Evaluate expression
            try:
                value = self.visit(expr)
                formatted = self._format_print_value(value)
                output_parts.append(formatted)
                col += len(formatted)
            except (ValueError, IndexError, KeyError, AttributeError, TypeError, ZeroDivisionError) as e:
                error = self.emulator.error_context.runtime_error(
                    f"Error evaluating PRINT expression: {e}",
                    suggestions=[
                        'Check that all variables are defined',
                        'Verify expression syntax is correct',
                        'Example: PRINT X, "Hello", Y+5'
                    ]
                )
                return error_response(error)

            # Add separator spacing (not for trailing separator)
            if i < len(node.separators) and i < len(node.expressions) - 1:
                sep = node.separators[i]
                if sep == ',':
                    # Advance to next 16-column zone boundary
                    next_zone = ((col // ZONE_WIDTH) + 1) * ZONE_WIDTH
                    spaces = next_zone - col
                    output_parts.append(' ' * spaces)
                    col = next_zone
                # Semicolon = no spacing

        # Join parts
        output_text = ''.join(output_parts)

        # Trailing separator means inline output (no newline)
        has_trailing_separator = len(node.separators) >= len(node.expressions)
        if has_trailing_separator:
            # Trailing comma: advance to next zone
            if node.separators[-1] == ',':
                next_zone = ((col // ZONE_WIDTH) + 1) * ZONE_WIDTH
                spaces = next_zone - col
                output_text += ' ' * spaces
                col = next_zone
            self.emulator.print_column = col
            return [text_message(output_text, inline=True)]
        self.emulator.print_column = 0
        if '\r' in output_text:
            return [text_message(output_text, inline=True)]
        return [text_message(output_text)]

    def visit_assignment(self, node: AssignmentNode) -> Any:
        """Visit assignment statement"""
        value = self.visit(node.value)

        if isinstance(node.target, ArrayAccessNode):
            # Array element assignment: A(5) = 42
            array_name = node.target.array_name.upper()
            err = self.emulator.check_reserved_name(array_name)
            if err:
                return err
            try:
                indices = [int(self.visit(idx)) for idx in node.target.indices]
            except (ValueError, TypeError) as e:
                err = self.emulator.error_context.runtime_error(
                    f"Invalid array index: {e}",
                    self.emulator.current_line,
                    suggestions=["Array indices must be numeric integers"])
                return error_response(err)
            err_msg = self.emulator.variable_manager.set_array_element(array_name, indices, value)
            if err_msg:
                err = self.emulator.error_context.runtime_error(
                    err_msg, self.emulator.current_line,
                    suggestions=["Check array dimensions with DIM"])
                return error_response(err)
        elif hasattr(node.target, 'name'):
            var_name = node.target.name.upper()
            if var_name == 'TIMER':
                try:
                    ticks = int(value)
                except (ValueError, TypeError):
                    err = self.emulator.error_context.type_error(
                        "TIMER value must be a number", "integer",
                        f"{type(value).__name__}")
                    return error_response(err)
                self.emulator.timer_epoch = time.time() - ticks / 60.0
                return []
            err = self.emulator.check_reserved_name(var_name)
            if err:
                return err
            self.emulator.variables[var_name] = value
        else:
            var_name = str(node.target).upper()
            self.emulator.variables[var_name] = value

        return []

    def visit_input_statement(self, node: InputStatementNode) -> Any:
        """Visit INPUT statement - request input from user"""
        # Extract prompt
        if node.prompt:
            prompt_text = self.visit(node.prompt)
            if not isinstance(prompt_text, str):
                prompt_text = str(prompt_text)
        else:
            prompt_text = "? "

        # Build variable descriptors (handle both simple variables and array elements)
        variables = []
        for var_node in node.variables:
            if isinstance(var_node, ArrayAccessNode):
                indices = [int(self.visit(idx)) for idx in var_node.indices]
                var_name = var_node.array_name.upper()
                variables.append({
                    'name': var_name,
                    'array': True,
                    'indices': indices
                })
            elif hasattr(var_node, 'name'):
                variables.append({
                    'name': var_node.name.upper(),
                    'array': False
                })
            else:
                variables.append({
                    'name': str(var_node).upper(),
                    'array': False
                })

        if not variables:
            error = self.emulator.error_context.syntax_error(
                "No variables specified in INPUT statement",
                self.emulator.current_line,
                suggestions=[
                    'Correct syntax: INPUT variable1, variable2, ...',
                    'Example: INPUT X, Y, NAME$',
                    'Specify at least one variable to input'
                ]
            )
            return error_response(error)

        # Store multi-variable INPUT state
        self.emulator.input_variables = variables
        self.emulator.input_prompt = prompt_text
        self.emulator.current_input_index = 0

        # Set flags and request input
        self.emulator.waiting_for_input = True
        self.emulator.program_counter = (self.emulator.current_line, self.emulator.current_sub_line)

        first_var = variables[0]
        return [{'type': 'input_request', 'prompt': prompt_text, 'variable': first_var['name'],
                 'array': first_var['array'], 'indices': first_var.get('indices')}]

    def visit_end_statement(self, node: EndStatementNode) -> Any:
        """Visit END statement - stop program execution"""
        self.emulator.running = False
        self.emulator.stopped_position = None
        return []

    def _resolve_target_line(self, node):
        """Resolve a GOTO/GOSUB target that may be a label or line number expression.

        If the target AST node is a bare variable whose name matches a label,
        return the label's line number.  Otherwise evaluate the expression
        normally and convert to int.
        """
        # Check for label reference before evaluating as variable
        if isinstance(node, VariableNode):
            label_line = self.emulator.resolve_label(node.name)
            if label_line is not None:
                return label_line
        value = self.visit(node)
        return int(value)

    def _resolve_target_with_error(self, node, command_name, suggestions):
        """Resolve a target line, returning (line_num, None) or (None, error_response).

        Wraps _resolve_target_line with standard error handling used by
        GOTO, GOSUB, ON...GOTO/GOSUB, and ON ERROR GOTO.
        """
        try:
            line_num = self._resolve_target_line(node)
        except (ValueError, TypeError):
            error = self.emulator.error_context.syntax_error(
                f"Invalid {command_name} target",
                self.emulator.current_line,
                suggestions=suggestions
            )
            return None, error_response(error)
        return line_num, None

    def _validate_line_number(self, line_num):
        """Return error_response if line_num <= 0, else None."""
        if line_num <= 0:
            error = self.emulator.error_context.runtime_error(
                f"Invalid line number {line_num}",
                self.emulator.current_line,
                suggestions=[
                    "Line numbers must be positive integers",
                    "Use line numbers that exist in your program",
                    "Check with LIST command to see available lines"
                ]
            )
            return error_response(error)
        return None

    def _push_gosub_frame(self):
        """Push GOSUB return frame onto call_stack and empty LOCAL frame onto local_stack."""
        self.emulator.call_stack.append((
            self.emulator.current_line, self.emulator.current_sub_line,
            len(self.emulator.if_stack), len(self.emulator.for_stack)))
        self.emulator.local_stack.append([])

    def visit_goto_statement(self, node: GotoStatementNode) -> Any:
        """Visit GOTO statement"""
        line_num, err = self._resolve_target_with_error(node.target_line, "GOTO", [
            "Correct syntax: GOTO line_number",
            "Example: GOTO 100 or GOTO L where L is a numeric variable",
            "Line number must be a positive integer"
        ])
        if err:
            return err

        err = self._validate_line_number(line_num)
        if err:
            return err

        return [{'type': 'jump', 'line': line_num}]

    def visit_gosub_statement(self, node: GosubStatementNode) -> Any:
        """Visit GOSUB statement"""
        line_num, err = self._resolve_target_with_error(node.target_line, "GOSUB", [
            "Correct syntax: GOSUB line_number",
            "Example: GOSUB 1000 or GOSUB SUB_LINE where SUB_LINE is a variable",
            "Make sure target line contains a subroutine that ends with RETURN"
        ])
        if err:
            return err

        err = self._validate_line_number(line_num)
        if err:
            return err

        self._push_gosub_frame()
        return [{'type': 'jump', 'line': line_num}]

    def visit_on_branch_statement(self, node: OnBranchStatementNode) -> Any:
        """Visit ON expr GOTO/GOSUB statement"""
        try:
            value = self.visit(node.expression)
            index = int(value)
        except (ValueError, TypeError) as e:
            error = self.emulator.error_context.runtime_error(
                f"ON expression error: {str(e)}",
                suggestions=["Ensure the expression evaluates to a number",
                             "Check variable values"])
            return error_response(error)

        # Out of range: continue to next statement (standard BASIC behavior)
        if index < 1 or index > len(node.targets):
            return []

        # Evaluate the selected target line number (may be a label)
        target_line, err = self._resolve_target_with_error(
            node.targets[index - 1], "ON", [
                "Use comma-separated line numbers or expressions",
                "Example: ON X GOTO 100,200,300"
            ])
        if err:
            return err

        if node.branch_type == 'GOSUB':
            self._push_gosub_frame()

        return [{'type': 'jump', 'line': target_line}]

    def visit_on_error_goto(self, node: OnErrorGotoNode) -> Any:
        """Visit ON ERROR GOTO statement"""
        target, err = self._resolve_target_with_error(node.target_line, "ON ERROR GOTO", [
            "Use ON ERROR GOTO 100",
            "Use ON ERROR GOTO 0 to disable handler"
        ])
        if err:
            return err

        if target == 0:
            self.emulator.on_error_goto_line = None
            if self.emulator.in_error_handler:
                self.emulator.in_error_handler = False
                error = self.emulator.error_context.runtime_error(
                    f"ERROR IN {self.emulator.error_line}")
                return error_response(error)
            return []

        self.emulator.on_error_goto_line = target
        return []

    def visit_return_statement(self, node: ReturnStatementNode) -> Any:
        """Visit RETURN statement"""
        if not self.emulator.call_stack:
            error = self.emulator.error_context.runtime_error(
                "RETURN WITHOUT GOSUB",
                self.emulator.current_line,
                suggestions=[
                    "RETURN must be preceded by a GOSUB statement",
                    "Example: GOSUB 1000: ... : 1000 RETURN",
                    "Check that subroutines are called with GOSUB before RETURN"
                ]
            )
            return error_response(error)

        entry = self.emulator.call_stack.pop()
        return_line, return_sub_line = entry[0], entry[1]
        saved_if_depth = entry[2] if len(entry) > 2 else None
        saved_for_depth = entry[3] if len(entry) > 3 else None
        # Restore LOCAL variables saved during this GOSUB call
        if self.emulator.local_stack:
            frame = self.emulator.local_stack.pop()
            for var_name, saved_value in reversed(frame):
                if saved_value is None:
                    # Variable didn't exist before LOCAL — remove it
                    self.emulator.variables.pop(var_name, None)
                else:
                    self.emulator.variables[var_name] = saved_value
        # Clean up stale if_stack/for_stack entries from early RETURN
        if saved_if_depth is not None:
            while len(self.emulator.if_stack) > saved_if_depth:
                self.emulator.if_stack.pop()
        if saved_for_depth is not None:
            while len(self.emulator.for_stack) > saved_for_depth:
                self.emulator.for_stack.pop()
        return [{'type': 'jump_return', 'line': return_line, 'sub_line': return_sub_line}]

    def visit_for_statement(self, node: ForStatementNode) -> Any:
        """Visit FOR statement - initialize loop variable and push to for_stack"""
        var_name = node.variable.name.upper() if hasattr(node.variable, 'name') else str(node.variable).upper()

        try:
            start_val = self.visit(node.start_value)
            end_val = self.visit(node.end_value)
            step_val = self.visit(node.step_value) if node.step_value else 1
        except (ValueError, TypeError) as e:
            err = self.emulator.error_context.runtime_error(
                str(e), self.emulator.current_line,
                suggestions=["FOR loop bounds must be numeric"])
            return error_response(err)

        # Ensure numeric values
        try:
            start_val = float(start_val) if isinstance(start_val, str) else start_val
            end_val = float(end_val) if isinstance(end_val, str) else end_val
            step_val = float(step_val) if isinstance(step_val, str) else step_val
        except (ValueError, TypeError):
            error = self.emulator.error_context.type_error(
                "FOR loop values must be numeric",
                "number",
                "non-numeric expression",
                suggestions=[
                    "Use numeric expressions: FOR I = 1 TO 10",
                    "Variables must contain numbers: LET N = 5; FOR I = 1 TO N",
                    "Check that all expressions evaluate to numbers"
                ]
            )
            return error_response(error)

        # Check if loop should execute at all
        if ((step_val > 0 and start_val > end_val) or
            (step_val < 0 and start_val < end_val)):
            self.emulator.variables[var_name] = start_val
            return [{'type': 'skip_for_loop', 'var': var_name}]

        self.emulator.variables[var_name] = start_val
        self.emulator.for_stack.append({
            'var': var_name,
            'end': end_val,
            'step': step_val,
            'line': self.emulator.current_line,
            'sub_line': self.emulator.current_sub_line
        })

        return []
