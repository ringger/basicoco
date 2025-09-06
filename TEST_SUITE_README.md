# TRS-80 Color Computer BASIC Emulator - Test Suite

## Overview
This document describes the comprehensive test suite created for the TRS-80 Color Computer BASIC emulator. The test suite provides structured, automated testing with detailed reporting and utilities for validating emulator functionality.

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

#### Usage
```bash
# Run all tests
python run_tests.py

# Run with verbose output
python run_tests.py -v

# Run tests in specific directory
python run_tests.py --directory tests

# Stop on first failure
python run_tests.py --stop-on-failure
```

### 3. Test Utilities (`test_utilities.py`)
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
- `TEST_SUITE_README.md` - This documentation

The test suite provides a solid foundation for validating the TRS-80 Color Computer BASIC emulator functionality and ensuring quality as new features are added.