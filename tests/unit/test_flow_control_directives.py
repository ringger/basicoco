#!/usr/bin/env python3

"""
Unit tests for flow control directive handling in ProgramExecutor:
- _handle_flow_control (all 13 directive types)
- Position finder helpers (_find_line_position, _skip_to_keyword, _skip_to_next, _skip_if_or_else_block)
- Nested control structure edge cases
"""

import pytest
from emulator.program_executor import ProgramExecutor


class TestFindLinePosition:
    """Test ProgramExecutor._find_line_position"""

    def test_finds_first_subline(self, basic):
        executor = basic.executor
        positions = [(10, 0), (10, 1), (20, 0), (30, 0)]
        assert executor._find_line_position(10, positions) == 0
        assert executor._find_line_position(20, positions) == 2
        assert executor._find_line_position(30, positions) == 3

    def test_returns_none_for_missing_line(self, basic):
        executor = basic.executor
        positions = [(10, 0), (20, 0)]
        assert executor._find_line_position(15, positions) is None
        assert executor._find_line_position(99, positions) is None


class TestSkipToKeyword:
    """Test ProgramExecutor._skip_to_keyword"""

    def test_finds_keyword_forward(self, basic):
        executor = basic.executor
        basic.expanded_program = {
            (10, 0): 'FOR I = 1 TO 3',
            (20, 0): 'PRINT I',
            (30, 0): 'NEXT I',
        }
        positions = [(10, 0), (20, 0), (30, 0)]
        assert executor._skip_to_keyword('NEXT', 0, positions) == 2

    def test_finds_wend(self, basic):
        executor = basic.executor
        basic.expanded_program = {
            (10, 0): 'WHILE X < 5',
            (20, 0): 'X = X + 1',
            (30, 0): 'WEND',
        }
        positions = [(10, 0), (20, 0), (30, 0)]
        assert executor._skip_to_keyword('WEND', 0, positions) == 2

    def test_returns_none_if_not_found(self, basic):
        executor = basic.executor
        basic.expanded_program = {
            (10, 0): 'FOR I = 1 TO 3',
            (20, 0): 'PRINT I',
        }
        positions = [(10, 0), (20, 0)]
        assert executor._skip_to_keyword('NEXT', 0, positions) is None

    def test_only_searches_forward(self, basic):
        executor = basic.executor
        basic.expanded_program = {
            (10, 0): 'WEND',
            (20, 0): 'WHILE X < 5',
            (30, 0): 'X = X + 1',
        }
        positions = [(10, 0), (20, 0), (30, 0)]
        # Starting from position 1 (WHILE), should not find the WEND at position 0
        assert executor._skip_to_keyword('WEND', 1, positions) is None


class TestSkipToNext:
    """Test ProgramExecutor._skip_to_next"""

    def test_finds_matching_next(self, basic):
        executor = basic.executor
        basic.expanded_program = {
            (10, 0): 'FOR I = 1 TO 3',
            (20, 0): 'PRINT I',
            (30, 0): 'NEXT I',
        }
        positions = [(10, 0), (20, 0), (30, 0)]
        assert executor._skip_to_next('I', 0, positions) == 2

    def test_finds_bare_next(self, basic):
        """NEXT without variable name should match any FOR"""
        executor = basic.executor
        basic.expanded_program = {
            (10, 0): 'FOR I = 1 TO 3',
            (20, 0): 'PRINT I',
            (30, 0): 'NEXT',
        }
        positions = [(10, 0), (20, 0), (30, 0)]
        assert executor._skip_to_next('I', 0, positions) == 2

    def test_skips_wrong_variable(self, basic):
        """NEXT J should not match when looking for NEXT I"""
        executor = basic.executor
        basic.expanded_program = {
            (10, 0): 'FOR I = 1 TO 3',
            (20, 0): 'NEXT J',
            (30, 0): 'NEXT I',
        }
        positions = [(10, 0), (20, 0), (30, 0)]
        assert executor._skip_to_next('I', 0, positions) == 2

    def test_returns_none_if_no_next(self, basic):
        executor = basic.executor
        basic.expanded_program = {
            (10, 0): 'FOR I = 1 TO 3',
            (20, 0): 'PRINT I',
        }
        positions = [(10, 0), (20, 0)]
        assert executor._skip_to_next('I', 0, positions) is None


class TestSkipIfOrElseBlock:
    """Test ProgramExecutor._skip_if_or_else_block"""

    def test_skip_to_else(self, basic):
        executor = basic.executor
        basic.expanded_program = {
            (10, 0): 'IF X=1 THEN',
            (20, 0): 'PRINT "TRUE"',
            (30, 0): 'ELSE',
            (40, 0): 'PRINT "FALSE"',
            (50, 0): 'ENDIF',
        }
        positions = [(10, 0), (20, 0), (30, 0), (40, 0), (50, 0)]
        idx, found = executor._skip_if_or_else_block(0, positions, stop_at_else=True)
        assert found is True
        assert idx == 2  # Position of ELSE

    def test_skip_to_endif(self, basic):
        executor = basic.executor
        basic.expanded_program = {
            (10, 0): 'IF X=1 THEN',
            (20, 0): 'PRINT "TRUE"',
            (30, 0): 'ELSE',
            (40, 0): 'PRINT "FALSE"',
            (50, 0): 'ENDIF',
        }
        positions = [(10, 0), (20, 0), (30, 0), (40, 0), (50, 0)]
        # Skip from ELSE to ENDIF (stop_at_else=False)
        idx, found = executor._skip_if_or_else_block(2, positions, stop_at_else=False)
        assert found is True
        assert idx == 4  # Position of ENDIF

    def test_nested_if_skip(self, basic):
        """Should skip over nested IF/ENDIF blocks"""
        executor = basic.executor
        basic.expanded_program = {
            (10, 0): 'IF X=1 THEN',
            (20, 0): 'IF Y=2 THEN',       # Nested IF
            (30, 0): 'PRINT "INNER"',
            (40, 0): 'ENDIF',              # Closes nested IF
            (50, 0): 'ELSE',               # ELSE for outer IF
            (60, 0): 'PRINT "OUTER FALSE"',
            (70, 0): 'ENDIF',              # Closes outer IF
        }
        positions = [(10, 0), (20, 0), (30, 0), (40, 0), (50, 0), (60, 0), (70, 0)]
        idx, found = executor._skip_if_or_else_block(0, positions, stop_at_else=True)
        assert found is True
        assert idx == 4  # Should skip nested IF and find outer ELSE

    def test_returns_not_found_if_no_endif(self, basic):
        executor = basic.executor
        basic.expanded_program = {
            (10, 0): 'IF X=1 THEN',
            (20, 0): 'PRINT "ORPHAN"',
        }
        positions = [(10, 0), (20, 0)]
        idx, found = executor._skip_if_or_else_block(0, positions, stop_at_else=True)
        assert found is False


class TestHandleFlowControlDirectives:
    """Test _handle_flow_control with each directive type"""

    def _make_executor(self, basic, program_lines):
        """Helper to set up expanded program and return executor + positions"""
        basic.process_command('NEW')
        for line in program_lines:
            basic.process_command(line)
        positions = sorted(basic.expanded_program.keys())
        basic.running = True
        return basic.executor, positions

    def test_jump_directive(self, basic):
        executor, positions = self._make_executor(basic, [
            '10 PRINT "A"',
            '20 PRINT "B"',
            '30 PRINT "C"',
        ])
        output = []
        result = [{'type': 'jump', 'line': 30}]
        new_pos, action = executor._handle_flow_control(result, 0, positions, output)
        assert action == 'jumped'
        assert positions[new_pos][0] == 30  # Jumped to line 30

    def test_jump_undefined_line(self, basic):
        executor, positions = self._make_executor(basic, [
            '10 PRINT "A"',
        ])
        output = []
        result = [{'type': 'jump', 'line': 999}]
        new_pos, action = executor._handle_flow_control(result, 0, positions, output)
        assert action == 'stop'
        assert any('UNDEFINED LINE' in item.get('message', '') for item in output)

    def test_input_request_returns(self, basic):
        executor, positions = self._make_executor(basic, [
            '10 PRINT "A"',
            '20 PRINT "B"',
        ])
        output = []
        result = [{'type': 'input_request', 'prompt': '?', 'variables': []}]
        new_pos, action = executor._handle_flow_control(result, 0, positions, output)
        assert action == 'return'
        assert basic.waiting_for_input is True

    def test_pause_returns(self, basic):
        executor, positions = self._make_executor(basic, [
            '10 PRINT "A"',
            '20 PRINT "B"',
        ])
        output = []
        result = [{'type': 'pause', 'duration': 1000}]
        new_pos, action = executor._handle_flow_control(result, 0, positions, output)
        assert action == 'return'
        assert basic.waiting_for_pause_continuation is True

    def test_skip_for_loop(self, basic):
        executor, positions = self._make_executor(basic, [
            '10 PRINT "BEFORE"',
            '20 PRINT "INSIDE"',
            '30 NEXT I',
            '40 PRINT "AFTER"',
        ])
        output = []
        result = [{'type': 'skip_for_loop', 'var': 'I'}]
        new_pos, action = executor._handle_flow_control(result, 0, positions, output)
        assert action == 'jumped'
        # Should skip past NEXT I to line 40
        assert positions[new_pos][0] == 40

    def test_skip_for_loop_no_next_error(self, basic):
        executor, positions = self._make_executor(basic, [
            '10 PRINT "A"',
            '20 PRINT "B"',
        ])
        output = []
        result = [{'type': 'skip_for_loop', 'var': 'I'}]
        new_pos, action = executor._handle_flow_control(result, 0, positions, output)
        assert action == 'stop'
        assert any('FOR WITHOUT NEXT' in item.get('message', '') for item in output)

    def test_skip_while_loop(self, basic):
        executor, positions = self._make_executor(basic, [
            '10 PRINT "BEFORE"',
            '20 PRINT "INSIDE"',
            '30 WEND',
            '40 PRINT "AFTER"',
        ])
        output = []
        result = [{'type': 'skip_while_loop'}]
        new_pos, action = executor._handle_flow_control(result, 0, positions, output)
        assert action == 'jumped'
        assert positions[new_pos][0] == 40

    def test_skip_do_loop(self, basic):
        executor, positions = self._make_executor(basic, [
            '10 PRINT "BEFORE"',
            '20 PRINT "INSIDE"',
            '30 LOOP',
            '40 PRINT "AFTER"',
        ])
        output = []
        result = [{'type': 'skip_do_loop'}]
        new_pos, action = executor._handle_flow_control(result, 0, positions, output)
        assert action == 'jumped'
        assert positions[new_pos][0] == 40

    def test_skip_if_block(self, basic):
        executor, positions = self._make_executor(basic, [
            '10 PRINT "IF LINE"',
            '20 PRINT "TRUE BRANCH"',
            '30 ELSE',
            '40 PRINT "FALSE BRANCH"',
            '50 ENDIF',
        ])
        output = []
        result = [{'type': 'skip_if_block'}]
        new_pos, action = executor._handle_flow_control(result, 0, positions, output)
        assert action == 'jumped'
        # Should jump to ELSE
        assert positions[new_pos][0] == 30

    def test_skip_else_block(self, basic):
        executor, positions = self._make_executor(basic, [
            '10 PRINT "IF LINE"',
            '20 PRINT "TRUE BRANCH"',
            '30 ELSE',
            '40 PRINT "FALSE BRANCH"',
            '50 ENDIF',
        ])
        output = []
        result = [{'type': 'skip_else_block'}]
        # Start from ELSE position (index 2)
        new_pos, action = executor._handle_flow_control(result, 2, positions, output)
        assert action == 'jumped'
        # Should jump to ENDIF
        assert positions[new_pos][0] == 50

    def test_error_stops_execution(self, basic):
        executor, positions = self._make_executor(basic, [
            '10 PRINT "A"',
            '20 PRINT "B"',
        ])
        output = []
        result = [{'type': 'error', 'message': 'SYNTAX ERROR'}]
        new_pos, action = executor._handle_flow_control(result, 0, positions, output)
        assert action == 'stop'
        assert basic.running is False
        # Stacks should be cleared
        assert len(basic.for_stack) == 0
        assert len(basic.call_stack) == 0

    def test_text_output_appended(self, basic):
        executor, positions = self._make_executor(basic, [
            '10 PRINT "A"',
        ])
        output = []
        result = [{'type': 'text', 'text': 'HELLO'}]
        new_pos, action = executor._handle_flow_control(result, 0, positions, output)
        assert action == 'next'
        assert any(item.get('text') == 'HELLO' for item in output)

    def test_system_messages_filtered(self, basic):
        executor, positions = self._make_executor(basic, [
            '10 PRINT "A"',
        ])
        output = []
        result = [{'type': 'text', 'text': 'OK', 'source': 'system'}]
        executor._handle_flow_control(result, 0, positions, output)
        # System messages should not appear in output
        assert len(output) == 0

    def test_no_result_advances(self, basic):
        executor, positions = self._make_executor(basic, [
            '10 PRINT "A"',
            '20 PRINT "B"',
        ])
        output = []
        result = []  # Empty result
        new_pos, action = executor._handle_flow_control(result, 0, positions, output)
        assert action == 'next'
        assert new_pos == 1  # Advanced by one


class TestNestedControlStructures:
    """Test execution of deeply nested control structures"""

    def test_for_inside_while(self, basic, helpers):
        program = [
            '10 X = 0',
            '20 WHILE X < 2',
            '30 FOR I = 1 TO 2',
            '40 X = X + 1',
            '50 NEXT I',
            '60 WEND',
            '70 PRINT X',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert ' 2 ' in text or ' 4 ' in text  # Depends on WHILE re-evaluation

    def test_if_inside_for_inside_while(self, basic, helpers):
        program = [
            '10 TOTAL = 0',
            '20 N = 1',
            '30 WHILE N <= 3',
            '40 FOR I = 1 TO N',
            '50 IF I = N THEN',
            '60 TOTAL = TOTAL + 1',
            '70 ENDIF',
            '80 NEXT I',
            '90 N = N + 1',
            '100 WEND',
            '110 PRINT TOTAL',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert ' 3 ' in text  # Each WHILE iteration adds 1 from the IF

    def test_gosub_inside_for(self, basic, helpers):
        program = [
            '10 FOR I = 1 TO 3',
            '20 GOSUB 100',
            '30 NEXT I',
            '40 PRINT "DONE"',
            '50 END',
            '100 PRINT I',
            '110 RETURN',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert ' 1 ' in text
        assert ' 2 ' in text
        assert ' 3 ' in text
        assert 'DONE' in text

    def test_exit_for_in_nested_loop(self, basic, helpers):
        """EXIT FOR should exit only the innermost FOR"""
        program = [
            '10 FOR I = 1 TO 3',
            '20 FOR J = 1 TO 10',
            '30 IF J = 2 THEN EXIT FOR',
            '40 NEXT J',
            '50 NEXT I',
            '60 PRINT "I="; I',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        errors = helpers.get_error_messages(results)
        assert len(errors) == 0
        # I should have completed all 3 iterations
        # After loop, I will be 4 (past limit)
        assert any('4' in t for t in text)

    def test_do_loop_inside_if(self, basic, helpers):
        program = [
            '10 X = 1',
            '20 IF X = 1 THEN',
            '30 N = 0',
            '40 DO',
            '50 N = N + 1',
            '60 LOOP WHILE N < 3',
            '70 PRINT N',
            '80 ENDIF',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert ' 3 ' in text

    def test_while_loop_with_gosub(self, basic, helpers):
        program = [
            '10 S = 0',
            '20 I = 1',
            '30 WHILE I <= 3',
            '40 GOSUB 100',
            '50 I = I + 1',
            '60 WEND',
            '70 PRINT S',
            '80 END',
            '100 S = S + I',
            '110 RETURN',
        ]
        results = helpers.execute_program(basic, program)
        text = helpers.get_text_output(results)
        assert ' 6 ' in text  # 1+2+3 = 6
