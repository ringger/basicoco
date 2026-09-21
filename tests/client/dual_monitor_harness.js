// Node harness for static/dual_monitor.js: runs the real client classes
// against a fake canvas that keeps an RGBA pixel array, so drawing, PAINT,
// PUT and the command line can be checked without a browser.
// Run by tests/unit/test_client_rendering.py:
//   node dual_monitor_harness.js <path/to/dual_monitor.js> <server_circle.json>
'use strict';
const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

function hexToRgb(hex) {
    const m = /^#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(hex);
    return m ? [parseInt(m[1], 16), parseInt(m[2], 16), parseInt(m[3], 16)] : [0, 0, 0];
}

class FakeCtx {
    constructor(canvas) { this.canvas = canvas; this.fillStyle = '#000000'; }
    get data() { return this.canvas.pixels; }
    fillRect(x, y, w, h) {
        const [r, g, b] = hexToRgb(this.fillStyle);
        for (let yy = Math.max(0, y); yy < Math.min(this.canvas.height, y + h); yy++) {
            for (let xx = Math.max(0, x); xx < Math.min(this.canvas.width, x + w); xx++) {
                const i = (yy * this.canvas.width + xx) * 4;
                this.data[i] = r; this.data[i + 1] = g; this.data[i + 2] = b; this.data[i + 3] = 255;
            }
        }
    }
    getImageData(x, y, w, h) {
        const out = new Uint8ClampedArray(w * h * 4);
        for (let yy = 0; yy < h; yy++) for (let xx = 0; xx < w; xx++) {
            const s = ((y + yy) * this.canvas.width + (x + xx)) * 4, d = (yy * w + xx) * 4;
            for (let k = 0; k < 4; k++) out[d + k] = this.data[s + k];
        }
        return { width: w, height: h, data: out };
    }
    putImageData(img, x, y) {
        for (let yy = 0; yy < img.height; yy++) for (let xx = 0; xx < img.width; xx++) {
            const X = x + xx, Y = y + yy;
            if (X < 0 || Y < 0 || X >= this.canvas.width || Y >= this.canvas.height) continue;
            const d = (Y * this.canvas.width + X) * 4, s = (yy * img.width + xx) * 4;
            for (let k = 0; k < 4; k++) this.data[d + k] = img.data[s + k];
        }
    }
    fillText() {}  // text glyphs aren't rasterized; the line buffer is checked instead
    beginPath() {} arc() {} stroke() {}
}

function makeCanvas(width, height) {
    const canvas = { width, height, pixels: new Uint8ClampedArray(width * height * 4) };
    canvas.getContext = () => (canvas.ctx = canvas.ctx || new FakeCtx(canvas));
    return canvas;
}

const canvases = { 'graphics-display': makeCanvas(512, 384), 'text-display': makeCanvas(720, 720) };
const document = {
    getElementById: (id) => canvases[id] || { textContent: '', addEventListener() {}, value: '', checked: false },
    addEventListener() {}, querySelectorAll: () => [],
};
const quietConsole = { log() {}, warn: console.warn, error: console.error };
const ctxGlobals = { document, window: {}, console: quietConsole, setInterval: () => 0, clearInterval() {},
                     setTimeout: () => 0, clearTimeout() {}, localStorage: { getItem: () => null, setItem() {} } };
vm.createContext(ctxGlobals);
const src = fs.readFileSync(process.argv[2], 'utf8') +
    '\n;globalThis.GraphicsDisplay = GraphicsDisplay; globalThis.TextDisplay = TextDisplay;' +
    ' globalThis.GPRINT_FONT = GPRINT_FONT;';
vm.runInContext(src, ctxGlobals);
const { GraphicsDisplay, TextDisplay, GPRINT_FONT } = ctxGlobals;

let passed = 0, failed = 0;
// Report each check and keep going, so a run shows every failure
function check(name, fn) {
    try { fn(); passed++; console.log('ok  ', name); }
    catch (e) { failed++; console.log('FAIL', name, '--', (e.message || String(e)).split('\n')[0]); }
}

const gd = () => {
    canvases['graphics-display'] = makeCanvas(512, 384);
    const g = new GraphicsDisplay('graphics-display');
    g.setPmode(4, 1);
    return g;
};
// Color of BASIC pixel (bx, by) in PMODE 4 (2x2 canvas blocks)
const px = (g, bx, by) => {
    const d = g.canvas.pixels, i = ((by * 2) * 512 + bx * 2) * 4;
    return '#' + [d[i], d[i + 1], d[i + 2]].map(v => v.toString(16).padStart(2, '0')).join('');
};
const lit = (g, color) => {
    const out = new Set();
    for (let y = 0; y < 192; y++) for (let x = 0; x < 256; x++) if (px(g, x, y) === color) out.add(`${x},${y}`);
    return out;
};

// 1. CIRCLE draws the server's pixels exactly, and PAINT stays inside it
const server = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
check('CIRCLE pixels match the server pixel record', () => {
    const g = gd();
    g.drawCircle(server.cx, server.cy, server.r, 1);
    const drawn = lit(g, g.colors[1]);
    const expected = new Set(server.pixels.map(([x, y]) => `${x},${y}`));
    assert.deepStrictEqual([...drawn].sort(), [...expected].sort());
});
check('PAINT inside a CIRCLE does not leak', () => {
    const g = gd();
    g.drawCircle(server.cx, server.cy, server.r, 1);
    g.paint(server.cx, server.cy, 4, 1);
    const painted = lit(g, g.colors[4]);
    assert.ok(painted.size > 0);
    for (const k of painted) {
        const [x, y] = k.split(',').map(Number);
        assert.ok(Math.hypot(x - server.cx, y - server.cy) < server.r, `paint leaked to ${k}`);
    }
    assert.strictEqual(px(g, 0, 0), g.colors[0]);
});

// 2. PUT actions
function putCase(action) {
    const g = gd();
    // stored block: left pixel on (green), right off (2x1 BASIC pixels at 10,10)
    g.pset(10, 10, 1);
    g.getGraphics(10, 10, 11, 10, 'A');
    // screen at 50,50: left off, right on (red)
    g.pset(51, 50, 4);
    g.putGraphics(50, 50, 'A', action);
    return [px(g, 50, 50), px(g, 51, 50), g];
}
check('PUT PSET copies the block', () => {
    const [l, r, g] = putCase('PSET'); assert.deepStrictEqual([l, r], [g.colors[1], g.colors[0]]);
});
check('PUT PRESET puts the inverse', () => {
    const [l, r, g] = putCase('PRESET'); assert.deepStrictEqual([l, r], [g.colors[0], g.currentColor]);
});
check('PUT AND keeps only pixels on in both', () => {
    const [l, r, g] = putCase('AND'); assert.deepStrictEqual([l, r], [g.colors[0], g.colors[0]]);
});
check('PUT OR overlays the block on the screen', () => {
    const [l, r, g] = putCase('OR'); assert.deepStrictEqual([l, r], [g.colors[1], g.colors[4]]);
});
check('PUT NOT inverts the screen area (not a copy of the block)', () => {
    // Screen left pixel on (red), right off; the block is (on, off), so a
    // copy would give (green, black) but inverting the screen gives (black, fg)
    const g = gd();
    g.pset(10, 10, 1);
    g.getGraphics(10, 10, 11, 10, 'A');
    g.pset(50, 50, 4);
    g.putGraphics(50, 50, 'A', 'NOT');
    assert.deepStrictEqual([px(g, 50, 50), px(g, 51, 50)], [g.colors[0], g.currentColor]);
});

// 3. Tab graphics state
check('new-tab graphics state uses palette strings and resets colors', () => {
    const g = gd();
    g.setColor(4, 3);
    g.restoreState(null);
    assert.strictEqual(g.currentColor, g.colors[1]);
    assert.strictEqual(g.backgroundColor, g.colors[0]);
    assert.strictEqual(g.currentDrawColor, 1);
    assert.strictEqual(px(g, 5, 5), g.colors[0]);
});
check('tab graphics state round-trips colors and GET blocks', () => {
    const g = gd();
    g.setColor(4, 3); g.pset(1, 1, 2); g.getGraphics(0, 0, 1, 1, 'B');
    const saved = g.saveState();
    g.setColor(2, 5);            // another tab changes the colors...
    g.spriteStorage = {};
    g.restoreState(saved);       // ...and switching back restores ours
    assert.strictEqual(g.currentDrawColor, 4);
    assert.strictEqual(g.backgroundColor, g.colors[3]);
    assert.ok(g.spriteStorage.B);
});

// 4. Command line: scrollback, wrapping, cursor erase, per-tab text
const td = () => { canvases['text-display'] = makeCanvas(720, 720); return new TextDisplay('text-display'); };
check('typed command is in the line buffer and wraps at 80 columns', () => {
    const t = td();
    t.showPrompt();
    const cmd = 'PRINT "' + 'X'.repeat(90) + '"';
    for (const ch of cmd) t.insertCharacter(ch);
    const start = t.promptBufIdx;
    assert.strictEqual(t.lineBuffer[start], ('> ' + cmd).substring(0, 80));
    assert.strictEqual(t.lineBuffer[start + 1], ('> ' + cmd).substring(80));
    assert.strictEqual(t.currentRow, t.promptRow + 1);
    assert.strictEqual(t.currentCol, (2 + cmd.length) % 80);
    t.moveCursorToStart();
    assert.deepStrictEqual([t.currentRow, t.currentCol], [t.promptRow, 2]);
});
check('Enter keeps the command in scrollback and moves below it', () => {
    const t = td();
    t.showPrompt();
    for (const ch of 'LIST') t.insertCharacter(ch);
    t.moveCursor(-2);
    const sent = [];
    t.handleKeyInput('Enter', (kind, text) => sent.push([kind, text]));
    assert.deepStrictEqual(sent, [['command', 'LIST']]);
    assert.ok(t.lineBuffer.includes('> LIST'), JSON.stringify(t.lineBuffer));
    assert.strictEqual(t.lineBuffer[t.lineBuffer.length - 1], '');
});
check('moving the cursor erases the old cursor block', () => {
    const t = td();
    t.showPrompt();
    for (const ch of 'ABC') t.insertCharacter(ch);
    const oldX = t.currentCol * t.charWidth, oldY = t.currentRow * t.charHeight;
    t.moveCursor(-2);
    const d = t.canvas.pixels, i = ((oldY + 2) * 720 + oldX + 2) * 4;
    assert.deepStrictEqual([d[i], d[i + 1], d[i + 2]], [0, 0, 0], 'old cursor cell still painted');
});
check('clearing a wrapped command removes its extra rows', () => {
    const t = td();
    t.showPrompt();
    for (const ch of 'Y'.repeat(100)) t.insertCharacter(ch);
    t.clearCommand();
    assert.strictEqual(t.lineBuffer.length - 1, t.promptBufIdx);
    assert.strictEqual(t.lineBuffer[t.promptBufIdx], '> ');
});
check('a wrapped command at the bottom scrolls the screen', () => {
    const t = td();
    for (let i = 0; i < 60; i++) t.printText(`LINE ${i}\n`);
    t.showPrompt();
    for (const ch of 'Z'.repeat(170)) t.insertCharacter(ch);
    // '> ' + 170 chars = 3 rows, so the prompt moves up to leave room
    assert.strictEqual(t.currentRow, t.rows - 1);
    assert.strictEqual(t.promptRow, t.rows - 3);
    assert.strictEqual(t.lineBuffer.length - t.promptBufIdx, 3);
});
check('text history and the command in progress survive a tab round trip', () => {
    const t = td();
    t.printText('HELLO\n');
    t.showPrompt();
    for (const ch of 'RUN') t.insertCharacter(ch);
    const saved = t.saveState();
    t.clearScreen();
    t.restoreState(saved);
    assert.ok(t.lineBuffer.includes('HELLO'));
    assert.strictEqual(t.currentCommand, 'RUN');
    t.insertCharacter('!');
    assert.strictEqual(t.lineBuffer[t.promptBufIdx], '> RUN!');
});

// 5. GPRINT glyphs
check('GPRINT font covers the symbols it used to draw as ?', () => {
    for (const ch of '#$%&;<=>@[\\]^_') {
        assert.ok(GPRINT_FONT[ch.charCodeAt(0)], `no glyph for ${ch}`);
        assert.strictEqual(GPRINT_FONT[ch.charCodeAt(0)].length, 6);
        assert.ok(GPRINT_FONT[ch.charCodeAt(0)].every(v => v >= 0 && v <= 15));
    }
});
check('GPRINT draws lowercase with the uppercase glyphs', () => {
    const a = gd(), b = gd();
    a.drawText(10, 10, 'solved', 1);
    b.drawText(10, 10, 'SOLVED', 1);
    assert.deepStrictEqual([...lit(a, a.colors[1])].sort(), [...lit(b, b.colors[1])].sort());
});

console.log(`\n${passed} checks passed, ${failed} failed`);
process.exitCode = failed ? 1 : 0;
