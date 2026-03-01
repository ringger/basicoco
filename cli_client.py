#!/usr/bin/env python3
"""
BasiCoCo - CLI Client
A standalone terminal interface for the BASIC emulator that connects to the Flask-SocketIO server.
"""

import socketio
import readline
import os
import threading

class TRS80CLI:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.sio = socketio.Client()
        self.connected = False
        self.waiting_for_input = False
        self.input_prompt = ""
        self.input_variable = ""
        self.input_metadata = {}
        self.response_received = threading.Event()
        self.running_program = False
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
        
        # Basic tab completion for BASIC keywords and CLI commands
        basic_keywords = [
            'PRINT', 'LET', 'IF', 'THEN', 'ELSE', 'FOR', 'TO', 'NEXT', 'STEP',
            'GOTO', 'GOSUB', 'RETURN', 'END', 'STOP', 'RUN', 'LIST', 'NEW',
            'SAVE', 'LOAD', 'FILES', 'KILL', 'DELETE', 'CD', 'INPUT', 'DATA', 'READ', 'RESTORE', 'DIM',
            'PSET', 'PRESET', 'PMODE', 'PCLS', 'SCREEN', 'COLOR', 'PAINT',
            'LINE', 'CIRCLE', 'DRAW', 'GET', 'PUT', 'CLS', 'SOUND',
            'RND', 'INT', 'ABS', 'SGN', 'SQR', 'SIN', 'COS', 'TAN', 'ATN',
            'LOG', 'EXP', 'LEN', 'MID$', 'LEFT$', 'RIGHT$', 'STR$', 'VAL',
            'CHR$', 'ASC', 'INKEY$', 'POS', 'PEEK', 'POKE',
            'EXIT', 'QUIT', 'BYE'  # CLI convenience commands
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
            print("Connected to BasiCoCo")
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
                        print(item['text'], flush=True)
                elif item['type'] == 'error':
                    print(f"ERROR: {item['message']}")
                elif item['type'] == 'input_request':
                    self.waiting_for_input = True
                    self.input_prompt = item.get('prompt', '?')
                    self.input_variable = item.get('variable', '')
                    # Store any additional metadata (like filename for KILL confirmation)
                    self.input_metadata = {k: v for k, v in item.items() if k not in ['type', 'prompt', 'variable']}
                elif item['type'] == 'graphics':
                    # For CLI, just show that graphics command was executed
                    print(f"[Graphics: {item.get('command', 'unknown')}]")
                elif item['type'] == 'sound':
                    # For CLI, just show that sound command was executed
                    print(f"[Sound: {item.get('frequency', 'unknown')} Hz]")
                elif item['type'] == 'clear':
                    # Clear screen
                    os.system('clear' if os.name == 'posix' else 'cls')
                elif item['type'] == 'pause':
                    # Handle non-blocking pause - schedule continuation after delay
                    duration = item.get('duration', 1.0)
                    threading.Timer(duration, self.continue_after_pause).start()
            
            # Signal that we've received and processed the response
            # Look for the universal command completion signal
            has_error = any(item.get('type') == 'error' for item in data)
            has_completion_signal = any(item.get('type') == 'command_complete' for item in data)
            has_pause = any(item.get('type') == 'pause' for item in data)
            has_input_request = any(item.get('type') == 'input_request' for item in data)
            
            # Signal completion for: errors, explicit completion, or input requests
            # Don't signal completion if we just received a pause - wait for actual completion
            if (has_error or has_completion_signal or has_input_request) and not has_pause:
                if self.running_program:
                    self.running_program = False
                # Ensure all output is flushed before signaling completion
                import sys
                sys.stdout.flush()
                # Small delay to ensure terminal output is complete
                import time
                time.sleep(0.01)
                self.response_received.set()
            # Don't signal for intermediate responses during program execution - let them stream through
    
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
            # For RUN command, enable streaming mode but still wait for program completion
            if command.strip().upper() == 'RUN':
                self.running_program = True
                self.response_received.clear()
                self.sio.emit('execute_command', {'command': command})
                # Wait for program to finish running (with timeout)
                if not self.response_received.wait(timeout=30):
                    print("Program execution timed out")
                    self.running_program = False
            else:
                # For other commands, wait for complete response before next prompt
                self.response_received.clear()  # Reset the event
                self.sio.emit('execute_command', {'command': command})
                # Wait for the response to arrive and be processed
                self.response_received.wait()
    
    def send_input_response(self, value: str):
        """Send input response to the BASIC emulator."""
        if self.connected and self.waiting_for_input:
            # Include any metadata in the response
            response = {
                'variable': self.input_variable,
                'value': value
            }
            response.update(self.input_metadata)
            
            self.response_received.clear()  # Reset the event
            self.sio.emit('input_response', response)
            self.waiting_for_input = False
            self.input_prompt = ""
            self.input_variable = ""
            self.input_metadata = {}
            # Wait for the response to arrive and be processed
            self.response_received.wait()
    
    def send_keypress(self, key: str):
        """Send keypress to the BASIC emulator for INKEY$ support."""
        if self.connected:
            self.sio.emit('keypress', {'key': key})
    
    def send_break_signal(self):
        """Send break signal to interrupt running BASIC program."""
        if self.connected:
            print("BREAK")
            self.sio.emit('break_execution')
            self.response_received.set()  # Unblock any waiting operations
    
    def continue_after_pause(self):
        """Continue program execution after a pause completes."""
        if self.connected:
            self.sio.emit('continue_execution')
    
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
                        command = input("> ")
                        if command.strip():
                            # Handle local EXIT command
                            if command.strip().upper() in ['EXIT', 'QUIT', 'BYE']:
                                print("Goodbye!")
                                break
                            self.send_command(command)
                        
                except EOFError:
                    # Ctrl+D pressed
                    break
                except KeyboardInterrupt:
                    # Ctrl+C pressed
                    if self.running_program or self.waiting_for_input:
                        # Send break signal to interrupt running BASIC program
                        print("\n^C")
                        self.send_break_signal()
                        # Reset states
                        self.running_program = False
                        self.waiting_for_input = False
                        self.input_prompt = ""
                        self.input_variable = ""
                        # Continue CLI (don't break)
                    else:
                        # No program running, exit CLI
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
    
    parser = argparse.ArgumentParser(description='BasiCoCo CLI Client')
    parser.add_argument('--host', default='localhost', 
                       help='Server host (default: localhost)')
    parser.add_argument('--port', type=int, default=5000,
                       help='Server port (default: 5000)')
    
    args = parser.parse_args()
    
    # Display banner
    print("BASICOCO V1.0")
    print("EDUCATIONAL COLOR COMPUTER BASIC")
    print("INSPIRED BY TANDY/RADIO SHACK")
    print()
    
    cli = TRS80CLI(args.host, args.port)
    cli.run()

if __name__ == '__main__':
    main()