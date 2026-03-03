"""
Tests for registry commands and file I/O commands inside control structure bodies.

Verifies that the AST converter correctly preserves command arguments when
commands appear inside IF/THEN, FOR, WHILE, and DO loop bodies. These commands
are handled by the command registry, not the AST parser, so the converter must
pass them through verbatim.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from emulator.ast_converter import parse_and_convert_single_line
from emulator.ast_parser import ASTParser


class TestRegistryCommandsInForBodies:
    """Registry commands in FOR loop bodies should preserve arguments."""

    def setup_method(self):
        self.parser = ASTParser()

    def test_sound_in_for_body(self):
        result = parse_and_convert_single_line(
            'FOR I=1 TO 3: SOUND 440,1: NEXT I', self.parser)
        assert 'SOUND 440,1' in result

    def test_sound_with_expressions_in_for_body(self):
        result = parse_and_convert_single_line(
            'FOR I=1 TO 3: SOUND F1+RF,8: NEXT I', self.parser)
        assert 'SOUND F1+RF,8' in result

    def test_dim_in_for_body(self):
        """DIM should not be parsed as a variable"""
        result = parse_and_convert_single_line(
            'FOR I=1 TO 3: DIM A(I): NEXT I', self.parser)
        assert 'DIM A(I)' in result


class TestRegistryCommandsInWhileBodies:
    """Registry commands in WHILE loop bodies should preserve arguments."""

    def setup_method(self):
        self.parser = ASTParser()

    def test_sound_in_while_body(self):
        result = parse_and_convert_single_line(
            'WHILE X<10: SOUND X*100,1: X=X+1: WEND', self.parser)
        assert 'SOUND X*100,1' in result


class TestRegistryCommandsInDoBodies:
    """Registry commands in DO loop bodies should preserve arguments."""

    def setup_method(self):
        self.parser = ASTParser()

    def test_sound_in_do_body(self):
        result = parse_and_convert_single_line(
            'DO: SOUND 440,1: LOOP UNTIL X>10', self.parser)
        assert 'SOUND 440,1' in result


class TestFileIOInIfThenBodies:
    """File I/O commands in IF/THEN bodies must not be mis-parsed by the AST.

    PRINT# would be silently converted to PRINT (dropping the #) if the AST
    parser's PRINT handler processes it. These commands need process_statement()
    intercepts at runtime.
    """

    def setup_method(self):
        self.parser = ASTParser()

    def test_print_hash_preserved(self):
        result = parse_and_convert_single_line(
            'IF F>0 THEN PRINT# 1, X', self.parser)
        assert 'PRINT# 1, X' in result

    def test_print_hash_with_space_preserved(self):
        result = parse_and_convert_single_line(
            'IF F>0 THEN PRINT # 1, X', self.parser)
        assert 'PRINT # 1, X' in result

    def test_input_hash_preserved(self):
        result = parse_and_convert_single_line(
            'IF F>0 THEN INPUT# 1, X', self.parser)
        assert 'INPUT# 1, X' in result

    def test_line_input_preserved(self):
        result = parse_and_convert_single_line(
            'IF F>0 THEN LINE INPUT A$', self.parser)
        assert 'LINE INPUT A$' in result

    def test_print_hash_in_else_body(self):
        result = parse_and_convert_single_line(
            'IF F=0 THEN PRINT "NO FILE" ELSE PRINT# 1, X', self.parser)
        assert 'PRINT# 1, X' in result

    def test_print_hash_with_colon(self):
        """PRINT# followed by other statements via colon"""
        result = parse_and_convert_single_line(
            'IF F>0 THEN PRINT# 1, X: Y=Y+1', self.parser)
        assert 'PRINT# 1, X' in result
        assert 'LET Y = Y + 1' in result

    def test_regular_print_still_ast_parsed(self):
        """Regular PRINT should still go through AST for proper formatting"""
        result = parse_and_convert_single_line(
            'IF A=1 THEN PRINT "HELLO"', self.parser)
        assert 'PRINT "HELLO"' in result


class TestFileIOInForBodies:
    """File I/O commands in FOR loop bodies."""

    def setup_method(self):
        self.parser = ASTParser()

    def test_print_hash_in_for_body(self):
        result = parse_and_convert_single_line(
            'FOR I=1 TO 5: PRINT# 1, I: NEXT I', self.parser)
        assert 'PRINT# 1, I' in result

    def test_input_hash_in_for_body(self):
        result = parse_and_convert_single_line(
            'FOR I=1 TO 5: INPUT# 1, X: NEXT I', self.parser)
        assert 'INPUT# 1, X' in result


class TestFileIOInWhileBodies:
    """File I/O commands in WHILE loop bodies."""

    def setup_method(self):
        self.parser = ASTParser()

    def test_print_hash_in_while_body(self):
        result = parse_and_convert_single_line(
            'WHILE NOT EOF(1): INPUT# 1, X: WEND', self.parser)
        assert 'INPUT# 1, X' in result


class TestImmediateModeIfConsistency:
    """Verify immediate mode IF/THEN uses the same AST conversion as program mode."""

    def test_immediate_if_then_converted(self, basic, helpers):
        """Immediate mode IF/THEN without colons should be AST-converted"""
        result = basic.process_command('IF 1=1 THEN PRINT "OK"')
        text = helpers.get_text_output(result)
        assert 'OK' in text

    def test_immediate_if_then_else(self, basic, helpers):
        """Immediate mode IF/THEN/ELSE should work"""
        result = basic.process_command('IF 0=1 THEN PRINT "NO" ELSE PRINT "YES"')
        text = helpers.get_text_output(result)
        assert 'YES' in text
        assert 'NO' not in text
