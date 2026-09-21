"""Robustness sweep (#86): features that work, tried with awkward inputs.
A test that exposes a bug is marked xfail against the task that fixes it."""

import pytest


def run(basic, helpers, lines, max_frames=5000):
    helpers.load_program(basic, lines)
    results = helpers.run_to_completion(basic, max_frames=max_frames)
    return helpers.get_text_output(results), helpers.get_error_messages(results)


# -- file I/O ------------------------------------------------------------------

class TestFiles:
    @pytest.fixture(autouse=True)
    def _sandbox(self, temp_programs_dir):
        pass

    def test_three_files_open_at_once(self, basic, helpers):
        texts, errors = run(basic, helpers, [
            '10 OPEN "O",#1,"A": OPEN "O",#2,"B": OPEN "O",#3,"C"',
            '20 PRINT #1,"ONE": PRINT #2,"TWO": PRINT #3,"THREE"',
            '30 CLOSE #1: CLOSE #2: CLOSE #3',
            '40 OPEN "I",#1,"A": OPEN "I",#2,"B": OPEN "I",#3,"C"',
            '50 INPUT #3,C$: INPUT #1,A$: INPUT #2,B$',   # read out of order
            '60 PRINT A$;B$;C$: CLOSE'])
        assert errors == [] and texts == ['ONETWOTHREE']

    def test_eof_turns_true_exactly_after_the_last_record(self, basic, helpers):
        texts, errors = run(basic, helpers, [
            '10 OPEN "O",#1,"N": FOR I=1 TO 3: PRINT #1,I: NEXT: CLOSE #1',
            '20 OPEN "I",#1,"N"',
            '30 WHILE NOT EOF(1): INPUT #1,X: PRINT X;: WEND',
            '40 PRINT "EOF=";EOF(1)',
            '50 INPUT #1,X'])
        assert ''.join(texts).split() == ['1', '2', '3', 'EOF=-1']
        assert len(errors) == 1 and 'INPUT PAST END OF FILE: #1' in errors[0]

    def test_a_file_of_thousands_of_lines(self, basic, helpers):
        texts, errors = run(basic, helpers, [
            '10 OPEN "O",#1,"BIG": FOR I=1 TO 5000: PRINT #1,"LINE"+STR$(I): NEXT: CLOSE #1',
            '20 OPEN "I",#1,"BIG": N=0',
            '30 WHILE NOT EOF(1): LINE INPUT #1,L$: N=N+1: WEND: CLOSE #1',
            '40 PRINT N;L$'])
        assert errors == [] and texts == [' 5000 LINE 5000']

    def test_numbers_written_with_semicolons_read_back_separately(self, basic, helpers):
        texts, errors = run(basic, helpers, [
            '10 OPEN "O",#1,"N": PRINT #1,5;6;-3: CLOSE #1',
            '20 OPEN "I",#1,"N": INPUT #1,A,B,C: CLOSE #1',
            '30 PRINT A;B;C'])
        assert errors == [] and texts == [' 5  6 -3 ']

    def test_graph_chart_save_and_load_round_trip(self, basic, helpers):
        """graph_chart.bas's own save (830-850) and load (440-480) lines."""
        texts, errors = run(basic, helpers, [
            '10 NC=2: DIM LB$(2),VL(2): LB$(1)="APPLES": VL(1)=120: LB$(2)="PEARS": VL(2)=-6.5',
            '20 OPEN "O",#1,"CHART": PRINT #1, NC',
            '30 FOR I=1 TO NC: PRINT #1, LB$(I); ","; VL(I): NEXT: CLOSE #1',
            '40 NC=0: LB$(1)="": VL(1)=0: LB$(2)="": VL(2)=0',
            '50 OPEN "I",#1,"CHART": INPUT #1, NC',
            '60 FOR I=1 TO NC: INPUT #1, LB$(I), VL(I): NEXT: CLOSE #1',
            '70 PRINT NC;LB$(1);VL(1);LB$(2);VL(2)'])
        assert errors == [] and texts == [' 2 APPLES 120 PEARS-6.5 ']

    def test_reading_after_close_is_an_error(self, basic, helpers):
        texts, errors = run(basic, helpers, [
            '10 OPEN "O",#1,"M": PRINT #1,"A": PRINT #1,"B": CLOSE #1',
            '20 OPEN "I",#1,"M": INPUT #1,A$: CLOSE #1',
            '30 INPUT #1,B$'])
        assert len(errors) == 1 and 'FILE NOT OPEN: #1' in errors[0]

    def test_reopening_reads_from_the_top(self, basic, helpers):
        texts, errors = run(basic, helpers, [
            '10 OPEN "O",#1,"M": PRINT #1,"A": PRINT #1,"B": CLOSE #1',
            '20 OPEN "I",#1,"M": INPUT #1,A$: CLOSE #1',
            '30 OPEN "I",#1,"M": INPUT #1,B$: CLOSE #1: PRINT A$;B$'])
        assert errors == [] and texts == ['AA']


# -- ON ERROR / RESUME ----------------------------------------------------------

def test_error_in_a_nested_gosub_with_local(basic, helpers):
    texts, errors = run(basic, helpers, [
        '10 ON ERROR GOTO 100: X=1',
        '20 GOSUB 200: PRINT "BACK X=";X: END',
        '100 PRINT "TRAPPED": RESUME NEXT',
        '200 LOCAL X: X=5: GOSUB 300: PRINT "IN SUB X=";X: RETURN',
        '300 Y=1/0: PRINT "AFTER": RETURN'])
    assert errors == []
    assert texts == ['TRAPPED', 'AFTER', 'IN SUB X= 5 ', 'BACK X= 1 ']


def test_resume_next_continues_on_the_same_line(basic, helpers):
    texts, errors = run(basic, helpers, [
        '10 ON ERROR GOTO 100',
        '20 A=1: B=1/0: C=3: PRINT A;C',
        '30 END',
        '100 RESUME NEXT'])
    assert errors == [] and texts == [' 1  3 ']


def test_an_error_inside_the_handler_stops_the_program(basic, helpers):
    texts, errors = run(basic, helpers, [
        '10 ON ERROR GOTO 100', '20 X=1/0', '30 END',
        '100 PRINT "H": Y=1/0: RESUME NEXT'])
    assert texts == ['H']
    assert len(errors) == 1 and 'Division by zero' in errors[0] and 'line 100' in errors[0]


@pytest.mark.xfail(reason='#102: ERR codes mix numbering schemes (/0 is 99)', strict=True)
def test_err_for_division_by_zero_is_a_real_error_code(basic, helpers):
    texts, errors = run(basic, helpers, [
        '10 ON ERROR GOTO 100', '20 X=1/0', '30 END', '100 PRINT ERR: END'])
    assert texts != [' 99 ']


# -- CHAIN ALL ---------------------------------------------------------------

class TestChainAll:
    @pytest.fixture(autouse=True)
    def _sandbox(self, temp_programs_dir):
        pass

    def save(self, basic, helpers, name, lines):
        helpers.load_program(basic, lines)
        basic.process_command(f'SAVE "{name}"')

    def test_arrays_and_open_files_carry_over(self, basic, helpers):
        self.save(basic, helpers, 'PART2', [
            '10 PRINT A(3);B$(2)',
            '20 INPUT #1,L$: PRINT L$: CLOSE #1'])
        texts, errors = run(basic, helpers, [
            '10 OPEN "O",#1,"D": PRINT #1,"FROM FILE": CLOSE #1',
            '20 DIM A(5),B$(5): A(3)=33: B$(2)="BEE"',
            '30 OPEN "I",#1,"D"',
            '40 CHAIN "PART2",ALL'])
        assert errors == [], errors
        assert texts == [' 33 BEE', 'FROM FILE']

    def test_the_error_handler_line_is_the_new_programs(self, basic, helpers):
        # CHAIN ALL keeps variables; the old handler's line number means
        # nothing in the new program, so an error there is not trapped
        self.save(basic, helpers, 'PART2', ['10 X=1/0', '20 PRINT "NOT HERE"'])
        texts, errors = run(basic, helpers, [
            '10 ON ERROR GOTO 100', '20 CHAIN "PART2",ALL',
            '100 PRINT "OLD HANDLER": END'])
        assert 'OLD HANDLER' not in texts
        assert len(errors) == 1 and 'Division by zero' in errors[0]


# -- GOTO out of blocks, repeated -------------------------------------------------

@pytest.mark.parametrize('inner', [
    pytest.param('FOR J=1 TO 5', id='FOR'),
    pytest.param('WHILE 1', id='WHILE'),   # #100: used to leak a frame per pass
    pytest.param('DO', id='DO'),
])
def test_goto_out_of_a_loop_many_times_keeps_stacks_bounded(basic, helpers, inner):
    texts, errors = run(basic, helpers, [
        '10 FOR K=1 TO 2000',
        f'20 {inner}: IF 1 THEN GOTO 40',
        '30 PRINT "NEVER"',
        '40 NEXT K',
        '50 PRINT "DONE"'])
    assert errors == [] and texts == ['DONE']
    depth = len(basic.for_stack) + len(basic.while_stack) + len(basic.do_stack) + len(basic.if_stack)
    assert depth <= 2, (basic.for_stack, basic.while_stack, basic.do_stack, basic.if_stack)


def test_a_recursive_gosub_into_the_same_while_keeps_each_levels_loop(basic, helpers):
    """#100: re-entering a WHILE drops its old frame only within one GOSUB
    level; a recursive call's loop must not end its caller's."""
    texts, errors = run(basic, helpers, [
        '10 D=0: GOSUB 100: PRINT "DONE": END',
        '100 D=D+1: LOCAL I: I=0',
        '110 WHILE I<2: I=I+1: PRINT D;I;: IF D<2 THEN GOSUB 100',
        '120 WEND: D=D-1: RETURN'])
    assert errors == [], errors
    # Depth 1 loops twice and recurses each time; depth 2 loops twice
    assert ''.join(texts).split() == ['1', '1', '2', '1', '2', '2',
                                      '1', '2', '2', '1', '2', '2', 'DONE']


# -- strings -----------------------------------------------------------------------

def test_strings_longer_than_255(basic, helpers):
    # BasiCoCo strings are not limited to Color BASIC's 255 characters
    texts, errors = run(basic, helpers, [
        '10 A$="": FOR I=1 TO 1000: A$=A$+"X": NEXT', '20 PRINT LEN(A$);RIGHT$(A$,3)'])
    assert errors == [] and texts == [' 1000 XXX']


def test_empty_strings(basic, helpers):
    texts, errors = run(basic, helpers, [
        '10 A$="": B$=A$+A$',
        '20 PRINT LEN(B$);"[";MID$(A$,1,1);LEFT$(A$,3);RIGHT$(A$,2);"]";INSTR(A$,"X")'])
    assert errors == [] and texts == [' 0 [] 0 ']


def test_comparisons_count_trailing_spaces(basic, helpers):
    texts, errors = run(basic, helpers, ['10 PRINT ("A"="A ");("A"<"A ");("A "<"A");("B">"A ")'])
    assert errors == [] and texts == [' 0 -1  0 -1 ']


def test_mid_from_position_zero_is_an_error(basic, helpers):
    texts, errors = run(basic, helpers, ['10 PRINT MID$("ABC",0,1)'])
    assert len(errors) == 1 and 'MID$ start position must be 1 or greater' in errors[0]


# -- graphics ----------------------------------------------------------------------

def test_line_crossing_the_screen_edge_draws_the_visible_part(basic, helpers):
    texts, errors = run(basic, helpers, [
        '10 PMODE 4,1: PCLS: LINE(-10,50)-(300,50),PSET',
        '20 PRINT PPOINT(0,50);PPOINT(128,50);PPOINT(255,50);PPOINT(128,51)'])
    assert errors == [] and texts == [' 1  1  1  0 ']


def test_draw_crossing_the_screen_edge_draws_the_visible_part(basic, helpers):
    texts, errors = run(basic, helpers, [
        '10 PMODE 4,1: PCLS: DRAW "BM250,100;R20;L40"',
        '20 PRINT PPOINT(240,100);PPOINT(255,100)'])
    assert errors == [] and texts == [' 1  1 ']


def test_switching_pmode_mid_drawing_keeps_earlier_pixels(basic, helpers):
    texts, errors = run(basic, helpers, [
        '10 PMODE 4,1: PCLS: PSET(10,10)',
        '20 PMODE 1,1: PSET(51,51)',       # 2x2 pixels in PMODE 1: lands on (50,50)
        '30 PRINT PPOINT(10,10);PPOINT(50,50)'])
    assert errors == [] and texts == [' 1  1 ']
