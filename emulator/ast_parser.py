"""
Advanced AST Parser for TRS-80 Color Computer BASIC Emulator

This module provides Abstract Syntax Tree generation for BASIC expressions and statements,
enabling better error reporting, optimization, and support for advanced language constructs.
"""

from typing import Any, List, Optional, Union, Dict
from dataclasses import dataclass
from enum import Enum
import re


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
    
    # Control Flow
    BLOCK = "block"
    PROGRAM = "program"


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


class PrintStatementNode(ASTNode):
    """Node for PRINT statements"""
    def __init__(self, expressions: List[ASTNode], separators: List[str], location: Optional[SourceLocation] = None):
        super().__init__(NodeType.PRINT_STATEMENT, location)
        self.expressions = expressions
        self.separators = separators


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
        self.current_line = 1
        self.current_column = 1
    
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
        self.tokens = self._tokenize(expr_str)
        self.current = 0
        
        if not self.tokens:
            raise ValueError("Empty expression")
        
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
        self.tokens = self._tokenize(stmt_str)
        self.current = 0
        
        if not self.tokens:
            raise ValueError("Empty statement")
        
        return self._parse_statement()
    
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
            'FOR', 'TO', 'STEP', 'NEXT',
            'WHILE', 'WEND', 'DO', 'LOOP', 'UNTIL',
            'GOTO', 'GOSUB', 'RETURN',
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
            raise ValueError(f"Unexpected end of input. {message}")
        if token['type'] != token_type:
            raise ValueError(f"Expected {token_type}, got {token['type']}. {message}")
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
        """Parse multiplication and division"""
        left = self._parse_power_expression()
        
        while self._match('OPERATOR') and self._current_token()['value'] in ['*', '/']:
            op_token = self._advance()
            right = self._parse_power_expression()
            op = Operator.MULTIPLY if op_token['value'] == '*' else Operator.DIVIDE
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
            raise ValueError("Unexpected end of expression")
        
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
        
        raise ValueError(f"Unexpected token: {token['value']}")
    
    def _parse_statement(self) -> ASTNode:
        """Parse a BASIC statement"""
        token = self._current_token()
        
        if not token:
            raise ValueError("Empty statement")
        
        # Assignment (LET X = 5 or X = 5)
        if (self._match('KEYWORD') and token['value'] == 'LET') or self._is_assignment():
            return self._parse_assignment()
        
        # IF statement
        if self._match('KEYWORD') and token['value'] == 'IF':
            return self._parse_if_statement()
        
        # FOR statement
        if self._match('KEYWORD') and token['value'] == 'FOR':
            return self._parse_for_statement()
        
        # PRINT statement
        if self._match('KEYWORD') and token['value'] == 'PRINT':
            return self._parse_print_statement()
        
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
    
    def _parse_if_statement(self) -> IfStatementNode:
        """Parse IF statement"""
        if_token = self._advance()  # consume 'IF'
        condition = self._parse_or_expression()
        
        self._consume('KEYWORD', "Expected 'THEN' after IF condition")
        then_branch = self._parse_statement()
        
        else_branch = None
        if self._match_value('ELSE'):
            self._advance()  # consume 'ELSE'
            else_branch = self._parse_statement()
        
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
        
        # For now, body is empty - will be filled by statement grouping
        body = BlockNode(statements=[], location=self._make_location(for_token))
        
        return ForStatementNode(
            variable=variable,
            start_value=start_value,
            end_value=end_value,
            step_value=step_value,
            body=body,
            location=self._make_location(for_token)
        )
    
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
                return float('inf')
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
        else:
            raise ValueError(f"Unknown binary operator: {node.operator}")
    
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
            raise ValueError(f"Unknown unary operator: {node.operator}")
    
    def visit_function_call(self, node: FunctionCallNode) -> Any:
        """Visit function call"""
        # Delegate to the expression evaluator's function registry
        func_name = node.function_name.upper()
        
        # Evaluate arguments
        arg_values = []
        for arg in node.arguments:
            arg_values.append(str(self.visit(arg)))
        
        # Call the function through the expression evaluator
        handler = self.emulator.expression_evaluator.function_registry.get_handler(func_name)
        if handler:
            return handler(self.emulator.expression_evaluator, arg_values)
        else:
            raise ValueError(f"Unknown function: {func_name}")
    
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