#!/usr/bin/env python3

"""
Unit tests for execution dispatch routing in process_command, process_line,
and process_statement.
"""

import pytest
from emulator.error_context import error_response, text_response


class TestProcessCommandRouting:
    """Test that process_command routes inputs to the correct handler"""

    def test_empty_command(self, basic):
        result = basic.process_command('')
        assert result == []

    def test_whitespace_command(self, basic):
        result = basic.process_command('   ')
        assert result == []

    def test_numbered_line_stores_in_program(self, basic):
        result = basic.process_command('10 PRINT "HELLO"')
        assert 10 in basic.program
        assert basic.program[10] == 'PRINT "HELLO"'
        # Should return system OK
        assert any(item.get('source') == 'system' for item in result)

    def test_numbered_line_expands_sublines(self, basic):
        basic.process_command('10 A = 5: B = 10')
        assert (10, 0) in basic.expanded_program
        assert (10, 1) in basic.expanded_program

    def test_empty_numbered_line_deletes(self, basic):
        basic.process_command('10 PRINT "HELLO"')
        assert 10 in basic.program
        basic.process_command('10')
        assert 10 not in basic.program

    def test_multi_statement_routes_to_process_line(self, basic, helpers):
        """Multi-statement lines should bypass registry and go to process_line"""
        result = basic.process_command('A = 5: B = 10')
        helpers.assert_variable_equals(basic, 'A', 5)
        helpers.assert_variable_equals(basic, 'B', 10)

    def test_registry_command_hits_registry(self, basic, helpers):
        """Single registry commands should be handled by the registry"""
        basic.process_command('DIM X(5)')
        assert 'X' in basic.arrays

    def test_registry_command_with_colon_bypasses_registry(self, basic, helpers):
        """Registry command + colon should go through process_line, not registry"""
        basic.process_command('DIM Y(3): Y(0) = 42')
        assert 'Y' in basic.arrays
        helpers.assert_array_element_equals(basic, 'Y', [0], 42)

    def test_ast_command_falls_through(self, basic, helpers):
        """AST-migrated commands (like PRINT) should work via fallthrough"""
        result = basic.process_command('PRINT "DISPATCH TEST"')
        text = helpers.get_text_output(result)
        assert text == ['DISPATCH TEST']

    def test_rem_with_colons_not_treated_as_multi(self, basic, helpers):
        """REM lines with colons should NOT be detected as multi-statement"""
        result = basic.process_command('REM A:B:C')
        errors = helpers.get_error_messages(result)
        assert len(errors) == 0

    def test_unrecognized_command_returns_error(self, basic, helpers):
        result = basic.process_command('XYZZY')
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0


class TestProcessLineDispatch:
    """Test that process_line routes to the correct execution path"""

    def test_rem_goes_to_process_statement(self, basic, helpers):
        """REM lines should go directly to process_statement (no splitting)"""
        result = basic.process_line('REM This: has: colons: and GOTO 100')
        errors = helpers.get_error_messages(result)
        assert len(errors) == 0

    def test_single_statement_goes_to_process_statement(self, basic, helpers):
        """Single statements should go directly to process_statement"""
        result = basic.process_line('PRINT "SINGLE"')
        text = helpers.get_text_output(result)
        assert text == ['SINGLE']

    def test_control_structure_with_colons_uses_ast(self, basic, helpers):
        """Control structures with colons should use AST conversion path"""
        basic.variables['X'] = 0
        result = basic.process_line('FOR I = 1 TO 3: X = X + I: NEXT I')
        # X should be 1+2+3 = 6
        helpers.assert_variable_equals(basic, 'X', 6)

    def test_if_with_colons_uses_ast(self, basic, helpers):
        result = basic.process_line('IF 1=1 THEN PRINT "YES": PRINT "ALSO"')
        text = helpers.get_text_output(result)
        assert 'YES' in text

    def test_while_with_colons_uses_ast(self, basic, helpers):
        basic.variables['N'] = 0
        result = basic.process_line('WHILE N<3: N=N+1: WEND')
        helpers.assert_variable_equals(basic, 'N', 3)

    def test_do_with_colons_uses_ast(self, basic, helpers):
        basic.variables['M'] = 0
        result = basic.process_line('DO: M=M+1: LOOP WHILE M<3')
        helpers.assert_variable_equals(basic, 'M', 3)

    def test_multi_statement_executes_sequentially(self, basic, helpers):
        """Plain multi-statement lines should execute each in order"""
        result = basic.process_line('A = 1: B = 2: C = A + B')
        helpers.assert_variable_equals(basic, 'A', 1)
        helpers.assert_variable_equals(basic, 'B', 2)
        helpers.assert_variable_equals(basic, 'C', 3)

    def test_multi_statement_collects_all_results(self, basic, helpers):
        """Results from all statements should be collected"""
        result = basic.process_line('PRINT "ONE": PRINT "TWO"')
        text = helpers.get_text_output(result)
        assert 'ONE' in text
        assert 'TWO' in text

    def test_multi_statement_stops_on_error(self, basic, helpers):
        """Error in a statement should stop subsequent statements"""
        basic.variables['Z'] = 0
        result = basic.process_line('A = 1: UNDIM(999) = 5: Z = 99')
        helpers.assert_variable_equals(basic, 'A', 1)
        helpers.assert_variable_equals(basic, 'Z', 0)  # Should not execute
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0

    def test_multi_statement_stops_on_jump(self, basic, helpers):
        """Jump directive should stop subsequent statements"""
        basic.variables['W'] = 0
        result = basic.process_line('PRINT "HI": GOTO 100: W = 99')
        helpers.assert_variable_equals(basic, 'W', 0)
        has_jump = any(item.get('type') == 'jump' for item in result)
        assert has_jump


class TestProcessStatementDispatch:
    """Test process_statement dispatch order: multi-line IF → AST → registry → error"""

    def test_multiline_if_handled_first(self, basic, helpers):
        """Bare 'IF cond THEN' should be handled as multi-line IF"""
        result = basic.process_statement('IF 1=1 THEN')
        # Should push to if_stack (condition met, no skip)
        assert len(basic.if_stack) == 1
        assert basic.if_stack[-1]['condition_met'] is True

    def test_multiline_if_false_returns_skip(self, basic, helpers):
        """False multi-line IF should return skip directive"""
        result = basic.process_statement('IF 0=1 THEN')
        assert len(basic.if_stack) == 1
        assert basic.if_stack[-1]['condition_met'] is False
        assert any(item.get('type') == 'skip_if_block' for item in result)

    def test_ast_command_dispatched(self, basic, helpers):
        """PRINT (AST-migrated) should be handled by AST path"""
        result = basic.process_statement('PRINT "AST"')
        text = helpers.get_text_output(result)
        assert text == ['AST']

    def test_goto_dispatched_to_ast(self, basic, helpers):
        """GOTO should be handled by AST path and return jump directive"""
        result = basic.process_statement('GOTO 100')
        assert any(item.get('type') == 'jump' for item in result)

    def test_implicit_assignment_dispatched_to_ast(self, basic, helpers):
        """Implicit assignment (no LET) should be handled by AST"""
        basic.process_statement('X = 42')
        helpers.assert_variable_equals(basic, 'X', 42)

    def test_registry_command_dispatched(self, basic, helpers):
        """DIM (registry command) should be handled by registry"""
        basic.process_statement('DIM Q(5)')
        assert 'Q' in basic.arrays

    def test_next_dispatched_to_registry(self, basic, helpers):
        """NEXT should be handled by registry"""
        result = basic.process_statement('NEXT I')
        # Should produce NEXT WITHOUT FOR error since no FOR is active
        errors = helpers.get_error_messages(result)
        assert any('NEXT WITHOUT FOR' in e for e in errors)

    def test_unrecognized_returns_syntax_error(self, basic, helpers):
        """Unrecognized command should return syntax error"""
        result = basic.process_statement('FROBULATE 42')
        errors = helpers.get_error_messages(result)
        assert len(errors) > 0
        assert any('Unrecognized' in e for e in errors)

    def test_empty_statement_returns_empty(self, basic):
        """Empty statement should return empty list"""
        result = basic.process_statement('')
        assert result == []

    def test_whitespace_only_returns_empty(self, basic):
        result = basic.process_statement('   ')
        assert result == []


class TestResponseBuilders:
    """Test error_response and text_response helpers"""

    def test_error_response_format(self, basic):
        error = basic.error_context.syntax_error("TEST ERROR")
        result = error_response(error)
        assert len(result) == 1
        assert result[0]['type'] == 'error'
        assert 'TEST ERROR' in result[0]['message']

    def test_text_response_format(self):
        result = text_response('HELLO')
        assert result == [{'type': 'text', 'text': 'HELLO'}]

    def test_text_response_empty_string(self):
        result = text_response('')
        assert result == [{'type': 'text', 'text': ''}]


class TestStateManagement:
    """Test save/restore execution state and clear_all_stacks"""

    def test_clear_all_stacks(self, basic):
        basic.for_stack.append({'var': 'I'})
        basic.call_stack.append({'line': 10})
        basic.if_stack.append({'condition_met': True})
        basic.while_stack.append({'line': 20})
        basic.do_stack.append({'line': 30})

        basic.clear_all_stacks()

        assert len(basic.for_stack) == 0
        assert len(basic.call_stack) == 0
        assert len(basic.if_stack) == 0
        assert len(basic.while_stack) == 0
        assert len(basic.do_stack) == 0

    def test_save_restore_execution_state(self, basic):
        """save/restore should preserve program, stacks, and position"""
        basic.process_command('10 PRINT "A"')
        basic.process_command('20 PRINT "B"')
        basic.for_stack.append({'var': 'I'})
        basic.current_line = 10
        basic.running = True

        state = basic.save_execution_state()

        # Mutate everything
        basic.program.clear()
        basic.expanded_program.clear()
        basic.for_stack.clear()
        basic.current_line = 99
        basic.running = False

        basic.restore_execution_state(state)

        assert 10 in basic.program
        assert 20 in basic.program
        assert len(basic.for_stack) == 1
        assert basic.current_line == 10
        assert basic.running is True

    def test_save_restore_does_not_share_references(self, basic):
        """Saved state should be independent copies"""
        basic.for_stack.append({'var': 'I'})
        state = basic.save_execution_state()

        basic.for_stack.append({'var': 'J'})

        assert len(state['for_stack']) == 1  # Saved copy unaffected
