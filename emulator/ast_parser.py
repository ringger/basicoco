"""
Advanced AST Parser for TRS-80 Color Computer BASIC Emulator

This module provides Abstract Syntax Tree generation for BASIC expressions and statements,
enabling better error reporting, optimization, and support for advanced language constructs.
"""

from typing import Any, List, Optional, Union, Dict
from dataclasses import dataclass
from enum import Enum
import re
from .error_context import ErrorContextManager


class NodeType(Enum):
    """Types of AST nodes"""
    # Literals
    NUMBER = "number"
    STRING = "string"
    VARIABLE = "variable"
    
    # Expressions
    BINARY_OP = "binary_op"
    UNARY_OP = "unary_op"
    FUNCTION_CALL = "function_call"
    ARRAY_ACCESS = "array_access"
    
    # Statements
    ASSIGNMENT = "assignment"
    IF_STATEMENT = "if_statement"
    FOR_STATEMENT = "for_statement"
    WHILE_STATEMENT = "while_statement"
    GOTO_STATEMENT = "goto_statement"
    GOSUB_STATEMENT = "gosub_statement"
    RETURN_STATEMENT = "return_statement"
    PRINT_STATEMENT = "print_statement"
    INPUT_STATEMENT = "input_statement"
    END_STATEMENT = "end_statement"
    
    # Control Flow
    BLOCK = "block"
    PROGRAM = "program"
    EXIT_FOR_STATEMENT = "exit_for_statement"


class Operator(Enum):
    """Binary and unary operators"""
    # Arithmetic
    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    POWER = "^"
    MOD = "MOD"
    
    # Comparison
    EQUAL = "="
    NOT_EQUAL = "<>"
    LESS_THAN = "<"
    GREATER_THAN = ">"
    LESS_EQUAL = "<="
    GREATER_EQUAL = ">="
    
    # Logical
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    
    # String
    CONCATENATE = "+"


@dataclass
class SourceLocation:
    """Source code location for error reporting"""
    line: int
    column: int
    length: int = 1


@dataclass 
class ASTNode:
    """Base class for all AST nodes"""
    node_type: NodeType
    location: Optional[SourceLocation] = None
    
    def accept(self, visitor):
        """Visitor pattern support"""
        method_name = f"visit_{self.node_type.value}"
        method = getattr(visitor, method_name, None)
        if method:
            return method(self)
        else:
            return visitor.generic_visit(self)


class LiteralNode(ASTNode):
    """Node for literal values (numbers, strings)"""
    def __init__(self, value: Union[int, float, str], location: Optional[SourceLocation] = None):
        if isinstance(value, str):
            node_type = NodeType.STRING
        else:
            node_type = NodeType.NUMBER
        super().__init__(node_type, location)
        self.value = value


class VariableNode(ASTNode):
    """Node for variable references"""
    def __init__(self, name: str, location: Optional[SourceLocation] = None):
        super().__init__(NodeType.VARIABLE, location)
        self.name = name


class BinaryOpNode(ASTNode):
    """Node for binary operations"""
    def __init__(self, operator: Operator, left: ASTNode, right: ASTNode, location: Optional[SourceLocation] = None):
        super().__init__(NodeType.BINARY_OP, location)
        self.operator = operator
        self.left = left
        self.right = right


class UnaryOpNode(ASTNode):
    """Node for unary operations"""
    def __init__(self, operator: Operator, operand: ASTNode, location: Optional[SourceLocation] = None):
        super().__init__(NodeType.UNARY_OP, location)
        self.operator = operator
        self.operand = operand


class FunctionCallNode(ASTNode):
    """Node for function calls"""
    def __init__(self, function_name: str, arguments: List[ASTNode], location: Optional[SourceLocation] = None):
        super().__init__(NodeType.FUNCTION_CALL, location)
        self.function_name = function_name
        self.arguments = arguments


class ArrayAccessNode(ASTNode):
    """Node for array element access"""
    def __init__(self, array_name: str, indices: List[ASTNode], location: Optional[SourceLocation] = None):
        super().__init__(NodeType.ARRAY_ACCESS, location)
        self.array_name = array_name
        self.indices = indices


class AssignmentNode(ASTNode):
    """Node for variable assignments"""
    def __init__(self, target: Union[VariableNode, ArrayAccessNode], value: ASTNode, location: Optional[SourceLocation] = None):
        super().__init__(NodeType.ASSIGNMENT, location)
        self.target = target
        self.value = value


class IfStatementNode(ASTNode):
    """Node for IF statements"""
    def __init__(self, condition: ASTNode, then_branch: ASTNode, else_branch: Optional[ASTNode] = None, location: Optional[SourceLocation] = None):
        super().__init__(NodeType.IF_STATEMENT, location)
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch


class ForStatementNode(ASTNode):
    """Node for FOR loops"""
    def __init__(self, variable: VariableNode, start_value: ASTNode, end_value: ASTNode, step_value: Optional[ASTNode], body: ASTNode, location: Optional[SourceLocation] = None):
        super().__init__(NodeType.FOR_STATEMENT, location)
        self.variable = variable
        self.start_value = start_value
        self.end_value = end_value
        self.step_value = step_value
        self.body = body


class WhileStatementNode(ASTNode):
    """Node for WHILE loops"""
    def __init__(self, condition: ASTNode, body: ASTNode, location: Optional[SourceLocation] = None):
        super().__init__(NodeType.WHILE_STATEMENT, location)
        self.condition = condition
        self.body = body


class DoLoopStatementNode(ASTNode):
    """Node for DO/LOOP constructs"""
    def __init__(self, body: ASTNode, condition: Optional[ASTNode] = None, condition_type: str = 'WHILE', condition_position: str = 'BOTTOM', location: Optional[SourceLocation] = None):
        super().__init__(NodeType.WHILE_STATEMENT, location)  # Reuse WHILE_STATEMENT type for now
        self.body = body
        self.condition = condition
        self.condition_type = condition_type  # 'WHILE' or 'UNTIL' 
        self.condition_position = condition_position  # 'TOP' (DO WHILE) or 'BOTTOM' (LOOP WHILE)


class ExitForStatementNode(ASTNode):
    """Node for EXIT FOR statements"""
    def __init__(self, location: Optional[SourceLocation] = None):
        super().__init__(NodeType.EXIT_FOR_STATEMENT, location)


class EndStatementNode(ASTNode):
    """Node for END statements"""
    def __init__(self, location: Optional[SourceLocation] = None):
        super().__init__(NodeType.END_STATEMENT, location)


class GotoStatementNode(ASTNode):
    """Node for GOTO statements"""
    def __init__(self, target_line: ASTNode, location: Optional[SourceLocation] = None):
        super().__init__(NodeType.GOTO_STATEMENT, location)
        self.target_line = target_line


class PrintStatementNode(ASTNode):
    """Node for PRINT statements"""
    def __init__(self, expressions: List[ASTNode], separators: List[str], location: Optional[SourceLocation] = None):
        super().__init__(NodeType.PRINT_STATEMENT, location)
        self.expressions = expressions
        self.separators = separators


class GosubStatementNode(ASTNode):
    """Node for GOSUB statements"""
    def __init__(self, target_line: ASTNode, location: Optional[SourceLocation] = None):
        super().__init__(NodeType.GOSUB_STATEMENT, location)
        self.target_line = target_line


class ReturnStatementNode(ASTNode):
    """Node for RETURN statements"""
    def __init__(self, location: Optional[SourceLocation] = None):
        super().__init__(NodeType.RETURN_STATEMENT, location)


class InputStatementNode(ASTNode):
    """Node for INPUT statements"""
    def __init__(self, prompt: Optional[ASTNode], variables: List[ASTNode], location: Optional[SourceLocation] = None):
        super().__init__(NodeType.INPUT_STATEMENT, location)
        self.prompt = prompt
        self.variables = variables


class ProgramNode(ASTNode):
    """Node for complete BASIC programs"""
    def __init__(self, statements: List[ASTNode], location: Optional[SourceLocation] = None):
        super().__init__(NodeType.PROGRAM, location)
        self.statements = statements


class BlockNode(ASTNode):
    """Node for statement blocks"""
    def __init__(self, statements: List[ASTNode], location: Optional[SourceLocation] = None):
        super().__init__(NodeType.BLOCK, location)
        self.statements = statements


class ASTParser:
    """
    Advanced parser that generates Abstract Syntax Trees for BASIC code.
    
    This parser provides better error reporting, supports complex nested expressions,
    and lays the foundation for advanced language features.
    """
    
    def __init__(self):
        self.tokens = []
        self.current = 0
        self.error_context = ErrorContextManager()
        self.current_line = 1
        self.current_column = 1
    
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
                except Exception:
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
            
            # Unknown character
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
            
            # Special case for INKEY$ which can be called without parentheses
            if name.upper() == 'INKEY$':
                # Check if it has parentheses
                if self._match('PUNCTUATION') and self._current_token()['value'] == '(':
                    self._advance()  # consume '('
                    # INKEY$ should have no arguments
                    self._consume('PUNCTUATION', "INKEY$ takes no arguments")
                # Either way, return as a function call with no arguments
                return FunctionCallNode(
                    function_name=name,
                    arguments=[],
                    location=self._make_location(name_token)
                )
            
            # Function call
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
            
            # Array access
            elif self._match('PUNCTUATION') and self._current_token()['value'] == '(':
                # Note: This is the same as function call syntax - we'll distinguish in semantic analysis
                self._advance()  # consume '('
                indices = []
                
                if not (self._match('PUNCTUATION') and self._current_token()['value'] == ')'):
                    indices.append(self._parse_or_expression())
                    while self._match('PUNCTUATION') and self._current_token()['value'] == ',':
                        self._advance()  # consume ','
                        indices.append(self._parse_or_expression())
                
                self._consume('PUNCTUATION', "Expected ')' after array indices")
                
                return ArrayAccessNode(
                    array_name=name,
                    indices=indices,
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

        # More statements can be added here...

        # Fallback: treat as expression
        return self._parse_or_expression()
    
    def _is_assignment(self) -> bool:
        """Check if the current tokens form an assignment"""
        # Look for pattern: IDENTIFIER [indices] = expression
        if not self._match('IDENTIFIER'):
            return False
        
        # Look ahead for = sign
        pos = 1
        token = self._peek_token(pos)
        
        # Skip array indices if present
        if token and token['type'] == 'PUNCTUATION' and token['value'] == '(':
            paren_count = 1
            pos += 1
            while pos <= len(self.tokens) and paren_count > 0:
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
                except Exception:
                    # If we can't parse a statement, break
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

        # Handle empty PRINT
        if not self._current_token() or self._current_token()['type'] in ['KEYWORD', 'PUNCTUATION']:
            if self._current_token() and self._current_token()['value'] in [';', ',']:
                self._advance()  # consume separator
                return PrintStatementNode(
                    expressions=expressions,
                    separators=[],
                    location=self._make_location(print_token)
                )
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

        # Parse first variable
        var_token = self._advance()
        variables.append(VariableNode(
            name=var_token['value'],
            location=self._make_location(var_token)
        ))

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

            var_token = self._advance()
            variables.append(VariableNode(
                name=var_token['value'],
                location=self._make_location(var_token)
            ))

        return InputStatementNode(
            prompt=prompt,
            variables=variables,
            location=self._make_location(input_token)
        )


class ASTVisitor:
    """Base class for AST visitors"""
    
    def visit(self, node: ASTNode) -> Any:
        """Visit a node using the visitor pattern"""
        return node.accept(self)
    
    def generic_visit(self, node: ASTNode) -> Any:
        """Default visit method for unhandled node types"""
        return None


class ASTEvaluator(ASTVisitor):
    """Evaluator that executes AST nodes"""
    
    def __init__(self, emulator):
        self.emulator = emulator
    
    def visit_number(self, node: LiteralNode) -> Union[int, float]:
        """Visit number literal"""
        return node.value
    
    def visit_string(self, node: LiteralNode) -> str:
        """Visit string literal"""
        return node.value
    
    def visit_variable(self, node: VariableNode) -> Any:
        """Visit variable reference"""
        var_name = node.name.upper()
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
            return left_val == right_val
        elif node.operator == Operator.NOT_EQUAL:
            return left_val != right_val
        elif node.operator == Operator.LESS_THAN:
            return left_val < right_val
        elif node.operator == Operator.GREATER_THAN:
            return left_val > right_val
        elif node.operator == Operator.LESS_EQUAL:
            return left_val <= right_val
        elif node.operator == Operator.GREATER_EQUAL:
            return left_val >= right_val
        elif node.operator == Operator.AND:
            return bool(left_val) and bool(right_val)
        elif node.operator == Operator.OR:
            return bool(left_val) or bool(right_val)
        elif node.operator == Operator.MOD:
            # Modulo operation
            if right_val == 0:
                raise ZeroDivisionError("Modulo by zero")
            return left_val % right_val
        else:
            error = self.emulator.expression_evaluator.error_context.runtime_error(
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
            return not bool(operand_val)
        else:
            error = self.emulator.expression_evaluator.error_context.runtime_error(
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
        handler = self.emulator.expression_evaluator.function_registry.get_handler(func_name)
        if handler:
            return handler(self.emulator.expression_evaluator, arg_values)
        
        # If not a function, check if it's an array access (dimensioned or not)
        # We need to treat anything with parentheses that's not a function as potential array access
        if len(arg_values) > 0:  # Has arguments, likely array access
            # Convert arguments to indices and delegate to array access
            indices = [int(val) for val in arg_values]
            return self.emulator.expression_evaluator._evaluate_array_access(func_name, ','.join(map(str, indices)))
        
        # Neither function nor array access
        available_functions = list(self.emulator.expression_evaluator.function_registry.list_functions()[:10])
        error = self.emulator.expression_evaluator.error_context.reference_error(
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
        """Visit WHILE statement - execute loop while condition is true"""
        results = []
        max_iterations = self.emulator.max_iterations
        iteration_count = 0
        
        while iteration_count < max_iterations:
            # Evaluate condition
            condition_result = self.visit(node.condition)
            
            # Convert to boolean (BASIC truth rules)
            condition_true = bool(condition_result) if isinstance(condition_result, (int, float)) else condition_result != 0
            
            if not condition_true:
                break
                
            # Execute body
            body_result = self.visit(node.body)
            if body_result:
                results.extend(body_result if isinstance(body_result, list) else [body_result])
            
            iteration_count += 1
        
        if iteration_count >= max_iterations:
            error = self.emulator.expression_evaluator.error_context.runtime_error(
                f"WHILE loop exceeded maximum iterations ({max_iterations})",
                suggestions=[
                    "Check loop condition to ensure it will eventually become false",
                    "Add a counter variable or break condition",
                    "Verify loop logic to prevent infinite loops"
                ]
            )
            raise ValueError(error.format_message())
        
        return results
    
    def visit_exit_for_statement(self, node: ExitForStatementNode) -> Any:
        """Visit EXIT FOR statement - signal to exit current FOR loop"""
        # Return a special signal that can be caught by the execution engine
        return [{'type': 'exit_for'}]
    
    def visit_if_statement(self, node: IfStatementNode) -> Any:
        """Visit IF statement - evaluate condition and execute appropriate branch"""
        # Evaluate condition
        condition_result = self.visit(node.condition)
        
        # Convert to boolean (BASIC truth rules)
        if isinstance(condition_result, (int, float)):
            condition_true = condition_result != 0
        elif isinstance(condition_result, str):
            condition_true = len(condition_result) > 0
        else:
            condition_true = bool(condition_result)
        
        # Execute appropriate branch
        if condition_true:
            # Execute THEN branch
            result = self.visit(node.then_branch)
            
            # Handle special case: if THEN branch evaluates to a number, it's a line jump
            if isinstance(result, (int, float)) and not isinstance(result, bool):
                line_num = int(result)
                return [{'type': 'jump', 'line': line_num}]
            
            return result
        elif node.else_branch:
            # Execute ELSE branch if condition is false and ELSE exists
            result = self.visit(node.else_branch)
            
            # Handle special case: if ELSE branch evaluates to a number, it's a line jump
            if isinstance(result, (int, float)) and not isinstance(result, bool):
                line_num = int(result)
                return [{'type': 'jump', 'line': line_num}]
            
            return result
        else:
            # No ELSE branch and condition is false - do nothing
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
            except Exception as e:
                # Add error to results and continue
                results.append({'type': 'error', 'message': str(e)})

        return results

    def visit_print_statement(self, node: PrintStatementNode) -> Any:
        """Visit PRINT statement"""
        # Build output from expressions and separators
        output_parts = []

        for i, expr in enumerate(node.expressions):
            # Evaluate expression
            value = self.visit(expr)
            output_parts.append(str(value))

            # Add separator if present
            if i < len(node.separators):
                sep = node.separators[i]
                if sep == ';':
                    # Semicolon = no space/newline
                    pass
                elif sep == ',':
                    # Comma = tab to next zone
                    output_parts.append('\t')

        # Join parts and return as text output
        output_text = ''.join(output_parts)
        return [{'type': 'text', 'text': output_text}]

    def visit_assignment(self, node: AssignmentNode) -> Any:
        """Visit assignment statement"""
        # Evaluate the value
        value = self.visit(node.value)

        # Get target variable name
        if hasattr(node.target, 'name'):
            var_name = node.target.name.upper()
        else:
            # For complex targets, convert back to string
            var_name = str(node.target)

        # Set variable in emulator
        self.emulator.variables[var_name] = value

        # Return empty result (assignments don't produce output)
        return []

    def visit_end_statement(self, node: EndStatementNode) -> Any:
        """Visit END statement - stop program execution"""
        self.emulator.running = False
        self.emulator.stopped_position = None
        return []

    def visit_goto_statement(self, node: GotoStatementNode) -> Any:
        """Visit GOTO statement"""
        try:
            target_line = self.visit(node.target_line)
            line_num = int(target_line)
        except (ValueError, TypeError) as e:
            error = self.emulator.error_context.syntax_error(
                "SYNTAX ERROR: Invalid GOTO target",
                self.emulator.current_line,
                suggestions=[
                    "Correct syntax: GOTO line_number",
                    "Example: GOTO 100 or GOTO L where L is a numeric variable",
                    "Line number must be a positive integer"
                ]
            )
            return [{'type': 'error', 'message': error.format_detailed()}]

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
            return [{'type': 'error', 'message': error.format_detailed()}]

        return [{'type': 'jump', 'line': line_num}]

    def visit_for_statement(self, node: ForStatementNode) -> Any:
        """Visit FOR statement"""
        # FOR loops require complex state management
        # For now, return a command that indicates FOR loop processing needed
        var_name = node.variable.name if hasattr(node.variable, 'name') else str(node.variable)
        start_val = self.visit(node.start_value)
        end_val = self.visit(node.end_value)
        step_val = self.visit(node.step_value) if node.step_value else 1

        return [{'type': 'for_loop', 'variable': var_name, 'start': start_val, 'end': end_val, 'step': step_val}]