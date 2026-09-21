"""CHAIN from a running program continues in the same execution loop
(task #20): no nested run, so INPUT in the chained program resumes correctly
and a program can CHAIN itself repeatedly without hitting recursion limits."""

import os


def write(programs_dir, name, lines):
    with open(os.path.join(programs_dir, f'{name}.bas'), 'w') as f:
        f.write('\n'.join(lines) + '\n')


def test_input_in_chained_program_resumes(basic, helpers, temp_programs_dir):
    write(temp_programs_dir, 'second', ['100 PRINT "IN B"', '200 INPUT N', '300 PRINT "GOT";N'])
    helpers.load_program(basic, ['10 PRINT "IN A"', '20 CHAIN "second"'])
    result = basic.process_command('RUN')
    assert any(r.get('type') == 'input_request' for r in result), result
    basic.store_input_value(basic.input_variables[0], '7')
    basic.clear_input_state()
    output = basic.continue_program_execution()
    assert helpers.get_error_messages(output) == []
    assert ' '.join(helpers.get_text_output(output)).split() == ['GOT', '7']


def test_self_chain_many_times(basic, helpers, temp_programs_dir):
    write(temp_programs_dir, 'loop', [
        '10 C=C+1',
        '20 IF C<500 THEN CHAIN "loop", ALL',
        '30 PRINT "DONE";C',
    ])
    basic.process_command('LOAD "loop"')
    results = helpers.run_to_completion(basic)
    assert helpers.get_error_messages(results) == []
    assert ' '.join(helpers.get_text_output(results)).split() == ['DONE', '500']


def test_chain_to_line_number(basic, helpers, temp_programs_dir):
    write(temp_programs_dir, 'target', ['100 PRINT "SKIPPED"', '200 PRINT "START HERE"'])
    helpers.load_program(basic, ['10 CHAIN "target", 200'])
    results = helpers.run_to_completion(basic)
    assert helpers.get_text_output(results) == ['START HERE']


def test_chain_restarts_data(basic, helpers, temp_programs_dir):
    write(temp_programs_dir, 'data2', ['100 DATA 9', '110 READ X: PRINT X'])
    helpers.load_program(basic, ['10 DATA 1', '20 READ A', '30 CHAIN "data2"'])
    results = helpers.run_to_completion(basic)
    assert helpers.get_error_messages(results) == []
    assert ' '.join(helpers.get_text_output(results)).split() == ['9']
