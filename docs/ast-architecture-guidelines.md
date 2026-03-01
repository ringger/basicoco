# AST Architecture Guidelines for TRS-80 Emulator

## Executive Summary

This document captures critical architectural lessons learned from attempting to integrate AST-based execution into the TRS-80 BASIC emulator. The integration initially led to 164 test failures, requiring systematic reversion and architectural clarification.

## Core Architectural Principle

**AST parsing and stateful execution are separate concerns that must be carefully coordinated, not blindly merged.**

## The Fundamental Question: Are AST Visitors and State Management Incompatible?

**No, they are not inherently incompatible.** This is a crucial clarification. AST visitors can absolutely manage state - many production compilers and interpreters do exactly this. The incompatibility we experienced was due to:

1. **Incomplete migration** - Mixing paradigms halfway
2. **Return format mismatches** - AST visitors returning incompatible formats
3. **Inconsistent state ownership** - Some state in visitors, some in execute methods
4. **Violated architectural contracts** - Breaking existing patterns without complete conversion

## Valid Architectural Approaches

### Approach 1: Stateful AST Visitors (Valid)

```python
class StatefulASTEvaluator:
    def __init__(self, emulator):
        self.emulator = emulator

    def visit_for_statement(self, node: ForStatementNode):
        # AST visitor directly manages emulator state
        self.emulator.for_stack.append({
            'var': node.variable.name,
            'end': self.visit(node.end_value),
            'step': self.visit(node.step_value),
            'line': self.emulator.current_line
        })
        self.emulator.variables[node.variable.name] = self.visit(node.start_value)
        return []  # Return format expected by execution engine
```

**Pros:**
- Single point of truth for each operation
- Can leverage AST structure for optimizations
- Modern, clean architecture

**Cons:**
- Requires complete rewrite of execution engine
- Must convert ALL commands simultaneously
- Breaks existing test expectations

### Approach 2: Pure AST + Separate Execution (Valid)

```python
class PureASTEvaluator:
    def visit_for_statement(self, node: ForStatementNode):
        # Pure visitor returns data structure
        return {
            'type': 'for_loop',
            'variable': node.variable.name,
            'start': self.visit(node.start_value),
            'end': self.visit(node.end_value),
            'step': self.visit(node.step_value)
        }

class ExecutionEngine:
    def handle_for_loop(self, ast_result):
        # Execution layer manages all state
        self.for_stack.append({
            'var': ast_result['variable'],
            'end': ast_result['end'],
            'step': ast_result['step']
        })
        self.variables[ast_result['variable']] = ast_result['start']
        return []
```

**Pros:**
- Clear separation of concerns
- Can be implemented incrementally
- Easier to test each layer independently

**Cons:**
- Two-step process for each operation
- Potential duplication of logic
- Extra translation layer

### Approach 3: Hybrid for Specific Use Cases (Our Current Approach)

```python
# Use AST for structural transformation
def parse_and_convert_single_line(statement):
    # Convert: IF X=1 THEN PRINT "A": GOTO 100
    # To: ["IF X=1 THEN", "PRINT \"A\"", "GOTO 100", "ENDIF"]
    ast = parse_statement(statement)
    return expand_control_structure(ast)

# Keep execution in execute_* methods
def execute_for(self, args):
    # Traditional stateful execution
    # Manages for_stack, variables, program_counter
    return self.execute_for(args)
```

**Pros:**
- Minimal disruption to existing code
- Leverages AST where it provides clear value
- Maintains backward compatibility

**Cons:**
- Not a "pure" architecture
- Must maintain two systems
- Complexity in deciding what uses which approach

## What Went Wrong in Our Implementation

### 1. Mixed Mental Models

We tried to use AST visitors as drop-in replacements for execute_* methods without fully converting the execution model:

```python
# WRONG: Incompatible return format
def visit_for_statement(self, node):
    return [{'type': 'for_loop', 'variable': var_name, ...}]

# Execution engine expected:
def execute_for(self, args):
    self.for_stack.append(...)  # Modifies state
    return []  # Returns empty list
```

### 2. Incomplete State Management

Some state was managed by visitors, some by execute methods:

```python
# WRONG: Visitor returns command, doesn't manage state
def visit_goto_statement(self, node):
    return [{'type': 'jump', 'line': target_line}]
    # But program_counter not updated!

# Should have been ALL or NOTHING:
# Either visitor manages program_counter
# OR visitor returns data for execution layer
```

### 3. Return Format Contract Violations

The execution engine expects specific return formats:

```python
# Contract: execute_* methods return List[Dict[str, Any]]
# Each dict must have 'type' field
# Common types: 'text', 'error', 'jump', 'input_request'

# WRONG: Mixed formats
results = [{'type': 'for_loop', ...}, 'NEXT I', {'text': '0', 'type': 'text'}]
```

## Architectural Guidelines for This Codebase

### ✅ DO: Use AST for These Cases

1. **Expression Evaluation** - Pure computation, no side effects
   ```python
   result = ast_evaluator.evaluate("3 + 4 * 5")  # Returns 23
   ```

2. **Structural Transformation** - Converting code structure
   ```python
   # Single-line to multi-line expansion
   "IF X=1 THEN A=5: B=10" → ["IF X=1 THEN", "A=5", "B=10", "ENDIF"]
   ```

3. **Program Analysis** - Reading without modifying
   ```python
   # Find all variable references
   variables = ast_analyzer.find_variables(program)
   ```

### ❌ DON'T: Use AST for These Cases

1. **State-Modifying Commands** - GOTO, GOSUB, FOR, RETURN
   - These need direct access to execution state
   - Must maintain specific return formats
   - Have complex interactions with program flow

2. **I/O Operations** - INPUT, PRINT with side effects
   - Need to interact with system state
   - Have specific output formatting requirements
   - May pause execution for user input

3. **Execution Control** - Program running, stopping, continuing
   - Requires careful state management
   - Must coordinate multiple subsystems
   - Has specific error recovery requirements

## State Manager Architecture (Future Enhancement)

To prevent future architectural confusion, implement clear state ownership:

```python
class StateArchitecture:
    """
    Clear ownership boundaries prevent mixing stateful/stateless operations
    """

    def __init__(self):
        self.variable_state = VariableStateManager()
        # Owns: variables, arrays, array_dims
        # Used by: LET, DIM, array access

        self.execution_state = ExecutionStateManager()
        # Owns: program_counter, call_stack, for_stack, if_stack
        # Used by: GOTO, GOSUB, RETURN, FOR, NEXT, IF

        self.io_state = IOStateManager()
        # Owns: keyboard_buffer, input_variables, waiting_for_input
        # Used by: INPUT, INKEY$, PRINT

        self.graphics_state = GraphicsStateManager()
        # Owns: graphics_mode, colors, cursor_position
        # Used by: PMODE, SCREEN, PSET, LINE, CIRCLE
```

With state managers, it becomes obvious which operations are stateful:

```python
def execute_goto(self, args):
    line_num = self.evaluate_expression(args)
    # Must interact with state manager - clearly stateful!
    self.state.execution.jump_to_line(line_num)
    return [{'type': 'jump', 'line': line_num}]
```

## Testing Guidelines

### Before Any Architectural Change

1. **Run full test suite**: `python -m pytest`
2. **Note baseline**: Document current pass/fail count
3. **Incremental changes**: Change one component at a time
4. **Test after each change**: Verify no regression
5. **Revert if failures increase**: Don't accumulate problems

### Test-Driven Architecture Changes

```python
# GOOD: Test contract explicitly
def test_execute_method_contract():
    """All execute_* methods must return List[Dict[str, Any]]"""
    result = basic.execute_for("I = 1 TO 10")
    assert isinstance(result, list)
    for item in result:
        assert isinstance(item, dict)
        assert 'type' in item

# BAD: Assuming implementation details
def test_for_loop_internals():
    """Don't test HOW it works, test WHAT it does"""
    basic.execute_for("I = 1 TO 10")
    assert len(basic.for_stack) == 1  # Too coupled to implementation
```

## Lessons Learned

1. **Architecture is about boundaries** - Clear boundaries prevent confusion
2. **Consistency over purity** - Better to be consistently "impure" than inconsistently "pure"
3. **Incremental migration needs complete steps** - Half-migrated code is broken code
4. **Tests are architectural documentation** - They encode the contracts
5. **State ownership must be explicit** - Ambiguous ownership leads to bugs

## Decision Record

**Decision**: Use AST for parsing and structural transformation, keep execution in execute_* methods

**Rationale**:
- Minimizes disruption to working code
- Leverages AST where it provides clear value
- Maintains testability and backward compatibility
- Clear separation of concerns

**Consequences**:
- Must maintain both AST and traditional execution
- Cannot leverage some AST optimizations
- Clear boundaries must be documented and enforced

**Alternatives Considered**:
1. Full AST-based execution - Too disruptive, too many test failures
2. No AST at all - Loses valuable parsing improvements
3. Gradual complete migration - High risk, long transition period

## Future Considerations

If we were starting fresh, a complete AST-based interpreter would be ideal:

```python
class ModernBASICInterpreter:
    def run_program(self, source: str):
        ast = self.parser.parse(source)
        optimized_ast = self.optimizer.optimize(ast)
        return self.evaluator.evaluate(optimized_ast)
```

But given our existing architecture, tests, and patterns, the hybrid approach provides the best balance of improvement and stability.

## Enforcement Checklist

Before implementing any AST-related change:

- [ ] Is this operation stateless or stateful?
- [ ] If stateful, who owns the state?
- [ ] What return format is expected?
- [ ] Are we mixing paradigms?
- [ ] Have we tested the contract?
- [ ] Is the boundary clear and documented?
- [ ] Can we revert if needed?

## Conclusion

AST visitors and state management are not incompatible - they just need clear architectural decisions about ownership and responsibilities. In our codebase, we've chosen separation for pragmatic reasons, not because it's the only way. The key is consistency, clarity, and respect for existing architectural patterns.