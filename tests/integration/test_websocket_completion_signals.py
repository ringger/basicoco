#!/usr/bin/env python3
"""
Integration tests for WebSocket completion signals and message flow.
These tests verify that the client-server communication properly handles
command completion signaling, preventing CLI prompt synchronization issues.
"""

import sys
import os
import time
import threading
import tempfile
import shutil
import pytest
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import socketio


class TestWebSocketCompletionSignals:
    """Test WebSocket completion signal behavior for all command types"""

    @pytest.fixture(autouse=True)
    def setup_websocket_test(self):
        """Set up WebSocket client and test environment"""
        self.sio = socketio.Client()
        self.messages = []
        self.completion_received = threading.Event()

        # Create temporary directory for file operations
        self.test_dir = tempfile.mkdtemp(prefix='trs80_websocket_test_')
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        os.makedirs('programs', exist_ok=True)

        yield  # This is where the test runs

        # Teardown
        if hasattr(self, 'sio') and self.sio.connected:
            self.sio.disconnect()

        # Restore directory and clean up
        os.chdir(self.original_cwd)
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def connect_websocket(self):
        """Connect to WebSocket server with message handlers"""
        try:
            self.sio.connect('http://localhost:5000', wait_timeout=5)

            @self.sio.event
            def output(data):
                """Capture all output messages"""
                # Ensure data is a list of dictionaries
                if isinstance(data, list):
                    self.messages.extend(data)
                else:
                    self.messages.append(data)

                # Check for completion signal - handle both list and single item
                items_to_check = data if isinstance(data, list) else [data]
                has_completion = any(
                    isinstance(item, dict) and item.get('type') == 'command_complete'
                    for item in items_to_check
                )
                if has_completion:
                    self.completion_received.set()

            return True
        except Exception as e:
            print(f"Failed to connect to WebSocket server: {e}")
            pytest.skip(f"WebSocket server not available on localhost:5000: {e}")
            return False

    def send_command_and_wait(self, command, timeout=5):
        """Send command and wait for completion signal"""
        # Ensure we're connected
        if not self.sio.connected:
            if not self.connect_websocket():
                return False, []  # Connection failed, already skipped

        self.messages.clear()
        self.completion_received.clear()

        self.sio.emit('execute_command', {'command': command})

        # Wait for completion signal
        completed = self.completion_received.wait(timeout=timeout)
        return completed, self.messages.copy()  # Return tuple as expected by existing tests

    def send_input_response(self, variable, value, metadata=None):
        """Send input response and wait for completion"""
        self.messages.clear()
        self.completion_received.clear()
        
        response = {'variable': variable, 'value': value}
        if metadata:
            response.update(metadata)
        
        self.sio.emit('input_response', response)
        
        # Wait for completion signal
        completed = self.completion_received.wait(timeout=5)
        return completed, self.messages.copy()

    def has_message_type(self, messages, message_type):
        """Check if messages contain specific type"""
        return any(
            isinstance(msg, dict) and msg.get('type') == message_type 
            for msg in messages
        )

    def get_messages_by_type(self, messages, message_type):
        """Get all messages of specific type"""
        return [msg for msg in messages if isinstance(msg, dict) and msg.get('type') == message_type]

    # Required abstract method from BaseTestCase
    def test_basic_functionality(self, basic, helpers):
        """Basic connectivity test"""
        if not self.connect_websocket():
            self.skip_test("Cannot connect to WebSocket server")
            return
        
        completed, messages = self.send_command_and_wait('PRINT "CONNECTION TEST"')
        
        assert completed, "Basic command should complete"
        assert self.has_message_type(messages, 'text', "Should have text output")
        assert self.has_message_type(messages, 'command_complete', "Should have completion signal")

    # Basic Command Completion Tests
    def test_simple_print_completion(self, basic, helpers):
        """Test that simple PRINT command sends completion signal"""
        if not self.connect_websocket():
            self.skip_test("Cannot connect to WebSocket server")
            return
        
        completed, messages = self.send_command_and_wait('PRINT "HELLO"')
        
        # Should complete and have completion signal
        assert completed, "Command should complete within timeout"
        assert self.has_message_type(messages, 'command_complete',
                       "Should have command_complete message")
        assert self.has_message_type(messages, 'text',
                       "Should have text output")

    def test_arithmetic_completion(self, basic, helpers):
        """Test arithmetic expressions send completion signal"""
        if not self.connect_websocket():
            self.skip_test("Cannot connect to WebSocket server")
            return
        
        completed, messages = self.send_command_and_wait('PRINT 2 + 3')
        
        assert completed, "Arithmetic should complete"
        assert self.has_message_type(messages, 'command_complete',
                       "Should have completion signal")

    def test_variable_assignment_completion(self, basic, helpers):
        """Test variable assignment sends completion signal"""
        if not self.connect_websocket():
            self.skip_test("Cannot connect to WebSocket server")
            return
        
        completed, messages = self.send_command_and_wait('A = 42')
        
        assert completed, "Variable assignment should complete"
        assert self.has_message_type(messages, 'command_complete',
                       "Should have completion signal")

    # Program Line Storage Tests
    def test_program_line_storage_completion(self, basic, helpers):
        """Test storing program lines sends completion signal"""
        if not self.connect_websocket():
            self.skip_test("Cannot connect to WebSocket server")
            return
        
        completed, messages = self.send_command_and_wait('10 PRINT "LINE 10"')
        
        assert completed, "Program line storage should complete"
        assert self.has_message_type(messages, 'command_complete',
                       "Should have completion signal")
        
        # Should have "OK" message
        text_messages = self.get_messages_by_type(messages, 'text')
        ok_found = any('OK' in msg.get('text', '') for msg in text_messages)
        assert ok_found, "Should have OK response for program line"

    def test_program_line_deletion_completion(self, basic, helpers):
        """Test deleting program lines sends completion signal"""
        if not self.connect_websocket():
            self.skip_test("Cannot connect to WebSocket server")
            return
        
        # First store a line
        _, _ = self.send_command_and_wait('20 PRINT "TO DELETE"')
        
        # Then delete it
        completed, messages = self.send_command_and_wait('20')
        
        assert completed, "Program line deletion should complete"
        assert self.has_message_type(messages, 'command_complete',
                       "Should have completion signal")

    # File Command Completion Tests
    def test_save_command_completion(self, basic, helpers):
        """Test SAVE command sends completion signal"""
        if not self.connect_websocket():
            self.skip_test("Cannot connect to WebSocket server")
            return
        
        # Create a program to save
        _, _ = self.send_command_and_wait('10 PRINT "SAVE TEST"')
        
        # Save it
        completed, messages = self.send_command_and_wait('SAVE "test_save"')
        
        assert completed, "SAVE command should complete"
        assert self.has_message_type(messages, 'command_complete',
                       "Should have completion signal")

    def test_files_command_completion(self, basic, helpers):
        """Test FILES command sends completion signal"""
        if not self.connect_websocket():
            self.skip_test("Cannot connect to WebSocket server")
            return
        
        completed, messages = self.send_command_and_wait('FILES')
        
        assert completed, "FILES command should complete"
        assert self.has_message_type(messages, 'command_complete',
                       "Should have completion signal")

    def test_load_command_completion(self, basic, helpers):
        """Test LOAD command sends completion signal"""
        if not self.connect_websocket():
            self.skip_test("Cannot connect to WebSocket server")
            return
        
        # Create a file to load
        with open('programs/load_test.bas', 'w') as f:
            f.write('10 PRINT "LOADED"\n')
        
        completed, messages = self.send_command_and_wait('LOAD "load_test"')
        
        assert completed, "LOAD command should complete"
        assert self.has_message_type(messages, 'command_complete',
                       "Should have completion signal")

    # KILL Command and Confirmation Tests  
    def test_kill_confirmation_request(self, basic, helpers):
        """Test KILL command requests confirmation without completion signal"""
        if not self.connect_websocket():
            self.skip_test("Cannot connect to WebSocket server")
            return
        
        # Create file to kill in server's working directory (not test temp directory)
        server_programs_dir = '/home/ringger/trs80/programs'
        os.makedirs(server_programs_dir, exist_ok=True)
        with open(f'{server_programs_dir}/kill_test.bas', 'w') as f:
            f.write('10 PRINT "DELETE ME"\n')
        
        self.messages.clear()
        self.completion_received.clear()
        
        self.sio.emit('execute_command', {'command': 'KILL "kill_test"'})
        
        # Wait briefly for initial response
        time.sleep(0.5)
        messages = self.messages.copy()
        
        # Should NOT have completion signal (waiting for confirmation)
        assert not self.has_message_type(messages, 'command_complete',
                        "Should NOT have completion signal before confirmation")
        assert self.has_message_type(messages, 'input_request',
                       "Should have input request for confirmation")
        
        # Clean up test file
        if os.path.exists(f'{server_programs_dir}/kill_test.bas'):
            os.remove(f'{server_programs_dir}/kill_test.bas')

    def test_kill_confirmation_cancel_completion(self, basic, helpers):
        """Test KILL confirmation cancellation sends completion signal"""
        if not self.connect_websocket():
            self.skip_test("Cannot connect to WebSocket server")
            return
        
        # Create file to kill in server's working directory
        server_programs_dir = '/home/ringger/trs80/programs'
        os.makedirs(server_programs_dir, exist_ok=True)
        filepath = f'{server_programs_dir}/cancel_test.bas'
        with open(filepath, 'w') as f:
            f.write('10 PRINT "DONT DELETE"\n')
        
        # Start KILL command
        self.sio.emit('execute_command', {'command': 'KILL "cancel_test"'})
        time.sleep(0.5)  # Wait for confirmation request
        
        # Cancel the kill
        completed, messages = self.send_input_response('_kill_confirm', 'N', 
                                                      {'filename': filepath})
        
        assert completed, "KILL cancellation should complete"
        assert self.has_message_type(messages, 'command_complete',
                       "Should have completion signal after cancellation")
        
        # File should still exist
        assert os.path.exists(filepath, "File should not be deleted after cancel")

    def test_kill_confirmation_delete_completion(self, basic, helpers):
        """Test KILL confirmation deletion sends completion signal"""
        if not self.connect_websocket():
            self.skip_test("Cannot connect to WebSocket server")
            return
        
        # Create file to kill in server's working directory
        server_programs_dir = '/home/ringger/trs80/programs'
        os.makedirs(server_programs_dir, exist_ok=True)
        filepath = f'{server_programs_dir}/delete_test.bas'
        with open(filepath, 'w') as f:
            f.write('10 PRINT "DELETE THIS"\n')
        
        # Start KILL command
        self.sio.emit('execute_command', {'command': 'KILL "delete_test"'})
        time.sleep(0.5)  # Wait for confirmation request
        
        # Confirm the kill
        completed, messages = self.send_input_response('_kill_confirm', 'Y',
                                                      {'filename': filepath})
        
        assert completed, "KILL confirmation should complete"
        assert self.has_message_type(messages, 'command_complete',
                       "Should have completion signal after deletion")
        
        # File should be deleted
        assert not os.path.exists(filepath, "File should be deleted after confirmation")

    # INPUT Command Tests
    def test_single_input_completion(self, basic, helpers):
        """Test single INPUT command completion after response"""
        if not self.connect_websocket():
            self.skip_test("Cannot connect to WebSocket server")
            return
        
        # Start INPUT command  
        self.sio.emit('execute_command', {'command': 'INPUT "Enter value"; A'})
        time.sleep(0.5)  # Wait for input request
        
        # Should NOT have completion signal yet
        assert not self.has_message_type(self.messages, 'command_complete',
                        "Should not complete before input provided")
        assert self.has_message_type(self.messages, 'input_request',
                       "Should have input request")
        
        # Provide input
        completed, messages = self.send_input_response('A', '42')
        
        assert completed, "INPUT should complete after response"
        assert self.has_message_type(messages, 'command_complete',
                       "Should have completion signal after input")

    def test_multi_variable_input_sequence(self, basic, helpers):
        """Test multi-variable INPUT does not complete until all variables input"""
        if not self.connect_websocket():
            self.skip_test("Cannot connect to WebSocket server")
            return
        
        # Start multi-variable INPUT
        self.sio.emit('execute_command', {'command': 'INPUT "Enter A,B"; A, B'})
        time.sleep(0.5)
        
        # First input should not complete
        self.messages.clear()
        self.completion_received.clear()
        
        self.sio.emit('input_response', {'variable': 'A', 'value': '10'})
        time.sleep(0.5)
        
        first_messages = self.messages.copy()
        
        # Should request second variable, not complete
        assert not self.has_message_type(first_messages, 'command_complete',
                        "Should not complete after first variable")
        assert self.has_message_type(first_messages, 'input_request',
                       "Should request second variable")
        
        # Second input should complete
        completed, final_messages = self.send_input_response('B', '20')
        
        assert completed, "Should complete after all variables input"
        assert self.has_message_type(final_messages, 'command_complete',
                       "Should have completion signal after all input")

    # PAUSE Command and Continuation Tests
    def test_pause_does_not_complete_immediately(self, basic, helpers):
        """Test PAUSE command does not send immediate completion signal"""
        if not self.connect_websocket():
            self.skip_test("Cannot connect to WebSocket server")
            return
        
        # Create program with PAUSE
        _, _ = self.send_command_and_wait('10 PRINT "BEFORE PAUSE"')
        _, _ = self.send_command_and_wait('20 PAUSE 0.1')
        _, _ = self.send_command_and_wait('30 PRINT "AFTER PAUSE"')
        
        # Run program
        self.messages.clear()
        self.completion_received.clear()
        
        self.sio.emit('execute_command', {'command': 'RUN'})
        time.sleep(0.2)  # Wait for pause to trigger
        
        messages = self.messages.copy()
        
        # Should have pause message but no completion signal
        assert self.has_message_type(messages, 'pause',
                       "Should have pause message")
        assert not self.has_message_type(messages, 'command_complete',
                        "Should NOT have completion signal during pause")

    def test_pause_continuation_completion(self, basic, helpers):
        """Test pause continuation sends completion when program finishes"""
        if not self.connect_websocket():
            self.skip_test("Cannot connect to WebSocket server") 
            return
        
        # Create simple program with short pause
        _, _ = self.send_command_and_wait('10 PRINT "START"')
        _, _ = self.send_command_and_wait('20 PAUSE 0.1') 
        _, _ = self.send_command_and_wait('30 PRINT "END"')
        
        # Run program
        self.sio.emit('execute_command', {'command': 'RUN'})
        time.sleep(0.2)  # Wait for pause
        
        # Continue after pause
        self.messages.clear()
        self.completion_received.clear()
        
        self.sio.emit('continue_execution')
        
        # Should complete since program finishes
        completed = self.completion_received.wait(timeout=2)
        messages = self.messages.copy()
        
        assert completed, "Should complete after program finishes"
        assert self.has_message_type(messages, 'command_complete',
                       "Should have completion signal when program ends")

    # Error Handling Completion Tests
    def test_syntax_error_completion(self, basic, helpers):
        """Test syntax errors send completion signal"""
        if not self.connect_websocket():
            self.skip_test("Cannot connect to WebSocket server")
            return
        
        completed, messages = self.send_command_and_wait('PRINT "UNCLOSED STRING')
        
        assert completed, "Syntax error should complete"
        assert self.has_message_type(messages, 'error',
                       "Should have error message")
        assert self.has_message_type(messages, 'command_complete',
                       "Should have completion signal for errors")

    def test_runtime_error_completion(self, basic, helpers):
        """Test runtime errors send completion signal"""
        if not self.connect_websocket():
            self.skip_test("Cannot connect to WebSocket server")
            return
        
        completed, messages = self.send_command_and_wait('PRINT 1/0')
        
        assert completed, "Runtime error should complete"
        assert self.has_message_type(messages, 'error',
                       "Should have error message")
        assert self.has_message_type(messages, 'command_complete',
                       "Should have completion signal for runtime errors")

    def test_file_not_found_error_completion(self, basic, helpers):
        """Test file errors send completion signal"""
        if not self.connect_websocket():
            self.skip_test("Cannot connect to WebSocket server")
            return
        
        completed, messages = self.send_command_and_wait('LOAD "nonexistent_file"')
        
        assert completed, "File error should complete"
        assert self.has_message_type(messages, 'error',
                       "Should have error message")  
        assert self.has_message_type(messages, 'command_complete',
                       "Should have completion signal for file errors")

    def test_graphics_pmode_command(self, basic, helpers):
        """Test PMODE graphics command completion signal"""
        completed, messages = self.send_command_and_wait('PMODE 4,1')
        assert self.has_message_type(messages, 'command_complete',
                       "PMODE command should send completion signal")

    def test_graphics_screen_command(self, basic, helpers):
        """Test SCREEN graphics command completion signal"""
        completed, messages = self.send_command_and_wait('SCREEN 1,1')
        assert self.has_message_type(messages, 'command_complete',
                       "SCREEN command should send completion signal")

    def test_graphics_pset_command(self, basic, helpers):
        """Test PSET graphics command completion signal"""
        # Setup graphics mode first
        _, _ = self.send_command_and_wait('PMODE 4,1')
        completed, messages = self.send_command_and_wait('PSET(128,96)')
        assert self.has_message_type(messages, 'command_complete',
                       "PSET command should send completion signal")

    def test_graphics_line_command(self, basic, helpers):
        """Test LINE graphics command completion signal"""
        # Setup graphics mode first
        _, _ = self.send_command_and_wait('PMODE 4,1')
        completed, messages = self.send_command_and_wait('LINE(0,0)-(255,191)')
        assert self.has_message_type(messages, 'command_complete',
                       "LINE command should send completion signal")

    def test_graphics_circle_command(self, basic, helpers):
        """Test CIRCLE graphics command completion signal"""
        # Setup graphics mode first  
        _, _ = self.send_command_and_wait('PMODE 4,1')
        completed, messages = self.send_command_and_wait('CIRCLE(128,96),50')
        assert self.has_message_type(messages, 'command_complete',
                       "CIRCLE command should send completion signal")

    def test_graphics_pcls_command(self, basic, helpers):
        """Test PCLS (clear graphics screen) command completion signal"""
        # Setup graphics mode first
        _, _ = self.send_command_and_wait('PMODE 4,1')  
        completed, messages = self.send_command_and_wait('PCLS')
        assert self.has_message_type(messages, 'command_complete',
                       "PCLS command should send completion signal")

    def test_graphics_color_command(self, basic, helpers):
        """Test COLOR command completion signal"""
        completed, messages = self.send_command_and_wait('COLOR 4,0')
        assert self.has_message_type(messages, 'command_complete',
                       "COLOR command should send completion signal")

    def test_sound_command(self, basic, helpers):
        """Test SOUND command completion signal"""
        completed, messages = self.send_command_and_wait('SOUND 1000,30')
        assert self.has_message_type(messages, 'command_complete',
                       "SOUND command should send completion signal")

    def test_print_hello_world(self, basic, helpers):
        """Test basic PRINT command with string literal"""
        completed, messages = self.send_command_and_wait('PRINT "HELLO WORLD"')
        assert self.has_message_type(messages, 'text',
                       "Should have text output")
        assert self.has_message_type(messages, 'command_complete',
                       "PRINT command should send completion signal")
        
        # Verify the actual output content
        text_messages = [msg for msg in messages if msg.get('type') == 'text']
        if text_messages:
            assert 'HELLO WORLD' in text_messages[0].get('text', '',
                           "Should print 'HELLO WORLD'")

    def test_variable_assignment_and_retrieval(self, basic, helpers):
        """Test variable assignment and PRINT with completion signals"""
        # Test assignment
        completed, messages = self.send_command_and_wait('A = 42')
        assert self.has_message_type(messages, 'command_complete',
                       "Variable assignment should send completion signal")
        
        # Test retrieval
        completed, messages = self.send_command_and_wait('PRINT A')
        assert self.has_message_type(messages, 'text',
                       "Should have text output for variable")
        assert self.has_message_type(messages, 'command_complete',
                       "PRINT variable should send completion signal")
        
        # Verify the actual output content
        text_messages = [msg for msg in messages if msg.get('type') == 'text']
        if text_messages:
            assert '42' in text_messages[0].get('text', '',
                           "Should print variable value '42'")

    def test_for_loop_program_execution(self, basic, helpers):
        """Test FOR loop program with completion signals"""
        # Load program lines
        _, _ = self.send_command_and_wait('10 FOR I=1 TO 3')
        _, _ = self.send_command_and_wait('20 PRINT I')
        _, _ = self.send_command_and_wait('30 NEXT I')
        
        # Run the program
        completed, messages = self.send_command_and_wait('RUN')
        
        # Should have multiple text outputs and final completion
        text_count = len([msg for msg in messages if msg.get('type') == 'text'])
        assert text_count >= 3, "Should have at least 3 text outputs from FOR loop"
        assert self.has_message_type(messages, 'command_complete',
                       "FOR loop program should send completion signal when done")

    def test_list_command_completion(self, basic, helpers):
        """Test LIST command completion signal"""
        # Add some program lines first
        _, _ = self.send_command_and_wait('10 PRINT "TEST"')
        _, _ = self.send_command_and_wait('20 PRINT "PROGRAM"')
        
        # Test LIST command
        completed, messages = self.send_command_and_wait('LIST')
        assert self.has_message_type(messages, 'command_complete',
                       "LIST command should send completion signal")

    def test_clear_command_completion(self, basic, helpers):
        """Test CLEAR command completion signal"""
        completed, messages = self.send_command_and_wait('CLEAR')
        assert self.has_message_type(messages, 'command_complete',
                       "CLEAR command should send completion signal")

    # Helper Methods
    def assertTrue(self, condition, message=""):
        """Basic assertion helper"""
        if not condition:
            raise AssertionError(message or "Assertion failed")
    
    def assertFalse(self, condition, message=""):
        """Basic assertion helper"""
        if condition:
            raise AssertionError(message or "Assertion failed")

    def skip_test(self, reason):
        """Skip test with reason"""
        print(f"SKIPPED: {reason}")


if __name__ == '__main__':
    print("WebSocket Completion Signals Integration Tests")
    print("=" * 60)
    print("NOTE: These tests require the Flask server to be running on localhost:5000")
    print("Start the server with: python app.py")
    print("=" * 60)
    
    # Run the tests
    test_suite = WebSocketCompletionSignalsTest()
    results = test_suite.run_all_tests()
    
    print(f"\nTest Results for {results.name}:")
    print(f"  Total: {results.total_count}")
    print(f"  Passed: {results.passed_count}") 
    print(f"  Failed: {results.failed_count}")
    
    if results.failed_count > 0:
        print("\nFailed Tests:")
        for result in results.results:
            if not result.passed:
                print(f"  ❌ {result.name}: {result.message}")
                if result.traceback:
                    print(f"     {result.traceback}")
    
    print(f"\nSuccess rate: {results.success_rate:.1%}")