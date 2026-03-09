"""Tests for CHAIN and MERGE commands."""

import os
import pytest


class TestMerge:
    """Test MERGE command - merges lines from a file into the current program."""

    @pytest.fixture(autouse=True)
    def setup(self, temp_programs_dir):
        self.programs_dir = temp_programs_dir

    def _write_bas(self, filename, lines):
        """Write a .bas file into the programs directory."""
        path = os.path.join(self.programs_dir, filename)
        with open(path, 'w') as f:
            for line in lines:
                f.write(line + '\n')

    def test_merge_adds_new_lines(self, basic, helpers):
        """MERGE inserts lines that don't exist in the current program."""
        basic.process_command('10 PRINT "MAIN"')

        self._write_bas('subs.bas', ['100 PRINT "SUB"', '110 RETURN'])

        result = basic.process_command('MERGE "subs"')
        text = helpers.get_text_output(result)
        assert any('MERGED 2 LINES' in t for t in text)

        # Original line still present
        assert 10 in basic.program
        assert basic.program[10] == 'PRINT "MAIN"'

        # New lines added
        assert 100 in basic.program
        assert 110 in basic.program

    def test_merge_replaces_matching_lines(self, basic, helpers):
        """MERGE replaces lines that already exist."""
        basic.process_command('10 PRINT "OLD"')
        basic.process_command('20 END')

        self._write_bas('patch.bas', ['10 PRINT "NEW"'])

        basic.process_command('MERGE "patch"')

        assert basic.program[10] == 'PRINT "NEW"'
        assert 20 in basic.program  # untouched

    def test_merge_preserves_variables(self, basic, helpers):
        """MERGE does not clear variables."""
        basic.process_command('A = 42')
        basic.process_command('10 PRINT A')

        self._write_bas('extra.bas', ['20 PRINT "HI"'])

        basic.process_command('MERGE "extra"')
        assert basic.variables.get('A') == 42

    def test_merge_file_not_found(self, basic, helpers):
        """MERGE with nonexistent file gives FILE NOT FOUND."""
        helpers.assert_error_output(basic, 'MERGE "nofile"', 'FILE NOT FOUND')

    def test_merge_no_filename(self, basic, helpers):
        """MERGE without filename gives error."""
        helpers.assert_error_output(basic, 'MERGE', 'Filename required')

    def test_merge_auto_extension(self, basic, helpers):
        """MERGE adds .bas extension automatically."""
        self._write_bas('autoext.bas', ['50 REM MERGED'])

        result = basic.process_command('MERGE "autoext"')
        text = helpers.get_text_output(result)
        assert any('MERGED' in t for t in text)
        assert 50 in basic.program

    def test_merge_then_run(self, basic, helpers):
        """A merged program can be run successfully."""
        basic.process_command('10 GOSUB 100')
        basic.process_command('20 END')

        self._write_bas('sub.bas', [
            '100 PRINT "FROM SUB"',
            '110 RETURN',
        ])

        basic.process_command('MERGE "sub"')
        result = basic.process_command('RUN')
        text = helpers.get_text_output(result)
        assert 'FROM SUB' in text


class TestChain:
    """Test CHAIN command - loads and runs another program."""

    @pytest.fixture(autouse=True)
    def setup(self, temp_programs_dir):
        self.programs_dir = temp_programs_dir

    def _write_bas(self, filename, lines):
        path = os.path.join(self.programs_dir, filename)
        with open(path, 'w') as f:
            for line in lines:
                f.write(line + '\n')

    def test_chain_loads_and_runs(self, basic, helpers):
        """CHAIN loads a new program and runs it."""
        self._write_bas('hello.bas', [
            '10 PRINT "CHAINED"',
            '20 END',
        ])

        result = basic.process_command('CHAIN "hello"')
        text = helpers.get_text_output(result)
        assert 'CHAINED' in text

    def test_chain_replaces_old_program(self, basic, helpers):
        """CHAIN replaces the current program."""
        basic.process_command('10 PRINT "OLD"')

        self._write_bas('new.bas', ['10 PRINT "NEW"', '20 END'])

        basic.process_command('CHAIN "new"')

        # Old program replaced
        assert basic.program[10] == 'PRINT "NEW"'

    def test_chain_clears_variables_by_default(self, basic, helpers):
        """CHAIN without ALL clears variables."""
        basic.process_command('X = 99')

        self._write_bas('prog.bas', ['10 END'])

        basic.process_command('CHAIN "prog"')
        assert basic.variables.get('X') is None

    def test_chain_all_preserves_variables(self, basic, helpers):
        """CHAIN with ALL preserves variables."""
        basic.process_command('X = 99')
        basic.process_command('A$ = "HELLO"')

        self._write_bas('prog.bas', [
            '10 PRINT X',
            '20 PRINT A$',
            '30 END',
        ])

        result = basic.process_command('CHAIN "prog", ALL')
        text = helpers.get_text_output(result)
        assert any('99' in t for t in text)
        assert any('HELLO' in t for t in text)

    def test_chain_all_preserves_arrays(self, basic, helpers):
        """CHAIN with ALL preserves dimensioned arrays."""
        basic.process_command('DIM B(5)')
        basic.process_command('B(3) = 42')

        self._write_bas('arr.bas', [
            '10 PRINT B(3)',
            '20 END',
        ])

        result = basic.process_command('CHAIN "arr", ALL')
        text = helpers.get_text_output(result)
        assert any('42' in t for t in text)

    def test_chain_with_start_line(self, basic, helpers):
        """CHAIN with a line number starts execution there."""
        self._write_bas('jump.bas', [
            '10 PRINT "SKIPPED"',
            '20 PRINT "STARTED HERE"',
            '30 END',
        ])

        result = basic.process_command('CHAIN "jump", 20')
        text = helpers.get_text_output(result)
        assert not any('SKIPPED' in t for t in text)
        assert any('STARTED HERE' in t for t in text)

    def test_chain_all_with_start_line(self, basic, helpers):
        """CHAIN with ALL and a start line."""
        basic.process_command('V = 7')

        self._write_bas('combo.bas', [
            '10 PRINT "SKIP"',
            '20 PRINT V',
            '30 END',
        ])

        result = basic.process_command('CHAIN "combo", ALL, 20')
        text = helpers.get_text_output(result)
        assert 'SKIP' not in [t.strip() for t in text]
        assert any('7' in t for t in text)

    def test_chain_file_not_found(self, basic, helpers):
        """CHAIN with nonexistent file gives FILE NOT FOUND."""
        helpers.assert_error_output(basic, 'CHAIN "nope"', 'FILE NOT FOUND')

    def test_chain_no_filename(self, basic, helpers):
        """CHAIN without filename gives error."""
        helpers.assert_error_output(basic, 'CHAIN', 'Filename required')

    def test_chain_invalid_start_line(self, basic, helpers):
        """CHAIN with a nonexistent start line gives error."""
        self._write_bas('noln.bas', ['10 PRINT "HI"', '20 END'])

        result = basic.process_command('CHAIN "noln", 999')
        errors = helpers.get_error_messages(result)
        assert any('UNDEFINED LINE' in e for e in errors)

    def test_chain_from_program(self, basic, helpers):
        """CHAIN can be executed from within a running program."""
        self._write_bas('part2.bas', [
            '10 PRINT "PART TWO"',
            '20 END',
        ])

        # Program that chains to part2
        basic.process_command('10 PRINT "PART ONE"')
        basic.process_command('20 CHAIN "part2"')

        result = basic.process_command('RUN')
        text = helpers.get_text_output(result)
        assert 'PART ONE' in text
        assert 'PART TWO' in text


class TestRuntimeMerge:
    """Test MERGE during program execution (rebuilds position list)."""

    @pytest.fixture(autouse=True)
    def setup(self, temp_programs_dir):
        self.programs_dir = temp_programs_dir

    def _write_bas(self, filename, lines):
        path = os.path.join(self.programs_dir, filename)
        with open(path, 'w') as f:
            for line in lines:
                f.write(line + '\n')

    def test_merge_during_run(self, basic, helpers):
        """MERGE inside a running program adds lines visible to later GOSUBs."""
        self._write_bas('subs.bas', [
            '100 DoWork:',
            '110 PRINT "WORKING"',
            '120 RETURN',
        ])

        result = helpers.execute_program(basic, [
            '10 MERGE "subs"',
            '20 GOSUB DoWork',
            '30 END',
        ])
        text = helpers.get_text_output(result)
        assert any('WORKING' in t for t in text)

    def test_merge_during_run_continues_after(self, basic, helpers):
        """Execution continues at the correct line after runtime MERGE."""
        self._write_bas('lib.bas', ['500 REM LIBRARY LOADED'])

        result = helpers.execute_program(basic, [
            '10 PRINT "BEFORE"',
            '20 MERGE "lib"',
            '30 PRINT "AFTER"',
            '40 END',
        ])
        text = helpers.get_text_output(result)
        assert 'BEFORE' in text
        assert 'AFTER' in text

    def test_merge_during_run_does_not_execute_merged_lines(self, basic, helpers):
        """Merged lines aren't executed just because they were added."""
        self._write_bas('extra.bas', [
            '500 PRINT "SHOULD NOT RUN"',
            '510 END',
        ])

        result = helpers.execute_program(basic, [
            '10 MERGE "extra"',
            '20 PRINT "DONE"',
            '30 END',
        ])
        text = helpers.get_text_output(result)
        assert 'DONE' in text
        assert not any('SHOULD NOT RUN' in t for t in text)


class TestLabels:
    """Test label definitions and GOTO/GOSUB label resolution."""

    def test_label_definition_and_goto(self, basic, helpers):
        """A label line registers in the label table and GOTO resolves it."""
        result = helpers.execute_program(basic, [
            '10 GOTO PrintMsg',
            '20 END',
            '30 PrintMsg:',
            '40 PRINT "LABELED"',
            '50 END',
        ])
        text = helpers.get_text_output(result)
        assert 'LABELED' in text

    def test_label_gosub_return(self, basic, helpers):
        """GOSUB with a label target works with RETURN."""
        result = helpers.execute_program(basic, [
            '10 GOSUB Greet',
            '20 PRINT "BACK"',
            '30 END',
            '100 Greet:',
            '110 PRINT "HI"',
            '120 RETURN',
        ])
        text = helpers.get_text_output(result)
        assert 'HI' in text
        assert 'BACK' in text

    def test_label_case_insensitive(self, basic, helpers):
        """Labels are case-insensitive."""
        result = helpers.execute_program(basic, [
            '10 GOTO mylab',
            '20 END',
            '30 MyLab:',
            '40 PRINT "FOUND"',
            '50 END',
        ])
        text = helpers.get_text_output(result)
        assert 'FOUND' in text

    def test_on_goto_with_labels(self, basic, helpers):
        """ON...GOTO resolves label targets."""
        result = helpers.execute_program(basic, [
            '10 X = 2',
            '20 ON X GOTO Alpha, Beta',
            '30 END',
            '100 Alpha:',
            '110 PRINT "A"',
            '120 END',
            '200 Beta:',
            '210 PRINT "B"',
            '220 END',
        ])
        text = helpers.get_text_output(result)
        assert 'B' in text
        assert 'A' not in text

    def test_on_gosub_with_labels(self, basic, helpers):
        """ON...GOSUB resolves label targets."""
        result = helpers.execute_program(basic, [
            '10 X = 1',
            '20 ON X GOSUB DoIt',
            '30 PRINT "DONE"',
            '40 END',
            '100 DoIt:',
            '110 PRINT "DID IT"',
            '120 RETURN',
        ])
        text = helpers.get_text_output(result)
        assert 'DID IT' in text
        assert 'DONE' in text

    def test_label_cleared_on_new(self, basic, helpers):
        """NEW clears the label table."""
        basic.process_command('10 MyLabel:')
        assert basic.resolve_label('MYLABEL') == 10
        basic.process_command('NEW')
        assert basic.resolve_label('MYLABEL') is None

    def test_label_with_trailing_spaces(self, basic, helpers):
        """Label detection handles trailing whitespace."""
        basic.process_command('50 Init:')
        assert basic.resolve_label('INIT') == 50

    def test_label_not_confused_with_assignment(self, basic, helpers):
        """A line like 'A = 5' is not a label."""
        basic.process_command('10 A = 5')
        assert basic.resolve_label('A') is None

    def test_label_variable_precedence(self, basic, helpers):
        """If a variable has the same name as a label, GOTO uses the label."""
        result = helpers.execute_program(basic, [
            '10 Target = 999',
            '20 GOTO Target',
            '30 END',
            '40 Target:',
            '50 PRINT "LABEL WINS"',
            '60 END',
        ])
        text = helpers.get_text_output(result)
        assert 'LABEL WINS' in text


class TestAutoNumbering:
    """Test auto-numbering of unnumbered lines in file loading."""

    @pytest.fixture(autouse=True)
    def setup(self, temp_programs_dir):
        self.programs_dir = temp_programs_dir

    def _write_bas(self, filename, lines):
        path = os.path.join(self.programs_dir, filename)
        with open(path, 'w') as f:
            for line in lines:
                f.write(line + '\n')

    def test_load_unnumbered_file(self, basic, helpers):
        """LOAD auto-numbers unnumbered lines."""
        self._write_bas('unnum.bas', [
            'PRINT "LINE ONE"',
            'PRINT "LINE TWO"',
            'END',
        ])

        basic.process_command('LOAD "unnum"')
        # Should have 3 lines auto-numbered
        assert len(basic.program) == 3
        # Lines should be in ascending order
        lines = sorted(basic.program.keys())
        assert lines[0] < lines[1] < lines[2]

    def test_load_unnumbered_then_run(self, basic, helpers):
        """An auto-numbered program runs correctly."""
        self._write_bas('runme.bas', [
            'PRINT "HELLO"',
            'PRINT "WORLD"',
            'END',
        ])

        basic.process_command('LOAD "runme"')
        result = basic.process_command('RUN')
        text = helpers.get_text_output(result)
        assert 'HELLO' in text
        assert 'WORLD' in text

    def test_mixed_numbered_and_unnumbered(self, basic, helpers):
        """Files can mix numbered and unnumbered lines."""
        self._write_bas('mixed.bas', [
            '10 PRINT "TEN"',
            'PRINT "AUTO"',
            '100 END',
        ])

        basic.process_command('LOAD "mixed"')
        assert 10 in basic.program
        assert 100 in basic.program
        # The unnumbered line should be between 10 and 100 (auto-assigned as 20)
        lines = sorted(basic.program.keys())
        assert len(lines) == 3
        assert lines[0] == 10
        assert 10 < lines[1] < 100

    def test_merge_unnumbered_into_numbered(self, basic, helpers):
        """MERGE auto-numbers unnumbered lines after existing program."""
        basic.process_command('10 PRINT "MAIN"')
        basic.process_command('20 END')

        self._write_bas('extra.bas', [
            'PRINT "MERGED"',
            'RETURN',
        ])

        basic.process_command('MERGE "extra"')
        # Should have 4 lines: 10, 20, plus 2 auto-numbered after 20
        assert len(basic.program) == 4
        lines = sorted(basic.program.keys())
        assert lines[0] == 10
        assert lines[1] == 20
        assert lines[2] > 20
        assert lines[3] > lines[2]

    def test_unnumbered_with_labels(self, basic, helpers):
        """Unnumbered files with labels work end-to-end."""
        self._write_bas('labeled.bas', [
            'GOSUB DoStuff',
            'END',
            'DoStuff:',
            'PRINT "STUFF DONE"',
            'RETURN',
        ])

        basic.process_command('LOAD "labeled"')
        result = basic.process_command('RUN')
        text = helpers.get_text_output(result)
        assert 'STUFF DONE' in text

    def test_chain_unnumbered(self, basic, helpers):
        """CHAIN works with unnumbered program files."""
        self._write_bas('nonum.bas', [
            'PRINT "CHAINED OK"',
            'END',
        ])

        result = basic.process_command('CHAIN "nonum"')
        text = helpers.get_text_output(result)
        assert 'CHAINED OK' in text

    def test_chain_with_label_start(self, basic, helpers):
        """CHAIN can start at a label."""
        self._write_bas('labstart.bas', [
            '10 PRINT "SKIP"',
            '20 END',
            '30 Entry:',
            '40 PRINT "ENTERED"',
            '50 END',
        ])

        result = basic.process_command('CHAIN "labstart", Entry')
        text = helpers.get_text_output(result)
        assert not any('SKIP' in t for t in text)
        assert any('ENTERED' in t for t in text)


class TestMergeIfGosubReturn:
    """Test MERGE with IF THEN GOSUB: RETURN pattern.

    Reproduces the DoMoves/DoTurn bug where a merged label-only library
    with IF cond THEN GOSUB sub: RETURN doesn't execute correctly.
    """

    @pytest.fixture(autouse=True)
    def setup(self, temp_programs_dir):
        self.programs_dir = temp_programs_dir

    def _write_bas(self, filename, lines):
        path = os.path.join(self.programs_dir, filename)
        with open(path, 'w') as f:
            for line in lines:
                f.write(line + '\n')

    def test_merged_if_gosub_return(self, basic, helpers):
        """Merged sub with IF THEN GOSUB: RETURN works."""
        self._write_bas('lib.bas', [
            'DoWork:',
            'IF 1=1 THEN GOSUB Worker: RETURN',
            'RETURN',
            'Worker:',
            'X=X+1',
            'RETURN',
        ])
        result = helpers.execute_program(basic, [
            '10 X=0',
            '20 MERGE "lib"',
            '30 GOSUB DoWork',
            '40 PRINT "X=";X',
            '50 END',
        ])
        errors = helpers.get_error_messages(result)
        assert errors == [], f"Errors: {errors}"
        text = helpers.get_text_output(result)
        output = ' '.join(text)
        assert '1' in output, f"X should be 1: {text}"

    def test_merged_for_loop_if_gosub_return(self, basic, helpers):
        """Merged library: FOR loop calling sub with IF THEN GOSUB: RETURN."""
        self._write_bas('lib.bas', [
            'Outer:',
            'LOCAL MI',
            'FOR MI=1 TO 3',
            '  GOSUB Inner',
            'NEXT MI',
            'RETURN',
            'Inner:',
            'IF 1=1 THEN GOSUB Worker: RETURN',
            'RETURN',
            'Worker:',
            'X=X+1',
            'RETURN',
        ])
        result = helpers.execute_program(basic, [
            '10 X=0',
            '20 MERGE "lib"',
            '30 GOSUB Outer',
            '40 PRINT "X=";X',
            '50 END',
        ])
        errors = helpers.get_error_messages(result)
        assert errors == [], f"Errors: {errors}"
        text = helpers.get_text_output(result)
        output = ' '.join(text)
        assert '3' in output, f"X should be 3: {text}"

    def test_merged_if_variable_gosub_return(self, basic, helpers):
        """Merged library: IF var=0 THEN GOSUB: RETURN (AN=0 pattern)."""
        self._write_bas('lib.bas', [
            'DoTurn:',
            'IF AN=0 THEN GOSUB Permute: RETURN',
            'REM animated path',
            'GOSUB Permute',
            'RETURN',
            'Permute:',
            'X=X+1',
            'RETURN',
        ])
        result = helpers.execute_program(basic, [
            '10 AN=0: X=0',
            '20 MERGE "lib"',
            '30 GOSUB DoTurn',
            '40 PRINT "X=";X',
            '50 END',
        ])
        errors = helpers.get_error_messages(result)
        assert errors == [], f"Errors: {errors}"
        text = helpers.get_text_output(result)
        output = ' '.join(text)
        assert '1' in output, f"X should be 1: {text}"

    def test_merged_full_domoves_pattern(self, basic, helpers):
        """Full DoMoves/DoTurn simulation with merged label-only library."""
        self._write_bas('engine.bas', [
            'DoMoves:',
            'LOCAL MI, MC$, UC$',
            'FOR MI=1 TO LEN(MS$)',
            '  MC$=MID$(MS$,MI,1)',
            '  GOSUB DoTurn',
            'NEXT MI',
            'RETURN',
            'DoTurn:',
            'IF AN=0 THEN GOSUB Permute: RETURN',
            'GOSUB Permute',
            'RETURN',
            'Permute:',
            'X=X+1',
            'RETURN',
        ])
        result = helpers.execute_program(basic, [
            '10 AN=0: X=0',
            '20 MERGE "engine"',
            '30 MS$="RUF"',
            '40 GOSUB DoMoves',
            '50 PRINT "X=";X',
            '60 END',
        ])
        errors = helpers.get_error_messages(result)
        assert errors == [], f"Errors: {errors}"
        text = helpers.get_text_output(result)
        output = ' '.join(text)
        assert '3' in output, f"X should be 3 (3 moves): {text}"
