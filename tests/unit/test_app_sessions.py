"""Unit tests for app.py's per-connection interpreter management."""

import app


def test_tab_limit_per_connection():
    manager = app.SessionManager()
    created = [manager.get_session('s', f'tab{i}') for i in range(app.MAX_TABS_PER_CONNECTION + 4)]
    assert sum(t is not None for t in created) == app.MAX_TABS_PER_CONNECTION
    assert created[-1] is None


def test_close_tab_frees_a_slot():
    manager = app.SessionManager()
    for i in range(app.MAX_TABS_PER_CONNECTION):
        manager.get_session('s', f'tab{i}')
    assert manager.get_session('s', 'extra') is None
    manager.close_tab('s', 'tab3')
    assert manager.get_session('s', 'extra') is not None


def test_main_tab_is_never_closed():
    manager = app.SessionManager()
    main = manager.get_session('s', 'main')
    manager.close_tab('s', 'main')
    assert manager.get_session('s', 'main') is main


def test_each_interpreter_has_its_own_lock():
    manager = app.SessionManager()
    a, b = manager.get_session('s', 'a'), manager.get_session('s', 'b')
    assert a.command_lock is not b.command_lock
    assert a.command_lock.acquire(blocking=False)
    assert b.command_lock.acquire(blocking=False)
