"""File I/O argument parsing (task #76): file-number expressions containing
commas, and array targets for LINE INPUT."""

import os


def run(basic, helpers, lines):
    helpers.load_program(basic, lines)
    results = helpers.run_to_completion(basic)
    return helpers.get_text_output(results), helpers.get_error_messages(results)


def test_file_number_expression_with_comma(basic, helpers, temp_programs_dir):
    texts, errors = run(basic, helpers, [
        '10 DIM F(2,2): F(1,2)=3',
        '20 OPEN "O",#3,"OUT.TXT"',
        '30 PRINT #F(1,2),5',
        '35 PRINT #F(1,2),"SECOND LINE"',
        '40 CLOSE #3',
        '50 OPEN "I",#F(1,2),"OUT.TXT"',
        '60 INPUT #F(1,2),A',
        '70 LINE INPUT #F(1,2),B$',
        '80 PRINT A;B$',
    ])
    assert errors == [], errors
    assert ' '.join(texts).split() == ['5', 'SECOND', 'LINE']


def test_file_number_comma_helper():
    from emulator.file_io import FileIOManager
    assert FileIOManager._file_number_comma('1, A') == 1
    assert FileIOManager._file_number_comma('F(1,2),A') == 6
    assert FileIOManager._file_number_comma('1') == -1
    assert FileIOManager._file_number_comma('N("A,B"),X') == 8


def test_line_input_into_array_element(basic, helpers):
    helpers.load_program(basic, ['10 DIM A$(5)', '20 LINE INPUT A$(3)', '30 PRINT A$(3)'])
    result = basic.process_command('RUN')
    request = next(r for r in result if r.get('type') == 'input_request')
    assert request['array'] is True and request['indices'] == [3]
    basic.store_input_value(basic.input_variables[0], 'HELLO, WORLD')
    basic.clear_input_state()
    output = basic.continue_program_execution()
    assert helpers.get_text_output(output) == ['HELLO, WORLD']
