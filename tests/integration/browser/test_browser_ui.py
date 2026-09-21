"""Web-client UI paths that only a real browser exercises (#81 coverage
pass): Ctrl+C, INKEY$ key forwarding, the Copy button, the graphics info
labels, PCLS with a color, and SOUND note queueing."""

import pytest

from conftest import open_basic_page

pytestmark = [pytest.mark.browser, pytest.mark.slow]

BLUE = (0, 0, 255)


def last_lines(basic_page, n=4):
    return [l.rstrip() for l in basic_page.lines()[-n:]]


def start_program(basic_page, command='RUN'):
    """Type a command that keeps running (no prompt comes back yet)."""
    basic_page.type_command(command)
    basic_page.page.keyboard.press('Enter')
    basic_page.page.wait_for_function('window.dualMonitor.programRunning === true')


def wait_for_prompt(basic_page):
    basic_page.page.wait_for_function(
        """() => { const dm = window.dualMonitor;
                   const buf = dm.displayManager.textDisplay.lineBuffer;
                   return !dm.programRunning && buf[buf.length - 1] === '> '; }""",
        timeout=15000)


def test_ctrl_c_stops_a_running_program(basic_page):
    basic_page.run('SAFETY OFF')
    basic_page.run('10 GOTO 10')
    start_program(basic_page)
    basic_page.page.wait_for_timeout(500)
    basic_page.page.keyboard.press('Control+c')
    wait_for_prompt(basic_page)
    assert any('BREAK' in l for l in last_lines(basic_page, 6)), last_lines(basic_page, 6)
    basic_page.run('PRINT "AFTER"')
    assert 'AFTER' in basic_page.text()


def test_keys_go_to_inkey_while_a_program_runs(basic_page):
    basic_page.run('SAFETY OFF')
    basic_page.run('10 A$=INKEY$: IF A$="" THEN 10')
    basic_page.run('20 PRINT "GOT ";A$')
    start_program(basic_page)
    basic_page.page.keyboard.press('q')
    wait_for_prompt(basic_page)
    lines = last_lines(basic_page, 4)
    assert 'GOT q' in lines, lines
    # The key went to the program, not into the command line
    assert basic_page.page.evaluate(
        'window.dualMonitor.displayManager.textDisplay.currentCommand') == ''


# Record what the page hands to the clipboard (headless Chrome's clipboard
# itself isn't reliable to read back)
RECORD_CLIPBOARD = """
window.__copied = [];
Object.defineProperty(navigator, 'clipboard', {
    value: { writeText: async (text) => { window.__copied.push(text); } },
});
"""


def test_copy_button_copies_the_terminal_text(chrome, live_server):
    page, context, errors = open_basic_page(chrome, live_server.url, init_script=RECORD_CLIPBOARD)
    try:
        page.run('PRINT "COPY ME"')
        page.page.click('#btn-copy-text')
        page.page.wait_for_function('window.__copied.length === 1', timeout=5000)
        copied = page.page.evaluate('window.__copied[0]')
        assert '> PRINT "COPY ME"' in copied
        assert 'COPY ME' in copied.splitlines()
        page.page.wait_for_function(
            "document.getElementById('btn-copy-text').textContent === 'Copied!'", timeout=5000)
        assert errors == []
    finally:
        context.close()


def test_color_label_names_both_colors(basic_page):
    basic_page.run('PMODE 4,1: SCREEN 1,1')
    basic_page.run('COLOR 4,3')
    label = basic_page.page.text_content('#graphics-color')
    assert label == 'Color: Red on Blue'


def test_pcls_with_a_color_clears_to_it(basic_page):
    basic_page.run('PMODE 4,1: SCREEN 1,1: PCLS 3')
    assert basic_page.canvas_pixel(10, 10) == BLUE
    assert basic_page.canvas_pixel(500, 380) == BLUE


@pytest.mark.parametrize('mode', [1, 4])
def test_mouse_readout_uses_coco_coordinates(basic_page, mode):
    basic_page.run(f'PMODE {mode},1: SCREEN 1,1')
    box = basic_page.page.locator('#graphics-display').bounding_box()
    # Point at the middle of the cell for coordinate (200, 150)
    x = box['x'] + (200.5 / 256) * box['width']
    y = box['y'] + (150.5 / 192) * box['height']
    basic_page.page.mouse.move(x, y)
    assert basic_page.page.text_content('#graphics-coords') == 'X: 200, Y: 150'


# Record when each oscillator is scheduled to start and stop
RECORD_OSCILLATORS = """
window.__notes = [];
const origStart = OscillatorNode.prototype.start;
OscillatorNode.prototype.start = function (when) {
    this.__note = { start: when };
    window.__notes.push(this.__note);
    return origStart.call(this, when);
};
const origStop = OscillatorNode.prototype.stop;
OscillatorNode.prototype.stop = function (when) {
    if (this.__note && when !== undefined && this.__note.stop === undefined) this.__note.stop = when;
    return origStop.call(this, when);
};
"""


def test_sound_notes_play_one_after_another(chrome, live_server):
    page, context, errors = open_basic_page(chrome, live_server.url, init_script=RECORD_OSCILLATORS)
    try:
        page.run('SOUND 100,6: SOUND 200,6: SOUND 300,6')
        page.page.wait_for_function('window.__notes.length === 3', timeout=5000)
        notes = page.page.evaluate('window.__notes')
        for earlier, later in zip(notes, notes[1:]):
            assert later['start'] >= earlier['stop'] - 1e-6, notes   # queued, not overlapping
        assert errors == []
    finally:
        context.close()
