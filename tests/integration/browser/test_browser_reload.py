"""Reloading the page picks up where you were (session save/load option 2):
the session id and tab strip live in the browser tab's sessionStorage, so a
reload within the server's grace period reconnects to the same server
session, whose interpreters kept every tab's program."""

import pytest

from conftest import add_tab, listing, switch_to, tab_ids, wait_for

pytestmark = [pytest.mark.browser, pytest.mark.slow]


def reload(basic_page):
    """Reload, then wait until the reconnect has finished: the message is
    shown and the remembered active tab is active again (restoring the tab
    strip switches tabs asynchronously)."""
    basic_page.page.reload()
    wait_for(basic_page.page,
             """() => {
                 const dm = window.dualMonitor;
                 if (!dm || !dm.displayManager.textDisplay.lineBuffer
                         .some(l => l.startsWith('RECONNECTED'))) return false;
                 const saved = JSON.parse(sessionStorage.getItem('basicoco.tabs'));
                 return !saved || dm.tabManager.activeTabId === saved.active;
             }""",
             'the reconnect to finish after reload')


def test_program_survives_a_reload(basic_page):
    basic_page.run('10 PRINT "KEPT"')
    reload(basic_page)
    assert listing(basic_page) == ['10 PRINT "KEPT"']


def test_every_tab_survives_a_reload_and_switching_wipes_nothing(basic_page):
    basic_page.run('10 PRINT "MAIN"')
    second = add_tab(basic_page, 2)
    basic_page.run('20 PRINT "SECOND"')

    reload(basic_page)
    assert tab_ids(basic_page) == ['main', second]
    switch_to(basic_page, second)
    assert listing(basic_page) == ['20 PRINT "SECOND"']
    switch_to(basic_page, 'main')
    assert listing(basic_page) == ['10 PRINT "MAIN"']
    switch_to(basic_page, second)
    assert listing(basic_page) == ['20 PRINT "SECOND"']


def test_new_tab_after_reload_does_not_reuse_an_old_tab(basic_page):
    add_tab(basic_page, 2)
    basic_page.run('10 PRINT "OLD TAB"')
    reload(basic_page)
    add_tab(basic_page, 3)
    assert listing(basic_page) == []


def test_a_closed_tab_stays_closed_after_reload(basic_page):
    second = add_tab(basic_page, 2)
    basic_page.page.click(f'.tab[data-tab-id="{second}"] .tab-close')
    wait_for(basic_page.page, "window.dualMonitor.tabManager.tabs.size === 1",
             'the tab to close')
    reload(basic_page)
    assert tab_ids(basic_page) == ['main']


def test_a_new_browser_session_starts_fresh(chrome, live_server, basic_page):
    basic_page.run('10 PRINT "PRIVATE"')
    other = chrome.new_context().new_page()
    other.goto(live_server.url)
    other.wait_for_function(
        "window.dualMonitor && window.dualMonitor.displayManager.textDisplay"
        ".lineBuffer.some(l => l.startsWith('BASICOCO'))", timeout=15000)
    try:
        # Another browser (its own sessionStorage) must not see our program
        assert listing(basic_page.__class__(other)) == []
    finally:
        other.context.close()


def test_old_save_session_controls_are_gone(basic_page):
    assert basic_page.page.query_selector('#btn-save-session') is None
    assert basic_page.page.query_selector('#pref-auto-save') is None
