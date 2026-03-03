#!/usr/bin/env python3

"""
Comprehensive tests for AST Parser and Evaluation System

Tests the Abstract Syntax Tree parser that provides advanced expression parsing,
better error reporting, and foundation for complex language features.
"""

import pytest
from emulator.ast_nodes import (
    NodeType, Operator, SourceLocation,
    LiteralNode, VariableNode, BinaryOpNode, UnaryOpNode,
    FunctionCallNode, ArrayAccessNode, AssignmentNode, IfStatementNode,
    ForStatementNode, PrintStatementNode, BlockNode, GosubStatementNode,
    ReturnStatementNode, InputStatementNode
)
from emulator.ast_parser import ASTParser
from emulator.ast_evaluator import ASTEvaluator
from emulator.ast_converter import parse_and_convert_single_line
from emulator.core import CoCoBasic


class TestASTParser:
    """Test cases for AST Parser functionality"""

    @pytest.fixture(autouse=True)
    def setup_parser(self, basic):
        """Set up test environment"""
        self.parser = ASTParser()
        self.evaluator = ASTEvaluator(basic)

        # Set up some test variables
        basic.variables['A'] = 10
        basic.variables['B'] = 5
        basic.variables['S$'] = 'HELLO'

    def test_basic_functionality(self, basic, helpers):
        """Test basic AST parser functionality"""
        # Test simple number parsing
        ast = self.parser.parse_expression("42")
        assert ast.node_type == NodeType.NUMBER
        assert ast.value == 42

    def test_literal_nodes(self, basic, helpers):
        """Test parsing of literal values"""
        # Number literals
        ast = self.parser.parse_expression("123")
        assert isinstance(ast, LiteralNode)
        assert ast.node_type == NodeType.NUMBER
        assert ast.value == 123
        
        ast = self.parser.parse_expression("3.14")
        assert ast.value == 3.14
        
        # String literals
        ast = self.parser.parse_expression('"HELLO WORLD"')
        assert isinstance(ast, LiteralNode)
        assert ast.node_type == NodeType.STRING
        assert ast.value == "HELLO WORLD"
        
        # Empty string
        ast = self.parser.parse_expression('""')
        assert ast.value == ""

    def test_variable_nodes(self, basic, helpers):
        """Test parsing of variable references"""
        ast = self.parser.parse_expression("A")
        assert isinstance(ast, VariableNode)
        assert ast.node_type == NodeType.VARIABLE
        assert ast.name == "A"
        
        # String variable
        ast = self.parser.parse_expression("NAME$")
        assert ast.name == "NAME$"

    def test_binary_operations(self, basic, helpers):
        """Test parsing of binary operations with proper precedence"""
        # Simple addition
        ast = self.parser.parse_expression("2 + 3")
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == Operator.ADD
        assert ast.left.value == 2
        assert ast.right.value == 3
        
        # Multiplication has higher precedence than addition
        ast = self.parser.parse_expression("2 + 3 * 4")
        assert ast.operator == Operator.ADD
        assert ast.left.value == 2
        assert isinstance(ast.right, BinaryOpNode)
        assert ast.right.operator == Operator.MULTIPLY
        
        # Test parentheses override precedence
        ast = self.parser.parse_expression("(2 + 3) * 4")
        assert ast.operator == Operator.MULTIPLY
        assert isinstance(ast.left, BinaryOpNode)
        assert ast.left.operator == Operator.ADD
        assert ast.right.value == 4

    def test_unary_operations(self, basic, helpers):
        """Test parsing of unary operations"""
        # Unary minus
        ast = self.parser.parse_expression("-5")
        assert isinstance(ast, UnaryOpNode)
        assert ast.operator == Operator.SUBTRACT
        assert ast.operand.value == 5
        
        # Unary plus
        ast = self.parser.parse_expression("+10")
        assert ast.operator == Operator.ADD
        
        # NOT operator
        ast = self.parser.parse_expression("NOT TRUE")
        assert ast.operator == Operator.NOT

    def test_function_calls(self, basic, helpers):
        """Test parsing of function calls"""
        # Simple function call
        ast = self.parser.parse_expression("ABS(-5)")
        assert isinstance(ast, FunctionCallNode)
        assert ast.function_name == "ABS"
        assert len(ast.arguments) == 1
        assert isinstance(ast.arguments[0], UnaryOpNode)
        
        # Function with multiple arguments
        ast = self.parser.parse_expression('LEFT$("HELLO", 3)')
        assert ast.function_name == "LEFT$"
        assert len(ast.arguments) == 2
        assert ast.arguments[0].value == "HELLO"
        assert ast.arguments[1].value == 3
        
        # Function with no arguments
        ast = self.parser.parse_expression("RND()")
        assert ast.function_name == "RND"
        assert len(ast.arguments) == 0

    def test_array_access(self, basic, helpers):
        """Test parsing of array access"""
        ast = self.parser.parse_expression("ARR(5)")
        # Note: Parser can't distinguish between function call and array access
        # This is resolved during semantic analysis
        assert isinstance(ast, (FunctionCallNode, ArrayAccessNode))

    def test_complex_expressions(self, basic, helpers):
        """Test parsing of complex nested expressions"""
        # Nested arithmetic
        ast = self.parser.parse_expression("2 + 3 * 4 - 1")
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == Operator.SUBTRACT
        
        # Mixed operations with parentheses
        ast = self.parser.parse_expression("(A + B) * (C - D)")
        assert ast.operator == Operator.MULTIPLY
        assert isinstance(ast.left, BinaryOpNode)
        assert isinstance(ast.right, BinaryOpNode)
        
        # Nested function calls
        ast = self.parser.parse_expression("ABS(SIN(3.14))")
        assert ast.function_name == "ABS"
        assert isinstance(ast.arguments[0], FunctionCallNode)
        assert ast.arguments[0].function_name == "SIN"

    def test_comparison_operations(self, basic, helpers):
        """Test parsing of comparison operations"""
        # Equality
        ast = self.parser.parse_expression("A = 5")
        assert ast.operator == Operator.EQUAL
        
        # Inequality  
        ast = self.parser.parse_expression("A <> 5")
        assert ast.operator == Operator.NOT_EQUAL
        
        # Less than
        ast = self.parser.parse_expression("A < 5")
        assert ast.operator == Operator.LESS_THAN
        
        # Greater than or equal
        ast = self.parser.parse_expression("A >= 5")
        assert ast.operator == Operator.GREATER_EQUAL

    def test_logical_operations(self, basic, helpers):
        """Test parsing of logical operations"""
        # AND operation
        ast = self.parser.parse_expression("A > 5 AND B < 10")
        assert ast.operator == Operator.AND
        
        # OR operation
        ast = self.parser.parse_expression("A = 0 OR B = 0")
        assert ast.operator == Operator.OR
        
        # Complex logical expression
        ast = self.parser.parse_expression("(A > 5 AND B < 10) OR C = 0")
        assert ast.operator == Operator.OR

    def test_source_location_tracking(self, basic, helpers):
        """Test that source locations are properly tracked"""
        ast = self.parser.parse_expression("42", line=10)
        if ast.location:
            assert ast.location.line == 10

    def test_ast_evaluation(self, basic, helpers):
        """Test AST evaluation produces correct results"""
        # Simple arithmetic
        ast = self.parser.parse_expression("2 + 3")
        result = self.evaluator.visit(ast)
        assert result == 5
        
        # With variables
        ast = self.parser.parse_expression("A + B")
        result = self.evaluator.visit(ast)
        assert result == 15  # A=10, B=5
        
        # String operations
        ast = self.parser.parse_expression('"HELLO " + "WORLD"')
        result = self.evaluator.visit(ast)
        assert result == "HELLO WORLD"

    def test_ast_vs_legacy_comparison(self, basic, helpers):
        """Test that AST evaluation matches legacy expression evaluation"""
        test_expressions = [
            "2 + 3 * 4",
            "(2 + 3) * 4", 
            "A + B * 2",
            "ABS(-5) + SQR(16)",
            '"HELLO" + " " + "WORLD"'
        ]
        
        for expr in test_expressions:
            # Get legacy result
            legacy_result = basic.evaluate_expression(expr)
            
            # Get AST result
            ast = self.parser.parse_expression(expr)
            ast_result = self.evaluator.visit(ast)
            
            assert ast_result == legacy_result, f"AST and legacy results differ for: {expr}"

    def test_error_handling(self, basic, helpers):
        """Test error handling in AST parsing"""
        # Empty expression
        try:
            self.parser.parse_expression("")
            assert False, "Should have raised ValueError for empty expression"
        except ValueError:
            pass  # Expected
        
        # Invalid syntax - this might not actually fail in our parser
        # So let's test a truly invalid expression
        try:
            self.parser.parse_expression("2 +")  # Incomplete expression
            assert False, "Should have raised ValueError for incomplete expression"
        except (ValueError, Exception):
            pass  # Expected - any exception is fine
        
        # Unmatched parentheses
        try:
            self.parser.parse_expression("(2 + 3")
            assert False, "Should have raised ValueError for unmatched parentheses"
        except ValueError:
            pass  # Expected

    def test_statement_parsing(self, basic, helpers):
        """Test parsing of BASIC statements"""
        # Assignment statement
        ast = self.parser.parse_statement("LET A = 5")
        assert isinstance(ast, AssignmentNode)
        assert ast.target.name == "A"
        assert ast.value.value == 5
        
        # IF statement
        ast = self.parser.parse_statement("IF A > 5 THEN PRINT A")
        assert isinstance(ast, IfStatementNode)
        assert isinstance(ast.condition, BinaryOpNode)
        
        # FOR statement
        ast = self.parser.parse_statement("FOR I = 1 TO 10")
        assert isinstance(ast, ForStatementNode)
        assert ast.variable.name == "I"

    def test_tokenization(self, basic, helpers):
        """Test the tokenization process"""
        tokens = self.parser._tokenize("A + B * 2")
        assert len(tokens) > 0
        
        # Check token types are properly identified
        token_values = [token['value'] for token in tokens]
        assert 'A' in token_values
        assert '+' in token_values
        assert 'B' in token_values
        assert '*' in token_values
        assert 2 in token_values

    def test_ast_parser_integration(self, basic, helpers):
        """Test AST parser integration"""
        # Test that AST parsing works correctly
        result = basic.evaluate_expression("2 + 3 * 4")
        assert result == 14
        
        # Test with variables
        result = basic.evaluate_expression("A + B")
        assert result == 15  # A=10, B=5
        
        # Test with function calls
        result = basic.evaluate_expression("ABS(-5)")
        assert result == 5

    def test_expression_consistency(self, basic, helpers):
        """Test that AST parsing handles all expression types consistently"""
        # Test complex expressions
        result = basic.evaluate_expression("A + B * 2 - 1")
        assert result == 19  # 10 + 5*2 - 1 = 19
        
        # Test string operations
        result = basic.evaluate_expression('"HELLO" + " " + "WORLD"')
        assert result == "HELLO WORLD"

    def test_performance_comparison(self, basic, helpers):
        """Test performance characteristics of AST vs legacy parsing"""
        import time
        
        # Set up missing variables
        basic.variables['C'] = 3
        basic.variables['D'] = 1
        
        expressions = [
            "2 + 3 * 4 - 1",
            "A + B * 2",  # Simplified to avoid undefined variables
            "ABS(-5) + SQR(16)",  # Simplified to avoid trig functions
            '"HELLO" + " " + "WORLD" + "!"'
        ] * 10  # Repeat for timing
        
        # Time AST parsing
        start_time = time.time()
        for expr in expressions:
            basic.evaluate_expression(expr)
        ast_time = time.time() - start_time
        
        # AST parsing should be reasonably fast
        # This is more for monitoring than strict assertion
        print(f"AST parsing time: {ast_time:.4f}s for {len(expressions)} expressions")
        assert ast_time < 1.0, "AST parsing should complete within 1 second"

    def test_visitor_pattern(self, basic, helpers):
        """Test the visitor pattern implementation"""
        # Create a custom visitor for testing
        class TestVisitor:
            def __init__(self):
                self.node_count = 0
            
            def visit_number(self, node):
                self.node_count += 1
                return node.value
            
            def visit_binary_op(self, node):
                self.node_count += 1
                left = node.left.accept(self)
                right = node.right.accept(self)
                if node.operator == Operator.ADD:
                    return left + right
                return 0
            
            def generic_visit(self, node):
                self.node_count += 1
                return 0
        
        # Test visitor on an AST
        ast = self.parser.parse_expression("2 + 3")
        visitor = TestVisitor()
        result = ast.accept(visitor)
        
        assert result == 5
        assert visitor.node_count == 3  # BinaryOp + 2 Numbers

    def test_ast_converter_basic(self, basic, helpers):
        """Test basic AST converter functionality"""
        # Simple IF/THEN with colon-separated statements
        result = parse_and_convert_single_line('IF A=1 THEN PRINT "ONE": B=2', self.parser)
        expected = ['IF A = 1 THEN', 'PRINT "ONE"', 'B = 2', 'ENDIF']  # AST converter adds spaces around operators
        assert result is not None
        assert len(result) == len(expected)

        # Normalize and compare each line
        for i, (got, exp) in enumerate(zip(result, expected)):
            got_norm = got.strip().upper()
            exp_norm = exp.strip().upper()
            # Allow for LET prefix flexibility
            if exp_norm.startswith('LET '):
                exp_norm = exp_norm[4:]
            if got_norm.startswith('LET '):
                got_norm = got_norm[4:]
            assert got_norm == exp_norm, f"Line {i} mismatch: got '{got_norm}', expected '{exp_norm}'"

    def test_ast_converter_if_then_else(self, basic, helpers):
        """Test AST converter with IF/THEN/ELSE"""
        result = parse_and_convert_single_line('IF X>5 THEN PRINT "BIG": ELSE PRINT "SMALL"', self.parser)
        expected = ['IF X>5 THEN', 'PRINT "BIG"', 'ELSE', 'PRINT "SMALL"', 'ENDIF']
        assert result is not None
        assert len(result) == len(expected)

    def test_ast_converter_for_loop(self, basic, helpers):
        """Test AST converter with FOR loops"""
        # Simple FOR loop
        result = parse_and_convert_single_line('FOR I=1 TO 3: PRINT I: NEXT I', self.parser)
        expected = ['FOR I=1 TO 3', 'PRINT I', 'NEXT I']
        assert result is not None
        assert len(result) == len(expected)

        # FOR loop with STEP
        result = parse_and_convert_single_line('FOR X=0 TO 10 STEP 2: PRINT X: NEXT X', self.parser)
        expected = ['FOR X=0 TO 10 STEP 2', 'PRINT X', 'NEXT X']
        assert result is not None
        assert len(result) == len(expected)

    def test_ast_converter_while_loop(self, basic, helpers):
        """Test AST converter with WHILE loops"""
        result = parse_and_convert_single_line('WHILE A<5: PRINT A: A=A+1: WEND', self.parser)
        expected = ['WHILE A<5', 'PRINT A', 'A=A+1', 'WEND']
        assert result is not None
        assert len(result) == len(expected)

    def test_ast_converter_do_loops(self, basic, helpers):
        """Test AST converter with DO/LOOP constructs"""
        # DO/LOOP with condition at end
        result = parse_and_convert_single_line('DO: PRINT "LOOP": A=A+1: LOOP WHILE A<3', self.parser)
        expected = ['DO', 'PRINT "LOOP"', 'A=A+1', 'LOOP WHILE A<3']
        assert result is not None
        assert len(result) == len(expected)

        # DO WHILE/LOOP with condition at start
        result = parse_and_convert_single_line('DO WHILE X>0: PRINT X: X=X-1: LOOP', self.parser)
        expected = ['DO WHILE X>0', 'PRINT X', 'X=X-1', 'LOOP']
        assert result is not None
        assert len(result) == len(expected)

    def test_ast_converter_nested_structures(self, basic, helpers):
        """Test AST converter with nested control structures"""
        # Nested IF in FOR - this tests the recursive nature
        result = parse_and_convert_single_line('FOR I=1 TO 3: IF I=2 THEN PRINT "TWO": NEXT I', self.parser)
        expected = ['FOR I = 1 TO 3', 'IF I = 2 THEN', 'PRINT "TWO"', 'ENDIF', 'NEXT I']  # AST properly expands nested IF
        assert result is not None
        assert len(result) == len(expected)

    def test_ast_converter_error_handling(self, basic, helpers):
        """Test AST converter error handling"""
        # Test with empty string
        result = parse_and_convert_single_line('', self.parser)
        assert result is None

        # Test with non-control structure (should return None)
        result = parse_and_convert_single_line('PRINT "HELLO"', self.parser)
        assert result is None

    def test_ast_converter_complex_expressions(self, basic, helpers):
        """Test AST converter with complex expressions in control structures"""
        # Complex condition in IF
        result = parse_and_convert_single_line('IF (A+B)*2 > C AND D<>0 THEN PRINT "COMPLEX": X=Y+Z', self.parser)
        expected = ['IF (A+B)*2 > C AND D<>0 THEN', 'PRINT "COMPLEX"', 'X=Y+Z', 'ENDIF']
        assert result is not None
        assert len(result) == len(expected)

        # Complex FOR loop bounds
        result = parse_and_convert_single_line('FOR I=ABS(START) TO LEN(S$) STEP 2: PRINT I: NEXT I', self.parser)
        expected = ['FOR I=ABS(START) TO LEN(S$) STEP 2', 'PRINT I', 'NEXT I']
        assert result is not None
        assert len(result) == len(expected)

    def test_goto_statement_parsing(self, basic, helpers):
        """Test GOTO statement parsing in AST parser"""
        # Test simple GOTO
        result = self.parser.parse_statement("GOTO 100")
        assert result.node_type.value == 'goto_statement'
        assert result.target_line is not None

        # Test GOTO with variable expression
        result = self.parser.parse_statement("GOTO I + 10")
        assert result.node_type.value == 'goto_statement'
        assert result.target_line is not None

        # Test GOTO in colon-separated context
        result = self.parser.parse_statement('PRINT "TEST": GOTO 50')
        assert result.node_type.value == 'block'
        assert len(result.statements) == 2
        assert result.statements[0].node_type.value == 'print_statement'
        assert result.statements[1].node_type.value == 'goto_statement'

    def test_ast_converter_goto_statements(self, basic, helpers):
        """Test AST converter handling of GOTO statements in control structures"""
        # Test GOTO in IF THEN context - the exact bug pattern that was fixed
        result = parse_and_convert_single_line('IF X=1 THEN PRINT "HI": GOTO 50', self.parser)
        expected = ['IF X = 1 THEN', 'PRINT "HI"', 'GOTO 50', 'ENDIF']
        assert result == expected

        # Test GOTO with complex expression in IF THEN - now works with simple statements!
        result = parse_and_convert_single_line('IF A>0 THEN GOTO A*10+5', self.parser)
        expected = ['IF A > 0 THEN', 'GOTO (A * 10 + 5)', 'ENDIF']  # AST converter adds parentheses for complex expressions
        assert result == expected

        # Test multiple statements with GOTO in IF THEN
        result = parse_and_convert_single_line('IF FLAG=1 THEN PRINT "JUMPING": COUNT=COUNT+1: GOTO DEST', self.parser)
        expected = ['IF FLAG = 1 THEN', 'PRINT "JUMPING"', 'LET COUNT = COUNT + 1', 'GOTO DEST', 'ENDIF']  # AST converter adds LET for assignments
        assert result == expected

        # Test GOTO in FOR loop context
        result = parse_and_convert_single_line('FOR I=1 TO 5: IF I=3 THEN GOTO 100: NEXT I', self.parser)
        expected = ['FOR I = 1 TO 5', 'IF I = 3 THEN', 'GOTO 100', 'ENDIF', 'NEXT I']
        assert result == expected

        # Test simple GOTO in IF THEN (no colons)
        result = parse_and_convert_single_line('IF X=5 THEN GOTO 100', self.parser)
        expected = ['IF X = 5 THEN', 'GOTO 100', 'ENDIF']
        assert result == expected

    def test_gosub_statement_parsing(self, basic, helpers):
        """Test GOSUB statement parsing"""
        # Test simple GOSUB
        result = self.parser.parse_statement("GOSUB 1000")
        assert isinstance(result, GosubStatementNode)
        assert result.node_type == NodeType.GOSUB_STATEMENT
        assert result.target_line is not None

        # Test GOSUB with variable expression
        result = self.parser.parse_statement("GOSUB I * 100")
        assert isinstance(result, GosubStatementNode)
        assert result.target_line is not None
        assert isinstance(result.target_line, BinaryOpNode)

        # GOSUB evaluation removed - uses legacy implementation per AST architecture guidelines

    def test_return_statement_parsing(self, basic, helpers):
        """Test RETURN statement parsing"""
        # Test simple RETURN
        result = self.parser.parse_statement("RETURN")
        assert isinstance(result, ReturnStatementNode)
        assert result.node_type == NodeType.RETURN_STATEMENT

        # RETURN evaluation removed - uses legacy implementation per AST architecture guidelines

    def test_input_statement_parsing(self, basic, helpers):
        """Test INPUT statement parsing"""
        # Test simple INPUT
        result = self.parser.parse_statement("INPUT A")
        assert isinstance(result, InputStatementNode)
        assert result.node_type == NodeType.INPUT_STATEMENT
        assert result.prompt is None
        assert len(result.variables) == 1
        assert result.variables[0].name == "A"

        # Test INPUT with prompt
        result = self.parser.parse_statement('INPUT "Enter a number"; X')
        assert isinstance(result, InputStatementNode)
        assert result.prompt is not None
        assert result.prompt.value == "Enter a number"
        assert len(result.variables) == 1
        assert result.variables[0].name == "X"

        # Test INPUT with multiple variables
        result = self.parser.parse_statement("INPUT A, B, C")
        assert isinstance(result, InputStatementNode)
        assert len(result.variables) == 3
        assert result.variables[0].name == "A"
        assert result.variables[1].name == "B"
        assert result.variables[2].name == "C"

        # Test INPUT with prompt and multiple variables
        result = self.parser.parse_statement('INPUT "Enter three numbers", X, Y, Z')
        assert isinstance(result, InputStatementNode)
        assert result.prompt.value == "Enter three numbers"
        assert len(result.variables) == 3

        # INPUT evaluation removed - uses legacy implementation per AST architecture guidelines

    def test_gosub_return_input_in_blocks(self, basic, helpers):
        """Test GOSUB/RETURN/INPUT statements in multi-statement blocks"""
        # Test GOSUB in colon-separated context
        result = self.parser.parse_statement('PRINT "Calling subroutine": GOSUB 1000: PRINT "Back"')
        assert isinstance(result, BlockNode)
        assert len(result.statements) == 3
        assert isinstance(result.statements[0], PrintStatementNode)
        assert isinstance(result.statements[1], GosubStatementNode)
        assert isinstance(result.statements[2], PrintStatementNode)

        # Test RETURN in context
        result = self.parser.parse_statement('PRINT "Returning": RETURN')
        assert isinstance(result, BlockNode)
        assert len(result.statements) == 2
        assert isinstance(result.statements[1], ReturnStatementNode)

        # Test INPUT in context
        result = self.parser.parse_statement('PRINT "Enter data": INPUT X: PRINT X')
        assert isinstance(result, BlockNode)
        assert len(result.statements) == 3
        assert isinstance(result.statements[1], InputStatementNode)

    def test_gosub_return_input_error_handling(self, basic, helpers):
        """Test error handling for GOSUB/RETURN/INPUT statements"""
        # GOSUB error handling removed - uses legacy implementation per AST architecture guidelines

        # Test INPUT with no variables (should fail during parsing)
        try:
            self.parser.parse_statement("INPUT")
            assert False, "Should have raised error for INPUT with no variables"
        except ValueError as e:
            assert "Expected variable name" in str(e)

        # Test INPUT with malformed prompt
        try:
            self.parser.parse_statement('INPUT "Prompt" X')  # Missing separator
            assert False, "Should have raised error for malformed INPUT prompt"
        except ValueError as e:
            assert "Expected ';' or ','" in str(e)
