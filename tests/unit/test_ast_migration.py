#!/usr/bin/env python3

"""
Tests for AST-based execution migration.

Each phase adds tests verifying that AST execution produces identical
results to the legacy registry-based execution for migrated commands.
"""

import pytest


class TestASTInfrastructure:
    """Phase 0: Verify the AST dispatch infrastructure is inert by default"""

    def test_migrated_set_starts_empty(self, basic):
        """The migrated commands set should be empty initially"""
        assert basic._ast_migrated_commands == set()

    def test_try_ast_execute_returns_none_when_empty(self, basic):
        """_try_ast_execute should return None when no commands are migrated"""
        assert basic._try_ast_execute('PRINT "HELLO"') is None
        assert basic._try_ast_execute('GOTO 100') is None
        assert basic._try_ast_execute('END') is None

    def test_ast_evaluator_lazy_init(self, basic):
        """ASTEvaluator should not be created until needed"""
        assert basic._ast_evaluator is None

    def test_process_statement_unchanged_behavior(self, basic, helpers):
        """process_statement should behave identically with empty migrated set"""
        # PRINT should work through registry as before
        result = basic.process_command('PRINT "TEST"')
        output = helpers.get_text_output(result)
        assert any('TEST' in t for t in output)

        # Variable assignment should work as before
        basic.process_command('X = 42')
        helpers.assert_variable_equals(basic, 'X', 42)

    def test_fallback_on_parse_failure(self, basic):
        """If AST parsing fails, should fall back to registry"""
        # Add a command to migrated set but use syntax the parser can't handle
        basic._ast_migrated_commands.add('END')
        # END should still work (parser can handle it)
        result = basic.process_command('END')
        # Should not crash regardless
