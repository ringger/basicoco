"""
Tests for INPUT followed by program continuation.

These tests verify that continue_program_execution() correctly handles
flow-control items (skip_if_block, skip_else_block, exit_for_loop,
jump_after_while, skip_do_loop, jump_after_do) after resuming from
an INPUT pause, and that INPUT into array elements works end-to-end.
"""

import pytest


def run_with_inputs(basic, program_lines, input_values):
    """Load a program, run it, and feed input values through each INPUT pause.

    Returns the combined text output from the entire execution.
    """
    basic.process_command('NEW')
    for line in program_lines:
        basic.process_command(line)

    all_text = []
    input_idx = 0
    output = basic.process_command('RUN')

    while True:
        # Collect text output
        for item in output:
            if item.get('type') == 'text':
                all_text.append(item['text'])
            elif item.get('type') == 'error':
                all_text.append(f"ERROR: {item['message']}")

        # Find input request
        input_req = next((item for item in output if item.get('type') == 'input_request'), None)
        if not input_req:
            break

        # Feed next input value
        assert input_idx < len(input_values), (
            f"Program requested more inputs than provided (got {len(input_values)})"
        )
        value = input_values[input_idx]
        input_idx += 1

        # Store using the variable descriptor from input_variables
        if basic.input_variables:
            var_desc = basic.input_variables[basic.current_input_index]
        else:
            var_desc = input_req.get('variable', '')
        basic.store_input_value(var_desc, value)

        # Handle multi-variable INPUT
        if basic.input_variables:
            basic.current_input_index += 1
            while basic.current_input_index < len(basic.input_variables):
                assert input_idx < len(input_values), (
                    f"Program requested more inputs than provided (got {len(input_values)})"
                )
                var_desc = basic.input_variables[basic.current_input_index]
                value = input_values[input_idx]
                input_idx += 1
                basic.store_input_value(var_desc, value)
                basic.current_input_index += 1
            basic.input_variables = None
            basic.input_prompt = None
            basic.current_input_index = 0

        # Resume
        basic.waiting_for_input = False
        if basic.program_counter is not None and basic.program_counter != (0, 0):
            output = basic.continue_program_execution()
        else:
            break

    return all_text


class TestInputThenIfBlock:
    """INPUT followed by IF/THEN should correctly skip or enter the block."""

    def test_input_then_true_if(self, basic):
        program = [
            '10 INPUT "VAL"; X',
            '20 IF X > 10 THEN PRINT "BIG"',
            '30 PRINT "DONE"',
            '40 END',
        ]
        text = run_with_inputs(basic, program, ['20'])
        assert 'BIG' in text
        assert 'DONE' in text

    def test_input_then_false_if(self, basic):
        program = [
            '10 INPUT "VAL"; X',
            '20 IF X > 10 THEN PRINT "BIG"',
            '30 PRINT "DONE"',
            '40 END',
        ]
        text = run_with_inputs(basic, program, ['5'])
        assert 'BIG' not in text
        assert 'DONE' in text

    def test_input_then_if_else(self, basic):
        program = [
            '10 INPUT "VAL"; X',
            '20 IF X > 10 THEN',
            '30   PRINT "BIG"',
            '40 ELSE',
            '50   PRINT "SMALL"',
            '60 ENDIF',
            '70 PRINT "DONE"',
            '80 END',
        ]
        text = run_with_inputs(basic, program, ['5'])
        assert 'BIG' not in text
        assert 'SMALL' in text
        assert 'DONE' in text

    def test_input_then_if_else_true_branch(self, basic):
        program = [
            '10 INPUT "VAL"; X',
            '20 IF X > 10 THEN',
            '30   PRINT "BIG"',
            '40 ELSE',
            '50   PRINT "SMALL"',
            '60 ENDIF',
            '70 PRINT "DONE"',
            '80 END',
        ]
        text = run_with_inputs(basic, program, ['20'])
        assert 'BIG' in text
        assert 'SMALL' not in text
        assert 'DONE' in text

    def test_input_in_loop_with_if(self, basic):
        """The guess-the-number pattern: INPUT inside a loop with IF checks."""
        program = [
            '10 N = 50',
            '20 INPUT "GUESS"; G',
            '30 IF G < N THEN PRINT "LOW": GOTO 20',
            '40 IF G > N THEN PRINT "HIGH": GOTO 20',
            '50 PRINT "CORRECT"',
            '60 END',
        ]
        text = run_with_inputs(basic, program, ['25', '75', '50'])
        assert 'LOW' in text
        assert 'HIGH' in text
        assert 'CORRECT' in text


class TestInputThenWhileLoop:
    """INPUT followed by WHILE/WEND should correctly handle loop control."""

    def test_input_before_while(self, basic):
        program = [
            '10 INPUT "COUNT"; N',
            '20 I = 1',
            '30 WHILE I <= N',
            '40   PRINT I',
            '50   I = I + 1',
            '60 WEND',
            '70 PRINT "DONE"',
            '80 END',
        ]
        text = run_with_inputs(basic, program, ['3'])
        assert ' 1 ' in text
        assert ' 2 ' in text
        assert ' 3 ' in text
        assert 'DONE' in text

    def test_input_inside_while(self, basic):
        program = [
            '10 S = 0',
            '20 WHILE S < 10',
            '30   INPUT "ADD"; V',
            '40   S = S + V',
            '50   PRINT "SUM ="; S',
            '60 WEND',
            '70 PRINT "REACHED 10"',
            '80 END',
        ]
        text = run_with_inputs(basic, program, ['3', '4', '5'])
        combined = ' '.join(text)
        assert 'REACHED 10' in combined


class TestInputThenDoLoop:
    """INPUT followed by DO/LOOP should correctly handle loop control."""

    def test_input_inside_do_loop(self, basic):
        program = [
            '10 S = 0',
            '20 DO',
            '30   INPUT "VAL"; X',
            '40   S = S + X',
            '50   PRINT "SUM ="; S',
            '60 LOOP WHILE S < 10',
            '70 PRINT "DONE"',
            '80 END',
        ]
        text = run_with_inputs(basic, program, ['3', '4', '5'])
        combined = ' '.join(text)
        assert 'DONE' in combined


class TestInputThenExitFor:
    """INPUT followed by EXIT FOR should correctly skip to after NEXT."""

    def test_input_with_exit_for(self, basic):
        program = [
            '10 FOR I = 1 TO 100',
            '20   INPUT "VAL"; X',
            '30   IF X = 0 THEN EXIT FOR',
            '40   PRINT X',
            '50 NEXT I',
            '60 PRINT "DONE"',
            '70 END',
        ]
        text = run_with_inputs(basic, program, ['7', '3', '0'])
        assert ' 7 ' in text
        assert ' 3 ' in text
        assert 'DONE' in text


class TestInputWithArrayVariables:
    """INPUT into array elements should store values at the correct indices."""

    def test_input_into_string_array(self, basic):
        program = [
            '10 DIM N$(3)',
            '20 INPUT "NAME"; N$(1)',
            '30 PRINT "GOT: "; N$(1)',
            '40 END',
        ]
        text = run_with_inputs(basic, program, ['ALICE'])
        combined = ' '.join(text)
        assert 'ALICE' in combined

    def test_input_into_numeric_array(self, basic):
        program = [
            '10 DIM V(3)',
            '20 INPUT "VAL"; V(1)',
            '30 PRINT V(1) * 2',
            '40 END',
        ]
        text = run_with_inputs(basic, program, ['21'])
        assert ' 42 ' in text

    def test_input_into_array_in_loop(self, basic):
        """The bar-chart pattern: INPUT into array elements inside a FOR loop."""
        program = [
            '10 N = 3',
            '20 DIM L$(N), V(N)',
            '30 FOR I = 1 TO N',
            '40   INPUT "LABEL"; L$(I)',
            '50   INPUT "VALUE"; V(I)',
            '60 NEXT I',
            '70 FOR I = 1 TO N',
            '80   PRINT L$(I); " = "; V(I)',
            '90 NEXT I',
            '100 END',
        ]
        text = run_with_inputs(basic, program, [
            'JAN', '10', 'FEB', '25', 'MAR', '15'
        ])
        combined = ' '.join(text)
        assert 'JAN' in combined
        assert 'FEB' in combined
        assert 'MAR' in combined
        assert '10' in combined
        assert '25' in combined
        assert '15' in combined

    def test_input_array_element_with_expression_index(self, basic):
        """INPUT into array element whose index is an expression."""
        program = [
            '10 DIM A(5)',
            '20 I = 2',
            '30 INPUT "VAL"; A(I + 1)',
            '40 PRINT A(3)',
            '50 END',
        ]
        text = run_with_inputs(basic, program, ['99'])
        assert ' 99 ' in text


class TestStoreInputValue:
    """Unit tests for CoCoBasic.store_input_value()."""

    def test_store_simple_numeric(self, basic):
        basic.store_input_value({'name': 'X', 'array': False}, '42')
        assert basic.variables['X'] == 42

    def test_store_simple_float(self, basic):
        basic.store_input_value({'name': 'X', 'array': False}, '3.14')
        assert basic.variables['X'] == 3.14

    def test_store_simple_string(self, basic):
        basic.store_input_value({'name': 'N$', 'array': False}, 'HELLO')
        assert basic.variables['N$'] == 'HELLO'

    def test_store_invalid_numeric_defaults_to_zero(self, basic):
        basic.store_input_value({'name': 'X', 'array': False}, 'abc')
        assert basic.variables['X'] == 0

    def test_store_array_element(self, basic):
        basic.process_command('DIM A(5)')
        basic.store_input_value({'name': 'A', 'array': True, 'indices': [3]}, '77')
        val, err = basic.variable_manager.get_array_element('A', [3])
        assert val == 77

    def test_store_string_array_element(self, basic):
        basic.process_command('DIM N$(5)')
        basic.store_input_value({'name': 'N$', 'array': True, 'indices': [2]}, 'BOB')
        val, err = basic.variable_manager.get_array_element('N$', [2])
        assert val == 'BOB'

    def test_store_legacy_string_variable_name(self, basic):
        """Backwards compatibility: plain string var_desc."""
        basic.store_input_value('X', '10')
        assert basic.variables['X'] == 10

    def test_store_legacy_string_variable_name_string(self, basic):
        basic.store_input_value('N$', 'WORLD')
        assert basic.variables['N$'] == 'WORLD'


class TestInputParserArraySupport:
    """The AST parser should parse INPUT with array subscripts."""

    def test_parse_input_array_variable(self, basic):
        basic.process_command('DIM A(5)')
        result = basic._try_ast_execute('INPUT "VAL"; A(3)')
        assert result is not None
        assert result[0]['type'] == 'input_request'
        assert result[0]['variable'] == 'A'
        assert result[0]['array'] is True
        assert result[0]['indices'] == [3]

    def test_parse_input_string_array_variable(self, basic):
        basic.process_command('DIM N$(5)')
        result = basic._try_ast_execute('INPUT "NAME"; N$(2)')
        assert result is not None
        assert result[0]['type'] == 'input_request'
        assert result[0]['variable'] == 'N$'
        assert result[0]['array'] is True
        assert result[0]['indices'] == [2]

    def test_parse_input_simple_variable_not_array(self, basic):
        result = basic._try_ast_execute('INPUT "VAL"; X')
        assert result is not None
        assert result[0]['type'] == 'input_request'
        assert result[0]['variable'] == 'X'
        assert result[0]['array'] is False

    def test_input_variables_descriptor_has_array_info(self, basic):
        basic.process_command('DIM V(5)')
        basic._try_ast_execute('INPUT "VAL"; V(1)')
        assert len(basic.input_variables) == 1
        desc = basic.input_variables[0]
        assert desc['name'] == 'V'
        assert desc['array'] is True
        assert desc['indices'] == [1]
