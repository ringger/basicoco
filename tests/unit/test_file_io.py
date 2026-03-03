"""
Tests for sequential file I/O: OPEN, CLOSE, PRINT#, INPUT#, LINE INPUT, EOF.
"""

import os
import pytest


class TestOpen:
    """Test OPEN command."""

    @pytest.fixture(autouse=True)
    def test_dir(self, temp_programs_dir):
        self.programs_dir = temp_programs_dir
        yield

    def test_open_output_creates_file(self, basic):
        result = basic.process_command('OPEN "O", #1, "TEST.DAT"')
        assert not any(r.get('type') == 'error' for r in result)
        assert os.path.exists(os.path.join(self.programs_dir, 'TEST.DAT'))
        basic.process_command('CLOSE #1')

    def test_open_input_existing_file(self, basic):
        # Create a file first
        path = os.path.join(self.programs_dir, 'READ.DAT')
        with open(path, 'w') as f:
            f.write("hello\n")
        result = basic.process_command('OPEN "I", #1, "READ.DAT"')
        assert not any(r.get('type') == 'error' for r in result)
        basic.process_command('CLOSE #1')

    def test_open_input_missing_file(self, basic, helpers):
        result = basic.process_command('OPEN "I", #1, "NOEXIST.DAT"')
        errors = helpers.get_error_messages(result)
        assert any('FILE NOT FOUND' in e for e in errors)

    def test_open_invalid_mode(self, basic, helpers):
        result = basic.process_command('OPEN "X", #1, "TEST.DAT"')
        errors = helpers.get_error_messages(result)
        assert any('FILE MODE ERROR' in e for e in errors)

    def test_open_file_already_open(self, basic, helpers):
        basic.process_command('OPEN "O", #1, "TEST.DAT"')
        result = basic.process_command('OPEN "O", #1, "TEST2.DAT"')
        errors = helpers.get_error_messages(result)
        assert any('FILE ALREADY OPEN' in e for e in errors)
        basic.process_command('CLOSE #1')

    def test_open_invalid_file_number(self, basic, helpers):
        result = basic.process_command('OPEN "O", #0, "TEST.DAT"')
        errors = helpers.get_error_messages(result)
        assert any('FILE NUMBER ERROR' in e for e in errors)

    def test_open_file_number_too_high(self, basic, helpers):
        result = basic.process_command('OPEN "O", #16, "TEST.DAT"')
        errors = helpers.get_error_messages(result)
        assert any('FILE NUMBER ERROR' in e for e in errors)

    def test_open_append_mode(self, basic):
        path = os.path.join(self.programs_dir, 'APPEND.DAT')
        with open(path, 'w') as f:
            f.write("first\n")
        basic.process_command('OPEN "A", #1, "APPEND.DAT"')
        basic.process_command('PRINT #1, "second"')
        basic.process_command('CLOSE #1')
        with open(path, 'r') as f:
            lines = f.readlines()
        assert len(lines) == 2
        assert lines[0].strip() == 'first'
        assert lines[1].strip() == 'second'

    def test_open_missing_args(self, basic, helpers):
        result = basic.process_command('OPEN "O", #1')
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0

    def test_open_multiple_files(self, basic):
        basic.process_command('OPEN "O", #1, "FILE1.DAT"')
        basic.process_command('OPEN "O", #2, "FILE2.DAT"')
        assert 1 in basic.file_io.open_files
        assert 2 in basic.file_io.open_files
        basic.process_command('CLOSE')


class TestClose:
    """Test CLOSE command."""

    @pytest.fixture(autouse=True)
    def test_dir(self, temp_programs_dir):
        self.programs_dir = temp_programs_dir
        yield

    def test_close_specific_file(self, basic):
        basic.process_command('OPEN "O", #1, "TEST.DAT"')
        assert 1 in basic.file_io.open_files
        basic.process_command('CLOSE #1')
        assert 1 not in basic.file_io.open_files

    def test_close_all_files(self, basic):
        basic.process_command('OPEN "O", #1, "FILE1.DAT"')
        basic.process_command('OPEN "O", #2, "FILE2.DAT"')
        basic.process_command('CLOSE')
        assert len(basic.file_io.open_files) == 0

    def test_close_unopened_file_no_error(self, basic):
        result = basic.process_command('CLOSE #5')
        assert not any(r.get('type') == 'error' for r in result)

    def test_new_closes_files(self, basic):
        basic.process_command('OPEN "O", #1, "TEST.DAT"')
        basic.process_command('NEW')
        assert len(basic.file_io.open_files) == 0


class TestPrintFile:
    """Test PRINT# command."""

    @pytest.fixture(autouse=True)
    def test_dir(self, temp_programs_dir):
        self.programs_dir = temp_programs_dir
        yield

    def _read_file(self, name):
        path = os.path.join(self.programs_dir, name)
        with open(path, 'r') as f:
            return f.read()

    def test_print_string(self, basic):
        basic.process_command('OPEN "O", #1, "TEST.DAT"')
        basic.process_command('PRINT #1, "HELLO"')
        basic.process_command('CLOSE #1')
        assert self._read_file('TEST.DAT').strip() == 'HELLO'

    def test_print_number(self, basic):
        basic.process_command('OPEN "O", #1, "TEST.DAT"')
        basic.process_command('PRINT #1, 42')
        basic.process_command('CLOSE #1')
        assert self._read_file('TEST.DAT').strip() == '42'

    def test_print_variable(self, basic):
        basic.process_command('LET A = 100')
        basic.process_command('OPEN "O", #1, "TEST.DAT"')
        basic.process_command('PRINT #1, A')
        basic.process_command('CLOSE #1')
        assert self._read_file('TEST.DAT').strip() == '100'

    def test_print_comma_separator(self, basic):
        basic.process_command('OPEN "O", #1, "TEST.DAT"')
        basic.process_command('PRINT #1, 1, 2, 3')
        basic.process_command('CLOSE #1')
        content = self._read_file('TEST.DAT').strip()
        assert content == '1,2,3'

    def test_print_semicolon_separator(self, basic):
        basic.process_command('OPEN "O", #1, "TEST.DAT"')
        basic.process_command('PRINT #1, "A"; "B"; "C"')
        basic.process_command('CLOSE #1')
        content = self._read_file('TEST.DAT').strip()
        assert content == 'ABC'

    def test_print_trailing_semicolon_no_newline(self, basic):
        basic.process_command('OPEN "O", #1, "TEST.DAT"')
        basic.process_command('PRINT #1, "A";')
        basic.process_command('PRINT #1, "B"')
        basic.process_command('CLOSE #1')
        content = self._read_file('TEST.DAT')
        assert content == 'AB\n'

    def test_print_empty_line(self, basic):
        basic.process_command('OPEN "O", #1, "TEST.DAT"')
        basic.process_command('PRINT #1,')
        basic.process_command('CLOSE #1')
        content = self._read_file('TEST.DAT')
        assert content == '\n'

    def test_print_to_input_file_error(self, basic, helpers):
        path = os.path.join(self.programs_dir, 'TEST.DAT')
        with open(path, 'w') as f:
            f.write("data\n")
        basic.process_command('OPEN "I", #1, "TEST.DAT"')
        result = basic.process_command('PRINT #1, "HELLO"')
        errors = helpers.get_error_messages(result)
        assert any('FILE MODE ERROR' in e for e in errors)
        basic.process_command('CLOSE #1')

    def test_print_to_unopened_file(self, basic, helpers):
        result = basic.process_command('PRINT #5, "HELLO"')
        errors = helpers.get_error_messages(result)
        assert any('FILE NOT OPEN' in e for e in errors)

    def test_print_expression(self, basic):
        basic.process_command('LET X = 10')
        basic.process_command('OPEN "O", #1, "TEST.DAT"')
        basic.process_command('PRINT #1, X * 2 + 1')
        basic.process_command('CLOSE #1')
        assert self._read_file('TEST.DAT').strip() == '21'

    def test_print_multiple_lines(self, basic):
        basic.process_command('OPEN "O", #1, "TEST.DAT"')
        basic.process_command('PRINT #1, "LINE1"')
        basic.process_command('PRINT #1, "LINE2"')
        basic.process_command('PRINT #1, "LINE3"')
        basic.process_command('CLOSE #1')
        lines = self._read_file('TEST.DAT').strip().split('\n')
        assert lines == ['LINE1', 'LINE2', 'LINE3']

    def test_print_no_hash_still_console(self, basic, helpers):
        """PRINT without # should still go to console."""
        result = basic.process_command('PRINT "HELLO"')
        text = helpers.get_text_output(result)
        assert text == ['HELLO']


class TestInputFile:
    """Test INPUT# command."""

    @pytest.fixture(autouse=True)
    def test_dir(self, temp_programs_dir):
        self.programs_dir = temp_programs_dir
        yield

    def _write_file(self, name, content):
        path = os.path.join(self.programs_dir, name)
        with open(path, 'w') as f:
            f.write(content)

    def test_input_string(self, basic, helpers):
        self._write_file('TEST.DAT', 'HELLO\n')
        basic.process_command('OPEN "I", #1, "TEST.DAT"')
        basic.process_command('INPUT #1, A$')
        assert basic.variables.get('A$') == 'HELLO'
        basic.process_command('CLOSE #1')

    def test_input_number(self, basic):
        self._write_file('TEST.DAT', '42\n')
        basic.process_command('OPEN "I", #1, "TEST.DAT"')
        basic.process_command('INPUT #1, X')
        assert basic.variables.get('X') == 42
        basic.process_command('CLOSE #1')

    def test_input_comma_separated(self, basic):
        self._write_file('TEST.DAT', '10,20,30\n')
        basic.process_command('OPEN "I", #1, "TEST.DAT"')
        basic.process_command('INPUT #1, A, B, C')
        assert basic.variables.get('A') == 10
        assert basic.variables.get('B') == 20
        assert basic.variables.get('C') == 30
        basic.process_command('CLOSE #1')

    def test_input_multiple_lines(self, basic):
        self._write_file('TEST.DAT', '100\n200\n')
        basic.process_command('OPEN "I", #1, "TEST.DAT"')
        basic.process_command('INPUT #1, A')
        basic.process_command('INPUT #1, B')
        assert basic.variables.get('A') == 100
        assert basic.variables.get('B') == 200
        basic.process_command('CLOSE #1')

    def test_input_past_eof_error(self, basic, helpers):
        self._write_file('TEST.DAT', '42\n')
        basic.process_command('OPEN "I", #1, "TEST.DAT"')
        basic.process_command('INPUT #1, A')
        result = basic.process_command('INPUT #1, B')
        errors = helpers.get_error_messages(result)
        assert any('INPUT PAST END' in e for e in errors)
        basic.process_command('CLOSE #1')

    def test_input_from_output_file_error(self, basic, helpers):
        basic.process_command('OPEN "O", #1, "TEST.DAT"')
        result = basic.process_command('INPUT #1, A')
        errors = helpers.get_error_messages(result)
        assert any('FILE MODE ERROR' in e for e in errors)
        basic.process_command('CLOSE #1')

    def test_input_quoted_string(self, basic):
        self._write_file('TEST.DAT', '"HELLO, WORLD"\n')
        basic.process_command('OPEN "I", #1, "TEST.DAT"')
        basic.process_command('INPUT #1, A$')
        assert basic.variables.get('A$') == 'HELLO, WORLD'
        basic.process_command('CLOSE #1')

    def test_input_float(self, basic):
        self._write_file('TEST.DAT', '3.14\n')
        basic.process_command('OPEN "I", #1, "TEST.DAT"')
        basic.process_command('INPUT #1, X')
        assert basic.variables.get('X') == 3.14
        basic.process_command('CLOSE #1')

    def test_input_no_hash_still_console(self, basic, helpers):
        """INPUT without # should still go to console (input_request)."""
        result = basic.process_command('INPUT "Name"; A$')
        assert any(r.get('type') == 'input_request' for r in result)


class TestLineInput:
    """Test LINE INPUT command."""

    @pytest.fixture(autouse=True)
    def test_dir(self, temp_programs_dir):
        self.programs_dir = temp_programs_dir
        yield

    def _write_file(self, name, content):
        path = os.path.join(self.programs_dir, name)
        with open(path, 'w') as f:
            f.write(content)

    def test_line_input_file(self, basic):
        self._write_file('TEST.DAT', 'Hello, World\n')
        basic.process_command('OPEN "I", #1, "TEST.DAT"')
        basic.process_command('LINE INPUT #1, A$')
        assert basic.variables.get('A$') == 'Hello, World'
        basic.process_command('CLOSE #1')

    def test_line_input_preserves_commas(self, basic):
        self._write_file('TEST.DAT', 'A,B,C,D\n')
        basic.process_command('OPEN "I", #1, "TEST.DAT"')
        basic.process_command('LINE INPUT #1, A$')
        assert basic.variables.get('A$') == 'A,B,C,D'
        basic.process_command('CLOSE #1')

    def test_line_input_multiple_lines(self, basic):
        self._write_file('TEST.DAT', 'LINE1\nLINE2\n')
        basic.process_command('OPEN "I", #1, "TEST.DAT"')
        basic.process_command('LINE INPUT #1, A$')
        basic.process_command('LINE INPUT #1, B$')
        assert basic.variables.get('A$') == 'LINE1'
        assert basic.variables.get('B$') == 'LINE2'
        basic.process_command('CLOSE #1')

    def test_line_input_past_eof_error(self, basic, helpers):
        self._write_file('TEST.DAT', 'ONE\n')
        basic.process_command('OPEN "I", #1, "TEST.DAT"')
        basic.process_command('LINE INPUT #1, A$')
        result = basic.process_command('LINE INPUT #1, B$')
        errors = helpers.get_error_messages(result)
        assert any('INPUT PAST END' in e for e in errors)
        basic.process_command('CLOSE #1')

    def test_line_input_console(self, basic):
        """LINE INPUT to console should return input_request with line_input flag."""
        result = basic.process_command('LINE INPUT A$')
        assert any(r.get('type') == 'input_request' for r in result)
        req = [r for r in result if r.get('type') == 'input_request'][0]
        assert req.get('line_input') is True

    def test_line_input_console_with_prompt(self, basic):
        result = basic.process_command('LINE INPUT "Enter text"; T$')
        req = [r for r in result if r.get('type') == 'input_request'][0]
        assert req['prompt'] == 'Enter text'
        assert req.get('line_input') is True


class TestEOF:
    """Test EOF function."""

    @pytest.fixture(autouse=True)
    def test_dir(self, temp_programs_dir):
        self.programs_dir = temp_programs_dir
        yield

    def _write_file(self, name, content):
        path = os.path.join(self.programs_dir, name)
        with open(path, 'w') as f:
            f.write(content)

    def test_eof_not_at_end(self, basic):
        self._write_file('TEST.DAT', 'data\n')
        basic.process_command('OPEN "I", #1, "TEST.DAT"')
        result = basic.evaluate_expression('EOF(1)')
        assert result == 0
        basic.process_command('CLOSE #1')

    def test_eof_at_end(self, basic):
        self._write_file('TEST.DAT', 'data\n')
        basic.process_command('OPEN "I", #1, "TEST.DAT"')
        basic.process_command('INPUT #1, A$')
        result = basic.evaluate_expression('EOF(1)')
        assert result == -1
        basic.process_command('CLOSE #1')

    def test_eof_unopened_file(self, basic, helpers):
        helpers.assert_error_output(basic, 'PRINT EOF(3)', 'FILE NOT OPEN')

    def test_eof_on_output_file(self, basic, helpers):
        basic.process_command('OPEN "O", #1, "TEST.DAT"')
        helpers.assert_error_output(basic, 'PRINT EOF(1)', 'EOF only valid')
        basic.process_command('CLOSE #1')


class TestWriteThenRead:
    """Integration tests: write data then read it back."""

    @pytest.fixture(autouse=True)
    def test_dir(self, temp_programs_dir):
        self.programs_dir = temp_programs_dir
        yield

    def test_write_read_cycle(self, basic):
        """Write values then read them back."""
        basic.process_command('OPEN "O", #1, "DATA.DAT"')
        basic.process_command('PRINT #1, "ALICE"')
        basic.process_command('PRINT #1, 42')
        basic.process_command('PRINT #1, 3.14')
        basic.process_command('CLOSE #1')

        basic.process_command('OPEN "I", #1, "DATA.DAT"')
        basic.process_command('INPUT #1, N$')
        basic.process_command('INPUT #1, AGE')
        basic.process_command('INPUT #1, PI')
        basic.process_command('CLOSE #1')

        assert basic.variables.get('N$') == 'ALICE'
        assert basic.variables.get('AGE') == 42
        assert basic.variables.get('PI') == 3.14

    def test_write_comma_separated_read_back(self, basic):
        """Write comma-separated values and read them back."""
        basic.process_command('OPEN "O", #1, "DATA.DAT"')
        basic.process_command('PRINT #1, 10, 20, 30')
        basic.process_command('CLOSE #1')

        basic.process_command('OPEN "I", #1, "DATA.DAT"')
        basic.process_command('INPUT #1, A, B, C')
        basic.process_command('CLOSE #1')

        assert basic.variables.get('A') == 10
        assert basic.variables.get('B') == 20
        assert basic.variables.get('C') == 30

    def test_program_write_read(self, basic, helpers):
        """Test file I/O in a running program."""
        helpers.load_program(basic, [
            '10 OPEN "O", #1, "PROG.DAT"',
            '20 FOR I = 1 TO 3',
            '30 PRINT #1, I',
            '40 NEXT I',
            '50 CLOSE #1',
            '60 OPEN "I", #1, "PROG.DAT"',
            '70 S = 0',
            '80 IF EOF(1) THEN 110',
            '90 INPUT #1, X',
            '100 S = S + X: GOTO 80',
            '110 CLOSE #1',
            '120 PRINT S',
            '130 END',
        ])
        result = basic.process_command('RUN')
        text = helpers.get_text_output(result)
        # Sum of 1+2+3 = 6
        assert any('6' in t for t in text)

    def test_multi_file_operations(self, basic):
        """Test using multiple files simultaneously."""
        basic.process_command('OPEN "O", #1, "FILE1.DAT"')
        basic.process_command('OPEN "O", #2, "FILE2.DAT"')
        basic.process_command('PRINT #1, "HELLO"')
        basic.process_command('PRINT #2, "WORLD"')
        basic.process_command('CLOSE')

        basic.process_command('OPEN "I", #1, "FILE1.DAT"')
        basic.process_command('OPEN "I", #2, "FILE2.DAT"')
        basic.process_command('INPUT #1, A$')
        basic.process_command('INPUT #2, B$')
        basic.process_command('CLOSE')

        assert basic.variables.get('A$') == 'HELLO'
        assert basic.variables.get('B$') == 'WORLD'
