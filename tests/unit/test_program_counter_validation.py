"""Tests for program counter validation when resuming after edits."""

import pytest


class TestProgramCounterValidation:
    """Test that program counter is validated when resuming execution."""

    def test_resume_after_deleting_paused_line(self, basic, helpers):
        """Resuming after the paused-at line was deleted should give an error."""
        helpers.load_program(basic, [
            '10 INPUT "NAME"; N$',
            '20 PRINT N$',
        ])
        result = basic.process_command('RUN')

        # Program is waiting for input at line 10
        assert basic.waiting_for_input

        # Delete the program and replace with something else
        basic.program.clear()
        basic.expanded_program.clear()
        basic.process_command('10 PRINT "DIFFERENT"')

        # Set a bogus program_counter that doesn't exist
        basic.program_counter = (99, 0)
        basic.waiting_for_input = False

        result = basic.continue_program_execution()
        errors = helpers.get_error_messages(result)
        assert any('modified' in e.lower() for e in errors)

    def test_cont_after_stop_with_deleted_line(self, basic, helpers):
        """CONT after STOP should handle missing lines gracefully."""
        helpers.load_program(basic, [
            '10 PRINT "A"',
            '20 STOP',
            '30 PRINT "B"',
        ])
        result = basic.process_command('RUN')
        text = helpers.get_text_output(result)
        assert 'A' in text

        # Delete line 30 (where CONT would resume)
        basic.process_command('30')  # Delete line 30

        result = basic.process_command('CONT')
        # Should handle gracefully (either error or READY, not crash)
        assert result is not None
