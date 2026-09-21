"""Shared fixtures for integration tests that need a live BasiCoCo server.

The ``live_server`` fixture launches ``app.py`` as a subprocess on a free
localhost port with its working directory set to a fresh temp directory, so
anything the server writes (SAVE, KILL, OPEN "O") lands in that temp
``programs/`` directory — never in the repo's real ``programs/``. Tests that
need the server get its port and programs directory from the fixture instead
of assuming a server someone started by hand on DEFAULT_PORT.
"""

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SERVER_START_TIMEOUT = 20  # seconds


@dataclass
class LiveServer:
    port: int
    url: str
    workdir: str
    programs_dir: str
    log_path: str

    def cli_command(self):
        """Shell command that starts the CLI client against this server."""
        client = os.path.join(PROJECT_ROOT, 'cli_client.py')
        return f'{sys.executable} {client} --host localhost --port {self.port}'


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def _wait_for_port(port, proc, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return False
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.1)
    return False


@pytest.fixture(scope='session')
def live_server():
    """Start a BasiCoCo server in a temp directory for the whole test session."""
    workdir = tempfile.mkdtemp(prefix='basicoco_live_server_')
    programs_dir = os.path.join(workdir, 'programs')
    os.makedirs(programs_dir)
    log_path = os.path.join(workdir, 'server.log')
    port = _free_port()

    env = dict(os.environ, PORT=str(port), DEBUG='false')
    with open(log_path, 'w') as log:
        proc = subprocess.Popen(
            [sys.executable, os.path.join(PROJECT_ROOT, 'app.py')],
            cwd=workdir, env=env, stdout=log, stderr=subprocess.STDOUT,
        )

    try:
        if not _wait_for_port(port, proc, SERVER_START_TIMEOUT):
            with open(log_path) as f:
                tail = f.read()[-2000:]
            pytest.fail(f'BasiCoCo server did not start on port {port}.\n{tail}')
        yield LiveServer(port=port, url=f'http://localhost:{port}', workdir=workdir,
                         programs_dir=programs_dir, log_path=log_path)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        shutil.rmtree(workdir, ignore_errors=True)
