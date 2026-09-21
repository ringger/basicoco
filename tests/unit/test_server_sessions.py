"""Server session handling through Flask-SocketIO's test client (#81
coverage pass): the tab limit, expiry of disconnected sessions, Ctrl+C when
no statement is executing, multi-variable INPUT, stray continuations and
resuming a paused program after a tab switch."""

import pytest

import app as server
from app import app, socketio


@pytest.fixture
def client():
    c = socketio.test_client(app)
    c.session_id = c.get_received()[0]['args'][0]['session_id']
    yield c
    if c.is_connected():
        c.disconnect()


def outputs(client):
    """Everything the server sent on 'output' since the last call, flattened."""
    items = []
    for message in client.get_received():
        if message['name'] == 'output':
            items.extend(message['args'][0])
    return items


def texts(items):
    return [i['text'] for i in items if i.get('type') == 'text']


def types(items):
    return [i['type'] for i in items]


def run(client, command, tab='main'):
    client.emit('execute_command', {'command': command, 'tabId': tab})
    return outputs(client)


def test_tabs_beyond_the_limit_are_refused(client):
    for n in range(server.MAX_TABS_PER_CONNECTION):
        assert 'error' not in types(run(client, 'PRINT 1', tab=f'tab{n}'))
    refused = run(client, 'PRINT 1', tab='one-too-many')
    assert refused[0]['type'] == 'error'
    assert 'TOO MANY TABS' in refused[0]['message']
    assert refused[-1]['type'] == 'command_complete'


def test_a_closed_tab_frees_its_slot(client):
    for n in range(server.MAX_TABS_PER_CONNECTION):
        run(client, 'PRINT 1', tab=f'tab{n}')
    assert 'error' in types(run(client, 'PRINT 1', tab='replacement'))
    client.emit('close_tab', {'tabId': 'tab0'})
    assert 'error' not in types(run(client, 'PRINT 1', tab='replacement'))


def test_an_expired_session_is_dropped_and_cannot_be_resumed(monkeypatch):
    first = socketio.test_client(app)
    session_id = first.get_received()[0]['args'][0]['session_id']
    first.emit('execute_command', {'command': '10 PRINT "OLD"', 'tabId': 'main'})
    first.disconnect()
    assert session_id in server.orphaned_sessions

    # Pretend the client left longer ago than the grace period
    monkeypatch.setitem(server.orphaned_sessions, session_id,
                        server.orphaned_sessions[session_id] - server.SESSION_GRACE_SECONDS - 1)
    late = socketio.test_client(app, auth={'session_id': session_id})
    try:
        greeting = late.get_received()[0]['args'][0]
        assert greeting['resumed'] is False
        assert greeting['session_id'] != session_id
        assert session_id not in server.orphaned_sessions
        assert session_id not in server.session_manager.sessions
    finally:
        late.disconnect()


def test_ctrl_c_at_an_input_prompt_abandons_the_program(client):
    run(client, '10 INPUT A')
    run(client, '20 PRINT "NEVER"')
    assert 'input_request' in types(run(client, 'RUN'))

    client.emit('break_execution', {'tabId': 'main'})
    items = outputs(client)
    assert texts(items) == ['^C', 'BREAK']
    assert types(items)[-1] == 'command_complete'

    basic = server.session_manager.sessions[client.session_id]['main']
    assert basic.waiting_for_input is False
    assert basic.program_counter is None
    # The prompt works again, and the program was not continued
    assert texts(run(client, 'PRINT "NEXT"')) == ['NEXT']


def test_ctrl_c_with_nothing_running_just_acknowledges(client):
    client.emit('break_execution', {'tabId': 'main'})
    assert outputs(client) == [{'type': 'command_complete'}]


def test_multi_variable_input_asks_for_each_variable(client):
    run(client, '10 INPUT A,B')
    run(client, '20 PRINT A+B')
    first = run(client, 'RUN')
    assert first[-1]['type'] == 'input_request'

    client.emit('input_response', {'variable': first[-1]['variable'], 'value': '2', 'tabId': 'main'})
    second = outputs(client)
    assert [i['type'] for i in second] == ['input_request']
    assert second[0]['variable'] == 'B'

    client.emit('input_response', {'variable': 'B', 'value': '3', 'tabId': 'main'})
    rest = outputs(client)
    assert ' 5 ' in texts(rest)
    assert types(rest)[-1] == 'command_complete'


def test_a_stray_continue_just_completes(client):
    client.emit('continue_execution', {'tabId': 'main'})
    assert outputs(client) == [{'type': 'command_complete'}]


def test_a_paused_program_resumes_after_a_tab_switch(client):
    run(client, '10 PAUSE 1')
    run(client, '20 PRINT "RESUMED"')
    assert 'pause' in types(run(client, 'RUN'))

    client.emit('pause_for_tab_switch', {'tabId': 'main'})
    paused = client.get_received()
    assert paused[0]['name'] == 'tab_switch_paused'
    assert paused[0]['args'][0] == {'success': True, 'wasRunning': True}

    client.emit('resume_from_tab_switch', {'tabId': 'main'})
    items = outputs(client)
    assert 'RESUMED' in texts(items)
    assert types(items)[-1] == 'command_complete'
