#!/usr/bin/env python3

"""
Unit tests for program management commands: DIR, FILES, DRIVE, SAVE, CLOAD, CSAVE
Tests individual command functionality in isolation.
"""

import sys
import os
import tempfile
import shutil
import pytest
from pathlib import Path

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from test_base import BaseTestCase


class TestProgramManagementCommand:
    """Test program management commands"""
    
    @pytest.fixture
    def temp_setup(self):
        """Set up test environment with temporary directory"""
        # Create a temporary directory for test files
        temp_dir = tempfile.mkdtemp()
        original_cwd = os.getcwd()

        # Create a test programs directory
        programs_dir = os.path.join(temp_dir, 'programs')
        os.makedirs(programs_dir, exist_ok=True)

        # Create some test program files
        with open(os.path.join(programs_dir, 'test1.bas'), 'w') as f:
            f.write('10 PRINT "TEST PROGRAM 1"\n')
        with open(os.path.join(programs_dir, 'test2.bas'), 'w') as f:
            f.write('10 PRINT "TEST PROGRAM 2"\n20 END\n')

        # Change to temp directory so programs are saved here
        os.chdir(temp_dir)

        yield programs_dir

        # Cleanup
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)


    def test_basic_functionality(self, basic, helpers):
        """Test basic program management command functionality"""
        # Test DIR command shows available programs
        result = basic.process_command('DIR')
        assert any('BASIC PROGRAM FILES' in str(r.get('text', '')) for r in result)
        
        # Test FILES command (no-op)
        result = basic.process_command('FILES 4')
        result = basic.process_command('FILES 4')
        text_output = helpers.get_text_output(result)
        assert text_output == ['OK']
        
        # Test DRIVE command (no-op) 
        result = basic.process_command('DRIVE 0')
        result = basic.process_command('DRIVE 0')
        text_output = helpers.get_text_output(result)
        assert text_output == ['OK']

    def test_dir_command(self, basic, helpers):
        """Test DIR command functionality"""
        result = basic.process_command('DIR')
        
        # Should show header
        assert any('BASIC PROGRAM FILES' in str(r.get('text', '')) for r in result)
        
        # Should show test files if they exist
        dir_output = ' '.join(str(r.get('text', '')) for r in result)
        
        # Should show total count
        assert 'FILE(S)' in dir_output or 'NO .BAS FILES FOUND' in dir_output

    def test_files_command_no_op(self, basic, helpers):
        """Test FILES command is a no-op"""
        # FILES with no arguments
        result = basic.process_command('FILES')
        text_output = helpers.get_text_output(result)
        assert text_output == ['OK']
        
        # FILES with various argument patterns
        result = basic.process_command('FILES 4')
        text_output = helpers.get_text_output(result)
        assert text_output == ['OK']
        result = basic.process_command('FILES 8')
        text_output = helpers.get_text_output(result)
        assert text_output == ['OK']
        result = basic.process_command('FILES 15')
        text_output = helpers.get_text_output(result)
        assert text_output == ['OK']

    def test_drive_command_no_op(self, basic, helpers):
        """Test DRIVE command is a no-op"""
        # DRIVE with valid drive numbers
        result = basic.process_command('DRIVE 0')
        text_output = helpers.get_text_output(result)
        assert text_output == ['OK']
        result = basic.process_command('DRIVE 1')
        text_output = helpers.get_text_output(result)
        assert text_output == ['OK']
        result = basic.process_command('DRIVE 2')
        text_output = helpers.get_text_output(result)
        assert text_output == ['OK']
        result = basic.process_command('DRIVE 3')
        text_output = helpers.get_text_output(result)
        assert text_output == ['OK']

    def test_save_command(self, basic, helpers, temp_setup):
        """Test SAVE command functionality"""
        # Create a test program
        basic.process_command('10 PRINT "SAVE TEST"')
        basic.process_command('20 END')
        
        # Test SAVE with quoted filename
        result = basic.process_command('SAVE "savetest"')
        assert any('SAVED' in str(r.get('text', '')) for r in result)
        
        # Verify file was created
        saved_file = os.path.join(temp_setup, 'savetest.bas')
        assert os.path.exists(saved_file)
        
        # Verify file contents
        with open(saved_file, 'r') as f:
            content = f.read()
            assert '10 PRINT "SAVE TEST"' in content
            assert '20 END' in content

    def test_save_command_no_program(self, basic, helpers):
        """Test SAVE command with no program loaded"""
        # Clear any program
        basic.process_command('NEW')
        
        # Try to save - should show error
        result = basic.process_command('SAVE "empty"')
        assert any('NO PROGRAM TO SAVE' in str(r.get('message', '')) for r in result)

    def test_save_command_auto_extension(self, basic, helpers):
        """Test SAVE command automatically adds .bas extension"""
        # Create a test program
        basic.process_command('10 PRINT "EXTENSION TEST"')
        
        # Save without extension
        basic.process_command('SAVE "autoext"')
        
        # Verify file was created with .bas extension
        saved_file = os.path.join(temp_setup, 'autoext.bas')
        assert os.path.exists(saved_file)

    def test_cload_command_alias(self, basic, helpers):
        """Test CLOAD command works as LOAD alias"""
        # Create a test file first
        test_file = os.path.join(temp_setup, 'cloadtest.bas')
        with open(test_file, 'w') as f:
            f.write('10 PRINT "CLOAD TEST"\n20 END\n')
        
        # Clear current program
        basic.process_command('NEW')
        
        # Use CLOAD to load the program
        result = basic.process_command('CLOAD "cloadtest"')
        
        # Should show loaded message
        assert any('LOADED' in str(r.get('text', '') for r in result))
        
        # Verify program was loaded by listing it
        list_result = basic.process_command('LIST')
        list_output = ' '.join(str(r.get('text', '')) for r in list_result)
        assert 'PRINT "CLOAD TEST"' in list_output

    def test_csave_command_alias(self, basic, helpers):
        """Test CSAVE command works as SAVE alias"""
        # Create a test program
        basic.process_command('10 PRINT "CSAVE TEST"')
        basic.process_command('20 PRINT "CASSETTE"')
        
        # Use CSAVE to save the program
        result = basic.process_command('CSAVE "csavetest"')
        assert any('SAVED' in str(r.get('text', '')) for r in result)
        
        # Verify file was created
        saved_file = os.path.join(temp_setup, 'csavetest.bas')
        assert os.path.exists(saved_file)
        
        # Verify file contents
        with open(saved_file, 'r') as f:
            content = f.read()
            assert 'PRINT "CSAVE TEST"' in content
            assert 'PRINT "CASSETTE"' in content

    def test_save_command_syntax_errors(self, basic, helpers):
        """Test SAVE command syntax error handling"""
        # Create a test program
        basic.process_command('10 PRINT "TEST"')
        
        # Test SAVE without filename
        result = basic.process_command('SAVE')
        assert any('SYNTAX ERROR' in str(r.get('message', '')) for r in result)
        
        # Test SAVE with empty quotes
        result = basic.process_command('SAVE ""')
        assert any('SYNTAX ERROR' in str(r.get('message', '')) for r in result)

    def test_program_persistence_workflow(self, basic, helpers):
        """Test complete save/load workflow"""
        # Create a program
        basic.process_command('10 FOR I = 1 TO 5')
        basic.process_command('20 PRINT "HELLO"; I')
        basic.process_command('30 NEXT I')
        
        # Save it
        basic.process_command('SAVE "workflow"')
        
        # Clear program
        basic.process_command('NEW')
        
        # Verify program is cleared
        list_result = basic.process_command('LIST')
        list_output = ' '.join(str(r.get('text', '')) for r in list_result)
        assert 'FOR I' not in list_output
        
        # Load it back using CLOAD (alias test)
        basic.process_command('CLOAD "workflow"')
        
        # Verify program is loaded
        list_result = basic.process_command('LIST')
        list_output = ' '.join(str(r.get('text', '')) for r in list_result)
        assert 'FOR I = 1 TO 5' in list_output
        assert 'PRINT "HELLO"; I' in list_output
        assert 'NEXT I' in list_output

    def test_dir_command_with_no_files(self, basic, helpers):
        """Test DIR command shows appropriate output format"""
        result = basic.process_command('DIR')
        dir_output = ' '.join(str(r.get('text', '')) for r in result)
        
        # Should show basic header and total
        assert 'BASIC PROGRAM FILES:' in dir_output
        assert 'TOTAL:' in dir_output 
        assert 'FILE(S)' in dir_output

    def test_save_with_path(self, basic, helpers):
        """Test SAVE command with directory path"""
        # Create a test program
        basic.process_command('10 PRINT "PATH TEST"')
        
        # Try to save with explicit programs/ path
        result = basic.process_command('SAVE "programs/pathtest"')
        
        # Should succeed
        assert any('SAVED' in str(r.get('text', '')) for r in result)
        
        # Verify file was created in programs directory
        saved_file = os.path.join(temp_setup, 'pathtest.bas')
        assert os.path.exists(saved_file)

    def test_command_registry_integration(self, basic, helpers):
        """Test that all commands are properly registered"""
        # Test that commands are recognized and produce appropriate responses
        
        # Commands that work without arguments (no-ops)
        no_arg_commands = ['DIR', 'FILES', 'DRIVE']
        for command in no_arg_commands:
            result = basic.process_command(command)
            # These should either succeed or give specific parameter errors, not generic syntax errors
            error_messages = [str(r.get('message', '')) for r in result if r.get('type') == 'error']
            for msg in error_messages:
                assert 'UNKNOWN COMMAND' not in msg.upper(), f"Command {command} not recognized"
        
        # Commands that require arguments
        arg_commands = ['SAVE', 'CLOAD', 'CSAVE']
        for command in arg_commands:
            result = basic.process_command(command)
            # These should give specific "filename required" type errors, not "unknown command"
            error_messages = [str(r.get('message', '')) for r in result if r.get('type') == 'error']
            for msg in error_messages:
                assert 'UNKNOWN COMMAND' not in msg.upper(), f"Command {command} not recognized"
                # Should get specific parameter error
                assert 'FILENAME' in msg.upper() or 'REQUIRED' in msg.upper(), f"Command {command} should give filename error, got: {msg}"
