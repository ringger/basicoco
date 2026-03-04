"""Tests for stack initialization and clearing between programs."""

import pytest
from emulator.core import CoCoBasic


class TestStackClearing:
    """Verify stacks are cleared between programs to prevent state leaks."""

    def test_new_clears_all_stacks(self, basic):
        """NEW command should clear all control flow stacks."""
        # Manually push entries onto each stack
        basic.for_stack.append({'var': 'I', 'start': 1, 'end': 10, 'step': 1})
        basic.call_stack.append({'line': 100, 'sub_line': 0})
        basic.if_stack.append({'condition': True, 'line': 50})
        basic.while_stack.append({'condition': 'X<10', 'line': 30})
        basic.do_stack.append({'line': 20, 'condition': None})

        basic.process_command('NEW')

        assert basic.for_stack == []
        assert basic.call_stack == []
        assert basic.if_stack == []
        assert basic.while_stack == []
        assert basic.do_stack == []

    def test_run_clears_stacks(self, basic):
        """RUN should clear stacks before executing a program."""
        # Push stale entries
        basic.for_stack.append({'var': 'I', 'start': 1, 'end': 10, 'step': 1})
        basic.if_stack.append({'condition': True, 'line': 50})
        basic.while_stack.append({'condition': 'X<10', 'line': 30})
        basic.do_stack.append({'line': 20, 'condition': None})

        # Load and run a simple program
        basic.process_command('10 PRINT "HELLO"')
        basic.process_command('RUN')

        # Stacks should be clean after program finishes
        assert basic.for_stack == []
        assert basic.if_stack == []
        assert basic.while_stack == []
        assert basic.do_stack == []

    def test_sequential_programs_no_stack_leak(self, basic):
        """Running multiple programs sequentially should not leak stack state."""
        # First program with a FOR loop
        basic.process_command('10 FOR I=1 TO 3')
        basic.process_command('20 PRINT I')
        basic.process_command('30 NEXT I')
        basic.process_command('RUN')

        # Second program should start with clean stacks
        basic.process_command('NEW')
        basic.process_command('10 PRINT "CLEAN"')
        result = basic.process_command('RUN')

        assert basic.for_stack == []
        assert basic.call_stack == []
        assert basic.if_stack == []
        assert basic.while_stack == []
        assert basic.do_stack == []
