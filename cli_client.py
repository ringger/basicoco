#!/usr/bin/env python3
"""
TRS-80 Color Computer BASIC Emulator - CLI Client
A standalone terminal interface for the BASIC emulator that connects to the Flask-SocketIO server.
"""

import socketio
import readline
import sys
import os
import threading
import time
from typing import Dict, Any, List

class TRS80CLI:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.sio = socketio.Client()
        self.connected = False
        self.waiting_for_input = False
        self.input_prompt = ""
        self.input_variable = ""
        self.setup_socketio_handlers()
        self.setup_readline()
        
    def setup_readline(self):
        """Configure readline for command history and editing."""
        # Enable history file
        histfile = os.path.join(os.path.expanduser("~"), ".trs80_history")
        try:
            readline.read_history_file(histfile)
            readline.set_history_length(1000)
        except FileNotFoundError:
            pass
        
        # Save history on exit
        import atexit
        atexit.register(readline.write_history_file, histfile)
        
        # Basic tab completion for BASIC keywords
        basic_keywords = [
            'PRINT', 'LET', 'IF', 'THEN', 'ELSE', 'FOR', 'TO', 'NEXT', 'STEP',
            'GOTO', 'GOSUB', 'RETURN', 'END', 'STOP', 'RUN', 'LIST', 'NEW',
            'SAVE', 'LOAD', 'INPUT', 'DATA', 'READ', 'RESTORE', 'DIM',
            'PSET', 'PRESET', 'PMODE', 'PCLS', 'SCREEN', 'COLOR', 'PAINT',
            'LINE', 'CIRCLE', 'DRAW', 'GET', 'PUT', 'CLS', 'SOUND',
            'RND', 'INT', 'ABS', 'SGN', 'SQR', 'SIN', 'COS', 'TAN', 'ATN',
            'LOG', 'EXP', 'LEN', 'MID$', 'LEFT$', 'RIGHT$', 'STR$', 'VAL',
            'CHR$', 'ASC', 'INKEY$', 'POS', 'PEEK', 'POKE'
        ]
        
        def complete(text, state):
            matches = [cmd for cmd in basic_keywords if cmd.startswith(text.upper())]
            if state < len(matches):
                return matches[state]
            return None
        
        readline.set_completer(complete)
        readline.parse_and_bind('tab: complete')
    
    def setup_socketio_handlers(self):
        """Set up Socket.IO event handlers."""
        
        @self.sio.event
        def connect():
            self.connected = True
            print("Connected to TRS-80 Color Computer BASIC Emulator")
            print("Type BASIC commands or programs. Press Ctrl+C to exit.")
            print("=" * 60)
        
        @self.sio.event
        def disconnect():
            self.connected = False
            print("\nDisconnected from server")
        
        @self.sio.event
        def output(data):
            """Handle output from the BASIC emulator."""
            for item in data:
                if item['type'] == 'text':
                    if item.get('inline'):
                        # Handle inline text with carriage return
                        text = item['text']
                        if '\r' in text:
                            # Print without newline and flush
                            print(text.replace('\r', ''), end='', flush=True)
                            # Move cursor to beginning of line
                            print('\r', end='', flush=True)
                        else:
                            print(text, end='', flush=True)
                    else:
                        print(item['text'])
                elif item['type'] == 'error':
                    print(f"ERROR: {item['message']}")
                elif item['type'] == 'input_request':
                    self.waiting_for_input = True
                    self.input_prompt = item.get('prompt', '?')
                    self.input_variable = item.get('variable', '')
                elif item['type'] == 'graphics':
                    # For CLI, just show that graphics command was executed
                    print(f"[Graphics: {item.get('command', 'unknown')}]")
                elif item['type'] == 'sound':
                    # For CLI, just show that sound command was executed
                    print(f"[Sound: {item.get('frequency', 'unknown')} Hz]")
                elif item['type'] == 'clear':
                    # Clear screen
                    os.system('clear' if os.name == 'posix' else 'cls')
    
    def connect_to_server(self):
        """Connect to the Flask-SocketIO server."""
        try:
            self.sio.connect(f'http://{self.host}:{self.port}')
            return True
        except Exception as e:
            print(f"Failed to connect to server at {self.host}:{self.port}: {e}")
            return False
    
    def send_command(self, command: str):
        """Send a command to the BASIC emulator."""
        if self.connected:
            self.sio.emit('execute_command', {'command': command})
    
    def send_input_response(self, value: str):
        """Send input response to the BASIC emulator."""
        if self.connected and self.waiting_for_input:
            self.sio.emit('input_response', {
                'variable': self.input_variable,
                'value': value
            })
            self.waiting_for_input = False
            self.input_prompt = ""
            self.input_variable = ""
    
    def send_keypress(self, key: str):
        """Send keypress to the BASIC emulator for INKEY$ support."""
        if self.connected:
            self.sio.emit('keypress', {'key': key})
    
    def run(self):
        """Main CLI loop."""
        if not self.connect_to_server():
            return
        
        try:
            while True:
                try:
                    if self.waiting_for_input:
                        # Handle INPUT requests
                        prompt = f"{self.input_prompt} "
                        user_input = input(prompt)
                        self.send_input_response(user_input)
                    else:
                        # Normal command input
                        command = input("READY\n")
                        if command.strip():
                            self.send_command(command)
                        
                except EOFError:
                    # Ctrl+D pressed
                    break
                except KeyboardInterrupt:
                    # Ctrl+C pressed
                    print("\nInterrupted")
                    break
                    
        except Exception as e:
            print(f"Error in main loop: {e}")
        finally:
            if self.connected:
                self.sio.disconnect()

def main():
    """Entry point for the CLI client."""
    import argparse
    
    parser = argparse.ArgumentParser(description='TRS-80 Color Computer BASIC CLI Client')
    parser.add_argument('--host', default='localhost', 
                       help='Server host (default: localhost)')
    parser.add_argument('--port', type=int, default=5000,
                       help='Server port (default: 5000)')
    
    args = parser.parse_args()
    
    # Display banner
    print("TRS-80 COLOR COMPUTER BASIC V1.0")
    print("(C) 1980 BY TANDY")
    print("ENHANCED EMULATOR VERSION")
    print()
    
    cli = TRS80CLI(args.host, args.port)
    cli.run()

if __name__ == '__main__':
    main()