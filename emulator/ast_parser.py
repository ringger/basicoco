"""
AST Parser for TRS-80 Color Computer BASIC Emulator

This module provides the parser that generates Abstract Syntax Trees for BASIC
expressions and statements. Node definitions are in ast_nodes.py; the evaluator
is in ast_evaluator.py.
"""

from typing import Any, List, Optional, Dict

from .ast_nodes import (
    ASTNode, SourceLocation, NodeType, Operator,
    LiteralNode, VariableNode, BinaryOpNode, UnaryOpNode,
    FunctionCallNode, ArrayAccessNode, AssignmentNode,
    IfStatementNode, ForStatementNode, WhileStatementNode,
    DoLoopStatementNode, ExitForStatementNode, EndStatementNode,
    GotoStatementNode, PrintStatementNode, GosubStatementNode,
    ReturnStatementNode, InputStatementNode,
    OnBranchStatementNode, OnErrorGotoNode,
    ProgramNode, BlockNode
)
from .error_context import ErrorContextManager


class RegistryCommandError(ValueError):
    """Raised when the parser encounters a registry command it can't handle."""
    pass


class ASTParser:
    """
    Advanced parser that generates Abstract Syntax Trees for BASIC code.

    This parser provides better error reporting, supports complex nested expressions,
    and lays the foundation for advanced language features.
    """

    def __init__(self, known_functions=None, registry_commands=None):
        self.tokens = []
        self.current = 0
        self.error_context = ErrorContextManager()
        self.current_line = 1
        self.current_column = 1
        self.known_functions = known_functions or set()
        self.registry_commands = registry_commands or set()

    def parse_program(self, program_lines: Dict[int, str]) -> ProgramNode:
        """Parse a complete BASIC program into a PROGRAM node"""
        statements = []

        # Sort lines by line number
        for line_num in sorted(program_lines.keys()):
            code = program_lines[line_num]
            if code.strip():  # Skip empty lines
                try:
                    # Parse each line as a statement
                    statement = self.parse_statement(code)
                    if statement:
                        statements.append(statement)
                except (ValueError, IndexError, KeyError, AttributeError):
                    # If parsing fails, create a literal node for the raw line
                    statements.append(LiteralNode(code))

        return ProgramNode(statements)

    def parse_expression(self, expr_str: str, line: int = 1) -> ASTNode:
        """
        Parse a BASIC expression into an AST.

        Args:
            expr_str: The expression string to parse
            line: Source line number for error reporting

        Returns:
            AST node representing the expression
        """
        self.current_line = line
        self.error_context.set_context(line, expr_str)
        self.tokens = self._tokenize(expr_str)
        self.current = 0

        if not self.tokens:
            error = self.error_context.syntax_error(
                "Empty expression",
                line,
                suggestions=[
                    "Provide a valid expression",
                    "Example: 2 + 3 or \"HELLO\""
                ]
            )
            raise ValueError(error.format_message())

        return self._parse_or_expression()

    def parse_statement(self, stmt_str: str, line: int = 1) -> ASTNode:
        """
        Parse a BASIC statement into an AST.

        Args:
            stmt_str: The statement string to parse
            line: Source line number for error reporting

        Returns:
            AST node representing the statement
        """
        self.current_line = line
        self.error_context.set_context(line, stmt_str)
        self.tokens = self._tokenize(stmt_str)
        self.current = 0

        if not self.tokens:
            error = self.error_context.syntax_error(
                "Empty statement",
                line,
                suggestions=[
                    "Provide a valid BASIC statement",
                    "Example: LET A = 5 or PRINT \"HELLO\""
                ]
            )
            raise ValueError(error.format_message())

        return self._parse_statement_sequence()

    def _parse_statement_sequence(self) -> ASTNode:
        """
        Parse a sequence of statements separated by colons.
        Returns a single statement or a BlockNode for multiple statements.
        """
        statements = []

        while self.current < len(self.tokens):
            # Parse a single statement
            stmt = self._parse_statement()
            statements.append(stmt)

            # Check for colon separator
            if (self.current < len(self.tokens) and
                self._match('PUNCTUATION') and
                self._current_token().get('value') == ':'):
                self._advance()  # consume ':'
            else:
                # No more colons, we're done
                break

        # Return single statement or block
        if len(statements) == 1:
            return statements[0]
        else:
            return BlockNode(
                statements=statements,
                location=statements[0].location if statements else None
            )

    def _tokenize(self, text: str) -> List[Dict[str, Any]]:
        """
        Tokenize BASIC code into a list of tokens.

        Returns:
            List of token dictionaries with 'type', 'value', 'line', 'column'
        """
        tokens = []
        i = 0
        line = self.current_line
        column = 1

        while i < len(text):
            char = text[i]

            # Skip whitespace
            if char.isspace():
                if char == '\n':
                    line += 1
                    column = 1
                else:
                    column += 1
                i += 1
                continue

            # String literals
            if char == '"':
                start_col = column
                i += 1
                column += 1
                value = ''
                while i < len(text) and text[i] != '"':
                    value += text[i]
                    i += 1
                    column += 1
                if i < len(text):
                    i += 1  # Skip closing quote
                    column += 1
                    tokens.append({
                        'type': 'STRING',
                        'value': value,
                        'line': line,
                        'column': start_col,
                        'length': column - start_col
                    })
                else:
                    # Unclosed string error
                    error = self.error_context.syntax_error(
                        f"Unclosed string literal starting at column {start_col}",
                        line,
                        suggestions=[
                            "Add closing double quote to complete the string",
                            "Example: PRINT \"HELLO WORLD\""
                        ]
                    )
                    raise ValueError(error.format_message())
                continue

            # Numbers
            if char.isdigit() or char == '.':
                start_col = column
                value = ''
                while i < len(text) and (text[i].isdigit() or text[i] == '.'):
                    value += text[i]
                    i += 1
                    column += 1

                # Handle scientific notation
                if i < len(text) and text[i].upper() == 'E':
                    value += text[i]
                    i += 1
                    column += 1
                    if i < len(text) and text[i] in '+-':
                        value += text[i]
                        i += 1
                        column += 1
                    while i < len(text) and text[i].isdigit():
                        value += text[i]
                        i += 1
                        column += 1

                tokens.append({
                    'type': 'NUMBER',
                    'value': float(value) if '.' in value or 'E' in value.upper() else int(value),
                    'line': line,
                    'column': start_col,
                    'length': column - start_col
                })
                continue

            # Identifiers and keywords
            if char.isalpha() or char == '_':
                start_col = column
                value = ''
                while i < len(text) and (text[i].isalnum() or text[i] in '_$'):
                    value += text[i]
                    i += 1
                    column += 1

                # Check if it's a keyword or identifier
                token_type = 'KEYWORD' if value.upper() in self._get_keywords() else 'IDENTIFIER'
                tokens.append({
                    'type': token_type,
                    'value': value.upper(),
                    'line': line,
                    'column': start_col,
                    'length': column - start_col
                })
                continue

            # Two-character operators
            if i + 1 < len(text):
                two_char = text[i:i+2]
                if two_char in ['<=', '>=', '<>', '**']:
                    tokens.append({
                        'type': 'OPERATOR',
                        'value': two_char,
                        'line': line,
                        'column': column,
                        'length': 2
                    })
                    i += 2
                    column += 2
                    continue

            # Single-character operators and punctuation
            if char in '+-*/^=<>()[],:;':
                tokens.append({
                    'type': 'OPERATOR' if char in '+-*/^=<>' else 'PUNCTUATION',
                    'value': char,
                    'line': line,
                    'column': column,
                    'length': 1
                })
                i += 1
                column += 1
                continue

            # Unknown character — silently skipped. This includes '#' which is
            # used by file I/O commands (PRINT#, INPUT#). Those commands are
            # intercepted before reaching the AST parser (see process_statement()
            # in core.py and _parse_body_statement() in ast_converter.py).
            i += 1
            column += 1

        return tokens

    def _get_keywords(self) -> set:
        """Return set of BASIC keywords"""
        return {
            'AND', 'OR', 'NOT', 'MOD',
            'IF', 'THEN', 'ELSE', 'ENDIF',
            'FOR', 'TO', 'STEP', 'NEXT', 'EXIT',
            'WHILE', 'WEND', 'DO', 'LOOP', 'UNTIL',
            'GOTO', 'GOSUB', 'RETURN', 'ON',
            'PRINT', 'INPUT', 'LET',
            'DIM', 'DATA', 'READ', 'RESTORE',
            'END', 'STOP', 'CONT', 'NEW', 'RUN', 'LIST'
        }

    def _current_token(self) -> Optional[Dict[str, Any]]:
        """Get the current token"""
        if self.current < len(self.tokens):
            return self.tokens[self.current]
        return None

    def _peek_token(self, offset: int = 1) -> Optional[Dict[str, Any]]:
        """Peek at a token ahead of current position"""
        pos = self.current + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return None

    def _advance(self) -> Optional[Dict[str, Any]]:
        """Consume and return the current token"""
        token = self._current_token()
        if token:
            self.current += 1
        return token

    def _match(self, *token_types: str) -> bool:
        """Check if current token matches any of the given types"""
        token = self._current_token()
        return token is not None and token['type'] in token_types

    def _match_value(self, value: str) -> bool:
        """Check if current token has the given value"""
        token = self._current_token()
        return token is not None and token['value'] == value

    def _consume(self, token_type: str, message: str = "") -> Dict[str, Any]:
        """Consume a token of the expected type or raise an error"""
        token = self._current_token()
        if not token:
            error = self.error_context.syntax_error(
                f"Unexpected end of input" + (f": {message}" if message else ""),
                self.current_line,
                suggestions=[
                    f"Expected {token_type}",
                    "Check for missing parentheses, quotes, or operators"
                ]
            )
            raise ValueError(error.format_message())
        if token['type'] != token_type:
            error = self.error_context.syntax_error(
                f"Expected {token_type}, got {token['type']} ('{token['value']}')",
                self.current_line,
                suggestions=[
                    f"Use a {token_type} token here",
                    "Check syntax for this BASIC construct"
                ]
            )
            raise ValueError(error.format_message())
        return self._advance()

    def _make_location(self, token: Dict[str, Any]) -> SourceLocation:
        """Create a source location from a token"""
        return SourceLocation(
            line=token['line'],
            column=token['column'],
            length=token.get('length', 1)
        )

    # Expression parsing with proper precedence
    def _parse_or_expression(self) -> ASTNode:
        """Parse OR expressions (lowest precedence)"""
        left = self._parse_and_expression()

        while self._match_value('OR'):
            op_token = self._advance()
            right = self._parse_and_expression()
            left = BinaryOpNode(
                operator=Operator.OR,
                left=left,
                right=right,
                location=self._make_location(op_token)
            )

        return left

    def _parse_and_expression(self) -> ASTNode:
        """Parse AND expressions"""
        left = self._parse_equality_expression()

        while self._match_value('AND'):
            op_token = self._advance()
            right = self._parse_equality_expression()
            left = BinaryOpNode(
                operator=Operator.AND,
                left=left,
                right=right,
                location=self._make_location(op_token)
            )

        return left

    def _parse_equality_expression(self) -> ASTNode:
        """Parse equality/comparison expressions"""
        left = self._parse_relational_expression()

        while self._match('OPERATOR') and self._current_token()['value'] in ['=', '<>']:
            op_token = self._advance()
            right = self._parse_relational_expression()
            op = Operator.EQUAL if op_token['value'] == '=' else Operator.NOT_EQUAL
            left = BinaryOpNode(
                operator=op,
                left=left,
                right=right,
                location=self._make_location(op_token)
            )

        return left

    def _parse_relational_expression(self) -> ASTNode:
        """Parse relational expressions (<, >, <=, >=)"""
        left = self._parse_additive_expression()

        while self._match('OPERATOR') and self._current_token()['value'] in ['<', '>', '<=', '>=']:
            op_token = self._advance()
            right = self._parse_additive_expression()

            op_map = {
                '<': Operator.LESS_THAN,
                '>': Operator.GREATER_THAN,
                '<=': Operator.LESS_EQUAL,
                '>=': Operator.GREATER_EQUAL
            }

            left = BinaryOpNode(
                operator=op_map[op_token['value']],
                left=left,
                right=right,
                location=self._make_location(op_token)
            )

        return left

    def _parse_additive_expression(self) -> ASTNode:
        """Parse addition and subtraction"""
        left = self._parse_multiplicative_expression()

        while self._match('OPERATOR') and self._current_token()['value'] in ['+', '-']:
            op_token = self._advance()
            right = self._parse_multiplicative_expression()
            op = Operator.ADD if op_token['value'] == '+' else Operator.SUBTRACT
            left = BinaryOpNode(
                operator=op,
                left=left,
                right=right,
                location=self._make_location(op_token)
            )

        return left

    def _parse_multiplicative_expression(self) -> ASTNode:
        """Parse multiplication, division, and modulo"""
        left = self._parse_power_expression()

        while (self._match('OPERATOR') and self._current_token()['value'] in ['*', '/']) or \
              (self._match('KEYWORD') and self._current_token()['value'].upper() == 'MOD'):
            op_token = self._advance()
            right = self._parse_power_expression()

            if op_token['value'] == '*':
                op = Operator.MULTIPLY
            elif op_token['value'] == '/':
                op = Operator.DIVIDE
            else:  # MOD
                op = Operator.MOD

            left = BinaryOpNode(
                operator=op,
                left=left,
                right=right,
                location=self._make_location(op_token)
            )

        return left

    def _parse_power_expression(self) -> ASTNode:
        """Parse exponentiation (right-associative)"""
        left = self._parse_unary_expression()

        if self._match('OPERATOR') and self._current_token()['value'] in ['^', '**']:
            op_token = self._advance()
            right = self._parse_power_expression()  # Right associative
            return BinaryOpNode(
                operator=Operator.POWER,
                left=left,
                right=right,
                location=self._make_location(op_token)
            )

        return left

    def _parse_unary_expression(self) -> ASTNode:
        """Parse unary expressions"""
        if self._match('OPERATOR') and self._current_token()['value'] in ['+', '-']:
            op_token = self._advance()
            operand = self._parse_unary_expression()
            op = Operator.ADD if op_token['value'] == '+' else Operator.SUBTRACT
            return UnaryOpNode(
                operator=op,
                operand=operand,
                location=self._make_location(op_token)
            )

        if self._match_value('NOT'):
            op_token = self._advance()
            operand = self._parse_unary_expression()
            return UnaryOpNode(
                operator=Operator.NOT,
                operand=operand,
                location=self._make_location(op_token)
            )

        return self._parse_primary_expression()

    def _parse_primary_expression(self) -> ASTNode:
        """Parse primary expressions (literals, variables, function calls, parentheses)"""
        token = self._current_token()

        if not token:
            error = self.error_context.syntax_error(
                "Unexpected end of expression",
                self.current_line,
                suggestions=[
                    "Add a value, variable, or function call",
                    "Check for balanced parentheses",
                    "Example: 42 or \"HELLO\" or ABS(-5)"
                ]
            )
            raise ValueError(error.format_message())

        # Parentheses
        if self._match('PUNCTUATION') and token['value'] == '(':
            self._advance()  # consume '('
            expr = self._parse_or_expression()
            self._consume('PUNCTUATION', "Expected ')' after expression")
            return expr

        # String literal
        if self._match('STRING'):
            token = self._advance()
            return LiteralNode(
                value=token['value'],
                location=self._make_location(token)
            )

        # Number literal
        if self._match('NUMBER'):
            token = self._advance()
            return LiteralNode(
                value=token['value'],
                location=self._make_location(token)
            )

        # Identifier (variable, function call, or array access)
        if self._match('IDENTIFIER'):
            name_token = self._advance()
            name = name_token['value']

            # Function call (also handles array access — distinguished at evaluation
            # time in visit_function_call)
            if self._match('PUNCTUATION') and self._current_token()['value'] == '(':
                self._advance()  # consume '('
                args = []

                if not (self._match('PUNCTUATION') and self._current_token()['value'] == ')'):
                    args.append(self._parse_or_expression())
                    while self._match('PUNCTUATION') and self._current_token()['value'] == ',':
                        self._advance()  # consume ','
                        args.append(self._parse_or_expression())

                self._consume('PUNCTUATION', "Expected ')' after function arguments")

                return FunctionCallNode(
                    function_name=name,
                    arguments=args,
                    location=self._make_location(name_token)
                )

            # Known function without parentheses (e.g., INKEY$, MEM)
            elif name.upper() in self.known_functions:
                return FunctionCallNode(
                    function_name=name,
                    arguments=[],
                    location=self._make_location(name_token)
                )

            # Simple variable
            else:
                return VariableNode(
                    name=name,
                    location=self._make_location(name_token)
                )

        error = self.error_context.syntax_error(
            f"Unexpected token: {token['value']} ({token['type']})",
            self.current_line,
            suggestions=[
                "Check if this token belongs here",
                "Valid primary expressions: numbers, strings, variables, function calls",
                "Use parentheses for grouping: (expression)"
            ]
        )
        raise ValueError(error.format_message())

    def _parse_statement(self) -> ASTNode:
        """Parse a BASIC statement"""
        token = self._current_token()

        if not token:
            error = self.error_context.syntax_error(
                "Empty statement",
                self.current_line,
                suggestions=[
                    "Provide a valid BASIC statement",
                    "Examples: LET A = 5, PRINT \"HELLO\", FOR I = 1 TO 10"
                ]
            )
            raise ValueError(error.format_message())

        # Assignment (LET X = 5 or X = 5)
        if (self._match('KEYWORD') and token['value'] == 'LET') or self._is_assignment():
            return self._parse_assignment()

        # IF statement
        if self._match('KEYWORD') and token['value'] == 'IF':
            return self._parse_if_statement()

        # FOR statement
        if self._match('KEYWORD') and token['value'] == 'FOR':
            return self._parse_for_statement()

        # WHILE statement
        if self._match('KEYWORD') and token['value'] == 'WHILE':
            return self._parse_while_statement()

        # DO statement
        if self._match('KEYWORD') and token['value'] == 'DO':
            return self._parse_do_loop_statement()

        # EXIT statement
        if self._match('KEYWORD') and token['value'] == 'EXIT':
            return self._parse_exit_statement()

        # PRINT statement
        if self._match('KEYWORD') and token['value'] == 'PRINT':
            return self._parse_print_statement()

        # END statement
        if self._match('KEYWORD') and token['value'] == 'END':
            return self._parse_end_statement()

        # GOTO statement
        if self._match('KEYWORD') and token['value'] == 'GOTO':
            return self._parse_goto_statement()

        # GOSUB statement
        if self._match('KEYWORD') and token['value'] == 'GOSUB':
            return self._parse_gosub_statement()

        # RETURN statement
        if self._match('KEYWORD') and token['value'] == 'RETURN':
            return self._parse_return_statement()

        # INPUT statement
        if self._match('KEYWORD') and token['value'] == 'INPUT':
            return self._parse_input_statement()

        # ON statement (ON GOTO/GOSUB, ON ERROR GOTO)
        if self._match('KEYWORD') and token['value'] == 'ON':
            return self._parse_on_statement()

        # Bare number = implicit GOTO (e.g., IF A=5 THEN 50)
        if self._match('NUMBER'):
            target = self._parse_or_expression()
            return GotoStatementNode(target, location=target.location)

        # Known registry command — parser can't handle it
        token_value = str(token['value']).upper()
        if token_value in self.registry_commands:
            raise RegistryCommandError(f"Registry command: {token_value}")

        # Reject anything else — bare expressions aren't valid statements
        raise ValueError(f"Unrecognized command: {token_value}")

    def _is_assignment(self) -> bool:
        """Check if the current tokens form an assignment"""
        # Look for pattern: IDENTIFIER [indices] = expression
        if not self._match('IDENTIFIER'):
            return False

        # Reject registry command names as assignment targets
        if self._current_token()['value'].upper() in self.registry_commands:
            return False

        # Look ahead for = sign
        pos = 1
        token = self._peek_token(pos)

        # Skip array indices if present
        if token and token['type'] == 'PUNCTUATION' and token['value'] == '(':
            paren_count = 1
            pos += 1
            while pos < len(self.tokens) and paren_count > 0:
                token = self._peek_token(pos)
                if not token:
                    break
                if token['value'] == '(':
                    paren_count += 1
                elif token['value'] == ')':
                    paren_count -= 1
                pos += 1

            token = self._peek_token(pos)

        return token is not None and token['type'] == 'OPERATOR' and token['value'] == '='

    def _parse_assignment(self) -> AssignmentNode:
        """Parse assignment statement"""
        # Skip LET if present
        if self._match_value('LET'):
            self._advance()

        # Parse target (variable or array element)
        name_token = self._consume('IDENTIFIER', "Expected variable name")
        target_location = self._make_location(name_token)

        if self._match('PUNCTUATION') and self._current_token()['value'] == '(':
            # Array assignment
            self._advance()  # consume '('
            indices = []

            if not (self._match('PUNCTUATION') and self._current_token()['value'] == ')'):
                indices.append(self._parse_or_expression())
                while self._match('PUNCTUATION') and self._current_token()['value'] == ',':
                    self._advance()  # consume ','
                    indices.append(self._parse_or_expression())

            self._consume('PUNCTUATION', "Expected ')' after array indices")

            target = ArrayAccessNode(
                array_name=name_token['value'],
                indices=indices,
                location=target_location
            )
        else:
            # Simple variable assignment
            target = VariableNode(
                name=name_token['value'],
                location=target_location
            )

        self._consume('OPERATOR', "Expected '=' in assignment")
        value = self._parse_or_expression()

        return AssignmentNode(
            target=target,
            value=value,
            location=target_location
        )

    def _parse_colon_separated_statements(self) -> ASTNode:
        """Parse a sequence of colon-separated statements"""
        statements = []

        # Parse first statement
        statements.append(self._parse_statement())

        # Parse additional statements after colons
        while self._match('PUNCTUATION') and self._current_token()['value'] == ':':
            self._advance()  # consume ':'
            if self._current_token() and not self._match_value('ELSE'):  # Don't consume ELSE
                statements.append(self._parse_statement())

        # If only one statement, return it directly
        if len(statements) == 1:
            return statements[0]

        # Multiple statements - return as a block
        return BlockNode(statements=statements)

    def _parse_if_statement(self) -> IfStatementNode:
        """Parse IF statement"""
        if_token = self._advance()  # consume 'IF'
        condition = self._parse_or_expression()

        self._consume('KEYWORD', "Expected 'THEN' after IF condition")
        then_branch = self._parse_colon_separated_statements()

        else_branch = None
        if self._match_value('ELSE'):
            self._advance()  # consume 'ELSE'
            else_branch = self._parse_colon_separated_statements()

        return IfStatementNode(
            condition=condition,
            then_branch=then_branch,
            else_branch=else_branch,
            location=self._make_location(if_token)
        )

    def _parse_for_statement(self) -> ForStatementNode:
        """Parse FOR statement"""
        for_token = self._advance()  # consume 'FOR'

        var_token = self._consume('IDENTIFIER', "Expected variable name after FOR")
        variable = VariableNode(
            name=var_token['value'],
            location=self._make_location(var_token)
        )

        self._consume('OPERATOR', "Expected '=' after FOR variable")
        start_value = self._parse_or_expression()

        self._consume('KEYWORD', "Expected 'TO' in FOR statement")
        end_value = self._parse_or_expression()

        step_value = None
        if self._match_value('STEP'):
            self._advance()  # consume 'STEP'
            step_value = self._parse_or_expression()

        # Parse body statements if there are colons (single-line FOR loop)
        body_statements = []

        # Check if there's a colon indicating body statements
        if self._match('PUNCTUATION') and self._current_token().get('value') == ':':
            self._advance()  # consume ':'

            # Parse statements until we hit NEXT or end of tokens
            while self.current < len(self.tokens):
                current_token = self._current_token()

                # Stop if we hit NEXT (end of FOR body)
                if (current_token and current_token.get('type') == 'KEYWORD'
                    and current_token.get('value', '').upper() == 'NEXT'):
                    break

                # Stop if we hit another colon followed by NEXT
                if (current_token and current_token.get('type') == 'PUNCTUATION'
                    and current_token.get('value') == ':'
                    and self.current + 1 < len(self.tokens)):
                    next_token = self.tokens[self.current + 1]
                    if (next_token.get('type') == 'KEYWORD'
                        and next_token.get('value', '').upper() == 'NEXT'):
                        break

                # Parse the statement
                try:
                    stmt = self._parse_statement()
                    body_statements.append(stmt)

                    # Consume optional colon separator
                    if (self._match('PUNCTUATION') and
                        self._current_token().get('value') == ':'):
                        self._advance()
                except (ValueError, IndexError, KeyError, AttributeError):
                    # If we can't parse a statement, break out of body
                    break

        body = BlockNode(statements=body_statements, location=self._make_location(for_token))

        return ForStatementNode(
            variable=variable,
            start_value=start_value,
            end_value=end_value,
            step_value=step_value,
            body=body,
            location=self._make_location(for_token)
        )

    def _parse_while_statement(self) -> WhileStatementNode:
        """Parse WHILE statement"""
        while_token = self._advance()  # consume 'WHILE'
        condition = self._parse_or_expression()

        # For now, body is empty - will be filled by statement grouping
        # In a full implementation, we'd parse until WEND
        body = BlockNode(statements=[], location=self._make_location(while_token))

        return WhileStatementNode(
            condition=condition,
            body=body,
            location=self._make_location(while_token)
        )

    def _parse_do_loop_statement(self) -> DoLoopStatementNode:
        """Parse DO/LOOP statement"""
        do_token = self._advance()  # consume 'DO'

        # Check for DO WHILE or DO UNTIL
        condition = None
        condition_type = 'WHILE'
        condition_position = 'BOTTOM'

        if self._match_value('WHILE'):
            self._advance()  # consume 'WHILE'
            condition = self._parse_or_expression()
            condition_position = 'TOP'
        elif self._match_value('UNTIL'):
            self._advance()  # consume 'UNTIL'
            condition = self._parse_or_expression()
            condition_type = 'UNTIL'
            condition_position = 'TOP'

        # For now, body is empty - will be filled by statement grouping
        # In a full implementation, we'd parse until LOOP
        body = BlockNode(statements=[], location=self._make_location(do_token))

        return DoLoopStatementNode(
            body=body,
            condition=condition,
            condition_type=condition_type,
            condition_position=condition_position,
            location=self._make_location(do_token)
        )

    def _parse_exit_statement(self) -> ExitForStatementNode:
        """Parse EXIT FOR statement"""
        exit_token = self._advance()  # consume 'EXIT'

        # Expect 'FOR' after EXIT
        if not (self._match('KEYWORD') and self._current_token()['value'] == 'FOR'):
            current_token = self._current_token()
            token_info = f"'{current_token['value']}'" if current_token else "end of input"
            error = self.error_context.syntax_error(
                f"Expected 'FOR' after 'EXIT', found {token_info}",
                self.current_line,
                suggestions=[
                    "Use: EXIT FOR",
                    "EXIT statement can only exit FOR loops"
                ]
            )
            raise ValueError(error.format_message())

        self._advance()  # consume 'FOR'

        return ExitForStatementNode(location=self._make_location(exit_token))

    def _parse_end_statement(self) -> EndStatementNode:
        """Parse END statement"""
        end_token = self._advance()  # consume 'END'
        return EndStatementNode(location=self._make_location(end_token))

    def _parse_goto_statement(self) -> GotoStatementNode:
        """Parse GOTO statement"""
        goto_token = self._advance()  # consume 'GOTO'

        # Parse target line number expression
        target_line = self._parse_or_expression()

        return GotoStatementNode(target_line, location=self._make_location(goto_token))

    def _parse_print_statement(self) -> PrintStatementNode:
        """Parse PRINT statement"""
        print_token = self._advance()  # consume 'PRINT'

        expressions = []
        separators = []

        # Handle empty PRINT (but '(' starts an expression, not end-of-statement)
        if not self._current_token() or (
            self._current_token()['type'] == 'KEYWORD'
        ) or (
            self._current_token()['type'] == 'PUNCTUATION'
            and self._current_token()['value'] not in ['(', ';', ',', '-', '+']
        ):
            return PrintStatementNode(
                expressions=expressions,
                separators=[],
                location=self._make_location(print_token)
            )

        # Parse expressions and separators
        expressions.append(self._parse_or_expression())

        while self._match('PUNCTUATION') and self._current_token()['value'] in [';', ',']:
            sep_token = self._advance()
            separators.append(sep_token['value'])

            # Check if there's another expression
            if (self._current_token() and
                self._current_token()['type'] not in ['KEYWORD'] and
                not (self._current_token()['type'] == 'PUNCTUATION' and
                     self._current_token()['value'] in [';', ','])):
                expressions.append(self._parse_or_expression())

        return PrintStatementNode(
            expressions=expressions,
            separators=separators,
            location=self._make_location(print_token)
        )

    def _parse_gosub_statement(self) -> GosubStatementNode:
        """Parse GOSUB statement"""
        gosub_token = self._advance()  # consume 'GOSUB'

        # Parse target line number expression
        target_line = self._parse_or_expression()

        return GosubStatementNode(target_line, location=self._make_location(gosub_token))

    def _parse_return_statement(self) -> ReturnStatementNode:
        """Parse RETURN statement"""
        return_token = self._advance()  # consume 'RETURN'
        return ReturnStatementNode(location=self._make_location(return_token))

    def _parse_input_statement(self) -> InputStatementNode:
        """Parse INPUT statement"""
        input_token = self._advance()  # consume 'INPUT'

        prompt = None
        variables = []

        # Check for optional prompt string
        if self._match('STRING'):
            prompt_token = self._advance()
            prompt = LiteralNode(
                value=prompt_token['value'],
                location=self._make_location(prompt_token)
            )

            # Expect semicolon or comma after prompt
            if self._match('PUNCTUATION') and self._current_token()['value'] in [';', ',']:
                self._advance()  # consume separator
            else:
                error = self.error_context.syntax_error(
                    "Expected ';' or ',' after INPUT prompt",
                    self.current_line,
                    suggestions=[
                        "Use: INPUT \"prompt\"; variable",
                        "Use: INPUT \"prompt\", variable",
                        "Use: INPUT variable (without prompt)"
                    ]
                )
                raise ValueError(error.format_message())

        # Parse variable list
        if not self._match('IDENTIFIER'):
            error = self.error_context.syntax_error(
                "Expected variable name after INPUT",
                self.current_line,
                suggestions=[
                    "Use: INPUT variable_name",
                    "Use: INPUT \"prompt\"; variable_name",
                    "Multiple variables: INPUT A, B, C"
                ]
            )
            raise ValueError(error.format_message())

        # Parse first variable (may be simple variable or array element)
        var_node = self._parse_input_variable()
        variables.append(var_node)

        # Parse additional variables separated by commas
        while self._match('PUNCTUATION') and self._current_token()['value'] == ',':
            self._advance()  # consume ','

            if not self._match('IDENTIFIER'):
                error = self.error_context.syntax_error(
                    "Expected variable name after comma in INPUT statement",
                    self.current_line,
                    suggestions=[
                        "Use: INPUT A, B, C",
                        "Remove trailing comma if no more variables"
                    ]
                )
                raise ValueError(error.format_message())

            var_node = self._parse_input_variable()
            variables.append(var_node)

        return InputStatementNode(
            prompt=prompt,
            variables=variables,
            location=self._make_location(input_token)
        )

    def _parse_input_variable(self):
        """Parse a variable target for INPUT (simple variable or array element)."""
        var_token = self._advance()
        var_location = self._make_location(var_token)

        # Check for array subscript: L$(I)
        if self._match('PUNCTUATION') and self._current_token()['value'] == '(':
            self._advance()  # consume '('
            indices = []
            if not (self._match('PUNCTUATION') and self._current_token()['value'] == ')'):
                indices.append(self._parse_or_expression())
                while self._match('PUNCTUATION') and self._current_token()['value'] == ',':
                    self._advance()  # consume ','
                    indices.append(self._parse_or_expression())
            self._consume('PUNCTUATION', "Expected ')' after array indices")
            return ArrayAccessNode(
                array_name=var_token['value'],
                indices=indices,
                location=var_location
            )

        return VariableNode(name=var_token['value'], location=var_location)

    def _parse_on_statement(self) -> ASTNode:
        """Parse ON ERROR GOTO or ON expr GOTO/GOSUB"""
        on_token = self._advance()  # consume 'ON'

        # ON ERROR GOTO line
        if (self._current_token() and
                self._current_token()['value'].upper() == 'ERROR'):
            self._advance()  # consume 'ERROR'
            if not (self._match('KEYWORD') and
                    self._current_token()['value'] == 'GOTO'):
                error = self.error_context.syntax_error(
                    "Expected ON ERROR GOTO line",
                    self.current_line,
                    suggestions=["Use ON ERROR GOTO 100",
                                 "Use ON ERROR GOTO 0 to disable handler"])
                raise ValueError(error.format_message())
            self._advance()  # consume 'GOTO'
            target_line = self._parse_or_expression()
            return OnErrorGotoNode(target_line,
                                   location=self._make_location(on_token))

        # ON expr GOTO/GOSUB line1,line2,...
        expression = self._parse_or_expression()

        if not self._match('KEYWORD') or self._current_token()['value'] not in ('GOTO', 'GOSUB'):
            error = self.error_context.syntax_error(
                "ON requires GOTO or GOSUB",
                self.current_line,
                suggestions=["Use ON expression GOTO line1,line2,...",
                             "Use ON expression GOSUB line1,line2,..."])
            raise ValueError(error.format_message())

        branch_type = self._advance()['value']  # consume 'GOTO' or 'GOSUB'

        # Parse comma-separated list of target line expressions
        targets = [self._parse_or_expression()]
        while (self._match('PUNCTUATION') and
               self._current_token()['value'] == ','):
            self._advance()  # consume ','
            targets.append(self._parse_or_expression())

        return OnBranchStatementNode(expression, branch_type, targets,
                                     location=self._make_location(on_token))
