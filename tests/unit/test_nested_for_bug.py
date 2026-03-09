"""
Minimal reproduction test for nested FOR with multi-dim array access bug.

Bug: FOR IX=0 TO 2: FOR IY=0 TO 2: FOR IZ=0 TO 2: FOR F=0 TO 5
     followed by CL(IX,IY,IZ,F)=-1 on the next line causes BAD SUBSCRIPT.
     Same code works when each FOR is on its own line.

Root cause: _parse_ast_for_statement in ast_converter.py splits the body
on colons and treats each inner FOR as a flat body statement. The converter
then wraps each inner FOR with its own NEXT, making them self-contained
empty loops. The loop variables reach past-end values before execution
reaches the next program line.

Expected converter output for "FOR IX=0 TO 2: FOR IY=0 TO 2":
    FOR IX = 0 TO 2
    FOR IY = 0 TO 2

Actual converter output (buggy):
    FOR IX = 0 TO 2
    FOR IY = 0 TO 2
    NEXT IY          <-- spurious, makes IY loop self-contained
    NEXT IX
"""

import pytest


class TestNestedForColonBug:
    """Reproduce the single-line nested FOR with multi-dim array bug."""

    def test_separate_lines_works(self, basic, helpers):
        """Baseline: each FOR on its own line works correctly."""
        results = helpers.execute_program(basic, [
            '10 DIM CL(2,2,2,5)',
            '20 FOR IX=0 TO 2',
            '30 FOR IY=0 TO 2',
            '40 FOR IZ=0 TO 2',
            '50 FOR F=0 TO 5',
            '60 CL(IX,IY,IZ,F)=-1',
            '70 NEXT F',
            '80 NEXT IZ',
            '90 NEXT IY',
            '100 NEXT IX',
            '110 PRINT "DONE"',
        ])
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Expected no errors, got: {errors}"
        texts = helpers.get_text_output(results)
        assert any("DONE" in t for t in texts)

    def test_all_fors_on_one_line(self, basic, helpers):
        """All four FORs on one line via colons, body on subsequent lines."""
        results = helpers.execute_program(basic, [
            '10 DIM CL(2,2,2,5)',
            '20 FOR IX=0 TO 2: FOR IY=0 TO 2: FOR IZ=0 TO 2: FOR F=0 TO 5',
            '30 CL(IX,IY,IZ,F)=-1',
            '40 NEXT F',
            '50 NEXT IZ',
            '60 NEXT IY',
            '70 NEXT IX',
            '80 PRINT "DONE"',
        ])
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Expected no errors, got: {errors}"
        texts = helpers.get_text_output(results)
        assert any("DONE" in t for t in texts)

    def test_two_fors_on_one_line(self, basic, helpers):
        """Two FORs on one line -- minimal reproduction."""
        results = helpers.execute_program(basic, [
            '10 DIM CL(2,2)',
            '20 FOR IX=0 TO 2: FOR IY=0 TO 2',
            '30 CL(IX,IY)=-1',
            '40 NEXT IY',
            '50 NEXT IX',
            '60 PRINT "DONE"',
        ])
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Expected no errors, got: {errors}"
        texts = helpers.get_text_output(results)
        assert any("DONE" in t for t in texts)

    def test_three_fors_on_one_line(self, basic, helpers):
        """Three FORs on one line."""
        results = helpers.execute_program(basic, [
            '10 DIM CL(2,2,2)',
            '20 FOR IX=0 TO 2: FOR IY=0 TO 2: FOR IZ=0 TO 2',
            '30 CL(IX,IY,IZ)=-1',
            '40 NEXT IZ',
            '50 NEXT IY',
            '60 NEXT IX',
            '70 PRINT "DONE"',
        ])
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Expected no errors, got: {errors}"
        texts = helpers.get_text_output(results)
        assert any("DONE" in t for t in texts)

    def test_simple_variable_not_array(self, basic, helpers):
        """Bug affects simple variables too, not just arrays."""
        results = helpers.execute_program(basic, [
            '10 FOR IX=0 TO 2: FOR IY=0 TO 2',
            '20 PRINT IX;IY',
            '30 NEXT IY',
            '40 NEXT IX',
        ])
        errors = helpers.get_error_messages(results)
        assert errors == [], f"Expected no errors, got: {errors}"

    def test_converter_no_spurious_next_two_fors(self, basic):
        """Open FORs produce no NEXT — body continues on subsequent lines."""
        from emulator.ast_converter import parse_and_convert_single_line
        result = parse_and_convert_single_line(
            'FOR IX=0 TO 2: FOR IY=0 TO 2',
            basic.ast_parser
        )
        assert result is not None
        next_stmts = [s for s in result if s.strip().upper().startswith('NEXT')]
        assert len(next_stmts) == 0, f"Expected no NEXTs, got: {next_stmts}"
        for_stmts = [s for s in result if s.strip().upper().startswith('FOR')]
        assert len(for_stmts) == 2

    def test_converter_no_spurious_next_four_fors(self, basic):
        """Four open FORs produce no NEXTs."""
        from emulator.ast_converter import parse_and_convert_single_line
        result = parse_and_convert_single_line(
            'FOR IX=0 TO 2: FOR IY=0 TO 2: FOR IZ=0 TO 2: FOR F=0 TO 5',
            basic.ast_parser
        )
        assert result is not None
        for_stmts = [s for s in result if s.strip().upper().startswith('FOR')]
        next_stmts = [s for s in result if s.strip().upper().startswith('NEXT')]
        assert len(for_stmts) == 4
        assert len(next_stmts) == 0, f"Expected no NEXTs, got: {next_stmts}"
