"""Tests for comments (REM / '), block-IF detection and crunched spacing
that used to be misparsed by string heuristics (task #73)."""

import pytest


def run(basic, helpers, lines):
    helpers.load_program(basic, lines)
    results = helpers.run_to_completion(basic)
    return helpers.get_text_output(results), helpers.get_error_messages(results)


class TestApostropheComments:
    def test_colon_inside_comment_is_not_a_statement(self, basic, helpers):
        texts, errors = run(basic, helpers, ['10 A=1 \' NOTE: PRINT "LEAK"', '20 PRINT A'])
        assert errors == []
        assert texts == [' 1 ']

    def test_else_inside_comment_is_ignored(self, basic, helpers):
        texts, errors = run(basic, helpers, [
            '10 A=0', '20 IF A=1 THEN PRINT "Y" \' ELSE PRINT "N"', '30 PRINT "END"'])
        assert errors == []
        assert texts == ['END']

    @pytest.mark.parametrize('line', [
        "10 DIM A(5) ' arrays, etc",
        "10 FOR I=1 TO 1 ' loop: here",
        "10 X=5 ' set x",
    ])
    def test_comment_after_statement(self, basic, helpers, line):
        lines = [line, '20 NEXT I'] if 'FOR' in line else [line]
        texts, errors = run(basic, helpers, lines + ['30 PRINT "OK"'])
        assert errors == []
        assert 'OK' in texts

    def test_whole_line_comment(self, basic, helpers):
        texts, errors = run(basic, helpers, ["10 ' comment: with colon", '20 PRINT "X"'])
        assert errors == []
        assert texts == ['X']

    def test_single_quoted_filename_still_works(self, basic, helpers, temp_programs_dir):
        basic.process_command('10 PRINT 1')
        result = basic.process_command("SAVE 'quoted_name'")
        assert helpers.get_error_messages(result) == []


class TestRemPrefix:
    def test_remark_is_a_comment(self, basic, helpers):
        texts, errors = run(basic, helpers, ['10 A=1:REMARK:PRINT "X"', '20 PRINT "Y"'])
        assert errors == []
        assert texts == ['Y']


class TestBlockIfDetection:
    @pytest.mark.parametrize('if_line', [
        '20 IF(A=1)THEN',
        '20 IF A=1 THEN REM block if',
        "20 IF A=1 THEN ' block if",
    ])
    def test_block_if_variants_respect_condition(self, basic, helpers, if_line):
        texts, errors = run(basic, helpers, [
            '10 A=0', if_line, '30 PRINT "YES"', '40 ENDIF', '50 PRINT "DONE"'])
        assert errors == []
        assert texts == ['DONE']

    def test_then_inside_string_is_missing_then(self, basic, helpers):
        errors = helpers.get_error_messages(basic.process_command('IF A$="THEN" PRINT 1'))
        assert errors and 'THEN' in errors[0]


class TestErrorCodes:
    @pytest.mark.parametrize('message,code', [
        ('TYPE MISMATCH: cannot READ "SYNTAX" (line 10) into numeric A', 13),
        ('SYNTAX ERROR: Unexpected token at line 10', 1),
        ('Division by zero at line 20', 99),
        ('BAD SUBSCRIPT at line 5\nSuggestions:\n  - SYNTAX example', 9),
        ('OUT OF DATA at line 3', 4),
        ('something unknown', 0),
    ])
    def test_classify(self, message, code):
        from emulator.program_executor import _classify_error
        assert _classify_error(message) == code

    def test_err_not_confused_by_data_contents(self, basic, helpers):
        texts, errors = run(basic, helpers, [
            '10 ON ERROR GOTO 100', '20 DATA SYNTAX', '30 READ A', '40 END', '100 PRINT ERR',
        ])
        assert errors == []
        assert ' '.join(texts).split() == ['13']


class TestCrunchedSpacing:
    def test_crunched_line_number(self, basic, helpers):
        basic.process_command('10PRINT "HI"')
        assert basic.program == {10: 'PRINT "HI"'}

    def test_hex_and_octal_data(self, basic, helpers):
        texts, errors = run(basic, helpers, ['10 DATA &HFF,&O17,5', '20 READ A,B,C', '30 PRINT A;B;C'])
        assert errors == []
        assert ' '.join(texts).split() == ['255', '15', '5']

    def test_crunched_data(self, basic, helpers):
        texts, errors = run(basic, helpers, ['10 DATA"A","B"', '20 READ X$,Y$', '30 PRINT X$;Y$'])
        assert errors == []
        assert texts == ['AB']

    def test_line_input_with_extra_space(self, basic, helpers):
        result = basic.process_command('LINE  INPUT A$')
        assert any(r.get('type') == 'input_request' for r in result), result

    def test_loop_while_with_parenthesis(self, basic, helpers):
        texts, errors = run(basic, helpers, ['10 X=0', '20 DO', '30 X=X+1', '40 LOOP WHILE(X<3)', '50 PRINT X'])
        assert errors == []
        assert texts == [' 3 ']

    def test_loop_with_unknown_argument_is_error(self, basic, helpers):
        texts, errors = run(basic, helpers, ['10 DO', '20 LOOP FOREVER'])
        assert errors and 'WHILE or UNTIL' in errors[0], errors
