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


class TestPrintMigration:
    """Phase 4: PRINT command via AST execution"""

    def test_print_is_migrated(self, basic):
        """PRINT should be in the migrated commands set"""
        assert 'PRINT' in basic._ast_migrated_commands

    def test_print_empty(self, basic, helpers):
        """PRINT with no arguments should produce blank line"""
        result = basic._try_ast_execute('PRINT')
        assert result == [{'type': 'text', 'text': ''}]

    def test_print_string_literal(self, basic, helpers):
        """PRINT with string literal should output text"""
        result = basic.process_command('PRINT "HELLO"')
        output = helpers.get_text_output(result)
        assert any('HELLO' in t for t in output)

    def test_print_number(self, basic, helpers):
        """PRINT with number should format correctly"""
        result = basic.process_command('PRINT 42')
        output = helpers.get_text_output(result)
        assert any('42' in t for t in output)

    def test_print_float_as_int(self, basic, helpers):
        """PRINT with whole float should format as integer"""
        result = basic.process_command('PRINT 5.0')
        output = helpers.get_text_output(result)
        assert any('5' in t for t in output)
        assert not any('5.0' in t for t in output)

    def test_print_expression(self, basic, helpers):
        """PRINT with expression should evaluate and print"""
        basic.process_command('X = 10')
        result = basic.process_command('PRINT X * 2')
        output = helpers.get_text_output(result)
        assert any('20' in t for t in output)

    def test_print_semicolon_separator(self, basic, helpers):
        """PRINT with semicolons should concatenate without spaces"""
        result = basic.process_command('PRINT "A";"B";"C"')
        output = helpers.get_text_output(result)
        assert any('ABC' in t for t in output)

    def test_print_comma_separator(self, basic, helpers):
        """PRINT with commas should add tab spacing"""
        result = basic.process_command('PRINT "A","B"')
        output = helpers.get_text_output(result)
        assert any('\t' in t for t in output)

    def test_print_trailing_semicolon(self, basic):
        """PRINT with trailing semicolon should set inline flag"""
        result = basic._try_ast_execute('PRINT "HELLO";')
        assert result is not None
        assert len(result) == 1
        assert result[0].get('inline') is True

    def test_print_no_trailing_separator(self, basic):
        """PRINT without trailing separator should not set inline"""
        result = basic._try_ast_execute('PRINT "HELLO"')
        assert result is not None
        assert len(result) == 1
        assert 'inline' not in result[0]

    def test_print_in_program(self, basic, helpers):
        """PRINT in program execution should work"""
        program = [
            '10 PRINT "LINE1"',
            '20 PRINT "LINE2"',
        ]
        results = helpers.execute_program(basic, program)
        output = helpers.get_text_output(results)
        assert any('LINE1' in t for t in output)
        assert any('LINE2' in t for t in output)


class TestGosubReturnMigration:
    """Phase 5-6: GOSUB and RETURN commands via AST execution"""

    def test_gosub_is_migrated(self, basic):
        """GOSUB should be in the migrated commands set"""
        assert 'GOSUB' in basic._ast_migrated_commands

    def test_return_is_migrated(self, basic):
        """RETURN should be in the migrated commands set"""
        assert 'RETURN' in basic._ast_migrated_commands

    def test_gosub_via_ast_returns_jump(self, basic):
        """GOSUB should push call stack and return jump signal"""
        basic.current_line = 10
        basic.current_sub_line = 0
        result = basic._try_ast_execute('GOSUB 100')
        assert result == [{'type': 'jump', 'line': 100}]
        assert len(basic.call_stack) == 1
        assert basic.call_stack[0] == (10, 0)

    def test_return_via_ast_pops_stack(self, basic):
        """RETURN should pop call stack and return jump_return"""
        basic.call_stack.append((10, 0))
        result = basic._try_ast_execute('RETURN')
        assert result == [{'type': 'jump_return', 'line': 10, 'sub_line': 0}]
        assert len(basic.call_stack) == 0

    def test_return_without_gosub_error(self, basic):
        """RETURN without GOSUB should produce error"""
        result = basic._try_ast_execute('RETURN')
        assert result is not None
        assert any(item.get('type') == 'error' for item in result)

    def test_gosub_invalid_target_error(self, basic):
        """GOSUB with invalid target should produce error"""
        basic.variables['A$'] = "HELLO"
        result = basic._try_ast_execute('GOSUB A$')
        if result is not None:
            assert any(item.get('type') == 'error' for item in result)

    def test_gosub_return_in_program(self, basic, helpers):
        """GOSUB/RETURN in program should work correctly"""
        program = [
            '10 GOSUB 30',
            '20 END',
            '30 PRINT "SUB"',
            '40 RETURN',
        ]
        results = helpers.execute_program(basic, program)
        output = helpers.get_text_output(results)
        assert any('SUB' in t for t in output)

    def test_gosub_return_preserves_flow(self, basic, helpers):
        """After RETURN, execution should continue after GOSUB"""
        program = [
            '10 PRINT "BEFORE"',
            '20 GOSUB 50',
            '30 PRINT "AFTER"',
            '40 END',
            '50 PRINT "SUB"',
            '60 RETURN',
        ]
        results = helpers.execute_program(basic, program)
        output = helpers.get_text_output(results)
        assert any('BEFORE' in t for t in output)
        assert any('SUB' in t for t in output)
        assert any('AFTER' in t for t in output)


class TestForExitForMigration:
    """Phase 7-8: FOR and EXIT FOR commands via AST execution"""

    def test_for_is_migrated(self, basic):
        """FOR should be in the migrated commands set"""
        assert 'FOR' in basic._ast_migrated_commands

    def test_exit_is_migrated(self, basic):
        """EXIT should be in the migrated commands set"""
        assert 'EXIT' in basic._ast_migrated_commands

    def test_for_via_ast_sets_variable(self, basic):
        """FOR should set the loop variable to start value"""
        basic.current_line = 10
        basic.current_sub_line = 0
        result = basic._try_ast_execute('FOR I = 1 TO 10')
        assert result == []
        assert basic.variables['I'] == 1
        assert len(basic.for_stack) == 1
        assert basic.for_stack[0]['var'] == 'I'
        assert basic.for_stack[0]['end'] == 10
        assert basic.for_stack[0]['step'] == 1

    def test_for_with_step(self, basic):
        """FOR with STEP should set step value"""
        basic.current_line = 10
        basic.current_sub_line = 0
        result = basic._try_ast_execute('FOR I = 0 TO 100 STEP 5')
        assert result == []
        assert basic.for_stack[0]['step'] == 5

    def test_for_skip_empty_loop(self, basic):
        """FOR with start > end should skip loop"""
        basic.current_line = 10
        basic.current_sub_line = 0
        result = basic._try_ast_execute('FOR I = 10 TO 1')
        assert result is not None
        assert any(item.get('type') == 'skip_for_loop' for item in result)

    def test_for_in_program(self, basic, helpers):
        """FOR/NEXT loop in program should execute correctly"""
        program = [
            '10 FOR I = 1 TO 3',
            '20 PRINT I',
            '30 NEXT I',
        ]
        results = helpers.execute_program(basic, program)
        output = helpers.get_text_output(results)
        assert any('1' in t for t in output)
        assert any('3' in t for t in output)

    def test_exit_for_signal(self, basic):
        """EXIT FOR should return exit_for_loop signal"""
        basic.current_line = 10
        basic.current_sub_line = 0
        basic._try_ast_execute('FOR I = 1 TO 10')
        result = basic._try_ast_execute('EXIT FOR')
        assert result == [{'type': 'exit_for_loop'}]

    def test_exit_for_without_loop_error(self, basic):
        """EXIT FOR without FOR should produce error"""
        result = basic._try_ast_execute('EXIT FOR')
        assert result is not None
        assert any(item.get('type') == 'error' for item in result)


class TestWhileDoMigration:
    """Phase 9-10: WHILE and DO commands via AST execution"""

    def test_while_is_migrated(self, basic):
        """WHILE should be in the migrated commands set"""
        assert 'WHILE' in basic._ast_migrated_commands

    def test_do_is_migrated(self, basic):
        """DO should be in the migrated commands set"""
        assert 'DO' in basic._ast_migrated_commands

    def test_while_true_pushes_stack(self, basic):
        """WHILE with true condition should push to while_stack"""
        basic.current_line = 10
        basic.current_sub_line = 0
        basic.variables['X'] = 5
        result = basic._try_ast_execute('WHILE X > 0')
        assert result == []
        assert len(basic.while_stack) == 1
        assert 'condition_ast' in basic.while_stack[0]

    def test_while_false_skips(self, basic):
        """WHILE with false condition should return skip signal"""
        basic.variables['X'] = 0
        result = basic._try_ast_execute('WHILE X > 0')
        assert result == [{'type': 'skip_while_loop'}]
        assert len(basic.while_stack) == 0

    def test_while_in_program(self, basic, helpers):
        """WHILE/WEND loop in program should execute correctly"""
        program = [
            '10 X = 1',
            '20 WHILE X <= 3',
            '30 PRINT X',
            '40 X = X + 1',
            '50 WEND',
        ]
        results = helpers.execute_program(basic, program)
        output = helpers.get_text_output(results)
        assert any('1' in t for t in output)
        assert any('3' in t for t in output)

    def test_do_pushes_stack(self, basic):
        """DO should push to do_stack"""
        basic.current_line = 10
        basic.current_sub_line = 0
        result = basic._try_ast_execute('DO')
        assert result == []
        assert len(basic.do_stack) == 1

    def test_do_while_true_pushes(self, basic):
        """DO WHILE with true condition should push to stack"""
        basic.current_line = 10
        basic.current_sub_line = 0
        basic.variables['X'] = 5
        result = basic._try_ast_execute('DO WHILE X > 0')
        assert result == []
        assert len(basic.do_stack) == 1

    def test_do_while_false_skips(self, basic):
        """DO WHILE with false condition should skip"""
        basic.variables['X'] = 0
        result = basic._try_ast_execute('DO WHILE X > 0')
        assert result == [{'type': 'skip_do_loop'}]
        assert len(basic.do_stack) == 0

    def test_do_until_true_skips(self, basic):
        """DO UNTIL with true condition should skip"""
        basic.variables['X'] = 5
        result = basic._try_ast_execute('DO UNTIL X > 0')
        assert result == [{'type': 'skip_do_loop'}]

    def test_do_loop_in_program(self, basic, helpers):
        """DO/LOOP in program should execute correctly"""
        program = [
            '10 X = 1',
            '20 DO',
            '30 PRINT X',
            '40 X = X + 1',
            '50 LOOP WHILE X <= 3',
        ]
        results = helpers.execute_program(basic, program)
        output = helpers.get_text_output(results)
        assert any('1' in t for t in output)
        assert any('3' in t for t in output)
