#!/usr/bin/env python3
"""
Debug version of CLI client to trace FILES command issue
"""

import socketio
import sys
import threading
import time

class DebugTRS80CLI:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.sio = socketio.Client()
        self.connected = False
        self.response_received = threading.Event()
        self.setup_socketio_handlers()
        
    def setup_socketio_handlers(self):
        """Set up Socket.IO event handlers with debug logging."""
        
        @self.sio.event
        def connect():
            self.connected = True
            print("DEBUG: Connected to server")
        
        @self.sio.event
        def disconnect():
            self.connected = False
            print("DEBUG: Disconnected from server")
        
        @self.sio.event
        def output(data):
            """Handle output from the BASIC emulator with debug logging."""
            print(f"DEBUG: Received output message with {len(data)} items")
            
            for i, item in enumerate(data):
                print(f"DEBUG: Item {i}: {item}")
                if item['type'] == 'text':
                    print(item['text'])
                elif item['type'] == 'error':
                    print(f"ERROR: {item['message']}")
            
            # Check for completion signal
            has_error = any(item.get('type') == 'error' for item in data)
            has_completion_signal = any(item.get('type') == 'command_complete' for item in data)
            
            print(f"DEBUG: has_error={has_error}, has_completion_signal={has_completion_signal}")
            
            if has_error or has_completion_signal:
                print("DEBUG: Setting response_received event")
                self.response_received.set()
    
    def connect_to_server(self):
        """Connect to the Flask-SocketIO server."""
        try:
            self.sio.connect(f'http://{self.host}:{self.port}')
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    def send_command(self, command: str):
        """Send a command to the BASIC emulator with debug logging."""
        if self.connected:
            print(f"DEBUG: Sending command: {command}")
            self.response_received.clear()
            self.sio.emit('execute_command', {'command': command})
            print("DEBUG: Waiting for response...")
            self.response_received.wait()
            print("DEBUG: Response received, continuing")
    
    def test_bounce_pause_command(self):
        """Test the bounce_pause animation specifically."""
        if not self.connect_to_server():
            return
        
        print("=== Testing bounce_pause animation ===")
        self.send_command('LOAD "bounce_pause"')
        print("=== Program loaded, starting animation ===")
        self.send_command('RUN')
        
        print("=== Animation test complete ===")
        
        if self.connected:
            self.sio.disconnect()

if __name__ == '__main__':
    debug_cli = DebugTRS80CLI()
    debug_cli.test_bounce_pause_command()