"""Fixtures for in-browser tests: headless Google Chrome (via Playwright)
driving the real web client against the session's live_server.

The installed Chrome is used (channel='chrome'), so no separate browser
download is needed. If Chrome can't be launched the tests are skipped with
the launch error as the reason.
"""

import pytest

playwright_api = pytest.importorskip('playwright.sync_api')

COMMAND_TIMEOUT_MS = 15000


@pytest.fixture(scope='session')
def chrome():
    with playwright_api.sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel='chrome', headless=True)
        except Exception as e:  # Chrome not installed / not launchable
            pytest.skip(f'Google Chrome could not be launched: {e}')
        yield browser
        browser.close()


class BasicPage:
    """The BasiCoCo page in a browser tab, driven through its real REPL."""

    def __init__(self, page):
        self.page = page

    # -- text terminal ---------------------------------------------------
    def lines(self):
        """The terminal's line buffer (everything printed, plus the prompt)."""
        return self.page.evaluate('window.dualMonitor.displayManager.textDisplay.lineBuffer')

    def text(self):
        return '\n'.join(line.rstrip() for line in self.lines())

    def type_command(self, command):
        self.page.click('#repl-container')
        self.page.keyboard.type(command)

    def run(self, command):
        """Type a command, press Enter, and wait until the prompt returns."""
        before = len(self.lines())
        self.type_command(command)
        self.page.keyboard.press('Enter')
        self.page.wait_for_function(
            """(before) => {
                const dm = window.dualMonitor;
                const buf = dm.displayManager.textDisplay.lineBuffer;
                return !dm.programRunning && buf.length > before
                    && buf[buf.length - 1] === '> ';
            }""", arg=before, timeout=COMMAND_TIMEOUT_MS)

    # -- graphics canvas ---------------------------------------------------
    def canvas_pixel(self, cx, cy):
        """RGB of one canvas pixel of the graphics display (512x384)."""
        return tuple(self.page.evaluate(
            """([x, y]) => Array.from(document.getElementById('graphics-display')
                   .getContext('2d').getImageData(x, y, 1, 1).data.slice(0, 3))""",
            [cx, cy]))

    def basic_pixel(self, x, y):
        """RGB at BASIC coordinate (x, y) of the 256x192 screen."""
        return self.canvas_pixel(x * 2, y * 2)

    def canvas_colors(self, x0, y0, x1, y1):
        """Set of distinct RGB colors in a canvas rectangle."""
        return {tuple(c) for c in self.page.evaluate(
            """([x0, y0, x1, y1]) => {
                const d = document.getElementById('graphics-display').getContext('2d')
                    .getImageData(x0, y0, x1 - x0, y1 - y0).data;
                const out = new Set();
                for (let i = 0; i < d.length; i += 4) out.add(d[i] + ',' + d[i+1] + ',' + d[i+2]);
                return Array.from(out).map(s => s.split(',').map(Number));
            }""", [x0, y0, x1, y1])}


def open_basic_page(chrome, url, init_script=None, **context_options):
    """Open the app in a new browser context and wait for its first prompt.
    Returns (BasicPage, context, errors) where errors collects page errors."""
    context = chrome.new_context(viewport={'width': 1400, 'height': 900}, **context_options)
    if init_script:
        context.add_init_script(init_script)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(url)
    # Connected once the first prompt is shown
    page.wait_for_function(
        "window.dualMonitor && window.dualMonitor.displayManager.textDisplay"
        ".lineBuffer.some(l => l.startsWith('> '))", timeout=COMMAND_TIMEOUT_MS)
    return BasicPage(page), context, errors


# -- tab and listing helpers ---------------------------------------------

PAGE_STATE_JS = """() => {
    const dm = window.dualMonitor;
    if (!dm) return 'page not initialized';
    return {
        tabs: Array.from(dm.tabManager.tabs.keys()),
        active: dm.tabManager.activeTabId,
        counter: dm.tabManager.tabCounter,
        session: dm.sessionId,
        remembered: sessionStorage.getItem('basicoco.tabs'),
        lastLines: dm.displayManager.textDisplay.lineBuffer.slice(-6),
    };
}"""


def wait_for(page, expression, what, arg=None, timeout=COMMAND_TIMEOUT_MS):
    """page.wait_for_function, but a timeout says what was awaited and
    what the page looked like."""
    try:
        page.wait_for_function(expression, arg=arg, timeout=timeout)
    except playwright_api.TimeoutError:
        pytest.fail(f'Timed out waiting for {what}; page state: {page.evaluate(PAGE_STATE_JS)}')


def listing(basic_page):
    """The program as LIST prints it."""
    basic_page.run('LIST')
    lines = [l.rstrip() for l in basic_page.lines()]
    start = len(lines) - 1 - lines[::-1].index('> LIST')
    return [l for l in lines[start + 1:] if l and l != '>']


def tab_ids(basic_page):
    return basic_page.page.eval_on_selector_all('.tab', 'els => els.map(e => e.dataset.tabId)')


def switch_to(basic_page, tab_id):
    basic_page.page.click(f'.tab[data-tab-id="{tab_id}"] .tab-title')
    wait_for(basic_page.page, "(id) => window.dualMonitor.tabManager.activeTabId === id",
             f'tab {tab_id} to become active', arg=tab_id)
    basic_page.run('')


def add_tab(basic_page, expected_count):
    """Click + and wait until the switch has finished: the new tab is active
    and its cleared screen shows a prompt."""
    basic_page.page.click('#btn-add-tab')
    wait_for(basic_page.page,
             """(n) => {
                 const dm = window.dualMonitor, tm = dm.tabManager;
                 const buf = dm.displayManager.textDisplay.lineBuffer;
                 return tm.tabs.size === n && tm.activeTabId !== 'main'
                     && tm.tabs.get(tm.activeTabId).hasContent
                     && buf.length === 1 && buf[0] === '> ';
             }""",
             f'the new tab (of {expected_count}) to be active with a prompt', arg=expected_count)
    return basic_page.page.evaluate('window.dualMonitor.tabManager.activeTabId')


@pytest.fixture
def basic_page(chrome, live_server):
    page, context, errors = open_basic_page(chrome, live_server.url)
    yield page
    context.close()
    assert errors == [], f'JavaScript errors on the page: {errors}'
