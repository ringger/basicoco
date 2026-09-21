"""Security tests against a live server: origin checks and the KILL protocol.

The server has no authentication, so it must only accept Socket.IO
connections from its own page (not from arbitrary web sites the user visits)
and must never let a client choose which file KILL deletes.
"""

import os
import threading

import pytest
import socketio


pytestmark = pytest.mark.slow


def _connect(url, origin=None):
    client = socketio.Client()
    headers = {'Origin': origin} if origin else None
    client.connect(url, headers=headers, wait_timeout=5)
    return client


def test_foreign_origin_is_rejected(live_server):
    with pytest.raises(socketio.exceptions.ConnectionError):
        _connect(live_server.url, origin='http://evil.example')


def test_same_origin_is_accepted(live_server):
    client = _connect(live_server.url, origin=live_server.url)
    try:
        assert client.connected
    finally:
        client.disconnect()


class _Session:
    """A Socket.IO client that collects output messages."""

    def __init__(self, url, auth=None):
        self.messages = []
        self.session_info = []
        self.complete = threading.Event()
        self.client = socketio.Client()
        self.client.on('session_id', lambda data: self.session_info.append(data))

        @self.client.on('output')
        def on_output(data):
            items = data if isinstance(data, list) else [data]
            self.messages.extend(items)
            if any(isinstance(d, dict) and d.get('type') == 'command_complete' for d in items):
                self.complete.set()

        self.client.connect(url, auth=auth, wait_timeout=5)
        threading.Event().wait(0.3)  # let the session_id event arrive

    def run(self, command, timeout=5):
        self.complete.clear()
        self.client.emit('execute_command', {'command': command})
        return self.complete.wait(timeout)

    def texts(self):
        return [m.get('text', '') for m in self.messages if m.get('type') == 'text']


def test_ctrl_c_stops_a_running_program(live_server):
    session = _Session(live_server.url)
    try:
        session.run('SAFETY OFF')
        session.run('10 X=X+1: GOTO 10')
        session.complete.clear()
        session.client.emit('execute_command', {'command': 'RUN'})
        assert not session.complete.wait(1.0), 'runaway loop should still be running'
        session.client.emit('break_execution', {})
        assert session.complete.wait(5), 'Ctrl+C did not stop the program'
        assert any(t.startswith('BREAK IN 10') for t in session.texts())
        # The interpreter is usable again and kept the loop's variables
        assert session.run('PRINT X>0')
        assert '-1' in ' '.join(session.texts())
    finally:
        session.client.disconnect()


def test_second_command_waits_for_the_first(live_server):
    """Commands for one interpreter run one at a time, never concurrently."""
    session = _Session(live_server.url)
    try:
        session.run('10 FOR I=1 TO 20000: NEXT I: PRINT "FIRST"')
        session.complete.clear()
        session.client.emit('execute_command', {'command': 'RUN'})
        session.client.emit('execute_command', {'command': 'PRINT "SECOND"'})
        deadline = threading.Event()
        for _ in range(50):
            texts = session.texts()
            if 'FIRST' in texts and 'SECOND' in texts:
                break
            deadline.wait(0.1)
        texts = session.texts()
        assert texts.index('FIRST') < texts.index('SECOND')
    finally:
        session.client.disconnect()


def test_tab_switch_resume_does_not_skip_pending_input(live_server):
    session = _Session(live_server.url)
    try:
        session.run('10 INPUT "N";N')
        session.run('20 PRINT "GOT";N')
        session.complete.clear()
        session.client.emit('execute_command', {'command': 'RUN'})
        threading.Event().wait(0.5)  # INPUT request arrives; no command_complete
        session.client.emit('pause_for_tab_switch', {'tabId': 'main'})
        session.client.emit('resume_from_tab_switch', {'tabId': 'main'})
        threading.Event().wait(0.5)
        assert not any('GOT' in t for t in session.texts()), \
            'resuming the tab must not skip the pending INPUT'
    finally:
        session.client.disconnect()


def test_reconnect_resumes_session_with_program(live_server):
    first = _Session(live_server.url)
    first.run('10 PRINT "KEPT"')
    old_session = first.session_info[0]['session_id']
    first.client.disconnect()

    second = _Session(live_server.url, auth={'session_id': old_session})
    try:
        assert second.session_info == [{'session_id': old_session, 'resumed': True}]
        assert second.run('LIST')
        assert '10 PRINT "KEPT"' in second.texts()
    finally:
        second.client.disconnect()


def test_unknown_session_id_gets_fresh_session(live_server):
    session = _Session(live_server.url, auth={'session_id': 'not-a-real-session'})
    try:
        info = session.session_info[0]
        assert info['resumed'] is False
        assert info['session_id'] != 'not-a-real-session'
    finally:
        session.client.disconnect()


def test_forged_kill_confirmation_cannot_delete_outside_sandbox(live_server):
    victim = os.path.join(live_server.workdir, 'victim.txt')
    with open(victim, 'w') as f:
        f.write('keep me')
    done = threading.Event()
    client = socketio.Client()

    @client.on('output')
    def on_output(data):
        if any(isinstance(d, dict) and d.get('type') == 'command_complete' for d in data):
            done.set()

    client.connect(live_server.url, wait_timeout=5)
    try:
        client.emit('input_response',
                    {'variable': '_kill_confirm', 'value': 'Y', 'filename': victim})
        assert done.wait(5)
    finally:
        client.disconnect()
    assert os.path.exists(victim)
