"""Tests for ON ERROR GOTO / RESUME error handling."""

import pytest


class TestOnErrorGoto:
    """Test ON ERROR GOTO handler registration and error interception."""

    def test_basic_error_handler(self, basic, helpers):
        """ON ERROR GOTO jumps to handler on error."""
        result = helpers.execute_program(basic, [
            '10 ON ERROR GOTO 100',
            '20 PRINT 1/0',
            '30 PRINT "SHOULD NOT PRINT"',
            '40 END',
            '100 PRINT "CAUGHT"',
        ])
        texts = helpers.get_text_output(result)
        assert any('CAUGHT' in t for t in texts)
        assert not any('SHOULD NOT PRINT' in t for t in texts)

    def test_resume_next_continues(self, basic, helpers):
        """RESUME NEXT skips the error line and continues."""
        result = helpers.execute_program(basic, [
            '10 ON ERROR GOTO 100',
            '20 PRINT 1/0',
            '30 PRINT "CONTINUED"',
            '40 END',
            '100 RESUME NEXT',
        ])
        texts = helpers.get_text_output(result)
        assert any('CONTINUED' in t for t in texts)

    def test_resume_retries(self, basic, helpers):
        """RESUME (bare) retries the error-causing line after fixing the cause."""
        result = helpers.execute_program(basic, [
            '10 ON ERROR GOTO 100',
            '20 X = 0',
            '30 PRINT 10/X',
            '40 PRINT "DONE"',
            '50 END',
            '100 X = 2',
            '110 RESUME',
        ])
        texts = helpers.get_text_output(result)
        assert any('5' in t for t in texts)
        assert any('DONE' in t for t in texts)

    def test_resume_line(self, basic, helpers):
        """RESUME <line> jumps to specified line."""
        result = helpers.execute_program(basic, [
            '10 ON ERROR GOTO 100',
            '20 PRINT 1/0',
            '30 PRINT "SKIP"',
            '40 PRINT "TARGET"',
            '50 END',
            '100 RESUME 40',
        ])
        texts = helpers.get_text_output(result)
        assert any('TARGET' in t for t in texts)
        assert not any('SKIP' in t for t in texts)

    def test_on_error_goto_0_disables(self, basic, helpers):
        """ON ERROR GOTO 0 disables the handler."""
        result = helpers.execute_program(basic, [
            '10 ON ERROR GOTO 100',
            '20 ON ERROR GOTO 0',
            '30 PRINT 1/0',
            '40 END',
            '100 PRINT "SHOULD NOT REACH"',
        ])
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0
        texts = helpers.get_text_output(result)
        assert not any('SHOULD NOT REACH' in t for t in texts)

    def test_on_error_goto_0_inside_handler_reraises(self, basic, helpers):
        """ON ERROR GOTO 0 inside handler re-raises the error."""
        result = helpers.execute_program(basic, [
            '10 ON ERROR GOTO 100',
            '20 PRINT 1/0',
            '30 END',
            '100 ON ERROR GOTO 0',
        ])
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0

    def test_handler_fires_repeatedly(self, basic, helpers):
        """Handler fires for multiple errors."""
        result = helpers.execute_program(basic, [
            '10 ON ERROR GOTO 100',
            '20 PRINT 1/0',
            '30 PRINT 1/0',
            '40 PRINT "BOTH HANDLED"',
            '50 END',
            '100 RESUME NEXT',
        ])
        texts = helpers.get_text_output(result)
        assert any('BOTH HANDLED' in t for t in texts)

    def test_error_in_handler_halts(self, basic, helpers):
        """Error inside error handler halts (no re-entrant handling)."""
        result = helpers.execute_program(basic, [
            '10 ON ERROR GOTO 100',
            '20 PRINT 1/0',
            '30 END',
            '100 PRINT 1/0',
        ])
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0


class TestErrErl:
    """Test ERR and ERL pseudo-variables."""

    def test_erl_reflects_error_line(self, basic, helpers):
        """ERL returns the line number where the error occurred."""
        result = helpers.execute_program(basic, [
            '10 ON ERROR GOTO 100',
            '20 PRINT 1/0',
            '30 END',
            '100 PRINT ERL',
            '110 RESUME NEXT',
        ])
        texts = helpers.get_text_output(result)
        assert any('20' in t for t in texts)

    def test_err_reflects_error_code(self, basic, helpers):
        """ERR returns a numeric error code for the trapped error."""
        result = helpers.execute_program(basic, [
            '10 ON ERROR GOTO 100',
            '20 PRINT 1/0',
            '30 END',
            '100 PRINT ERR',
            '110 RESUME NEXT',
        ])
        texts = helpers.get_text_output(result)
        # Division by zero should give error code 99
        assert any('99' in t for t in texts)

    def test_err_erl_default_zero(self, basic):
        """ERR and ERL default to 0 before any error."""
        result = basic.process_command('PRINT ERR')
        assert any('0' in str(item.get('text', '')) for item in result)
        result = basic.process_command('PRINT ERL')
        assert any('0' in str(item.get('text', '')) for item in result)


class TestResumeErrors:
    """Test RESUME error conditions."""

    def test_resume_without_error(self, basic, helpers):
        """RESUME outside error handler gives error."""
        result = basic.process_command('RESUME')
        errors = helpers.get_error_messages(result)
        assert any('RESUME WITHOUT ERROR' in e for e in errors)

    def test_resume_next_without_error(self, basic, helpers):
        """RESUME NEXT outside error handler gives error."""
        result = basic.process_command('RESUME NEXT')
        errors = helpers.get_error_messages(result)
        assert any('RESUME WITHOUT ERROR' in e for e in errors)


class TestOnErrorSyntax:
    """Test ON ERROR GOTO syntax parsing."""

    def test_on_error_goto_registers(self, basic):
        """ON ERROR GOTO N sets the handler line."""
        basic.process_command('ON ERROR GOTO 100')
        assert basic.on_error_goto_line == 100

    def test_on_error_goto_0_clears(self, basic):
        """ON ERROR GOTO 0 clears the handler."""
        basic.process_command('ON ERROR GOTO 100')
        basic.process_command('ON ERROR GOTO 0')
        assert basic.on_error_goto_line is None

    def test_on_error_bad_syntax(self, basic, helpers):
        """ON ERROR without GOTO gives syntax error."""
        result = basic.process_command('ON ERROR 100')
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0
