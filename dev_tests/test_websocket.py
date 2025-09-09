#!/usr/bin/env python3

"""
Test the emulator via WebSocket to check which examples work
"""

import socketio
import time

# Create a Socket.IO client
sio = socketio.SimpleClient()

def test_examples():
    try:
        # Connect to the server
        sio.connect('http://localhost:5000')
        
        examples = [
            'PRINT "HELLO WORLD"',
            'A = 42',
            'PRINT A',
            '10 FOR I=1 TO 5',
            '20 PRINT I', 
            '30 NEXT I',
            'LIST',
            'RUN',
            'CLEAR',
            'PMODE 4,1',
            'SCREEN 1,1', 
            'PSET(128,96)',
            'LINE(0,0)-(255,191)',
            'CIRCLE(128,96),50',
            'PCLS',
            'COLOR 4,0',
            'SOUND 1000,30'
        ]
        
        print("Testing TRS-80 Color Computer Emulator Examples:")
        print("=" * 60)
        
        for example in examples:
            print(f"\nTesting: {example}")
            
            # Send the command
            sio.emit('execute_command', {'command': example})
            
            # Wait for response
            time.sleep(0.1)
            
            # Listen for output (this is simplified - normally would use event handlers)
            try:
                response = sio.receive(timeout=1)
                if response:
                    print(f"  Response: {response}")
                else:
                    print("  No response received")
            except:
                print("  Timeout waiting for response")
                
        print("\n" + "=" * 60)
        print("Test completed!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sio.disconnect()

if __name__ == '__main__':
    test_examples()