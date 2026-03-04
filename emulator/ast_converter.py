"""
AST Statement Converter for TRS-80 Color Computer BASIC Emulator

This module converts complex single-line BASIC control structures into their
multi-line equivalents using the AST parser infrastructure.
"""

import re
from typing import List, Optional
from .parser import BasicParser
from .ast_nodes import (
    ASTNode, IfStatementNode, ForStatementNode, WhileStatementNode,
    DoLoopStatementNode, ExitForStatementNode, EndStatementNode, GotoStatementNode, PrintStatementNode,
    GosubStatementNode, ReturnStatementNode, InputStatementNode,
    AssignmentNode, BlockNode, VariableNode, LiteralNode,
    BinaryOpNode, UnaryOpNode, FunctionCallNode, ArrayAccessNode,
    OnBranchStatementNode, OnErrorGotoNode,
    Operator, NodeType, ASTVisitor
)


class ASTStatementConverter(ASTVisitor):
    """
    Converts AST nodes representing single-line control structures
    into equivalent multi-line BASIC statement sequences.
    """

    def __init__(self):
        self.statements = []
        self.indent_level = 0

    def convert(self, node: ASTNode) -> List[str]:
        """
        Convert an AST node to multi-line BASIC statements.

        Args:
            node: The AST node to convert

        Returns:
            List of BASIC statement strings
        """
        self.statements = []
        self.indent_level = 0
        self.visit(node)
        return self.statements

    def visit_if_statement(self, node: IfStatementNode) -> None:
        """Convert IF statement node to multi-line format"""
        # Generate IF condition THEN line
        # Don't add outer parentheses for the top-level condition
        condition_str = self._expression_to_string(node.condition, add_outer_parens=False)
        self.statements.append(f"IF {condition_str} THEN")

        # Process THEN branch
        if node.then_branch:
            self.indent_level += 1
            self.visit(node.then_branch)
            self.indent_level -= 1

        # Process ELSE branch if present
        if node.else_branch:
            self.statements.append("ELSE")
            self.indent_level += 1
            self.visit(node.else_branch)
            self.indent_level -= 1

        # Add ENDIF
        self.statements.append("ENDIF")

    def visit_for_statement(self, node: ForStatementNode) -> None:
        """Convert FOR statement node to multi-line format"""
        # Generate FOR variable = start TO end [STEP step]
        var_name = node.variable.name if isinstance(node.variable, VariableNode) else str(node.variable)
        start_str = self._expression_to_string(node.start_value)
        end_str = self._expression_to_string(node.end_value)

        for_line = f"FOR {var_name} = {start_str} TO {end_str}"
        if node.step_value:
            step_str = self._expression_to_string(node.step_value)
            for_line += f" STEP {step_str}"

        self.statements.append(for_line)

        # Process loop body
        if node.body:
            self.indent_level += 1
            self.visit(node.body)
            self.indent_level -= 1

        # Add NEXT
        self.statements.append(f"NEXT {var_name}")

    def visit_while_statement(self, node: WhileStatementNode) -> None:
        """Convert WHILE/WEND statement node to multi-line format"""
        condition_str = self._expression_to_string(node.condition)
        self.statements.append(f"WHILE {condition_str}")

        # Process loop body
        if node.body:
            self.indent_level += 1
            self.visit(node.body)
            self.indent_level -= 1

        # Add WEND
        self.statements.append("WEND")

    def visit_do_loop_statement(self, node: DoLoopStatementNode) -> None:
        """Convert DO/LOOP statement node to multi-line format"""
        if node.condition_position == 'TOP':
            # DO WHILE/UNTIL condition
            condition_str = self._expression_to_string(node.condition) if node.condition else ""
            if node.condition_type == 'WHILE':
                self.statements.append(f"DO WHILE {condition_str}")
            else:
                self.statements.append(f"DO UNTIL {condition_str}")
        else:
            # Plain DO or LOOP WHILE/UNTIL
            self.statements.append("DO")

        # Process loop body
        if node.body:
            self.indent_level += 1
            self.visit(node.body)
            self.indent_level -= 1

        # Add LOOP with condition if at bottom
        if node.condition_position == 'BOTTOM' and node.condition:
            condition_str = self._expression_to_string(node.condition)
            if node.condition_type == 'WHILE':
                self.statements.append(f"LOOP WHILE {condition_str}")
            else:
                self.statements.append(f"LOOP UNTIL {condition_str}")
        else:
            self.statements.append("LOOP")

    def visit_exit_for_statement(self, node: ExitForStatementNode) -> None:
        """Convert EXIT FOR statement"""
        self.statements.append("EXIT FOR")

    def visit_end_statement(self, node: EndStatementNode) -> None:
        """Convert END statement"""
        self.statements.append("END")

    def visit_goto_statement(self, node: GotoStatementNode) -> None:
        """Convert GOTO statement"""
        target_str = self._expression_to_string(node.target_line)
        self.statements.append(f"GOTO {target_str}")

    def visit_gosub_statement(self, node: GosubStatementNode) -> None:
        """Convert GOSUB statement"""
        target_str = self._expression_to_string(node.target_line)
        self.statements.append(f"GOSUB {target_str}")

    def visit_return_statement(self, node: ReturnStatementNode) -> None:
        """Convert RETURN statement"""
        self.statements.append("RETURN")

    def visit_input_statement(self, node: InputStatementNode) -> None:
        """Convert INPUT statement"""
        if node.prompt:
            prompt_str = self._expression_to_string(node.prompt)
            # Determine if we should use semicolon or comma after prompt
            # For now, use semicolon as it's more common
            input_str = f"INPUT {prompt_str};"
        else:
            input_str = "INPUT"

        # Add variable list
        var_list = []
        for var_node in node.variables:
            if isinstance(var_node, VariableNode):
                var_list.append(var_node.name)
            else:
                # Fallback to expression string
                var_list.append(self._expression_to_string(var_node))

        if var_list:
            input_str += " " + ", ".join(var_list)

        self.statements.append(input_str)

    def visit_print_statement(self, node: PrintStatementNode) -> None:
        """Convert PRINT statement"""
        if not node.expressions:
            self.statements.append("PRINT")
            return

        # Build PRINT statement with expressions and separators
        print_str = "PRINT "
        for i, expr in enumerate(node.expressions):
            expr_str = self._expression_to_string(expr)
            print_str += expr_str

            # Add separator if present
            if i < len(node.separators):
                print_str += node.separators[i]

        self.statements.append(print_str)

    def visit_assignment(self, node: AssignmentNode) -> None:
        """Convert assignment statement"""
        # Get target (variable or array access)
        if isinstance(node.target, VariableNode):
            target_str = node.target.name
        elif isinstance(node.target, ArrayAccessNode):
            target_str = node.target.array_name + "("
            indices = [self._expression_to_string(idx) for idx in node.target.indices]
            target_str += ",".join(indices) + ")"
        else:
            target_str = self._expression_to_string(node.target)

        # Get value expression
        value_str = self._expression_to_string(node.value)

        # Generate assignment (using LET for clarity in converted code)
        self.statements.append(f"LET {target_str} = {value_str}")

    def visit_block(self, node: BlockNode) -> None:
        """Convert block of statements"""
        for statement in node.statements:
            self.visit(statement)


    def visit_number(self, node: LiteralNode) -> None:
        """Convert number literal nodes - handle bare numbers as GOTO statements"""
        # Convert bare numbers to GOTO statements
        # This handles cases like "IF A = 5 THEN 50" where 50 should be "GOTO 50"
        self.statements.append(f"GOTO {node.value}")

    def visit_string(self, node: LiteralNode) -> None:
        """Convert string literal nodes"""
        self.statements.append(str(node.value))

    def visit_on_branch_statement(self, node: OnBranchStatementNode) -> None:
        """Convert ON expr GOTO/GOSUB back to string form"""
        expr_str = self._expression_to_string(node.expression)
        targets_str = ','.join(self._expression_to_string(t) for t in node.targets)
        self.statements.append(f"ON {expr_str} {node.branch_type} {targets_str}")

    def visit_on_error_goto(self, node: OnErrorGotoNode) -> None:
        """Convert ON ERROR GOTO back to string form"""
        target_str = self._expression_to_string(node.target_line)
        self.statements.append(f"ON ERROR GOTO {target_str}")

    def generic_visit(self, node: ASTNode) -> None:
        """Handle any other statement types by converting to string"""
        # For unhandled nodes, try to convert to expression string
        expr_str = self._expression_to_string(node)
        if expr_str:
            self.statements.append(expr_str)

    def _expression_to_string(self, node: ASTNode, add_outer_parens=True) -> str:
        """Convert an expression AST node back to BASIC syntax string"""
        if isinstance(node, LiteralNode):
            if node.node_type == NodeType.STRING:
                return f'"{node.value}"'
            else:
                return str(node.value)

        elif isinstance(node, VariableNode):
            return node.name

        elif isinstance(node, BinaryOpNode):
            # For operands, we need to consider if they need parentheses based on precedence
            left_str = self._expression_to_string_with_precedence(node.left, node.operator)
            right_str = self._expression_to_string_with_precedence(node.right, node.operator)
            op_str = self._operator_to_string(node.operator)
            # Only add parentheses for complex expressions that actually need them
            # Simple comparisons like "A = 1" don't need parentheses
            # Also respect the add_outer_parens parameter for top-level expressions
            if add_outer_parens and self._needs_parentheses(node):
                return f"({left_str} {op_str} {right_str})"
            else:
                return f"{left_str} {op_str} {right_str}"

        elif isinstance(node, UnaryOpNode):
            operand_str = self._expression_to_string(node.operand)
            if node.operator == Operator.NOT:
                return f"NOT {operand_str}"
            elif node.operator == Operator.SUBTRACT:
                return f"-{operand_str}"
            else:
                return f"+{operand_str}"

        elif isinstance(node, FunctionCallNode):
            func_str = node.function_name
            if node.arguments:
                args = [self._expression_to_string(arg) for arg in node.arguments]
                func_str += f"({','.join(args)})"
            elif node.function_name.upper() != 'INKEY$':
                # Most functions need parentheses even with no args
                func_str += "()"
            return func_str

        elif isinstance(node, ArrayAccessNode):
            indices = [self._expression_to_string(idx) for idx in node.indices]
            return f"{node.array_name}({','.join(indices)})"

        elif isinstance(node, AssignmentNode):
            # For assignments within expressions (shouldn't normally happen)
            target_str = self._expression_to_string(node.target)
            value_str = self._expression_to_string(node.value)
            return f"{target_str} = {value_str}"

        else:
            # For unknown nodes, return empty string
            return ""

    def _expression_to_string_with_precedence(self, node, parent_op):
        """Convert expression to string, adding parentheses based on operator precedence"""
        if not hasattr(node, 'operator'):
            # Not a binary operation, just convert normally
            return self._expression_to_string(node, add_outer_parens=True)

        # Define operator precedence (higher number = higher precedence)
        precedence = {
            'OR': 1,
            'AND': 2,
            'EQUAL': 3, 'NOT_EQUAL': 3, 'LESS_THAN': 3, 'GREATER_THAN': 3,
            'LESS_EQUAL': 3, 'GREATER_EQUAL': 3,
            'ADD': 4, 'SUBTRACT': 4,
            'MULTIPLY': 5, 'DIVIDE': 5, 'MOD': 5,
            'POWER': 6
        }

        parent_prec = precedence.get(parent_op.name, 0)
        node_prec = precedence.get(node.operator.name, 0)

        # Need parentheses if child has lower precedence than parent
        # or equal precedence and is right-associative
        needs_parens = node_prec < parent_prec

        if needs_parens:
            return f"({self._expression_to_string(node, add_outer_parens=False)})"
        else:
            return self._expression_to_string(node, add_outer_parens=False)

    def _needs_parentheses(self, node) -> bool:
        """Determine if a binary operation needs parentheses for clarity"""
        # For now, always add parentheses around any nested binary operations
        # This is conservative but ensures correct precedence
        return (hasattr(node, 'left') and hasattr(node.left, 'operator') or
                hasattr(node, 'right') and hasattr(node.right, 'operator'))

    def _operator_to_string(self, operator: Operator) -> str:
        """Convert an Operator enum to its string representation"""
        operator_map = {
            Operator.ADD: "+",
            Operator.SUBTRACT: "-",
            Operator.MULTIPLY: "*",
            Operator.DIVIDE: "/",
            Operator.POWER: "^",
            Operator.MOD: "MOD",
            Operator.EQUAL: "=",
            Operator.NOT_EQUAL: "<>",
            Operator.LESS_THAN: "<",
            Operator.GREATER_THAN: ">",
            Operator.LESS_EQUAL: "<=",
            Operator.GREATER_EQUAL: ">=",
            Operator.AND: "AND",
            Operator.OR: "OR",
            Operator.NOT: "NOT",
            Operator.CONCATENATE: "+"
        }
        return operator_map.get(operator, str(operator.value))


def parse_and_convert_single_line(statement: str, parser) -> Optional[List[str]]:
    """
    Parse a single-line control structure and convert it to multi-line format.

    Args:
        statement: The single-line BASIC statement
        parser: An instance of ASTParser

    Returns:
        List of multi-line statements if conversion successful, None otherwise
    """
    # Detect control structure keywords
    statement_upper = statement.upper().strip()

    # Check for control structures that can be single-line
    control_keywords = ['IF ', 'FOR ', 'WHILE ', 'DO:', 'DO ']

    # Check if statement starts with a control keyword
    starts_with_control = any(statement_upper.startswith(kw) for kw in control_keywords)

    # Check if statement contains colons (multi-statement indicator)
    has_colons = ':' in statement

    if not starts_with_control:
        # Not a control structure at all
        return None

    # For IF statements, we should process them even without colons
    # since simple IF THEN GOTO is a valid single-line structure
    is_if_statement = statement_upper.startswith('IF ')

    if not has_colons and not is_if_statement:
        # Other control structures require colons to be considered single-line
        return None

    converter = ASTStatementConverter()

    # Parse the complete statement and convert to multi-line format
    # Returns None on failure, letting core.py fall back to normal processing
    if statement_upper.startswith('IF '):
        return _parse_ast_if_statement(statement, parser, converter)
    elif statement_upper.startswith('FOR '):
        return _parse_ast_for_statement(statement, parser, converter)
    elif statement_upper.startswith('WHILE '):
        return _parse_ast_while_statement(statement, parser, converter)
    elif statement_upper.startswith('DO:') or statement_upper.startswith('DO '):
        return _parse_ast_do_statement(statement, parser, converter)

    return None


def _parse_ast_if_statement(statement: str, parser, converter) -> Optional[List[str]]:
    """Parse and convert single-line IF statement using AST parser"""
    try:
        # For complex single-line IF statements, we need to parse them specially
        # Example: IF A=1 THEN FOR I=1 TO 3: PRINT I: NEXT I: ELSE PRINT "NO"

        # Split into IF condition THEN body parts
        statement_upper = statement.upper()
        then_pos = statement_upper.find(' THEN ')
        if then_pos < 0:
            return None

        condition_part = statement[3:then_pos].strip()  # Skip 'IF '
        body_part = statement[then_pos + 6:].strip()    # Skip ' THEN '

        # Parse the condition using AST parser
        condition_ast = parser.parse_expression(condition_part)

        # Parse the body - may contain multiple statements and ELSE
        body_statements = []
        else_statements = []

        # Split by ELSE first to separate THEN and ELSE parts.
        # Must be quote-aware — PRINT " ELSE " contains ELSE inside a string.
        else_pos = _find_else_outside_quotes(body_part)
        if else_pos >= 0:
            then_body = body_part[:else_pos].strip()
            else_body = body_part[else_pos + 6:].strip()  # Skip ' ELSE '
        else:
            then_body = body_part
            else_body = None

        # Parse THEN body: try whole-body parse first (needed for FOR loops),
        # fall back to colon-splitting if parse is incomplete
        if then_body:
            body_statements = _parse_if_body(then_body, parser)

        # Parse ELSE body the same way
        if else_body:
            else_statements = _parse_if_body(else_body, parser)

        # Create IF statement AST node
        then_branch = _make_body_node(body_statements)
        else_branch = _make_body_node(else_statements)

        if_node = IfStatementNode(condition_ast, then_branch, else_branch)
        return converter.convert(if_node)

    except (ValueError, IndexError, KeyError, AttributeError):
        # Parsing/conversion error — return None to let core.py handle normally
        return None


def _parse_ast_for_statement(statement: str, parser, converter) -> Optional[List[str]]:
    """Parse and convert single-line FOR statement using AST parser"""
    try:
        # For complex single-line FOR statements, parse components separately
        # Example: FOR I=1 TO 10: PRINT I: IF I=5 THEN PRINT "FIVE": NEXT I

        # Find the colon that separates FOR header from body
        colon_pos = statement.find(':')
        if colon_pos < 0:
            return None

        for_header = statement[:colon_pos].strip()
        body_part = statement[colon_pos + 1:].strip()

        # Parse the FOR header using regex to extract components
        match = re.match(r'FOR\s+(\w+)\s*=\s*(.+?)\s+TO\s+(.+?)(?:\s+STEP\s+(.+?))?$', for_header, re.IGNORECASE)
        if not match:
            return None

        var_name = match.group(1)
        start_expr = match.group(2).strip()
        end_expr = match.group(3).strip()
        step_expr = match.group(4).strip() if match.group(4) else "1"

        # Parse expressions using AST parser
        variable_node = VariableNode(var_name)
        start_node = parser.parse_expression(start_expr)
        end_node = parser.parse_expression(end_expr)
        step_node = parser.parse_expression(step_expr) if step_expr != "1" else None

        # Parse body statements (excluding any NEXT statement)
        body_parts = BasicParser.split_on_delimiter_paren_aware(body_part)
        body_statements = []

        for part in body_parts:
            part_stripped = part.strip()
            # Skip NEXT statements as they'll be added automatically
            if not part_stripped.upper().startswith('NEXT'):
                body_statements.append(_parse_body_statement(part_stripped, parser))

        # Create FOR statement AST node
        body_node = _make_body_node(body_statements)
        for_node = ForStatementNode(variable_node, start_node, end_node, step_node, body_node)
        return converter.convert(for_node)

    except (ValueError, IndexError, KeyError, AttributeError):
        # Parsing/conversion error — return None to let core.py handle normally
        return None


def _parse_ast_while_statement(statement: str, parser, converter) -> Optional[List[str]]:
    """Parse and convert single-line WHILE statement using AST parser"""
    try:
        # For complex single-line WHILE statements, parse components separately
        # Example: WHILE X<10: PRINT X: X=X+1: WEND

        # Find the colon that separates WHILE header from body
        colon_pos = statement.find(':')
        if colon_pos < 0:
            return None

        while_header = statement[:colon_pos].strip()
        body_part = statement[colon_pos + 1:].strip()

        # Extract condition from WHILE header
        condition_part = while_header[6:].strip()  # Skip 'WHILE '

        # Parse the condition using AST parser
        condition_node = parser.parse_expression(condition_part)

        # Parse body statements (excluding any WEND statement)
        body_parts = BasicParser.split_on_delimiter_paren_aware(body_part)
        body_statements = []

        for part in body_parts:
            part_stripped = part.strip()
            # Skip WEND statements as they'll be added automatically
            if part_stripped.upper() != 'WEND':
                body_statements.append(_parse_body_statement(part_stripped, parser))

        # Create WHILE statement AST node
        body_node = _make_body_node(body_statements)
        while_node = WhileStatementNode(condition_node, body_node)
        return converter.convert(while_node)

    except (ValueError, IndexError, KeyError, AttributeError):
        # Parsing/conversion error — return None to let core.py handle normally
        return None


def _parse_ast_do_statement(statement: str, parser, converter) -> Optional[List[str]]:
    """Parse and convert single-line DO statement using AST parser"""
    try:
        # For complex single-line DO statements, parse components separately
        # Examples:
        # DO WHILE X>0: PRINT X: X=X-1: LOOP
        # DO: PRINT "HELLO": LOOP WHILE Y<5

        statement_upper = statement.upper()

        # Find the colon that separates DO header from body
        colon_pos = statement.find(':')
        if colon_pos < 0:
            return None

        do_header = statement[:colon_pos].strip()
        body_part = statement[colon_pos + 1:].strip()

        # Parse DO header to determine condition position and type
        condition_node = None
        condition_type = 'WHILE'
        condition_position = 'BOTTOM'

        if do_header.upper().startswith('DO WHILE '):
            condition_part = do_header[9:].strip()  # Skip 'DO WHILE '
            condition_node = parser.parse_expression(condition_part)
            condition_position = 'TOP'
        elif do_header.upper().startswith('DO UNTIL '):
            condition_part = do_header[9:].strip()  # Skip 'DO UNTIL '
            condition_node = parser.parse_expression(condition_part)
            condition_type = 'UNTIL'
            condition_position = 'TOP'

        # Parse body statements and look for LOOP statement
        body_parts = BasicParser.split_on_delimiter_paren_aware(body_part)
        body_statements = []

        for part in body_parts:
            part_stripped = part.strip()
            part_upper = part_stripped.upper()

            # Check for LOOP with condition
            if part_upper.startswith('LOOP WHILE '):
                condition_part = part_stripped[11:].strip()  # Skip 'LOOP WHILE '
                condition_node = parser.parse_expression(condition_part)
                condition_type = 'WHILE'
                condition_position = 'BOTTOM'
            elif part_upper.startswith('LOOP UNTIL '):
                condition_part = part_stripped[11:].strip()  # Skip 'LOOP UNTIL '
                condition_node = parser.parse_expression(condition_part)
                condition_type = 'UNTIL'
                condition_position = 'BOTTOM'
            elif part_upper == 'LOOP':
                # Plain LOOP statement - condition stays as set from DO header
                pass
            else:
                # Regular body statement
                body_statements.append(_parse_body_statement(part_stripped, parser))

        # Create DO/LOOP statement AST node
        body_node = _make_body_node(body_statements)
        do_node = DoLoopStatementNode(body_node, condition_node, condition_type, condition_position)
        return converter.convert(do_node)

    except (ValueError, IndexError, KeyError, AttributeError):
        # Parsing/conversion error — return None to let core.py handle normally
        return None


def _find_else_outside_quotes(text: str) -> int:
    """Find position of ' ELSE ' in text, ignoring occurrences inside quoted strings.

    Returns the index of the space before ELSE, or -1 if not found.
    """
    upper = text.upper()
    in_quotes = False
    # Search for ' ELSE ' — need at least 6 chars remaining
    for i, char in enumerate(text):
        if char == '"':
            in_quotes = not in_quotes
        elif not in_quotes and char == ' ' and upper[i:i + 6] == ' ELSE ':
            return i
    return -1


def _has_file_io_command(text: str) -> bool:
    """Check if text contains file I/O commands that the AST parser can't handle."""
    upper = text.upper()
    return ('PRINT#' in upper or 'PRINT #' in upper or
            'INPUT#' in upper or 'INPUT #' in upper or
            'LINE INPUT' in upper)


def _make_body_node(statements: list) -> Optional[ASTNode]:
    """Create a body node from a list of AST statements."""
    if not statements:
        return None
    if len(statements) == 1:
        return statements[0]
    return BlockNode(statements)


def _parse_if_body(body: str, parser) -> list:
    """Parse an IF/THEN or ELSE body into a list of AST nodes.

    Tries parsing the whole body at once first (needed for FOR loops where
    the FOR, body statements, and NEXT must be parsed together). If the
    whole-body parse is incomplete (e.g., registry commands like SOUND whose
    arguments get silently dropped), falls back to splitting on colons and
    parsing each part individually.
    """
    # Control structure types that intentionally leave closing keywords
    # (NEXT, WEND, LOOP) unconsumed — the converter adds them
    _CONTROL_STRUCTURES = (
        ForStatementNode, WhileStatementNode, DoLoopStatementNode,
    )

    # Skip whole-body parse if body contains file I/O commands — the AST
    # parser's PRINT handler would silently drop the '#' from PRINT#
    if not _has_file_io_command(body):
        try:
            result = parser.parse_statement(body)
            if parser.current >= len(parser.tokens):
                # Parser consumed everything — use this result
                return [result]
            # Partial consumption is OK for control structures (FOR leaves NEXT
            # unconsumed, WHILE leaves WEND, etc.) — the converter handles it
            if isinstance(result, _CONTROL_STRUCTURES):
                return [result]
        except (ValueError, IndexError, KeyError, AttributeError):
            pass

    # Whole-body parse failed, incomplete, or contains file I/O — split on colons
    parts = BasicParser.split_on_delimiter_paren_aware(body)
    statements = []
    for part in parts:
        part_stripped = part.strip()
        if part_stripped:
            node = _parse_body_statement(part_stripped, parser)
            # In IF/THEN bodies, a LiteralNode that isn't a registry command is
            # an implicit GOTO target (e.g., IF A=5 THEN A*B means GOTO A*B).
            # Try parsing as expression and wrap in GotoStatementNode.
            if isinstance(node, LiteralNode) and node.value == part_stripped:
                try:
                    expr = parser.parse_expression(part_stripped)
                    # Only use if the parser consumed all tokens (otherwise
                    # it partially parsed e.g. "SOUND" and dropped args)
                    if parser.current >= len(parser.tokens):
                        node = GotoStatementNode(expr, location=expr.location)
                except (ValueError, IndexError, KeyError, AttributeError):
                    pass
            statements.append(node)
    return statements


def _parse_body_statement(statement: str, parser) -> ASTNode:
    """Parse a single body statement and return appropriate AST node.

    Tries AST parsing first, but verifies the parser consumed ALL tokens.
    If the parse was incomplete (e.g., SOUND parsed as a variable, dropping
    its arguments), falls back to a LiteralNode that preserves the original
    statement text for the command registry to handle at runtime.
    """
    if not statement.strip():
        return LiteralNode("")

    # File I/O commands must bypass AST parsing — PRINT# would be mis-parsed
    # as PRINT (dropping the #), and INPUT#/LINE INPUT need process_statement()
    # intercepts that the AST parser doesn't have
    stmt_upper = statement.upper().lstrip()
    if (stmt_upper.startswith('PRINT#') or stmt_upper.startswith('PRINT #') or
            stmt_upper.startswith('INPUT#') or stmt_upper.startswith('INPUT #') or
            stmt_upper.startswith('LINE INPUT')):
        return LiteralNode(statement)

    try:
        result = parser.parse_statement(statement)
        # Verify the parser consumed all tokens — a partial parse means
        # the parser didn't understand the full statement (e.g., it parsed
        # "SOUND" as a variable name and dropped "F1+RF,8")
        if parser.current < len(parser.tokens):
            return LiteralNode(statement)
        return result
    except (ValueError, IndexError, KeyError, AttributeError):
        return LiteralNode(statement)


