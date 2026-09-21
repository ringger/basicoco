"""#87: Color BASIC's machine-language words say they're unsupported,
instead of acting as arrays (USR(1) was 0, PEEK(100) was BAD SUBSCRIPT)
or unknown commands."""

import pytest


def errors(helpers, result):
    return '\n'.join(helpers.get_error_messages(result))


@pytest.mark.parametrize('word, statement', [
    ('PEEK', 'PRINT PEEK(100)'),
    ('VARPTR', 'X=VARPTR(A)'),
    ('USR', 'X=USR(1)'),
    ('USR', 'X=USR3(1)'),
    ('POKE', 'POKE 1024,65'),
    ('EXEC', 'EXEC 100'),
])
def test_each_word_says_it_is_not_supported(basic, helpers, word, statement):
    message = errors(helpers, basic.process_command(statement))
    assert f'{word} is not supported in BasiCoCo' in message, message
    assert 'X' not in basic.variables


@pytest.mark.parametrize('name', ['PEEK', 'VARPTR', 'USR'])
def test_the_words_are_reserved(basic, helpers, name):
    assert 'reserved' in errors(helpers, basic.process_command(f'DIM {name}(5)'))


def test_on_error_traps_it_as_illegal_function_call(basic, helpers):
    helpers.load_program(basic, ['10 ON ERROR GOTO 100', '20 POKE 1,1', '30 END',
                                 '100 PRINT ERR: END'])
    assert helpers.get_text_output(basic.process_command('RUN')) == [' 5 ']
