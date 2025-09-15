#!/usr/bin/env python3

"""
Unit tests for program management commands: DIR, FILES, DRIVE, SAVE, CLOAD, CSAVE
Tests individual command functionality in isolation.
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from test_base import BaseTestCase


class ProgramManagementCommandTest(BaseTestCase):
    """Test program management commands"""
    
    def setUp(self):
        """Set up test environment with temporary directory"""
        super().setUp()
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        
        # Create a test programs directory
        self.programs_dir = os.path.join(self.temp_dir, 'programs')
        os.makedirs(self.programs_dir, exist_ok=True)
        
        # Create some test program files
        with open(os.path.join(self.programs_dir, 'test1.bas'), 'w') as f:
            f.write('10 PRINT "TEST PROGRAM 1"\n')
        with open(os.path.join(self.programs_dir, 'test2.bas'), 'w') as f:
            f.write('10 PRINT "TEST PROGRAM 2"\n20 END\n')
        
        # Change to temp directory so programs are saved here
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test environment"""
        super().tearDown()
        # Restore original directory
        os.chdir(self.original_cwd)
        # Clean up temp directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_basic_functionality(self):
        """Test basic program management command functionality"""
        # Test DIR command shows available programs
        result = self.basic.execute_command('DIR')
        self.assertTrue(any('BASIC PROGRAM FILES' in str(r.get('text', '')) for r in result))
        
        # Test FILES command (no-op)
        result = self.basic.execute_command('FILES 4')
        self.assert_text_output('FILES 4', 'OK')
        
        # Test DRIVE command (no-op) 
        result = self.basic.execute_command('DRIVE 0')
        self.assert_text_output('DRIVE 0', 'OK')

    def test_dir_command(self):
        """Test DIR command functionality"""
        result = self.basic.execute_command('DIR')
        
        # Should show header
        self.assertTrue(any('BASIC PROGRAM FILES' in str(r.get('text', '')) for r in result))
        
        # Should show test files if they exist
        dir_output = ' '.join(str(r.get('text', '')) for r in result)
        
        # Should show total count
        self.assertTrue('FILE(S)' in dir_output or 'NO .BAS FILES FOUND' in dir_output)

    def test_files_command_no_op(self):
        """Test FILES command is a no-op"""
        # FILES with no arguments
        self.assert_text_output('FILES', 'OK')
        
        # FILES with various argument patterns
        self.assert_text_output('FILES 4', 'OK')
        self.assert_text_output('FILES 8,256', 'OK')
        self.assert_text_output('FILES 15', 'OK')

    def test_drive_command_no_op(self):
        """Test DRIVE command is a no-op"""
        # DRIVE with valid drive numbers
        self.assert_text_output('DRIVE 0', 'OK')
        self.assert_text_output('DRIVE 1', 'OK')
        self.assert_text_output('DRIVE 2', 'OK')
        self.assert_text_output('DRIVE 3', 'OK')

    def test_save_command(self):
        """Test SAVE command functionality"""
        # Create a test program
        self.basic.execute_command('10 PRINT "SAVE TEST"')
        self.basic.execute_command('20 END')
        
        # Test SAVE with quoted filename
        result = self.basic.execute_command('SAVE "savetest"')
        self.assertTrue(any('SAVED' in str(r.get('text', '')) for r in result))
        
        # Verify file was created
        saved_file = os.path.join(self.programs_dir, 'savetest.bas')
        self.assertTrue(os.path.exists(saved_file))
        
        # Verify file contents
        with open(saved_file, 'r') as f:
            content = f.read()
            self.assertIn('10 PRINT "SAVE TEST"', content)
            self.assertIn('20 END', content)

    def test_save_command_no_program(self):
        """Test SAVE command with no program loaded"""
        # Clear any program
        self.basic.execute_command('NEW')
        
        # Try to save - should show error
        result = self.basic.execute_command('SAVE "empty"')
        self.assertTrue(any('NO PROGRAM TO SAVE' in str(r.get('message', '')) for r in result))

    def test_save_command_auto_extension(self):
        """Test SAVE command automatically adds .bas extension"""
        # Create a test program
        self.basic.execute_command('10 PRINT "EXTENSION TEST"')
        
        # Save without extension
        self.basic.execute_command('SAVE "autoext"')
        
        # Verify file was created with .bas extension
        saved_file = os.path.join(self.programs_dir, 'autoext.bas')
        self.assertTrue(os.path.exists(saved_file))

    def test_cload_command_alias(self):
        """Test CLOAD command works as LOAD alias"""
        # Create a test file first
        test_file = os.path.join(self.programs_dir, 'cloadtest.bas')
        with open(test_file, 'w') as f:
            f.write('10 PRINT "CLOAD TEST"\n20 END\n')
        
        # Clear current program
        self.basic.execute_command('NEW')
        
        # Use CLOAD to load the program
        result = self.basic.execute_command('CLOAD "cloadtest"')
        
        # Should show loaded message
        self.assertTrue(any('LOADED' in str(r.get('text', '')) for r in result))
        
        # Verify program was loaded by listing it
        list_result = self.basic.execute_command('LIST')
        list_output = ' '.join(str(r.get('text', '')) for r in list_result)
        self.assertIn('PRINT "CLOAD TEST"', list_output)

    def test_csave_command_alias(self):
        """Test CSAVE command works as SAVE alias"""
        # Create a test program
        self.basic.execute_command('10 PRINT "CSAVE TEST"')
        self.basic.execute_command('20 PRINT "CASSETTE"')
        
        # Use CSAVE to save the program
        result = self.basic.execute_command('CSAVE "csavetest"')
        self.assertTrue(any('SAVED' in str(r.get('text', '')) for r in result))
        
        # Verify file was created
        saved_file = os.path.join(self.programs_dir, 'csavetest.bas')
        self.assertTrue(os.path.exists(saved_file))
        
        # Verify file contents
        with open(saved_file, 'r') as f:
            content = f.read()
            self.assertIn('PRINT "CSAVE TEST"', content)
            self.assertIn('PRINT "CASSETTE"', content)

    def test_save_command_syntax_errors(self):
        """Test SAVE command syntax error handling"""
        # Create a test program
        self.basic.execute_command('10 PRINT "TEST"')
        
        # Test SAVE without filename
        result = self.basic.execute_command('SAVE')
        self.assertTrue(any('SYNTAX ERROR' in str(r.get('message', '')) for r in result))
        
        # Test SAVE with empty quotes
        result = self.basic.execute_command('SAVE ""')
        self.assertTrue(any('SYNTAX ERROR' in str(r.get('message', '')) for r in result))

    def test_program_persistence_workflow(self):
        """Test complete save/load workflow"""
        # Create a program
        self.basic.execute_command('10 FOR I = 1 TO 5')
        self.basic.execute_command('20 PRINT "HELLO"; I')
        self.basic.execute_command('30 NEXT I')
        
        # Save it
        self.basic.execute_command('SAVE "workflow"')
        
        # Clear program
        self.basic.execute_command('NEW')
        
        # Verify program is cleared
        list_result = self.basic.execute_command('LIST')
        list_output = ' '.join(str(r.get('text', '')) for r in list_result)
        self.assertNotIn('FOR I', list_output)
        
        # Load it back using CLOAD (alias test)
        self.basic.execute_command('CLOAD "workflow"')
        
        # Verify program is loaded
        list_result = self.basic.execute_command('LIST')
        list_output = ' '.join(str(r.get('text', '')) for r in list_result)
        self.assertIn('FOR I = 1 TO 5', list_output)
        self.assertIn('PRINT "HELLO"; I', list_output)
        self.assertIn('NEXT I', list_output)

    def test_dir_command_with_no_files(self):
        """Test DIR command shows appropriate output format"""
        result = self.basic.execute_command('DIR')
        dir_output = ' '.join(str(r.get('text', '')) for r in result)
        
        # Should show basic header and total
        self.assertIn('BASIC PROGRAM FILES:', dir_output)
        self.assertIn('TOTAL:', dir_output) 
        self.assertIn('FILE(S)', dir_output)

    def test_save_with_path(self):
        """Test SAVE command with directory path"""
        # Create a test program
        self.basic.execute_command('10 PRINT "PATH TEST"')
        
        # Try to save with explicit programs/ path
        result = self.basic.execute_command('SAVE "programs/pathtest"')
        
        # Should succeed
        self.assertTrue(any('SAVED' in str(r.get('text', '')) for r in result))
        
        # Verify file was created in programs directory
        saved_file = os.path.join(self.programs_dir, 'pathtest.bas')
        self.assertTrue(os.path.exists(saved_file))

    def test_command_registry_integration(self):
        """Test that all commands are properly registered"""
        # Test that commands are recognized and produce appropriate responses
        
        # Commands that work without arguments (no-ops)
        no_arg_commands = ['DIR', 'FILES', 'DRIVE']
        for command in no_arg_commands:
            result = self.basic.execute_command(command)
            # These should either succeed or give specific parameter errors, not generic syntax errors
            error_messages = [str(r.get('message', '')) for r in result if r.get('type') == 'error']
            for msg in error_messages:
                self.assertNotIn('UNKNOWN COMMAND', msg.upper(), f"Command {command} not recognized")
        
        # Commands that require arguments
        arg_commands = ['SAVE', 'CLOAD', 'CSAVE']
        for command in arg_commands:
            result = self.basic.execute_command(command)
            # These should give specific "filename required" type errors, not "unknown command"
            error_messages = [str(r.get('message', '')) for r in result if r.get('type') == 'error']
            for msg in error_messages:
                self.assertNotIn('UNKNOWN COMMAND', msg.upper(), f"Command {command} not recognized")
                # Should get specific parameter error
                self.assertTrue('FILENAME' in msg.upper() or 'REQUIRED' in msg.upper(), 
                              f"Command {command} should give filename error, got: {msg}")


if __name__ == '__main__':
    test = ProgramManagementCommandTest()
    suite = test.run_all_tests()
    from test_base import print_test_results
    print_test_results(suite)