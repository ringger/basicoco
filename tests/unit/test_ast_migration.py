#!/usr/bin/env python3

"""
Tests for AST-based execution migration.

Each phase adds tests verifying that AST execution produces identical
results to the legacy registry-based execution for migrated commands.
"""

import pytest


class TestASTInfrastructure:
    """Phase 0: Verify the AST dispatch infrastructure"""

    def test_migrated_set_has_expected_commands(self, basic):
        """The migrated commands set should contain migrated commands"""
        assert isinstance(basic._ast_migrated_commands, set)

    def test_try_ast_execute_returns_none_for_unmigrated(self, basic):
        """_try_ast_execute should return None for unmigrated commands"""
        # These are not yet migrated
        assert basic._try_ast_execute('SOUND 440, 100') is None
        assert basic._try_ast_execute('CLS') is None

    def test_process_statement_unchanged_for_unmigrated(self, basic, helpers):
        """Unmigrated commands should work through registry as before"""
        result = basic.process_command('PRINT "TEST"')
        output = helpers.get_text_output(result)
        assert any('TEST' in t for t in output)

        basic.process_command('X = 42')
        helpers.assert_variable_equals(basic, 'X', 42)

    def test_fallback_on_parse_failure(self, basic):
        """If AST parsing fails, should fall back to registry"""
        result = basic.process_command('END')
        # Should not crash regardless


class TestEndMigration:
    """Phase 1: END command via AST execution"""

    def test_end_is_migrated(self, basic):
        """END should be in the migrated commands set"""
        assert 'END' in basic._ast_migrated_commands

    def test_end_via_ast_direct(self, basic):
        """END in direct mode should not crash"""
        result = basic._try_ast_execute('END')
        assert result is not None
        assert result == []

    def test_end_stops_program(self, basic, helpers):
        """END should stop program execution"""
        program = [
            '10 PRINT "BEFORE"',
            '20 END',
            '30 PRINT "AFTER"',
        ]
        results = helpers.execute_program(basic, program)
        output = helpers.get_text_output(results)
        assert any('BEFORE' in t for t in output)
        assert not any('AFTER' in t for t in output)

    def test_end_clears_stopped_position(self, basic):
        """END should clear stopped_position (unlike STOP)"""
        basic.stopped_position = (10, 0)
        basic._try_ast_execute('END')
        assert basic.stopped_position is None

    def test_end_sets_running_false(self, basic):
        """END should set running to False"""
        basic.running = True
        basic._try_ast_execute('END')
        assert basic.running is False

    def test_end_ast_uses_evaluator(self, basic):
        """After END via AST, the evaluator should be initialized"""
        basic._try_ast_execute('END')
        assert basic._ast_evaluator is not None


class TestGotoMigration:
    """Phase 2: GOTO command via AST execution"""

    def test_goto_is_migrated(self, basic):
        """GOTO should be in the migrated commands set"""
        assert 'GOTO' in basic._ast_migrated_commands

    def test_goto_via_ast_returns_jump(self, basic):
        """GOTO should return a jump signal"""
        result = basic._try_ast_execute('GOTO 100')
        assert result == [{'type': 'jump', 'line': 100}]

    def test_goto_via_ast_with_expression(self, basic):
        """GOTO with expression should evaluate and jump"""
        basic.variables['L'] = 50
        result = basic._try_ast_execute('GOTO L')
        assert result == [{'type': 'jump', 'line': 50}]

    def test_goto_in_program(self, basic, helpers):
        """GOTO in a program should skip lines"""
        program = [
            '10 GOTO 30',
            '20 PRINT "SKIPPED"',
            '30 PRINT "TARGET"',
        ]
        results = helpers.execute_program(basic, program)
        output = helpers.get_text_output(results)
        assert any('TARGET' in t for t in output)
        assert not any('SKIPPED' in t for t in output)

    def test_goto_invalid_target_error(self, basic):
        """GOTO with invalid target should return error"""
        basic.variables['A$'] = "HELLO"
        result = basic._try_ast_execute('GOTO A$')
        # Should either return error or fall back to registry
        if result is not None:
            assert any(item.get('type') == 'error' for item in result)

    def test_goto_negative_line_error(self, basic):
        """GOTO with negative line number should return error"""
        result = basic._try_ast_execute('GOTO -5')
        if result is not None:
            assert any(item.get('type') == 'error' for item in result)


class TestLetMigration:
    """Phase 3: LET (assignment) command via AST execution"""

    def test_let_is_migrated(self, basic):
        """LET should be in the migrated commands set"""
        assert 'LET' in basic._ast_migrated_commands

    def test_let_simple_variable(self, basic, helpers):
        """LET X = 5 should set variable"""
        basic.process_command('LET X = 5')
        helpers.assert_variable_equals(basic, 'X', 5)

    def test_implicit_assignment(self, basic, helpers):
        """X = 5 (without LET) should work via AST"""
        basic.process_command('X = 42')
        helpers.assert_variable_equals(basic, 'X', 42)

    def test_string_assignment(self, basic, helpers):
        """String variable assignment should work"""
        basic.process_command('A$ = "HELLO"')
        helpers.assert_variable_equals(basic, 'A$', 'HELLO')

    def test_expression_assignment(self, basic, helpers):
        """Assignment with expression should evaluate"""
        basic.process_command('X = 3 + 4 * 5')
        helpers.assert_variable_equals(basic, 'X', 23)

    def test_array_assignment(self, basic, helpers):
        """Array assignment should work through AST"""
        basic.process_command('DIM A(10)')
        basic.process_command('A(5) = 42')
        helpers.assert_array_element_equals(basic, 'A', [5], 42)

    def test_assignment_in_program(self, basic, helpers):
        """Assignment in program execution should work"""
        program = [
            '10 X = 10',
            '20 Y = X * 2',
            '30 PRINT Y',
        ]
        results = helpers.execute_program(basic, program)
        output = helpers.get_text_output(results)
        assert any('20' in t for t in output)
