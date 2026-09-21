"""Tab switching (#83): each tab's program lives in its own interpreter on
the server, so switching tabs must never push a copy of it back."""

import pytest

from conftest import add_tab, listing, switch_to

pytestmark = [pytest.mark.browser, pytest.mark.slow]

# Record every event the page sends, and hold back the answer to any
# request that expects one (as a slow network would)
RECORD_AND_DELAY_REPLIES = """() => {
    const socket = window.dualMonitor.socket;
    const emit = socket.emit.bind(socket);
    window.__sent = [];
    socket.emit = (event, ...args) => {
        window.__sent.push(event);
        const last = args[args.length - 1];
        if (typeof last === 'function') {
            args[args.length - 1] = (...reply) => setTimeout(() => last(...reply), 800);
        }
        return emit(event, ...args);
    };
}"""


def test_quick_switch_back_keeps_lines_typed_before_switching(basic_page):
    basic_page.run('10 PRINT "MAIN"')
    second = add_tab(basic_page, 2)
    switch_to(basic_page, 'main')
    basic_page.page.evaluate(RECORD_AND_DELAY_REPLIES)

    basic_page.run('20 PRINT "TYPED JUST BEFORE SWITCHING"')
    switch_to(basic_page, second)
    switch_to(basic_page, 'main')          # back before any reply could arrive
    basic_page.page.wait_for_timeout(1200)  # let any late reply land

    assert listing(basic_page) == ['10 PRINT "MAIN"', '20 PRINT "TYPED JUST BEFORE SWITCHING"']
    sent = basic_page.page.evaluate('window.__sent')
    assert 'set_state' not in sent and 'get_state' not in sent, sent


def test_switching_keeps_each_tabs_variables(basic_page):
    basic_page.run('DIM A(3): A(2)=7: X$="MAIN"')
    second = add_tab(basic_page, 2)
    basic_page.run('X$="SECOND"')
    switch_to(basic_page, 'main')
    basic_page.run('PRINT X$;A(2)')
    assert basic_page.lines()[-2].rstrip() == 'MAIN 7'
    switch_to(basic_page, second)
    basic_page.run('PRINT X$')
    assert basic_page.lines()[-2].rstrip() == 'SECOND'
