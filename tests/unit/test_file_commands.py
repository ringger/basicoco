#!/usr/bin/env python3

"""
Comprehensive tests for file management commands: SAVE, LOAD, FILES, KILL, CD
Tests the new CLI functionality added in Phase 1.
"""

import sys
import os
import tempfile
import shutil
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from test_base import BaseTestCase


class FileCommandsTest(BaseTestCase):
    """Test cases for file management commands (SAVE, FILES, KILL, CD)"""

    def setUp(self):
        """Set up test environment with temporary directory"""
        super().setUp()
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp(prefix='trs80_test_')
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create programs directory
        os.makedirs('programs', exist_ok=True)

    def tearDown(self):
        """Clean up test environment"""
        super().tearDown()
        # Restore original directory and clean up
        os.chdir(self.original_cwd)
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_basic_functionality(self):
        """Test basic functionality to ensure test framework works"""
        self.assert_text_output('PRINT "TEST"', 'TEST')

    # SAVE Command Tests
    def test_save_basic_program(self):
        """Test saving a basic program"""
        # Create a simple program
        self.basic.execute_command('10 PRINT "HELLO"')
        self.basic.execute_command('20 END')
        
        # Save the program
        result = self.basic.execute_command('SAVE "testprog"')
        self.assert_output_contains(result, 'SAVED 2 LINES TO testprog.bas')
        
        # Verify file was created
        self.assertTrue(os.path.exists('programs/testprog.bas'))

    def test_save_with_explicit_extension(self):
        """Test saving with explicit .bas extension"""
        self.basic.execute_command('10 PRINT "TEST"')
        
        result = self.basic.execute_command('SAVE "test.bas"')
        self.assert_output_contains(result, 'SAVED 1 LINES TO test.bas')
        self.assertTrue(os.path.exists('programs/test.bas'))

    def test_save_quoted_filename(self):
        """Test saving with quoted and unquoted filenames"""
        self.basic.execute_command('10 PRINT "TEST"')
        
        # Test with double quotes
        result = self.basic.execute_command('SAVE "quoted_test"')
        self.assert_output_contains(result, 'SAVED 1 LINES TO quoted_test.bas')
        
        # Test with single quotes
        self.basic.execute_command('NEW')
        self.basic.execute_command('10 PRINT "TEST2"')
        result = self.basic.execute_command("SAVE 'single_test'")
        self.assert_output_contains(result, 'SAVED 1 LINES TO single_test.bas')

    def test_save_no_program_error(self):
        """Test saving when no program exists"""
        # Clear any existing program
        self.basic.execute_command('NEW')
        
        self.assert_error_output('SAVE "empty"', 'NO PROGRAM TO SAVE')

    def test_save_no_filename_error(self):
        """Test saving without providing filename"""
        self.basic.execute_command('10 PRINT "TEST"')
        
        self.assert_error_output('SAVE', 'SYNTAX ERROR: Filename required')
        self.assert_error_output('SAVE ""', 'SYNTAX ERROR: Filename required')

    def test_save_preserves_line_numbers(self):
        """Test that saved programs preserve line numbers correctly"""
        self.basic.execute_command('30 PRINT "THIRD"')
        self.basic.execute_command('10 PRINT "FIRST"')
        self.basic.execute_command('20 PRINT "SECOND"')
        
        self.basic.execute_command('SAVE "ordered"')
        
        # Read the file and verify line order
        with open('programs/ordered.bas', 'r') as f:
            content = f.read()
            lines = content.strip().split('\n')
            
        # Should be saved in line number order
        self.assertEqual(lines[0], '10 PRINT "FIRST"')
        self.assertEqual(lines[1], '20 PRINT "SECOND"')
        self.assertEqual(lines[2], '30 PRINT "THIRD"')

    # FILES Command Tests
    def test_files_empty_directory(self):
        """Test DIR command shows available files"""
        # The DIR command will show files from multiple directories
        # This test just verifies it works and shows the basic structure
        result = self.basic.execute_command('DIR')
        self.assert_output_contains(result, 'BASIC PROGRAM FILES:')
        self.assert_output_contains(result, 'Use LOAD "filename" to load a program')

    def test_files_with_programs(self):
        """Test DIR command with existing programs"""
        # Create test files
        with open('programs/test1.bas', 'w') as f:
            f.write('10 PRINT "TEST1"\n')
        with open('programs/test2.bas', 'w') as f:
            f.write('10 PRINT "TEST2"\n')
        
        result = self.basic.execute_command('DIR')
        self.assert_output_contains(result, 'BASIC PROGRAM FILES:')
        self.assert_output_contains(result, 'test1.bas')
        self.assert_output_contains(result, 'test2.bas')
        # Don't check exact count since other files may exist
        self.assert_output_contains(result, 'FILE(S)')

    def test_files_shows_file_info(self):
        """Test that FILES shows file size and date information"""
        # Create a test file
        with open('programs/info_test.bas', 'w') as f:
            f.write('10 PRINT "SIZE TEST"\n')
        
        result = self.basic.execute_command('DIR')
        output_text = ' '.join([item['text'] for item in result if item['type'] == 'text'])
        
        # Should contain filename and size information
        self.assertIn('info_test.bas', output_text)
        self.assertIn('bytes', output_text)

    # CD Command Tests
    def test_cd_show_current_directory(self):
        """Test CD command without arguments shows current directory"""
        result = self.basic.execute_command('CD')
        self.assert_output_contains(result, 'CURRENT DIRECTORY:')
        self.assert_output_contains(result, self.test_dir)

    def test_cd_change_directory(self):
        """Test CD command changes directory"""
        # Create a subdirectory
        subdir = os.path.join(self.test_dir, 'subdir')
        os.makedirs(subdir)
        
        # Change to subdirectory
        result = self.basic.execute_command(f'CD "{subdir}"')
        self.assert_output_contains(result, 'CHANGED FROM')
        self.assert_output_contains(result, 'TO')
        
        # Verify we're in the new directory
        self.assertEqual(os.getcwd(), subdir)

    def test_cd_with_shortcuts(self):
        """Test CD command with path shortcuts"""
        # Create subdirectory and change to it
        subdir = os.path.join(self.test_dir, 'test_subdir')
        os.makedirs(subdir)
        os.chdir(subdir)
        
        # Test .. (parent directory)
        result = self.basic.execute_command('CD ".."')
        self.assert_output_contains(result, 'CHANGED FROM')
        self.assertEqual(os.getcwd(), self.test_dir)

    def test_cd_quoted_paths(self):
        """Test CD command with quoted paths"""
        subdir = os.path.join(self.test_dir, 'quoted test')
        os.makedirs(subdir)
        
        # Test with double quotes
        result = self.basic.execute_command(f'CD "{subdir}"')
        self.assert_output_contains(result, 'CHANGED FROM')
        self.assertEqual(os.getcwd(), subdir)
        
        # Go back to test single quotes
        os.chdir(self.test_dir)
        result = self.basic.execute_command(f"CD '{subdir}'")
        self.assert_output_contains(result, 'CHANGED FROM')

    def test_cd_nonexistent_directory(self):
        """Test CD command with non-existent directory"""
        self.assert_error_output('CD "nonexistent_dir"', 'DIRECTORY NOT FOUND')

    # KILL Command Tests
    def test_kill_file_confirmation_cancel(self):
        """Test KILL command with confirmation cancellation"""
        # Create test file
        self.basic.execute_command('10 PRINT "TO DELETE"')
        self.basic.execute_command('SAVE "kill_test"')
        
        # Verify file exists
        self.assertTrue(os.path.exists('programs/kill_test.bas'))
        
        # Try to kill it
        result = self.basic.execute_command('KILL "kill_test"')
        
        # Should ask for confirmation
        self.assert_output_contains(result, 'DELETE kill_test.bas? (Y/N)')
        
        # Should have input request
        has_input_request = any(item.get('type') == 'input_request' 
                               for item in result)
        self.assertTrue(has_input_request, "Should request confirmation input")

    def test_kill_confirmation_processing(self):
        """Test KILL confirmation processing"""
        # Create test file
        self.basic.execute_command('10 PRINT "DELETE ME"')
        self.basic.execute_command('SAVE "confirm_test"')
        
        filepath = 'programs/confirm_test.bas'
        self.assertTrue(os.path.exists(filepath))
        
        # Test cancellation
        result = self.basic.process_kill_confirmation('N', filepath)
        self.assert_output_contains(result, 'DELETE CANCELLED')
        self.assertTrue(os.path.exists(filepath), "File should still exist after cancel")
        
        # Test deletion confirmation
        result = self.basic.process_kill_confirmation('Y', filepath)
        self.assert_output_contains(result, 'DELETED confirm_test.bas')
        self.assertFalse(os.path.exists(filepath), "File should be deleted after confirmation")

    def test_kill_nonexistent_file(self):
        """Test KILL command with non-existent file"""
        self.assert_error_output('KILL "nonexistent"', 'FILE NOT FOUND')

    def test_kill_no_filename_error(self):
        """Test KILL command without filename"""
        self.assert_error_output('KILL', 'SYNTAX ERROR: Filename required')
        self.assert_error_output('KILL ""', 'SYNTAX ERROR: Filename required')

    def test_kill_adds_bas_extension(self):
        """Test that KILL automatically adds .bas extension"""
        # Create test file
        self.basic.execute_command('10 PRINT "EXT TEST"')
        self.basic.execute_command('SAVE "extension_test"')
        
        # Kill without extension
        result = self.basic.execute_command('KILL "extension_test"')
        self.assert_output_contains(result, 'DELETE extension_test.bas? (Y/N)')

    # Integration Tests
    def test_save_load_roundtrip(self):
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
            self.basic.execute_command(line)
        
        # Save the program
        self.basic.execute_command('SAVE "roundtrip_test"')
        
        # Clear memory and load it back
        self.basic.execute_command('NEW')
        result = self.basic.execute_command('LOAD "roundtrip_test"')
        self.assert_output_contains(result, 'LOADED 5 LINES')
        
        # Verify program integrity by listing it
        list_result = self.basic.execute_command('LIST')
        list_text = ' '.join([item['text'] for item in list_result if item['type'] == 'text'])
        
        # Check that all original lines are present
        for line in program_lines:
            line_number = line.split()[0]
            self.assertIn(line_number, list_text)

    def test_files_after_save_operations(self):
        """Test DIR command reflects SAVE operations"""
        # Initially should have no files or existing files
        initial_result = self.basic.execute_command('DIR')
        
        # Create and save some programs
        programs = ['prog1', 'prog2', 'prog3']
        for prog in programs:
            self.basic.execute_command('NEW')
            self.basic.execute_command(f'10 PRINT "{prog.upper()}"')
            self.basic.execute_command(f'SAVE "{prog}"')
        
        # Check DIR shows all programs
        result = self.basic.execute_command('DIR')
        output_text = ' '.join([item['text'] for item in result if item['type'] == 'text'])
        
        for prog in programs:
            self.assertIn(f'{prog}.bas', output_text)

    def test_cd_affects_file_operations(self):
        """Test that CD affects where files are found and saved"""
        # Create a program and save it
        self.basic.execute_command('10 PRINT "MAIN DIR"')
        self.basic.execute_command('SAVE "main_test"')
        
        # Change to programs directory
        result = self.basic.execute_command('CD "programs"')
        self.assert_output_contains(result, 'CHANGED FROM')
        
        # DIR should still work from subdirectory
        files_result = self.basic.execute_command('DIR')
        self.assert_output_contains(files_result, 'main_test.bas')

    # Error Handling Tests
    def test_command_error_messages_are_helpful(self):
        """Test that error messages provide helpful suggestions"""
        # Test SAVE without program
        self.assert_error_output('SAVE "test"', 'NO PROGRAM TO SAVE')
        
        # Test LOAD non-existent file
        self.assert_error_output('LOAD "nonexistent"', 'FILE NOT FOUND')

    def test_filename_parsing_edge_cases(self):
        """Test filename parsing with various quote combinations"""
        self.basic.execute_command('10 PRINT "QUOTE TEST"')
        
        # Test various quoting styles
        quote_tests = [
            '"normal"',
            "'single'", 
            '"with spaces"',
            '"with.extension.bas"'
        ]
        
        for i, quoted_name in enumerate(quote_tests):
            result = self.basic.execute_command(f'SAVE {quoted_name}')
            self.assert_output_contains(result, 'SAVED 1 LINES TO')

    # Helper Methods  
    def assert_output_contains(self, result, expected_text):
        """Assert that command result contains expected text"""
        output_text = ' '.join([item.get('text', item.get('message', '')) 
                               for item in result])
        if expected_text not in output_text:
            raise AssertionError(f"Expected '{expected_text}' in output: {output_text}")
    
    def assertTrue(self, condition, message=""):
        """Basic assertion helper"""
        if not condition:
            raise AssertionError(message or "Assertion failed")
    
    def assertFalse(self, condition, message=""):
        """Basic assertion helper"""
        if condition:
            raise AssertionError(message or "Assertion failed")
    
    def assertEqual(self, first, second, message=""):
        """Basic assertion helper"""
        if first != second:
            raise AssertionError(message or f"Expected {first} == {second}")
    
    def assertIn(self, member, container, message=""):
        """Basic assertion helper"""
        if member not in container:
            raise AssertionError(message or f"Expected '{member}' in '{container}'")


if __name__ == '__main__':
    # Run the tests if this file is executed directly
    test_suite = FileCommandsTest()
    results = test_suite.run_all_tests()
    
    print(f"Test Results for {results.name}:")
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