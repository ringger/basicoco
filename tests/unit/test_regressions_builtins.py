"""Regression tests for built-in functions, DATA/READ, DIM, file I/O and the
filesystem sandbox (Sept 2026 audit). Each test names its task number.
"""

import os

import pytest


def run(basic, helpers, lines):
    helpers.load_program(basic, lines)
    results = helpers.run_to_completion(basic)
    return helpers.get_text_output(results), helpers.get_error_messages(results)


def printed(basic, helpers, expr):
    result = basic.process_command(f'PRINT {expr}')
    return ' '.join(helpers.get_text_output(result)).split(), helpers.get_error_messages(result)


class TestRnd:
    """#4: RND(0) is a fresh value in [0,1); fractional args are not Python errors."""

    def test_rnd_zero_returns_fraction(self, basic, helpers):
        values = [basic.evaluate_expression('RND(0)') for _ in range(20)]
        assert all(0 <= v < 1 for v in values)
        assert len(set(values)) > 1

    def test_rnd_fractional_argument(self, basic, helpers):
        out, errors = printed(basic, helpers, 'RND(0.5)')
        assert not any('randrange' in e for e in errors), errors

    def test_rng_is_per_interpreter(self, helpers):
        from emulator.core import CoCoBasic
        a, b = CoCoBasic(), CoCoBasic()
        a.process_command('X=RND(-7)')
        first = [a.evaluate_expression('RND(100)') for _ in range(5)]
        a.process_command('X=RND(-7)')
        b.evaluate_expression('RND(100)')  # another session drawing numbers
        second = [a.evaluate_expression('RND(100)') for _ in range(5)]
        assert first == second


class TestInt:
    """#5: INT rounds toward negative infinity."""

    @pytest.mark.parametrize('arg,expected', [('-3.5', '-4'), ('-0.1', '-1'), ('3.7', '3'), ('-2', '-2')])
    def test_int_floor(self, basic, helpers, arg, expected):
        out, errors = printed(basic, helpers, f'INT({arg})')
        assert errors == []
        assert out == [expected]


class TestDataRead:
    """#6: empty DATA items read as 0/""; READ checks types and case."""

    def test_empty_data_item(self, basic, helpers):
        texts, errors = run(basic, helpers, [
            '10 DATA 1,,"X",HELLO WORLD',
            '20 READ A,B,C$,D$',
            '30 PRINT A;B;C$;D$',
        ])
        assert errors == []
        assert ' '.join(texts).split() == ['1', '0', 'XHELLO', 'WORLD']

    def test_read_string_into_numeric_is_type_mismatch(self, basic, helpers):
        texts, errors = run(basic, helpers, ['10 DATA ABC', '20 READ N', '30 PRINT N*2'])
        assert errors and 'TYPE' in errors[0].upper(), (texts, errors)

    def test_read_lowercase_variable_name(self, basic, helpers):
        texts, errors = run(basic, helpers, ['10 DATA 5', '20 read n', '30 PRINT N'])
        assert errors == []
        assert ' '.join(texts).split() == ['5']


class TestVal:
    """#9: VAL parses the leading numeric prefix, MS BASIC style."""

    @pytest.mark.parametrize('arg,expected', [
        ('"12ABC"', '12'), ('"1 2"', '12'), ('"&HFF"', '255'), ('"1_000"', '1'),
        ('"  -3.5"', '-3.5'), ('"ABC"', '0'),
    ])
    def test_val_prefix(self, basic, helpers, arg, expected):
        out, errors = printed(basic, helpers, f'VAL({arg})')
        assert errors == []
        assert out == [expected]


class TestDim:
    """#10: DIM A(0) is legal; undimensioned arrays auto-dimension to 10."""

    def test_dim_zero(self, basic, helpers):
        texts, errors = run(basic, helpers, ['10 DIM A(0)', '20 A(0)=5', '30 PRINT A(0)'])
        assert errors == []
        assert ' '.join(texts).split() == ['5']

    def test_auto_dimension(self, basic, helpers):
        texts, errors = run(basic, helpers, ['10 B(3)=7', '20 PRINT B(3);B(10)'])
        assert errors == []
        assert ' '.join(texts).split() == ['7', '0']

    def test_auto_dimension_limit(self, basic, helpers):
        texts, errors = run(basic, helpers, ['10 B(11)=7'])
        assert errors

    def test_huge_dim_is_rejected(self, basic, helpers):
        texts, errors = run(basic, helpers, ['10 DIM A(10000,10000)'])
        assert errors, 'a 100-million-element array should be refused'


class TestStringDollar:
    """#12: STRING$ validates its character code."""

    @pytest.mark.parametrize('args', ['3,-1', '3,300', '3,""'])
    def test_invalid_char_code_is_error(self, basic, helpers, args):
        out, errors = printed(basic, helpers, f'STRING$({args})')
        assert errors, out
        assert 'chr()' not in errors[0]


class TestStringFunctionStrictness:
    """#12: CoCo raises ?FC for INSTR start 0 and ?TM for LEN of a number."""

    def test_instr_start_zero_is_fc(self, basic, helpers):
        out, errors = printed(basic, helpers, 'INSTR(0,"ABC","B")')
        assert errors and 'ILLEGAL FUNCTION CALL' in errors[0]

    def test_instr_start_one_ok(self, basic, helpers):
        assert printed(basic, helpers, 'INSTR(1,"ABC","B")') == (['2'], [])

    def test_len_of_number_is_type_mismatch(self, basic, helpers):
        out, errors = printed(basic, helpers, 'LEN(12345)')
        assert errors and 'TYPE MISMATCH' in errors[0]

    def test_len_of_string_ok(self, basic, helpers):
        assert printed(basic, helpers, 'LEN("12345")') == (['5'], [])


class TestTypeMismatch:
    """#45: mixing strings and numbers is ?TM, as on the CoCo, never a Python
    message or Python semantics ("A"*2 was "AA")."""

    @pytest.mark.parametrize('expr', [
        '"A" + 1', '1 + "A"', '"A" - 1', '"A" * 2', '2 * "A"', '"A" / 2', '"A" ^ 2',
        '"A" MOD 2', '"A" < 1', '1 = "A"', '-"A"', 'NOT "A"', '"A" AND 1', '1 OR "A"',
    ])
    def test_mixed_operands_are_type_mismatch(self, basic, helpers, expr):
        out, errors = printed(basic, helpers, expr)
        assert errors and 'TYPE MISMATCH' in errors[0], (out, errors)

    @pytest.mark.parametrize('expr,expected', [
        ('"AB" + "CD"', ['ABCD']), ('"A" < "B"', ['-1']), ('"B" < "A"', ['0']),
        ('"A" = "A"', ['-1']), ('"A" <> "B"', ['-1']), ('2 * 3', ['6']),
    ])
    def test_same_type_operands_still_work(self, basic, helpers, expr, expected):
        assert printed(basic, helpers, expr) == (expected, [])

    @pytest.mark.parametrize('statement', [
        'A = "X"', 'A$ = 5', 'N(1) = "S"', 'S$(1) = 7',
    ])
    def test_assignment_type_mismatch(self, basic, helpers, statement):
        errors = helpers.get_error_messages(basic.process_command(statement))
        assert errors and 'TYPE MISMATCH' in errors[0], errors

    @pytest.mark.parametrize('statement', ['FOR A$=1 TO 3', 'FOR I="1" TO 3', 'FOR I=1 TO 3 STEP "1"'])
    def test_for_with_strings_is_type_mismatch(self, basic, helpers, statement):
        errors = helpers.get_error_messages(basic.process_command(statement))
        assert errors and 'TYPE MISMATCH' in errors[0], errors

    def test_line_input_into_numeric_is_type_mismatch(self, basic, helpers):
        out, errors = run(basic, helpers, ['10 LINE INPUT A', '20 END'])
        assert errors and 'TYPE MISMATCH' in errors[0], errors

    def test_assignment_type_mismatch_in_program_is_trappable(self, basic, helpers):
        out, errors = run(basic, helpers, [
            '10 ON ERROR GOTO 100', '20 A = "X"', '30 END',
            '100 PRINT "ERR"; ERR: END'])
        assert errors == [] and ' '.join(out).split() == ['ERR', '13']


class TestFileIoErrors:
    """#7: file errors are BASIC errors with correct wording."""

    def test_print_to_input_file_message(self, basic, helpers, temp_programs_dir):
        with open(os.path.join('programs', 'IN.TXT'), 'w') as f:
            f.write('1\n')
        texts, errors = run(basic, helpers, ['10 OPEN "I",#1,"IN.TXT"', '20 PRINT #1,"X"'])
        assert errors
        # PRINT# to an input file: the problem is that we can't WRITE to it.
        assert 'cannot read' not in errors[0].lower(), errors
        assert 'write' in errors[0].lower(), errors

    def test_open_directory_is_basic_error(self, basic, helpers, temp_programs_dir):
        result = basic.process_command('OPEN "I",#5,"."')
        assert helpers.get_error_messages(result)

    def test_input_hash_bad_subscript_is_error(self, basic, helpers, temp_programs_dir):
        with open(os.path.join('programs', 'NUMS.TXT'), 'w') as f:
            f.write('4\n')
        texts, errors = run(basic, helpers, [
            '10 DIM Z(2)', '20 OPEN "I",#1,"NUMS.TXT"', '30 INPUT #1,Z(9)', '40 PRINT "NO ERROR"',
        ])
        assert errors, texts

    def test_eof_true_with_only_blank_lines_left(self, basic, helpers, temp_programs_dir):
        with open(os.path.join('programs', 'BLANK.TXT'), 'w') as f:
            f.write('1\n\n')
        texts, errors = run(basic, helpers, [
            '10 OPEN "I",#1,"BLANK.TXT"', '20 INPUT #1,A', '30 PRINT EOF(1)',
        ])
        assert errors == []
        assert ' '.join(texts).split() == ['-1']


class TestSandbox:
    """#1, #3, #11: BASIC file commands stay inside the programs directory."""

    @pytest.fixture
    def outside(self, temp_programs_dir):
        """A directory next to (outside) the sandboxed programs/ dir."""
        path = os.path.join(os.path.dirname(temp_programs_dir), 'outside')
        os.makedirs(path)
        return path

    def test_open_output_absolute_path_refused(self, basic, helpers, outside):
        target = os.path.join(outside, 'abs.txt')
        texts, errors = run(basic, helpers, [f'10 OPEN "O",#1,"{target}"', '20 PRINT #1,"X"', '30 CLOSE #1'])
        assert not os.path.exists(target)
        assert errors

    def test_open_output_parent_traversal_refused(self, basic, helpers, outside):
        texts, errors = run(basic, helpers, ['10 OPEN "O",#1,"../outside/trav.txt"', '20 CLOSE #1'])
        assert not os.path.exists(os.path.join(outside, 'trav.txt'))
        assert errors

    def test_open_input_system_file_refused(self, basic, helpers, temp_programs_dir):
        texts, errors = run(basic, helpers, ['10 OPEN "I",#1,"/etc/hosts"', '20 LINE INPUT #1,A$'])
        assert errors

    def test_save_absolute_path_refused(self, basic, helpers, outside):
        basic.process_command('10 PRINT "X"')
        target = os.path.join(outside, 'absprog')
        result = basic.process_command(f'SAVE "{target}"')
        assert not os.path.exists(target + '.bas')
        assert helpers.get_error_messages(result)

    def test_save_parent_traversal_refused(self, basic, helpers, outside):
        basic.process_command('10 PRINT "X"')
        result = basic.process_command('SAVE "../outside/relprog"')
        assert not os.path.exists(os.path.join(outside, 'relprog.bas'))
        assert helpers.get_error_messages(result)

    def test_kill_outside_sandbox_refused(self, basic, helpers, outside):
        victim = os.path.join(outside, 'victim.bas')
        with open(victim, 'w') as f:
            f.write('10 PRINT "KEEP"\n')
        result = basic.process_command(f'KILL "{victim[:-4]}"')
        assert not any(r.get('type') == 'input_request' for r in result)
        assert os.path.exists(victim)

    def test_cd_does_not_change_process_directory(self, basic, helpers, temp_programs_dir):
        before = os.getcwd()
        basic.process_command('CD "/"')
        assert os.getcwd() == before

    def test_save_evaluates_string_variable_filename(self, basic, helpers, temp_programs_dir):
        basic.process_command('10 PRINT "X"')
        basic.process_command('F$="EXPRNAME"')
        basic.process_command('SAVE F$')
        assert os.path.exists(os.path.join(temp_programs_dir, 'EXPRNAME.bas'))
        assert not os.path.exists(os.path.join(temp_programs_dir, 'F$.bas'))


class TestKillConfirmationProtocol:
    """#2: the server must not delete a filename supplied by the client."""

    def test_forged_kill_confirmation_does_not_delete(self, temp_programs_dir):
        from app import app, socketio
        victim = os.path.join(os.path.dirname(temp_programs_dir), 'victim.txt')
        with open(victim, 'w') as f:
            f.write('keep me')
        client = socketio.test_client(app)
        try:
            client.emit('input_response',
                        {'variable': '_kill_confirm', 'value': 'Y', 'filename': victim})
        finally:
            client.disconnect()
        assert os.path.exists(victim)
