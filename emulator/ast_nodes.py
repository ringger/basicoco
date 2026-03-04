"""
AST Node Definitions for TRS-80 Color Computer BASIC Emulator

This module defines the AST node types, enums, and visitor base class used by
the parser (ast_parser.py) and evaluator (ast_evaluator.py).
"""

from typing import Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum


def basic_truthy(value) -> bool:
    """Convert a BASIC value to Python bool using CoCo semantics."""
    if isinstance(value, str):
        return len(value) > 0
    if isinstance(value, (int, float)):
        return bool(value)
    return value != 0


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

    DO_LOOP_STATEMENT = "do_loop_statement"
    ON_BRANCH_STATEMENT = "on_branch_statement"
    ON_ERROR_GOTO = "on_error_goto"

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
        super().__init__(NodeType.DO_LOOP_STATEMENT, location)
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


class OnBranchStatementNode(ASTNode):
    """Node for ON expr GOTO/GOSUB line1,line2,..."""
    def __init__(self, expression: ASTNode, branch_type: str, targets: List[ASTNode], location: Optional[SourceLocation] = None):
        super().__init__(NodeType.ON_BRANCH_STATEMENT, location)
        self.expression = expression      # Selector expression
        self.branch_type = branch_type    # 'GOTO' or 'GOSUB'
        self.targets = targets            # Line number expressions


class OnErrorGotoNode(ASTNode):
    """Node for ON ERROR GOTO line"""
    def __init__(self, target_line: ASTNode, location: Optional[SourceLocation] = None):
        super().__init__(NodeType.ON_ERROR_GOTO, location)
        self.target_line = target_line    # 0 to disable


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


class ASTVisitor:
    """Base class for AST visitors"""

    def visit(self, node: ASTNode) -> Any:
        """Visit a node using the visitor pattern"""
        return node.accept(self)

    def generic_visit(self, node: ASTNode) -> Any:
        """Default visit method for unhandled node types"""
        return None
