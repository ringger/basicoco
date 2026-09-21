"""Unit tests for the filesystem sandbox (program_files.FileManager).

Every BASIC file command is confined to ./programs (plus a per-session
virtual CD directory). The bundled project programs are read-only.
"""

import os

import pytest

from emulator.core import CoCoBasic
from emulator.program_files import SandboxError, PROJECT_PROGRAMS_DIR


@pytest.fixture
def files(basic, temp_programs_dir):
    return basic.file_manager


class TestResolver:
    @pytest.mark.parametrize('name', ['/etc/hosts', '~/x', 'C:\\x', '../x', 'a/../../x', 'a\\..\\x'])
    def test_escapes_are_refused(self, files, name):
        with pytest.raises(SandboxError):
            files.resolve_writable(name)

    def test_plain_and_subdirectory_names(self, files, temp_programs_dir):
        root = os.path.realpath(temp_programs_dir)
        assert files.resolve_writable('A.BAS') == os.path.join(root, 'A.BAS')
        assert files.resolve_writable('sub/A.BAS') == os.path.join(root, 'sub', 'A.BAS')

    def test_symlink_escape_is_refused(self, files, temp_programs_dir):
        outside = os.path.join(os.path.dirname(temp_programs_dir), 'outside')
        os.makedirs(outside)
        os.symlink(outside, os.path.join(temp_programs_dir, 'link'))
        with pytest.raises(SandboxError):
            files.resolve_writable('link/secret.txt')

    def test_bundled_programs_are_readable(self, files):
        if not os.path.isdir(PROJECT_PROGRAMS_DIR):
            pytest.skip('no bundled programs')
        assert files.find_readable('lunar_lander.bas') == \
            os.path.join(PROJECT_PROGRAMS_DIR, 'lunar_lander.bas')


class TestBundledProgramsAreReadOnly:
    def test_kill_cannot_target_bundled_program(self, basic, helpers, temp_programs_dir):
        helpers.assert_error_output(basic, 'KILL "lunar_lander"', 'FILE NOT FOUND')
        assert os.path.exists(os.path.join(PROJECT_PROGRAMS_DIR, 'lunar_lander.bas'))

    def test_save_writes_to_sandbox_not_bundled(self, basic, temp_programs_dir):
        basic.process_command('LOAD "lunar_lander"')
        basic.process_command('SAVE "lunar_lander"')
        assert os.path.exists(os.path.join(temp_programs_dir, 'lunar_lander.bas'))


class TestKillConfirmation:
    def test_confirmation_without_pending_kill(self, basic, helpers, temp_programs_dir):
        errors = helpers.get_error_messages(basic.process_kill_confirmation('Y'))
        assert errors and 'NO KILL PENDING' in errors[0]

    def test_client_filename_is_ignored(self, basic, temp_programs_dir):
        keep = os.path.join(temp_programs_dir, 'keep.bas')
        doomed = os.path.join(temp_programs_dir, 'doomed.bas')
        for path in (keep, doomed):
            with open(path, 'w') as f:
                f.write('10 END\n')
        basic.process_command('KILL "doomed"')
        basic.process_kill_confirmation('Y', keep)  # forged filename
        assert os.path.exists(keep)
        assert not os.path.exists(doomed)

    def test_input_request_does_not_leak_path(self, basic, temp_programs_dir):
        with open(os.path.join(temp_programs_dir, 'x.bas'), 'w') as f:
            f.write('10 END\n')
        result = basic.process_command('KILL "x"')
        request = next(r for r in result if r.get('type') == 'input_request')
        assert 'filename' not in request


class TestVirtualCd:
    def test_cd_is_per_interpreter(self, temp_programs_dir):
        os.makedirs(os.path.join(temp_programs_dir, 'games'))
        first, second = CoCoBasic(), CoCoBasic()
        first.process_command('CD "games"')
        first.process_command('10 PRINT 1')
        second.process_command('10 PRINT 2')
        first.process_command('SAVE "p"')
        second.process_command('SAVE "p"')
        assert os.path.exists(os.path.join(temp_programs_dir, 'games', 'p.bas'))
        assert os.path.exists(os.path.join(temp_programs_dir, 'p.bas'))

    def test_open_uses_cd_directory(self, basic, helpers, temp_programs_dir):
        os.makedirs(os.path.join(temp_programs_dir, 'data'))
        basic.process_command('CD "data"')
        helpers.execute_program(basic, ['10 OPEN "O",#1,"OUT.TXT"', '20 PRINT #1,"X"', '30 CLOSE #1'])
        assert os.path.exists(os.path.join(temp_programs_dir, 'data', 'OUT.TXT'))
