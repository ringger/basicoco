#!/usr/bin/env python3

"""
Comprehensive tests for file management commands: SAVE, LOAD, FILES, KILL, CD
Tests the new CLI functionality added in Phase 1.
"""

import sys
import os
import pytest
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))


class TestFileCommands:
    """Test cases for file management commands (SAVE, FILES, KILL, CD)"""

    def assert_output_contains(self, result, text):
        """Helper method to check if text is in output"""
        for item in result:
            if item.get('type') == 'text' and text in item.get('text', ''):
                return True
        pytest.fail(f"Text '{text}' not found in output")

    @pytest.fixture(autouse=True)
    def test_dir(self, temp_programs_dir):
        """Use shared temp directory fixture."""
        self.programs_dir = temp_programs_dir
        yield os.path.dirname(temp_programs_dir)  # parent of programs/

    def test_basic_functionality(self, basic, helpers):
        """Test basic functionality to ensure test framework works"""
        result = basic.process_command('PRINT "TEST"')
        text_output = helpers.get_text_output(result)
        assert text_output == ['TEST']

    # SAVE Command Tests
    def test_save_basic_program(self, basic, helpers):
        """Test saving a basic program"""
        # Create a simple program
        basic.process_command('10 PRINT "HELLO"')
        basic.process_command('20 END')
        
        # Save the program
        result = basic.process_command('SAVE "testprog"')
        self.assert_output_contains(result, 'SAVED 2 LINES TO testprog.bas')
        
        # Verify file was created
        assert os.path.exists('programs/testprog.bas')

    def test_save_with_explicit_extension(self, basic, helpers):
        """Test saving with explicit .bas extension"""
        basic.process_command('10 PRINT "TEST"')
        
        result = basic.process_command('SAVE "test.bas"')
        self.assert_output_contains(result, 'SAVED 1 LINES TO test.bas')
        assert os.path.exists('programs/test.bas')

    def test_save_quoted_filename(self, basic, helpers):
        """Test saving with quoted and unquoted filenames"""
        basic.process_command('10 PRINT "TEST"')
        
        # Test with double quotes
        result = basic.process_command('SAVE "quoted_test"')
        self.assert_output_contains(result, 'SAVED 1 LINES TO quoted_test.bas')
        
        # Test with single quotes
        basic.process_command('NEW')
        basic.process_command('10 PRINT "TEST2"')
        result = basic.process_command("SAVE 'single_test'")
        self.assert_output_contains(result, 'SAVED 1 LINES TO single_test.bas')

    def test_save_no_program_error(self, basic, helpers):
        """Test saving when no program exists"""
        # Clear any existing program
        basic.process_command('NEW')
        
        helpers.assert_error_output(basic, 'SAVE "empty"', 'NO PROGRAM TO SAVE')

    def test_save_no_filename_error(self, basic, helpers):
        """Test saving without providing filename"""
        basic.process_command('10 PRINT "TEST"')
        
        helpers.assert_error_output(basic, 'SAVE', 'SYNTAX ERROR: Filename required')
        helpers.assert_error_output(basic, 'SAVE ""', 'SYNTAX ERROR: Filename required')

    def test_save_preserves_line_numbers(self, basic, helpers):
        """Test that saved programs preserve line numbers correctly"""
        basic.process_command('30 PRINT "THIRD"')
        basic.process_command('10 PRINT "FIRST"')
        basic.process_command('20 PRINT "SECOND"')
        
        basic.process_command('SAVE "ordered"')
        
        # Read the file and verify line order
        with open('programs/ordered.bas', 'r') as f:
            content = f.read()
            lines = content.strip().split('\n')
            
        # Should be saved in line number order
        assert lines[0] == '10 PRINT "FIRST"'
        assert lines[1] == '20 PRINT "SECOND"'
        assert lines[2] == '30 PRINT "THIRD"'

    # FILES Command Tests
    def test_files_empty_directory(self, basic, helpers):
        """Test DIR command shows available files"""
        # The DIR command will show files from multiple directories
        # This test just verifies it works and shows the basic structure
        result = basic.process_command('DIR')
        self.assert_output_contains(result, 'BASIC PROGRAM FILES:')
        self.assert_output_contains(result, 'Use LOAD "filename" to load a program')

    def test_files_with_programs(self, basic, helpers):
        """Test DIR command with existing programs"""
        # Create test files
        with open('programs/test1.bas', 'w') as f:
            f.write('10 PRINT "TEST1"\n')
        with open('programs/test2.bas', 'w') as f:
            f.write('10 PRINT "TEST2"\n')
        
        result = basic.process_command('DIR')
        self.assert_output_contains(result, 'BASIC PROGRAM FILES:')
        self.assert_output_contains(result, 'test1.bas')
        self.assert_output_contains(result, 'test2.bas')
        # Don't check exact count since other files may exist
        self.assert_output_contains(result, 'FILE(S)')

    def test_files_shows_file_info(self, basic, helpers):
        """Test that FILES shows file size and date information"""
        # Create a test file
        with open('programs/info_test.bas', 'w') as f:
            f.write('10 PRINT "SIZE TEST"\n')
        
        result = basic.process_command('DIR')
        output_text = ' '.join([item['text'] for item in result if item['type'] == 'text'])
        
        # Should contain filename and size information
        assert 'info_test.bas' in output_text
        assert 'bytes' in output_text

    # CD Command Tests
    def test_cd_show_current_directory(self, basic, helpers, test_dir):
        """Test CD command without arguments shows current directory"""
        result = basic.process_command('CD')
        self.assert_output_contains(result, 'CURRENT DIRECTORY:')
        self.assert_output_contains(result, test_dir)

    def test_cd_change_directory(self, basic, helpers, test_dir):
        """Test CD command changes directory"""
        # Create a subdirectory
        subdir = os.path.join(test_dir, 'subdir')
        os.makedirs(subdir)
        
        # Change to subdirectory
        result = basic.process_command(f'CD "{subdir}"')
        self.assert_output_contains(result, 'CHANGED FROM')
        self.assert_output_contains(result, 'TO')
        
        # Verify we're in the new directory (use realpath to resolve symlinks, e.g. /var -> /private/var on macOS)
        assert os.path.realpath(os.getcwd()) == os.path.realpath(subdir)

    def test_cd_with_shortcuts(self, basic, helpers, test_dir):
        """Test CD command with path shortcuts"""
        # Create subdirectory and change to it
        subdir = os.path.join(test_dir, 'test_subdir')
        os.makedirs(subdir)
        os.chdir(subdir)

        # Test .. (parent directory)
        result = basic.process_command('CD ".."')
        self.assert_output_contains(result, 'CHANGED FROM')
        assert os.path.realpath(os.getcwd()) == os.path.realpath(test_dir)

    def test_cd_quoted_paths(self, basic, helpers, test_dir):
        """Test CD command with quoted paths"""
        subdir = os.path.join(test_dir, 'quoted test')
        os.makedirs(subdir)

        # Test with double quotes
        result = basic.process_command(f'CD "{subdir}"')
        self.assert_output_contains(result, 'CHANGED FROM')
        assert os.path.realpath(os.getcwd()) == os.path.realpath(subdir)
        
        # Go back to test single quotes
        os.chdir(test_dir)
        result = basic.process_command(f"CD '{subdir}'")
        self.assert_output_contains(result, 'CHANGED FROM')

    def test_cd_nonexistent_directory(self, basic, helpers):
        """Test CD command with non-existent directory"""
        helpers.assert_error_output(basic, 'CD "nonexistent_dir"', 'DIRECTORY NOT FOUND')

    # KILL Command Tests
    def test_kill_file_confirmation_cancel(self, basic, helpers):
        """Test KILL command with confirmation cancellation"""
        # Create test file
        basic.process_command('10 PRINT "TO DELETE"')
        basic.process_command('SAVE "kill_test"')
        
        # Verify file exists
        assert os.path.exists('programs/kill_test.bas')
        
        # Try to kill it
        result = basic.process_command('KILL "kill_test"')
        
        # Should ask for confirmation
        self.assert_output_contains(result, 'DELETE kill_test.bas? (Y/N)')
        
        # Should have input request
        has_input_request = any(item.get('type') == 'input_request' 
                               for item in result)
        assert has_input_request, "Should request confirmation input"

    def test_kill_confirmation_processing(self, basic, helpers):
        """Test KILL confirmation processing"""
        # Create test file
        basic.process_command('10 PRINT "DELETE ME"')
        basic.process_command('SAVE "confirm_test"')
        
        filepath = 'programs/confirm_test.bas'
        assert os.path.exists(filepath)
        
        # Test cancellation
        result = basic.process_kill_confirmation('N', filepath)
        self.assert_output_contains(result, 'DELETE CANCELLED')
        assert os.path.exists(filepath), "File should still exist after cancel"
        
        # Test deletion confirmation
        result = basic.process_kill_confirmation('Y', filepath)
        self.assert_output_contains(result, 'DELETED confirm_test.bas')
        assert not os.path.exists(filepath), "File should be deleted after confirmation"

    def test_kill_nonexistent_file(self, basic, helpers):
        """Test KILL command with non-existent file"""
        helpers.assert_error_output(basic, 'KILL "nonexistent"', 'FILE NOT FOUND')

    def test_kill_no_filename_error(self, basic, helpers):
        """Test KILL command without filename"""
        helpers.assert_error_output(basic, 'KILL', 'SYNTAX ERROR: Filename required')
        helpers.assert_error_output(basic, 'KILL ""', 'SYNTAX ERROR: Filename required')

    def test_kill_adds_bas_extension(self, basic, helpers):
        """Test that KILL automatically adds .bas extension"""
        # Create test file
        basic.process_command('10 PRINT "EXT TEST"')
        basic.process_command('SAVE "extension_test"')
        
        # Kill without extension
        result = basic.process_command('KILL "extension_test"')
        self.assert_output_contains(result, 'DELETE extension_test.bas? (Y/N)')

    # Integration Tests
    def test_save_load_roundtrip(self, basic, helpers):
        """Test saving and loading a program maintains integrity"""
        # Create a complex program
        program_lines = [
            '10 PRINT "HELLO WORLD"',
            '20 FOR I = 1 TO 5',
            '30 PRINT "LINE"; I',
            '40 NEXT I',
            '50 END'
        ]
        
        for line in program_lines:
            basic.process_command(line)
        
        # Save the program
        basic.process_command('SAVE "roundtrip_test"')
        
        # Clear memory and load it back
        basic.process_command('NEW')
        result = basic.process_command('LOAD "roundtrip_test"')
        self.assert_output_contains(result, 'LOADED 5 LINES')
        
        # Verify program integrity by listing it
        list_result = basic.process_command('LIST')
        list_text = ' '.join([item['text'] for item in list_result if item['type'] == 'text'])
        
        # Check that all original lines are present
        for line in program_lines:
            line_number = line.split()[0]
            assert line_number in list_text

    def test_files_after_save_operations(self, basic, helpers):
        """Test DIR command reflects SAVE operations"""
        # Initially should have no files or existing files
        initial_result = basic.process_command('DIR')
        
        # Create and save some programs
        programs = ['prog1', 'prog2', 'prog3']
        for prog in programs:
            basic.process_command('NEW')
            basic.process_command(f'10 PRINT "{prog.upper()}"')
            basic.process_command(f'SAVE "{prog}"')
        
        # Check DIR shows all programs
        result = basic.process_command('DIR')
        output_text = ' '.join([item['text'] for item in result if item['type'] == 'text'])
        
        for prog in programs:
            assert f'{prog}.bas' in output_text

    def test_cd_affects_file_operations(self, basic, helpers):
        """Test that CD affects where files are found and saved"""
        # Create a program and save it
        basic.process_command('10 PRINT "MAIN DIR"')
        basic.process_command('SAVE "main_test"')
        
        # Change to programs directory
        result = basic.process_command('CD "programs"')
        self.assert_output_contains(result, 'CHANGED FROM')
        
        # DIR should still work from subdirectory
        files_result = basic.process_command('DIR')
        self.assert_output_contains(files_result, 'main_test.bas')

    # Error Handling Tests
    def test_command_error_messages_are_helpful(self, basic, helpers):
        """Test that error messages provide helpful suggestions"""
        # Test SAVE without program
        helpers.assert_error_output(basic, 'SAVE "test"', 'NO PROGRAM TO SAVE')
        
        # Test LOAD non-existent file
        helpers.assert_error_output(basic, 'LOAD "nonexistent"', 'FILE NOT FOUND')

    def test_filename_parsing_edge_cases(self, basic, helpers):
        """Test filename parsing with various quote combinations"""
        basic.process_command('10 PRINT "QUOTE TEST"')
        
        # Test various quoting styles
        quote_tests = [
            '"normal"',
            "'single'", 
            '"with spaces"',
            '"with.extension.bas"'
        ]
        
        for i, quoted_name in enumerate(quote_tests):
            result = basic.process_command(f'SAVE {quoted_name}')
            self.assert_output_contains(result, 'SAVED 1 LINES TO')
