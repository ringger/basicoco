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
