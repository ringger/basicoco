#!/usr/bin/env python3
"""
BasiCoCo - Standalone CLI
A terminal REPL for the BASIC emulator. No server required.
"""

import argparse
import atexit
import os
import readline
import sys
import time

from emulator.core import CoCoBasic

BASIC_KEYWORDS = [
    'PRINT', 'LET', 'IF', 'THEN', 'ELSE', 'ENDIF', 'FOR', 'TO', 'NEXT',
    'STEP', 'GOTO', 'GOSUB', 'RETURN', 'END', 'STOP', 'CONT', 'RUN',
    'LIST', 'NEW', 'SAVE', 'LOAD', 'FILES', 'KILL', 'DELETE', 'CD',
    'INPUT', 'DATA', 'READ', 'RESTORE', 'DIM', 'ON', 'DO', 'LOOP',
    'WHILE', 'WEND', 'EXIT',
    'PSET', 'PRESET', 'PMODE', 'PCLS', 'SCREEN', 'COLOR', 'PAINT',
    'LINE', 'CIRCLE', 'DRAW', 'GET', 'PUT', 'CLS', 'SOUND', 'PAUSE',
    'RND', 'INT', 'ABS', 'SGN', 'SQR', 'SIN', 'COS', 'TAN', 'ATN',
    'LOG', 'EXP', 'LEN', 'MID$', 'LEFT$', 'RIGHT$', 'STR$', 'VAL',
    'CHR$', 'ASC', 'INKEY$', 'POS', 'PEEK', 'POKE',
]


def setup_readline():
    """Configure readline with history and tab completion."""
    histfile = os.path.join(os.path.expanduser("~"), ".basicoco_history")
    try:
        readline.read_history_file(histfile)
        readline.set_history_length(1000)
    except FileNotFoundError:
        pass
    atexit.register(readline.write_history_file, histfile)

    def complete(text, state):
        matches = [kw for kw in BASIC_KEYWORDS if kw.startswith(text.upper())]
        if state < len(matches):
            return matches[state]
        return None

    readline.set_completer(complete)
    readline.parse_and_bind('tab: complete')


def handle_input_request(basic, item):
    """Handle an input_request item: prompt user, store value, handle multi-var."""
    prompt = item.get('prompt', '? ')

    try:
        value = input(f"{prompt} ")
    except EOFError:
        value = ''

    # Use the variable descriptor from input_variables for proper array support
    if basic.input_variables:
        var_desc = basic.input_variables[basic.current_input_index]
    else:
        var_desc = item.get('variable', '')
    basic.store_input_value(var_desc, value)

    # Multi-variable INPUT: keep prompting until all variables are filled
    if basic.input_variables:
        basic.current_input_index += 1
        while basic.current_input_index < len(basic.input_variables):
            var_desc = basic.input_variables[basic.current_input_index]
            try:
                value = input(f"{basic.input_prompt} ")
            except EOFError:
                value = ''
            basic.store_input_value(var_desc, value)
            basic.current_input_index += 1

        # All done — clean up multi-var state
        basic.clear_input_state()


def process_output(basic, output):
    """Process output items from the emulator, handling input/pause loops.

    Returns True if we should continue processing (more output may follow),
    False if output is fully handled.
    """
    for item in output:
        item_type = item.get('type', '')

        if item_type == 'text':
            if item.get('inline'):
                text = item['text']
                if '\r' in text:
                    print(text.replace('\r', ''), end='', flush=True)
                    print('\r', end='', flush=True)
                else:
                    print(text, end='', flush=True)
            else:
                print(item['text'], flush=True)

        elif item_type == 'error':
            print(f"ERROR: {item['message']}")

        elif item_type == 'input_request':
            handle_input_request(basic, item)
            # Resume execution after input
            if basic.program_counter is not None and basic.program_counter != (0, 0):
                basic.waiting_for_input = False
                continuation = basic.continue_program_execution()
                process_output(basic, continuation)
            return

        elif item_type == 'pause':
            duration = item.get('duration', 1.0)
            time.sleep(duration)
            # Resume execution after pause
            if basic.program_counter is not None:
                continuation = basic.continue_program_execution()
                process_output(basic, continuation)
            return

        elif item_type == 'graphics':
            print(f"[Graphics: {item.get('command', 'unknown')}]")

        elif item_type == 'sound':
            print(f"[Sound: {item.get('frequency', 'unknown')} Hz]")

        elif item_type == 'clear':
            os.system('clear' if os.name == 'posix' else 'cls')

        # command_complete — ignore silently


def break_execution(basic):
    """Break any running program, resetting execution state."""
    basic.program_counter = None
    basic.waiting_for_input = False
    basic.clear_input_state()
    basic.running = False


def repl(basic):
    """Main read-eval-print loop."""
    while True:
        try:
            command = input("> ")
        except EOFError:
            break
        except KeyboardInterrupt:
            print()
            break

        if not command.strip():
            continue

        if command.strip().upper() in ('EXIT', 'QUIT', 'BYE'):
            print("GOODBYE!")
            break

        try:
            output = basic.process_command(command)
            process_output(basic, output)
        except KeyboardInterrupt:
            print("\nBREAK")
            break_execution(basic)
        except Exception as e:
            print(f"ERROR: {e}")


def main():
    parser = argparse.ArgumentParser(description='BasiCoCo - BASIC Interpreter')
    parser.add_argument('file', nargs='?', help='BASIC program file to load')
    parser.add_argument('--run', action='store_true',
                        help='Auto-run the loaded program')
    args = parser.parse_args()

    print("BASICOCO V1.0")
    print("EDUCATIONAL COLOR COMPUTER BASIC")
    print("INSPIRED BY TANDY/RADIO SHACK")
    print()

    setup_readline()
    basic = CoCoBasic()

    if args.file:
        output = basic.load_program(args.file)
        process_output(basic, output)
        if args.run:
            try:
                output = basic.process_command('RUN')
                process_output(basic, output)
            except KeyboardInterrupt:
                print("\nBREAK")
                break_execution(basic)
            return

    repl(basic)


if __name__ == '__main__':
    main()
