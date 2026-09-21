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


@pytest.fixture
def basic_page(chrome, live_server):
    context = chrome.new_context(viewport={'width': 1400, 'height': 900})
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(live_server.url)
    # Connected once the first prompt is shown
    page.wait_for_function(
        "window.dualMonitor && window.dualMonitor.displayManager.textDisplay"
        ".lineBuffer.some(l => l.startsWith('> '))", timeout=COMMAND_TIMEOUT_MS)
    yield BasicPage(page)
    context.close()
    assert errors == [], f'JavaScript errors on the page: {errors}'
