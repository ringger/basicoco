"""Regression tests for parser / AST-converter / evaluator bugs (Sept 2026 audit).

Each test names its task number. Expected values follow Microsoft-derived
Color BASIC semantics wherever the dialect is unambiguous; dialect-dependent
questions (MOD, number formatting) are left out until the target is decided.
"""

import pytest


def run(basic, helpers, lines):
    helpers.load_program(basic, lines)
    results = helpers.run_to_completion(basic)
    return helpers.get_text_output(results), helpers.get_error_messages(results)


def words(texts):
    return ' '.join(texts).split()


class TestSameLineLoopClosers:
    """#36: statements after NEXT/WEND/LOOP on the same line run once."""

    def test_statement_after_next(self, basic, helpers):
        texts, errors = run(basic, helpers, ['10 FOR I=1 TO 3: PRINT I: NEXT I: PRINT "DONE"'])
        assert errors == []
        assert words(texts) == ['1', '2', '3', 'DONE']

    def test_statement_after_wend(self, basic, helpers):
        texts, errors = run(basic, helpers, ['10 X=0: WHILE X<3: X=X+1: WEND: PRINT "DONE";X'])
        assert errors == []
        assert words(texts) == ['DONE', '3']

    def test_statement_after_loop_until(self, basic, helpers):
        texts, errors = run(basic, helpers, ['10 X=0: DO: X=X+1: LOOP UNTIL X=3: PRINT "DONE";X'])
        assert errors == []
        assert words(texts) == ['DONE', '3']

    def test_nested_for_on_one_line(self, basic, helpers):
        texts, errors = run(basic, helpers,
                            ['10 FOR I=1 TO 2: FOR J=1 TO 2: PRINT I;J: NEXT J: NEXT I'])
        assert errors == []
        assert words(texts) == ['1', '1', '1', '2', '2', '1', '2', '2']

    def test_nested_for_on_one_line_writes_array(self, basic, helpers):
        texts, errors = run(basic, helpers, [
            '10 DIM C(1,2)',
            '20 FOR M=0 TO 1: FOR J=0 TO 2: C(M,J)=M*10+J: NEXT J: NEXT M',
            '30 PRINT C(1,2)',
        ])
        assert errors == []
        assert words(texts) == ['12']


class TestConverterParentheses:
    """#37: expressions in converted single-line bodies keep their grouping."""

    @pytest.mark.parametrize('expr,expected', [
        ('10-(5-2)', '7'),
        ('-(2+3)', '-5'),
        ('12/(2*3)', '2'),
        ('(2^3)^2', '64'),
        ('2*(3+4)', '14'),
    ])
    def test_grouping_preserved_in_if_body(self, basic, helpers, expr, expected):
        texts, errors = run(basic, helpers, [f'10 IF 1 THEN X={expr}: PRINT X'])
        assert errors == []
        assert words(texts) == [expected]

    def test_not_of_comparison_in_if_body(self, basic, helpers):
        texts, errors = run(basic, helpers, ['10 A=3', '20 IF 1 THEN X=NOT (A=5): PRINT X'])
        assert errors == []
        assert words(texts) == ['-1']


class TestCrunchedThen:
    """#38: THEN without surrounding spaces still guards the whole line."""

    def test_string_comparison_then_without_space(self, basic, helpers):
        texts, errors = run(basic, helpers, ['10 A$="Y"', '20 IF A$="X"THEN PRINT "1": PRINT "2"'])
        assert errors == []
        assert texts == []

    def test_number_then_without_space(self, basic, helpers):
        texts, errors = run(basic, helpers, ['10 A=1', '20 IF A=0THEN PRINT "X": PRINT "Y"'])
        assert errors == []
        assert texts == []


class TestExponentiation:
    """#39: ^ is float-valued, left-associative, and can't hang the server."""

    def test_power_tower_is_bounded(self, basic, helpers):
        # 9^9^9 must not attempt a 370-million-digit integer.
        result = basic.process_command('PRINT 9^9^9')
        assert isinstance(result, list)

    def test_left_associative(self, basic, helpers):
        texts = helpers.get_text_output(basic.process_command('PRINT 2^3^2'))
        assert words(texts) == ['64']

    def test_unary_minus_binds_looser_than_power(self, basic, helpers):
        texts = helpers.get_text_output(basic.process_command('PRINT -2^2'))
        assert words(texts) == ['-4']

    def test_float_overflow_is_basic_error(self, basic, helpers):
        result = basic.process_command('PRINT 10.0^400')
        errors = helpers.get_error_messages(result)
        assert errors and 'OVERFLOW' in errors[0].upper()

    def test_float_overflow_in_program_is_trappable(self, basic, helpers):
        texts, errors = run(basic, helpers, [
            '10 ON ERROR GOTO 100', '20 X=10.0^400', '30 END', '100 PRINT "TRAPPED"',
        ])
        assert errors == []
        assert 'TRAPPED' in ' '.join(texts)

    def test_multiplication_overflow_is_error_not_inf(self, basic, helpers):
        result = basic.process_command('PRINT 1E308*10')
        assert 'inf' not in ' '.join(helpers.get_text_output(result)).lower()
        assert helpers.get_error_messages(result)

    def test_negative_base_fractional_power_is_function_call_error(self, basic, helpers):
        result = basic.process_command('PRINT (-8)^(1/3)')
        assert 'j' not in ' '.join(helpers.get_text_output(result))
        assert helpers.get_error_messages(result)


class TestNotPrecedence:
    """#40: NOT has lower precedence than the relational operators."""

    def test_not_applies_to_whole_comparison(self, basic, helpers):
        basic.process_command('A=3')
        texts = helpers.get_text_output(basic.process_command('PRINT NOT A=5'))
        assert words(texts) == ['-1']


class TestStrictParsing:
    """#41: leftover tokens and unknown characters are syntax errors."""

    @pytest.mark.parametrize('stmt', ['X=5 6', 'PRINT 1 2', 'PRINT 1E', 'PRINT 1.2.3'])
    def test_trailing_garbage_is_syntax_error(self, basic, helpers, stmt):
        result = basic.process_command(stmt)
        errors = helpers.get_error_messages(result)
        assert errors, f'{stmt!r} should be a syntax error, got {result}'
        assert 'could not convert' not in errors[0]

    def test_hex_literal(self, basic, helpers):
        texts = helpers.get_text_output(basic.process_command('PRINT &HFF'))
        assert words(texts) == ['255']


class TestConverterRemAndElse:
    """#42: REM ends the line inside bodies; ELSE binds to the nearest IF."""

    def test_rem_colon_in_if_body(self, basic, helpers):
        texts, errors = run(basic, helpers, ['10 IF 1 THEN PRINT "A": REM X: PRINT "B"'])
        assert errors == []
        assert words(texts) == ['A']

    @pytest.mark.parametrize('a,b,expected', [(1, 0, ['2']), (0, 0, []), (1, 1, ['1'])])
    def test_else_binds_to_inner_if(self, basic, helpers, a, b, expected):
        texts, errors = run(basic, helpers, [
            f'10 A={a}: B={b}',
            '20 IF A THEN IF B THEN PRINT 1 ELSE PRINT 2',
        ])
        assert errors == []
        assert words(texts) == expected


class TestBlockEvaluation:
    """#47: a multi-statement block (BlockNode) must stop at the first
    control-flow directive, error or INPUT request."""

    def visit(self, basic, code):
        return basic.ast_evaluator.visit(basic.ast_parser.parse_statement(code))

    @pytest.mark.parametrize('code,stop_type', [
        ('GOTO 100: PRINT "AFTER"', 'jump'),
        ('PRINT Q(20): PRINT "AFTER"', 'error'),
        ('INPUT A: PRINT "AFTER"', 'input_request'),
    ])
    def test_block_stops_at_directive(self, basic, helpers, code, stop_type):
        basic.process_command('100 END')
        result = self.visit(basic, code)
        assert result[-1]['type'] == stop_type
        assert 'AFTER' not in ' '.join(helpers.get_text_output(result))

    def test_block_stops_at_exit_for(self, basic, helpers):
        basic.process_command('FOR I=1 TO 2')
        result = self.visit(basic, 'EXIT FOR: PRINT "AFTER"')
        assert result[-1]['type'] == 'exit_for_loop'
        assert 'AFTER' not in ' '.join(helpers.get_text_output(result))

    def test_block_runs_all_plain_statements(self, basic, helpers):
        result = self.visit(basic, 'PRINT "A": PRINT "B"')
        assert words(helpers.get_text_output(result)) == ['A', 'B']


class TestElseTargetValidation:
    """#47: ELSE <line> must validate the target like THEN <line>."""

    def test_else_to_missing_line_is_undefined_line(self, basic, helpers):
        texts, errors = run(basic, helpers, ['10 IF 0 THEN 20 ELSE 999', '20 END'])
        assert errors and 'UNDEFINED LINE' in errors[0]


class TestExpressionCache:
    """#46: array reads must not grow the expression cache per index value."""

    def test_array_reads_do_not_fill_cache(self, basic, helpers):
        run(basic, helpers, ['10 DIM A(2000)', '20 FOR I=0 TO 2000: X=A(I): NEXT I'])
        assert len(basic._expr_cache) < 100
