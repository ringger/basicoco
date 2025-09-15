# TRS-80 Color Computer BASIC Emulator Test Suite

This directory contains the comprehensive test suite for the TRS-80 Color Computer BASIC emulator, organized into unit tests and integration tests.

## Test Structure

### Unit Tests (`unit/`)
Tests individual components in isolation:
- `test_ast_parser.py` - Abstract syntax tree parsing
- `test_command_*.py` - Individual BASIC command implementations
- `test_expressions.py` - Expression evaluation
- `test_functions.py` - Built-in BASIC functions
- `test_variables.py` - Variable management
- `test_error_*.py` - Error handling and context management
- `test_graphics_commands.py` - Graphics system components
- `test_output_manager.py` - Output streaming and management
- `test_direct_emulator.py` - Direct emulator unit testing
- `test_utilities.py` - Utility functions unit testing
- `test_program_management_commands.py` - DIR, FILES, DRIVE, SAVE, CLOAD, CSAVE commands
- `test_renum_command.py` - RENUM line renumbering functionality
- `test_on_commands.py` - ON GOTO and ON GOSUB multi-way branching
- And more...

### Integration Tests (`integration/`)
Tests multiple components working together:

#### Core Integration (`integration/`)
- `test_comprehensive_program.py` - Complex program execution
- `test_cross_command_interactions.py` - Command interaction testing
- `test_for_loops.py` - Loop execution testing
- `test_program_execution_flow.py` - Program flow control
- `test_state_isolation.py` - State management between sessions
- `test_websocket_completion_signals.py` - WebSocket communication
- `test_complex_if_then.py` - Complex conditional logic

#### CLI Tests (`integration/cli/`)
- `test_cli_with_pexpect.py` - Interactive CLI testing
- `test_cli_logged.py` - CLI with logging verification

#### End-to-End Tests (`integration/e2e/`)
- `test_minimal.py` - Basic functionality verification  
- `test_step_by_step.py` - Step-by-step execution testing
- `test_manual_lunar.py` - Complex lunar lander program
- `test_complete_lunar.py` - Full lunar lander execution
- `test_complex_lunar.py` - Advanced lunar lander scenarios
- `test_complex_lunar_fixed.py` - Lunar lander with fixes

## Test Suite Components

### 1. Base Test Framework (`test_base.py`)
- **BaseTestCase**: Abstract base class for all tests
- **TestResult**: Represents individual test outcomes  
- **TestSuite**: Collection of test results with statistics
- **Assertion Methods**: Comprehensive assertion methods for different result types
  - `assert_command_result()` - General command result validation
  - `assert_text_output()` - Text output validation
  - `assert_error_output()` - Error condition testing
  - `assert_graphics_output()` - Graphics command validation
  - `assert_variable_equals()` - Variable state validation
  - Standard assertions: `assertTrue()`, `assertEqual()`, `assertIn()`, etc.

### 2. Test Runner (`run_tests.py`)
- **Automatic Discovery**: Recursively finds all test files
- **Multiple Formats**: Supports both class-based and function-based tests
- **Detailed Reporting**: Progress tracking and comprehensive summaries
- **Command Line Interface**: Flexible execution options
- **Statistics**: Success rates, timing, and failure analysis

## Running Tests

### Run All Tests
```bash
python run_tests.py                    # All tests with discovery
python run_tests.py -v                 # Verbose output
python run_tests.py --stop-on-failure  # Stop on first failure
```

### Run Only Unit Tests
```bash
python run_unit_tests.py               # Fast, isolated component tests
python run_unit_tests.py -v            # Verbose unit test output
```

### Run Only Integration Tests  
```bash
python run_integration_tests.py        # Multi-component and E2E tests
python run_integration_tests.py -v     # Verbose integration test output
```

## Test Categories

- **Unit Tests**: Fast, isolated tests of individual components (~25 test suites)
- **Integration Tests**: Slower tests of component interactions (~15 test suites)
- **CLI Tests**: Interactive command-line interface testing
- **E2E Tests**: Full end-to-end program execution testing

## Development Guidelines

### Adding Unit Tests
- Place in `unit/` directory
- Test single components in isolation
- Use mocks/stubs for dependencies
- Focus on edge cases and error conditions
- Keep tests fast (< 100ms each)

### Adding Integration Tests
- Place in `integration/` or appropriate subdirectory
- Test component interactions
- Use real components (minimal mocking)
- Test realistic usage scenarios
- CLI tests go in `integration/cli/`
- Full program tests go in `integration/e2e/`

### Test Naming
- File names: `test_[component].py`
- Class names: `[Component]Test` (inherits from `BaseTestCase`)
- Method names: `test_[specific_behavior]`

### Test Structure
All tests inherit from `BaseTestCase` in `/test_base.py` which provides:
- Emulator instance setup/teardown
- Common assertion methods
- Test result collection
- Error handling and reporting

## Test Results

Recent test run results show excellent coverage:
- **Overall Success Rate**: 96.6% (368/381 unit tests passing)
- **Total Test Suites**: 37+ comprehensive test suites
- **Unit Tests**: Comprehensive coverage including new commands (DIR, SAVE, RENUM, ON GOTO/GOSUB)
- **Integration Tests**: Full end-to-end scenario validation

### New Command Coverage Added
- **Program Management**: DIR, FILES, DRIVE, SAVE, CLOAD, CSAVE (14 tests)
- **RENUM Command**: Line renumbering with reference updates (15 tests)
- **ON Commands**: ON GOTO and ON GOSUB multi-way branching (19 tests)

### Test Utilities (`test_utilities.py`)
- **MockGraphicsOutput**: Captures and validates graphics commands
- **MockSoundOutput**: Captures sound command execution
- **InputSimulator**: Simulates user input for INPUT/INKEY$ commands
- **TestCoCoBasic**: Extended emulator class with testing utilities
- **GraphicsTestHelper**: Specialized assertions for graphics testing
- **ProgramTestHelper**: Utilities for program testing
- **TestDataGenerator**: Generates common test programs

## Organized Test Structure

### Unit Tests (`tests/unit/`)
Individual command and feature testing:

#### `test_print_command.py` (10 tests, 90% success)
- Basic PRINT functionality
- String and numeric literals
- Variable printing
- Expression evaluation
- Concatenation with separators
- Program context testing

#### `test_variables.py` (11 tests, 100% success)
- Variable assignment and retrieval
- Numeric and string variables
- Variable overwriting
- Expression assignment
- LET command
- Multi-statement assignments

#### `test_graphics_commands.py` (16 tests, 81% success)
- PMODE, SCREEN setup
- PSET, PRESET pixel operations
- LINE and CIRCLE drawing
- Graphics bounds checking
- Coordinate systems
- Program integration

### Integration Tests (`tests/integration/`)
Multi-feature interaction testing:

#### `test_for_loops.py` (10 tests, 80% success)
- Basic FOR/NEXT loops
- STEP variations (positive/negative)
- Nested loops
- Loop calculations
- Boundary conditions
- Variable modification

#### `test_comprehensive_program.py` (9 tests, 89% success)
- Math and variable programs
- String operations
- Subroutine calls (GOSUB/RETURN)
- Complex nested structures
- DATA/READ processing
- Mathematical calculations

## Current Test Results

### Overall Statistics
- **Total Test Suites**: 5
- **Total Tests**: 56
- **Passed**: 49 ✅ (87.5% success rate)
- **Failed**: 7 ❌

### Success by Category
- **Variables**: 100% (11/11)
- **PRINT Commands**: 90% (9/10)
- **Comprehensive Programs**: 89% (8/9)
- **Graphics Commands**: 81% (13/16)
- **FOR Loops**: 80% (8/10)

### Known Issues Identified
1. **Division Results**: Returns "5.0" instead of "5" for integer division
2. **Graphics Command Types**: Some graphics commands return different type names than expected
3. **FOR Loop Edge Cases**: Some boundary condition handling differences
4. **DRAW Command**: May not be fully implemented
5. **Floating Point Loops**: Precision handling in FOR loops

## Testing Best Practices

### Writing New Tests
1. Inherit from `BaseTestCase`
2. Implement required `test_basic_functionality()` method
3. Use descriptive test method names starting with `test_`
4. Use appropriate assertion methods
5. Include both positive and negative test cases

### Test Organization
- **Unit Tests**: Single command/feature testing
- **Integration Tests**: Multi-feature interaction
- **Examples**: End-to-end program demonstrations

### Example Test Structure
```python
class MyCommandTest(BaseTestCase):
    def test_basic_functionality(self):
        """Test basic command functionality"""
        self.assert_text_output('MY_COMMAND "TEST"', 'EXPECTED')
    
    def test_error_conditions(self):
        """Test error handling"""
        self.assert_error_output('INVALID_SYNTAX')
```

## Future Enhancements

### Planned Improvements
1. **Mock System Integration**: Better graphics/sound mocking
2. **Input Simulation**: Complete INPUT/INKEY$ testing
3. **Performance Tests**: Timing and resource usage validation
4. **Regression Tests**: Automated bug prevention
5. **Coverage Analysis**: Code coverage measurement

### Test Categories to Add
- **String Functions**: LEN, LEFT$, RIGHT$, MID$, etc.
- **Math Functions**: SIN, COS, TAN, LOG, etc.
- **File Operations**: SAVE/LOAD simulation
- **Error Handling**: Comprehensive error condition testing
- **Memory Management**: Variable and program memory testing

## Running Specific Tests

### Individual Test Files
```bash
# Run specific unit test
python tests/unit/test_print_command.py

# Run specific integration test  
python tests/integration/test_for_loops.py
```

### Pattern Matching
```bash
# Run only graphics tests
python run_tests.py --pattern "*graphics*"

# Run only unit tests
python run_tests.py --directory tests/unit
```

## Debugging Failed Tests

### Verbose Output
Use `-v` flag for detailed failure information:
```bash
python run_tests.py -v
```

### Individual Test Debugging
Run individual test files to focus on specific failures:
```python
python tests/unit/test_graphics_commands.py
```

### Common Failure Patterns
1. **Type Mismatches**: Check expected vs. actual output types
2. **Precision Issues**: Floating point comparison problems
3. **Missing Features**: Commands not yet implemented
4. **Timing Issues**: Race conditions in complex tests

## Contributing

### Adding New Tests
1. Create test file in appropriate directory
2. Follow naming convention (`test_*.py`)
3. Use base framework and utilities
4. Run test runner to verify integration
5. Update this documentation

### Test Quality Guidelines
- Each test should test one specific behavior
- Include both success and failure cases
- Use descriptive assertions with clear messages
- Avoid testing implementation details
- Focus on user-visible behavior

## Test Infrastructure Files
- `test_base.py` - Core testing framework
- `run_tests.py` - Test discovery and execution
- `test_utilities.py` - Testing utilities and helpers
- `tests/README.md` - This documentation

The test suite provides a solid foundation for validating the TRS-80 Color Computer BASIC emulator functionality and ensuring quality as new features are added.