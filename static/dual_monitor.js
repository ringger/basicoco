/**
 * BasiCoCo - Dual Monitor Interface
 * Revolutionary split-screen interface with persistent REPL and dedicated graphics display
 */

// 4x6 pixel font for GPRINT (4 wide, 6 rows per glyph, MSB-first)
const GPRINT_FONT = {
    32: [0,0,0,0,0,0],             // space
    33: [4,4,4,0,4,0],             // !
    34: [10,10,0,0,0,0],           // "
    39: [4,4,0,0,0,0],             // '
    40: [2,4,4,4,2,0],             // (
    41: [8,4,4,4,8,0],             // )
    42: [0,10,4,10,0,0],           // *
    43: [0,4,14,4,0,0],            // +
    44: [0,0,0,4,4,8],             // ,
    45: [0,0,14,0,0,0],            // -
    46: [0,0,0,0,4,0],             // .
    47: [1,2,4,8,0,0],             // /
    48: [6,9,9,9,6,0],             // 0
    49: [4,12,4,4,14,0],           // 1
    50: [6,9,2,4,15,0],            // 2
    51: [6,9,2,9,6,0],             // 3
    52: [2,6,10,15,2,0],           // 4
    53: [15,8,14,1,14,0],          // 5
    54: [6,8,14,9,6,0],            // 6
    55: [15,1,2,4,4,0],            // 7
    56: [6,9,6,9,6,0],             // 8
    57: [6,9,7,1,6,0],             // 9
    58: [0,4,0,4,0,0],             // :
    63: [6,9,2,0,2,0],             // ?
    65: [6,9,15,9,9,0],            // A
    66: [14,9,14,9,14,0],          // B
    67: [6,9,8,9,6,0],             // C
    68: [14,9,9,9,14,0],           // D
    69: [15,8,14,8,15,0],          // E
    70: [15,8,14,8,8,0],           // F
    71: [6,8,11,9,6,0],            // G
    72: [9,9,15,9,9,0],            // H
    73: [14,4,4,4,14,0],           // I
    74: [1,1,1,9,6,0],             // J
    75: [9,10,12,10,9,0],          // K
    76: [8,8,8,8,15,0],            // L
    77: [9,15,15,9,9,0],           // M
    78: [9,13,11,9,9,0],           // N
    79: [6,9,9,9,6,0],             // O
    80: [14,9,14,8,8,0],           // P
    81: [6,9,9,10,5,0],            // Q
    82: [14,9,14,10,9,0],          // R
    83: [7,8,6,1,14,0],            // S
    84: [14,4,4,4,4,0],            // T
    85: [9,9,9,9,6,0],             // U
    86: [9,9,9,6,6,0],             // V
    87: [9,9,15,15,9,0],           // W
    88: [9,9,6,9,9,0],             // X
    89: [9,9,6,4,4,0],             // Y
    90: [15,1,6,8,15,0],           // Z
};

// Display Manager - Coordinates both text and graphics displays
class DisplayManager {
    constructor() {
        this.textDisplay = null;
        this.graphicsDisplay = null;
        this.activeDisplay = 'text';
    }
    
    initialize() {
        this.textDisplay = new TextDisplay('text-display');
        this.graphicsDisplay = new GraphicsDisplay('graphics-display');
    }
    
    routeOutput(output) {
        // Route output to appropriate display based on type
        switch (output.type) {
            case 'text':
                this.textDisplay.printText(output.text + (output.inline ? '' : '\n'));
                break;
            case 'clear_screen':
                this.textDisplay.clearScreen();
                break;
            case 'clear_graphics':
            case 'pcls':
                this.graphicsDisplay.clearGraphics();
                break;
            case 'pmode':
            case 'set_pmode':
                this.graphicsDisplay.setPmode(output.mode, output.page);
                this.updateGraphicsInfo();
                break;
            case 'set_screen':
                this.graphicsDisplay.setScreen(output.mode);
                break;
            case 'set_color':
                this.graphicsDisplay.setColor(output.fg, output.bg);
                this.updateGraphicsInfo();
                break;
            case 'pset':
                this.graphicsDisplay.pset(output.x, output.y, output.color);
                break;
            case 'preset':
                this.graphicsDisplay.preset(output.x, output.y);
                break;
            case 'line':
                if (output.box_type === 'BF') {
                    this.graphicsDisplay.drawFilledBox(output.x1, output.y1, output.x2, output.y2, output.color);
                } else if (output.box_type === 'B') {
                    this.graphicsDisplay.drawBox(output.x1, output.y1, output.x2, output.y2, output.color);
                } else {
                    this.graphicsDisplay.drawLine(output.x1, output.y1, output.x2, output.y2, output.color);
                }
                break;
            case 'circle':
                this.graphicsDisplay.drawCircle(output.x, output.y, output.radius, output.color);
                break;
            case 'paint':
                this.graphicsDisplay.paint(output.x, output.y, output.fill_color, output.boundary_color);
                break;
            case 'get':
                this.graphicsDisplay.getGraphics(output.x1, output.y1, output.x2, output.y2, output.array);
                break;
            case 'put':
                this.graphicsDisplay.putGraphics(output.x, output.y, output.array, output.action, output.data);
                break;
            case 'draw':
                this.graphicsDisplay.executeDraw(output.commands);
                break;
            case 'gtext':
                this.graphicsDisplay.drawText(output.x, output.y, output.text, output.color);
                break;
            case 'error':
                this.textDisplay.printText(`ERROR: ${output.message}\n`);
                break;
        }
    }
    
    updateGraphicsInfo() {
        const mode = this.graphicsDisplay.graphicsMode;
        const modeText = mode === 0 ? 'Text' : `PMODE ${mode}`;
        document.getElementById('graphics-mode').textContent = `Mode: ${modeText}`;
        
        const fg = this.graphicsDisplay.currentDrawColor;
        const bg = this.graphicsDisplay.backgroundColor;
        const colorNames = ['Black', 'Green', 'Yellow', 'Blue', 'Red', 'Buff', 'Cyan', 'Magenta', 'Orange'];
        document.getElementById('graphics-color').textContent = 
            `Color: ${colorNames[fg]} on ${colorNames[bg === '#000000' ? 0 : 1]}`;
    }
}

// Text Display - Handles unified REPL and text output
class TextDisplay {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        
        // Cursor rendering state
        this.cursorVisible = true;
        this.cursorBlinkTime = 0;
        
        // Text properties - optimized for 80-column terminal
        this.charWidth = 9;
        this.charHeight = 15;
        this.cols = 80;  // Standard terminal width
        this.rows = 48;  // Double height terminal
        this.currentRow = 0;
        this.currentCol = 0;
        
        // Colors
        this.textColor = '#e0e0e0';  // Softer white text, less bright
        this.backgroundColor = '#000000';
        
        // Rainbow cursor colors (authentic TRS-80 CoCo palette)
        this.rainbowColors = [
            '#00FF00',  // Green
            '#FFFF00',  // Yellow  
            '#FF8000',  // Orange
            '#FF0000',  // Red
            '#FF00FF',  // Magenta
            '#8000FF',  // Purple
            '#0080FF',  // Blue
            '#00FFFF'   // Cyan
        ];
        this.currentColorIndex = 0;
        
        // Scroll-back buffer
        this.lineBuffer = ['']; // Array of line strings (full history)
        this.scrollOffset = 0;  // 0 = viewing bottom (live), >0 = scrolled back
        this.maxBufferLines = 5000;

        // REPL state
        this.currentCommand = '';
        this.commandCursorPos = 0; // Position within current command for editing
        this.promptRow = 0;
        this.promptCol = 0;
        this.waitingForInput = false;
        this.inputPrompt = '';

        // Command history and completion
        this.commandHistory = [];
        this.historyIndex = -1;
        this.killRing = ''; // For Ctrl+K, Ctrl+U, Ctrl+Y (yank/kill)
        this.basicKeywords = [
            'PRINT', 'LET', 'IF', 'THEN', 'ELSE', 'FOR', 'TO', 'NEXT', 'STEP',
            'GOTO', 'GOSUB', 'RETURN', 'END', 'STOP', 'RUN', 'LIST', 'NEW',
            'SAVE', 'LOAD', 'FILES', 'KILL', 'DELETE', 'CD', 'INPUT', 'DATA', 'READ', 'RESTORE', 'DIM',
            'PSET', 'PRESET', 'PMODE', 'PCLS', 'SCREEN', 'COLOR', 'PAINT',
            'LINE', 'CIRCLE', 'DRAW', 'GET', 'PUT', 'GPRINT', 'CLS', 'SOUND',
            'RND', 'INT', 'ABS', 'SGN', 'SQR', 'SIN', 'COS', 'TAN', 'ATN',
            'LOG', 'EXP', 'LEN', 'MID$', 'LEFT$', 'RIGHT$', 'STR$', 'VAL',
            'CHR$', 'ASC', 'INKEY$', 'POS', 'PEEK', 'POKE'
        ];
        
        this.initDisplay();
        this.printText('Connecting...\n');
    }
    
    initDisplay() {
        // Enable crisp text rendering
        this.ctx.imageSmoothingEnabled = false;
        this.ctx.textRenderingOptimization = 'optimizeSpeed';
        
        this.ctx.fillStyle = this.backgroundColor;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.font = '400 14px "Monaco", "Menlo", "Ubuntu Mono", "Consolas", "source-code-pro", monospace';
        this.ctx.textBaseline = 'top';
        
        // Start cursor color cycling
        this.startCursorBlinking();
        this.drawCursor();
    }
    
    clearScreen() {
        this.ctx.fillStyle = this.backgroundColor;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        this.currentRow = 0;
        this.currentCol = 0;
        this.scrollOffset = 0;
        this.lineBuffer = [''];
        this.drawCursor();
    }
    
    printText(text) {
        // If scrolled back, snap to bottom for new output
        if (this.scrollOffset > 0) {
            this.scrollOffset = 0;
            this.renderFromBuffer();
        }

        this.ctx.fillStyle = this.textColor;

        for (let char of text) {
            if (char === '\r') {
                // Carriage return - move to beginning of line
                this.clearCurrentCursor();
                this.currentCol = 0;
                this.drawCursor();
                continue;
            }

            if (char === '\n' || this.currentCol >= this.cols) {
                this.newLine();
                if (char === '\n') continue;
            }

            // Write to line buffer
            this.bufferWriteChar(char, this.currentCol);

            // Clear cursor at current position before writing character
            this.clearCurrentCursor();

            // Calculate pixel-aligned positions
            const x = Math.round(this.currentCol * this.charWidth);
            const y = Math.round(this.currentRow * this.charHeight);

            // Clear character position before writing
            this.ctx.fillStyle = this.backgroundColor;
            this.ctx.fillRect(x, y, this.charWidth, this.charHeight);

            // Write character with pixel alignment
            this.ctx.fillStyle = this.textColor;
            this.ctx.fillText(char, x, y + 1);  // Add 1px offset for better alignment

            this.currentCol++;
        }

        this.drawCursor(); // Draw at new position
    }

    // Write a character to the current line in the buffer
    bufferWriteChar(char, col) {
        const bufIdx = this.lineBuffer.length - 1;
        const line = this.lineBuffer[bufIdx];
        const padded = line.padEnd(col, ' ');
        this.lineBuffer[bufIdx] = padded.substring(0, col) + char + padded.substring(col + 1);
    }
    
    newLine() {
        this.clearCurrentCursor();
        this.currentCol = 0;
        this.currentRow++;

        // Add new line to buffer
        this.lineBuffer.push('');

        // Trim buffer if too large
        if (this.lineBuffer.length > this.maxBufferLines) {
            this.lineBuffer.splice(0, this.lineBuffer.length - this.maxBufferLines);
        }

        if (this.currentRow >= this.rows) {
            this.scrollUp();
            this.currentRow = this.rows - 1;
        }

        // Redraw cursor at new position
        this.drawCursor();
    }

    scrollUp() {
        const imageData = this.ctx.getImageData(
            0, this.charHeight,
            this.canvas.width, this.canvas.height - this.charHeight
        );
        this.ctx.fillStyle = this.backgroundColor;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.putImageData(imageData, 0, 0);
    }

    scrollBack(lines) {
        const maxOffset = Math.max(0, this.lineBuffer.length - this.rows);
        this.scrollOffset = Math.min(this.scrollOffset + lines, maxOffset);
        this.renderFromBuffer();
    }

    scrollForward(lines) {
        this.scrollOffset = Math.max(0, this.scrollOffset - lines);
        if (this.scrollOffset === 0) {
            // Back at live view — re-render current screen
            this.renderFromBuffer();
            this.drawCursor();
        } else {
            this.renderFromBuffer();
        }
    }

    renderFromBuffer() {
        // Clear canvas
        this.ctx.fillStyle = this.backgroundColor;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Calculate which buffer lines to show
        const totalLines = this.lineBuffer.length;
        const endIdx = totalLines - this.scrollOffset;
        const startIdx = Math.max(0, endIdx - this.rows);

        this.ctx.fillStyle = this.textColor;
        for (let i = startIdx; i < endIdx; i++) {
            const screenRow = i - startIdx;
            const line = this.lineBuffer[i] || '';
            const y = Math.round(screenRow * this.charHeight);
            for (let col = 0; col < line.length && col < this.cols; col++) {
                const x = Math.round(col * this.charWidth);
                this.ctx.fillText(line[col], x, y + 1);
            }
        }

        // Draw cursor only if at live view
        if (this.scrollOffset === 0) {
            this.drawCursor();
        }
    }
    
    drawCursor() {
        // Don't draw cursor when scrolled back from live view
        if (this.scrollOffset > 0) return;

        const x = this.currentCol * this.charWidth;
        const y = this.currentRow * this.charHeight;  // Align exactly with text baseline

        if (this.cursorVisible) {
            // Use current rainbow color
            this.ctx.fillStyle = this.rainbowColors[this.currentColorIndex];
            this.ctx.fillRect(x, y, this.charWidth, this.charHeight);
        } else {
            // Clear cursor by drawing background color
            this.ctx.fillStyle = this.backgroundColor;
            this.ctx.fillRect(x, y, this.charWidth, this.charHeight);
        }
    }
    
    clearCurrentCursor() {
        // Clear the current cursor position
        const x = this.currentCol * this.charWidth;
        const y = this.currentRow * this.charHeight;  // Match drawCursor positioning
        
        this.ctx.fillStyle = this.backgroundColor;
        this.ctx.fillRect(x, y, this.charWidth, this.charHeight);
    }
    
    clearCursor() {
        // Don't clear if there might be text there - let the blink cycle handle it
        return;
    }
    
    startCursorBlinking() {
        // Store the interval ID so we can clear it if needed  
        this.cursorInterval = setInterval(() => {
            // Cycle to next rainbow color (always visible, just changing colors)
            this.currentColorIndex = (this.currentColorIndex + 1) % this.rainbowColors.length;
            this.cursorVisible = true; // Always visible
            
            this.drawCursor();
        }, 75);   // Perfect rainbow speed - fast but not overwhelming!
    }
    
    showPrompt() {
        // Show command prompt
        if (!this.waitingForInput) {
            this.printText('> ');
            this.promptRow = this.currentRow;
            this.promptCol = this.currentCol;
        }
    }
    
    showInputPrompt(prompt) {
        // Show input prompt (for INPUT statements)
        this.waitingForInput = true;
        this.inputPrompt = prompt;
        this.printText(prompt);
        this.promptRow = this.currentRow;
        this.promptCol = this.currentCol;
    }
    
    handleKeyInput(key, callback) {
        if (key === 'Enter') {
            if (this.waitingForInput) {
                // Submit input response
                callback('input', this.currentCommand);
                this.waitingForInput = false;
                this.inputPrompt = '';
            } else {
                // Add to history if not empty
                if (this.currentCommand.trim()) {
                    this.addToHistory(this.currentCommand);
                }
                // Execute BASIC command
                callback('command', this.currentCommand);
            }
            this.printText('\n');
            this.currentCommand = '';
            this.commandCursorPos = 0;
            this.historyIndex = -1;
        } else if (key === 'Tab' && !this.waitingForInput) {
            this.handleTabCompletion();
        } else if (key === 'ArrowUp' && !this.waitingForInput) {
            this.navigateHistory(-1);
        } else if (key === 'ArrowDown' && !this.waitingForInput) {
            this.navigateHistory(1);
        } else if (key === 'ArrowLeft') {
            this.moveCursor(-1);
        } else if (key === 'ArrowRight') {
            this.moveCursor(1);
        } else if (key === 'Home') {
            this.moveCursorToStart();
        } else if (key === 'End') {
            this.moveCursorToEnd();
        } else if (key === 'Backspace') {
            this.handleBackspace();
        } else if (key === 'Delete') {
            this.handleDelete();
        } else if (key.length === 1 && key.match(/[a-zA-Z0-9 !"#$%&'()*+,\-./:;<=>?@[\\\]^_`{|}~]/)) {
            this.insertCharacter(key);
        }
    }
    
    // Command history management
    addToHistory(command) {
        // Avoid duplicate consecutive entries
        if (this.commandHistory.length === 0 || this.commandHistory[this.commandHistory.length - 1] !== command) {
            this.commandHistory.push(command);
            // Limit history size
            if (this.commandHistory.length > 100) {
                this.commandHistory.shift();
            }
        }
    }
    
    navigateHistory(direction) {
        if (this.commandHistory.length === 0) return;
        
        // Save current command if we're starting to navigate
        if (this.historyIndex === -1) {
            this.tempCommand = this.currentCommand;
        }
        
        this.historyIndex += direction;
        
        // Circular bounds checking
        if (this.historyIndex < -1) {
            // Wrap to newest command when going past current command
            this.historyIndex = this.commandHistory.length - 1;
        } else if (this.historyIndex >= this.commandHistory.length) {
            // Wrap to current command when going past oldest command  
            this.historyIndex = -1;
        }
        
        // Update command line
        let newCommand;
        if (this.historyIndex === -1) {
            newCommand = this.tempCommand || '';
        } else {
            newCommand = this.commandHistory[this.commandHistory.length - 1 - this.historyIndex];
        }
        
        this.replaceCurrentCommand(newCommand);
    }
    
    // Tab completion
    handleTabCompletion() {
        const beforeCursor = this.currentCommand.substring(0, this.commandCursorPos);

        // Check for filename context: LOAD "partial or LOAD partial (quote optional)
        const fileMatch = beforeCursor.match(/^(?:\d+\s+)?(LOAD|SAVE|KILL)\s+"?([^"]*)$/i);
        if (fileMatch) {
            const hasQuote = beforeCursor.includes('"');
            const partial = fileMatch[2].toUpperCase();
            this.requestFileCompletion(partial, hasQuote);
            return;
        }

        const currentWord = this.getCurrentWord();
        if (!currentWord) return;

        const matches = this.basicKeywords.filter(keyword =>
            keyword.startsWith(currentWord.toUpperCase())
        );

        if (matches.length === 1) {
            // Single match - complete it
            this.replaceCurrentWord(matches[0]);
        } else if (matches.length > 1) {
            // Multiple matches - show them
            this.printText('\n');
            const matchesStr = matches.join('  ');
            this.printText(matchesStr + '\n');
            this.showPrompt();
            this.redrawCurrentCommand();
        }
    }

    requestFileCompletion(partial, hasQuote) {
        if (!this.onRequestFiles) return;
        this.onRequestFiles((files) => {
            const matches = files.filter(f => f.toUpperCase().startsWith(partial));
            if (matches.length === 1) {
                // Single match — complete with quotes
                const prefix = hasQuote ? '' : '"';
                this.replaceFilePartial(partial, prefix + matches[0] + '"', hasQuote);
            } else if (matches.length > 1) {
                // Complete common prefix
                const common = this.commonPrefix(matches);
                if (common.length > partial.length) {
                    const prefix = hasQuote ? '' : '"';
                    this.replaceFilePartial(partial, prefix + common, hasQuote);
                } else if (!hasQuote) {
                    // Insert opening quote even if no further completion
                    this.replaceFilePartial(partial, '"' + partial, hasQuote);
                }
                this.printText('\n');
                this.printText(matches.join('  ') + '\n');
                this.showPrompt();
                this.redrawCurrentCommand();
            }
        });
    }

    replaceFilePartial(oldPartial, newPartial) {
        const beforeCursor = this.currentCommand.substring(0, this.commandCursorPos);
        const afterCursor = this.currentCommand.substring(this.commandCursorPos);
        const newBefore = beforeCursor.substring(0, beforeCursor.length - oldPartial.length) + newPartial;
        this.currentCommand = newBefore + afterCursor;
        this.commandCursorPos = newBefore.length;
        this.redrawCurrentCommand();
    }

    commonPrefix(strings) {
        if (strings.length === 0) return '';
        let prefix = strings[0];
        for (let i = 1; i < strings.length; i++) {
            while (!strings[i].startsWith(prefix)) {
                prefix = prefix.substring(0, prefix.length - 1);
            }
        }
        return prefix;
    }

    getCurrentWord() {
        const beforeCursor = this.currentCommand.substring(0, this.commandCursorPos);
        const match = beforeCursor.match(/[A-Z$]*$/i);
        return match ? match[0] : '';
    }

    replaceCurrentWord(replacement) {
        const beforeCursor = this.currentCommand.substring(0, this.commandCursorPos);
        const afterCursor = this.currentCommand.substring(this.commandCursorPos);
        const wordStart = beforeCursor.match(/[A-Z$]*$/i);

        if (wordStart) {
            const newBeforeCursor = beforeCursor.substring(0, beforeCursor.length - wordStart[0].length) + replacement;
            this.currentCommand = newBeforeCursor + afterCursor;
            this.commandCursorPos = newBeforeCursor.length;
            this.redrawCurrentCommand();
        }
    }
    
    // Cursor movement
    moveCursor(delta) {
        const newPos = this.commandCursorPos + delta;
        if (newPos >= 0 && newPos <= this.currentCommand.length) {
            this.commandCursorPos = newPos;
            this.updateCursorPosition();
        }
    }
    
    moveCursorToStart() {
        this.commandCursorPos = 0;
        this.updateCursorPosition();
    }
    
    moveCursorToEnd() {
        this.commandCursorPos = this.currentCommand.length;
        this.updateCursorPosition();
    }
    
    updateCursorPosition() {
        this.currentCol = this.promptCol + this.commandCursorPos;
        this.drawCursor();
    }
    
    // Text editing
    insertCharacter(char) {
        const before = this.currentCommand.substring(0, this.commandCursorPos);
        const after = this.currentCommand.substring(this.commandCursorPos);
        this.currentCommand = before + char + after;
        this.commandCursorPos++;
        this.redrawCurrentCommand();
    }
    
    handleBackspace() {
        if (this.commandCursorPos > 0) {
            const before = this.currentCommand.substring(0, this.commandCursorPos - 1);
            const after = this.currentCommand.substring(this.commandCursorPos);
            this.currentCommand = before + after;
            this.commandCursorPos--;
            this.redrawCurrentCommand();
        }
    }
    
    handleDelete() {
        if (this.commandCursorPos < this.currentCommand.length) {
            const before = this.currentCommand.substring(0, this.commandCursorPos);
            const after = this.currentCommand.substring(this.commandCursorPos + 1);
            this.currentCommand = before + after;
            this.redrawCurrentCommand();
        }
    }
    
    replaceCurrentCommand(newCommand) {
        this.currentCommand = newCommand;
        this.commandCursorPos = newCommand.length;
        this.redrawCurrentCommand();
    }
    
    redrawCurrentCommand() {
        // Clear the current command line
        const lineY = this.currentRow * this.charHeight;
        const clearWidth = this.canvas.width - (this.promptCol * this.charWidth);
        this.ctx.fillStyle = this.backgroundColor;
        this.ctx.fillRect(this.promptCol * this.charWidth, lineY, clearWidth, this.charHeight);
        
        // Redraw the command character by character for precise positioning
        if (this.currentCommand) {
            this.ctx.fillStyle = this.textColor;
            for (let i = 0; i < this.currentCommand.length; i++) {
                const x = (this.promptCol + i) * this.charWidth;
                this.ctx.fillText(this.currentCommand[i], x, lineY);
            }
        }
        
        // Update cursor position to be after the text
        this.currentCol = this.promptCol + this.commandCursorPos;
        this.drawCursor();
    }
    
    // Emacs/readline key bindings
    handleEmacsKeybinding(key) {
        switch (key.toLowerCase()) {
            case 'a':  // Ctrl+A - Beginning of line
                this.moveCursorToStart();
                return true;
            case 'e':  // Ctrl+E - End of line
                this.moveCursorToEnd();
                return true;
            case 'f':  // Ctrl+F - Forward one character
                this.moveCursor(1);
                return true;
            case 'b':  // Ctrl+B - Backward one character
                this.moveCursor(-1);
                return true;
            case 'd':  // Ctrl+D - Delete character at cursor
                this.handleDelete();
                return true;
            case 'h':  // Ctrl+H - Delete character before cursor (same as Backspace)
                this.handleBackspace();
                return true;
            case 'k':  // Ctrl+K - Kill from cursor to end of line
                this.killToEndOfLine();
                return true;
            case 'u':  // Ctrl+U - Kill entire line
                this.killEntireLine();
                return true;
            case 'w':  // Ctrl+W - Kill word backwards
                this.killWordBackward();
                return true;
            case 'y':  // Ctrl+Y - Yank (paste) killed text
                this.yankText();
                return true;
            case 'l':  // Ctrl+L - Clear screen
                this.clearScreen();
                this.showPrompt();
                return true;
            case 'n':  // Ctrl+N - Next history (same as Down arrow)
                if (!this.waitingForInput) {
                    this.navigateHistory(1);
                    return true;
                }
                break;
            case 'p':  // Ctrl+P - Previous history (same as Up arrow)
                if (!this.waitingForInput) {
                    this.navigateHistory(-1);
                    return true;
                }
                break;
            default:
                return false; // Not handled
        }
        return false;
    }
    
    // Kill/Yank operations for Emacs bindings
    killToEndOfLine() {
        if (this.commandCursorPos < this.currentCommand.length) {
            this.killRing = this.currentCommand.substring(this.commandCursorPos);
            this.currentCommand = this.currentCommand.substring(0, this.commandCursorPos);
            this.redrawCurrentCommand();
        }
    }
    
    killEntireLine() {
        if (this.currentCommand.length > 0) {
            this.killRing = this.currentCommand;
            this.currentCommand = '';
            this.commandCursorPos = 0;
            this.redrawCurrentCommand();
        }
    }
    
    killWordBackward() {
        if (this.commandCursorPos > 0) {
            const beforeCursor = this.currentCommand.substring(0, this.commandCursorPos);
            const match = beforeCursor.match(/\S*\s*$/); // Find word and trailing whitespace
            
            if (match && match[0].length > 0) {
                const killStart = this.commandCursorPos - match[0].length;
                this.killRing = this.currentCommand.substring(killStart, this.commandCursorPos);
                
                const before = this.currentCommand.substring(0, killStart);
                const after = this.currentCommand.substring(this.commandCursorPos);
                this.currentCommand = before + after;
                this.commandCursorPos = killStart;
                this.redrawCurrentCommand();
            }
        }
    }
    
    yankText() {
        if (this.killRing) {
            const before = this.currentCommand.substring(0, this.commandCursorPos);
            const after = this.currentCommand.substring(this.commandCursorPos);
            this.currentCommand = before + this.killRing + after;
            this.commandCursorPos += this.killRing.length;
            this.redrawCurrentCommand();
        }
    }
    
    clearCommand() {
        // Clear current command and reset to prompt
        this.currentCommand = '';
        this.currentRow = this.promptRow;
        this.currentCol = this.promptCol;
        this.drawCursor();
        
        // Clear line after prompt
        this.ctx.fillStyle = this.backgroundColor;
        this.ctx.fillRect(
            this.promptCol * this.charWidth,
            this.promptRow * this.charHeight,
            (this.cols - this.promptCol) * this.charWidth,
            this.charHeight
        );
    }
    
    saveState() {
        // Save the current canvas content and cursor position
        return {
            imageData: this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height),
            currentRow: this.currentRow,
            currentCol: this.currentCol
        };
    }
    
    restoreState(state) {
        // Restore the canvas content and cursor position
        if (state.imageData) {
            this.ctx.putImageData(state.imageData, 0, 0);
        }
        this.currentRow = state.currentRow || 0;
        this.currentCol = state.currentCol || 0;
        this.drawCursor();
    }
}

// Graphics Display - Handles all graphics operations
class GraphicsDisplay {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        
        // Graphics mode properties
        this.graphicsMode = 0;
        this.screenMode = 1;
        this.currentDrawColor = 1;
        
        // TRS-80 Color Computer palette
        this.colors = [
            '#000000', '#00ff00', '#ffff00', '#0000ff',
            '#ff0000', '#ffaa88', '#00ffff', '#ff00ff', '#ff8800'
        ];
        
        this.currentColor = this.colors[1];
        this.backgroundColor = this.colors[0];
        
        // PMODE resolutions
        this.pmodeResolutions = {
            0: { width: 32, height: 16, pixelWidth: 16, pixelHeight: 24 },
            1: { width: 128, height: 96, pixelWidth: 4, pixelHeight: 4 },
            2: { width: 128, height: 96, pixelWidth: 4, pixelHeight: 4 },
            3: { width: 128, height: 192, pixelWidth: 4, pixelHeight: 2 },
            4: { width: 256, height: 192, pixelWidth: 2, pixelHeight: 2 }
        };
        
        // Sprite storage for GET/PUT
        this.spriteStorage = {};
        
        // DRAW command state
        this.drawX = 128;
        this.drawY = 96;
        this.drawAngle = 0;
        this.drawScale = 1;
        
        this.initDisplay();
    }
    
    initDisplay() {
        this.clearGraphics();
    }
    
    clearGraphics() {
        this.ctx.fillStyle = this.backgroundColor;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }
    
    setPmode(mode, page = 1) {
        this.graphicsMode = mode;
        this.clearGraphics();
    }

    setScreen(mode) {
        this.screenMode = mode;
    }
    
    setColor(fg, bg) {
        if (fg !== null && fg >= 0 && fg < this.colors.length) {
            this.currentColor = this.colors[fg];
            this.currentDrawColor = fg;
        }
        if (bg !== null && bg >= 0 && bg < this.colors.length) {
            this.backgroundColor = this.colors[bg];
            this.clearGraphics();
        }
    }
    
    pset(x, y, color = null) {
        if (this.graphicsMode === 0) return;

        const res = this.pmodeResolutions[this.graphicsMode];
        const pixelColor = color !== null ? this.colors[color % this.colors.length] : this.currentColor;

        this.ctx.fillStyle = pixelColor;
        this.ctx.fillRect(
            x * res.pixelWidth,
            y * res.pixelHeight,
            res.pixelWidth,
            res.pixelHeight
        );
    }
    
    preset(x, y) {
        this.pset(x, y, 0);
    }
    
    drawLine(x1, y1, x2, y2, color = null) {
        if (this.graphicsMode === 0) return;
        
        const res = this.pmodeResolutions[this.graphicsMode];
        const lineColor = color !== null ? this.colors[color % this.colors.length] : this.currentColor;
        
        // Bresenham's line algorithm for pixel-perfect lines
        const dx = Math.abs(x2 - x1);
        const dy = Math.abs(y2 - y1);
        const sx = x1 < x2 ? 1 : -1;
        const sy = y1 < y2 ? 1 : -1;
        let err = dx - dy;
        
        while (true) {
            this.ctx.fillStyle = lineColor;
            this.ctx.fillRect(
                x1 * res.pixelWidth,
                y1 * res.pixelHeight,
                res.pixelWidth,
                res.pixelHeight
            );
            
            if (x1 === x2 && y1 === y2) break;
            
            const e2 = 2 * err;
            if (e2 > -dy) {
                err -= dy;
                x1 += sx;
            }
            if (e2 < dx) {
                err += dx;
                y1 += sy;
            }
        }
    }
    
    drawBox(x1, y1, x2, y2, color = null) {
        // Draw rectangle outline using four lines
        this.drawLine(x1, y1, x2, y1, color);  // top
        this.drawLine(x2, y1, x2, y2, color);  // right
        this.drawLine(x2, y2, x1, y2, color);  // bottom
        this.drawLine(x1, y2, x1, y1, color);  // left
    }

    drawFilledBox(x1, y1, x2, y2, color = null) {
        if (this.graphicsMode === 0) return;

        const res = this.pmodeResolutions[this.graphicsMode];
        const fillColor = color !== null ? this.colors[color % this.colors.length] : this.currentColor;

        const minX = Math.min(x1, x2);
        const maxX = Math.max(x1, x2);
        const minY = Math.min(y1, y2);
        const maxY = Math.max(y1, y2);

        this.ctx.fillStyle = fillColor;
        this.ctx.fillRect(
            minX * res.pixelWidth,
            minY * res.pixelHeight,
            (maxX - minX + 1) * res.pixelWidth,
            (maxY - minY + 1) * res.pixelHeight
        );
    }

    drawCircle(x, y, radius, color = null) {
        if (this.graphicsMode === 0) return;

        const res = this.pmodeResolutions[this.graphicsMode];
        const circleColor = color !== null ? this.colors[color % this.colors.length] : this.currentColor;
        
        this.ctx.strokeStyle = circleColor;
        this.ctx.lineWidth = res.pixelWidth;
        this.ctx.beginPath();
        this.ctx.arc(
            x * res.pixelWidth + res.pixelWidth/2, 
            y * res.pixelHeight + res.pixelHeight/2, 
            radius * res.pixelWidth, 
            0, 
            2 * Math.PI
        );
        this.ctx.stroke();
    }
    
    paint(x, y, paintColor, borderColor) {
        if (this.graphicsMode === 0) return;

        const res = this.pmodeResolutions[this.graphicsMode];
        const fillColor = this.colors[paintColor % this.colors.length];
        const stopColor = borderColor !== undefined && borderColor !== null ?
            this.colors[borderColor % this.colors.length] : null;

        // Work at BASIC pixel granularity to match LINE drawing (which fills
        // pixelWidth x pixelHeight blocks). Operating at canvas pixel level
        // would leak through diagonal gaps between adjacent BASIC pixels.
        const pw = res.pixelWidth;
        const ph = res.pixelHeight;
        const bWidth = Math.floor(this.canvas.width / pw);
        const bHeight = Math.floor(this.canvas.height / ph);

        const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
        const pixels = imageData.data;

        // Sample a BASIC pixel's color from its top-left canvas pixel
        const sampleColor = (bx, by) => {
            const idx = (by * ph * this.canvas.width + bx * pw) * 4;
            return { r: pixels[idx], g: pixels[idx + 1], b: pixels[idx + 2] };
        };

        // Fill a BASIC pixel block
        const fillBlock = (bx, by, rgb) => {
            for (let dy = 0; dy < ph; dy++) {
                for (let dx = 0; dx < pw; dx++) {
                    const idx = ((by * ph + dy) * this.canvas.width + bx * pw + dx) * 4;
                    pixels[idx] = rgb.r;
                    pixels[idx + 1] = rgb.g;
                    pixels[idx + 2] = rgb.b;
                    pixels[idx + 3] = 255;
                }
            }
        };

        const startBX = Math.floor(x);
        const startBY = Math.floor(y);

        if (startBX < 0 || startBX >= bWidth || startBY < 0 || startBY >= bHeight) return;

        const startColor = sampleColor(startBX, startBY);
        const fillRGB = this.hexToRgb(fillColor);
        const stopRGB = stopColor !== null ? this.hexToRgb(stopColor) : null;

        // Stack-based flood fill at BASIC pixel granularity
        const stack = [[startBX, startBY]];
        const visited = new Set();

        while (stack.length > 0) {
            const [bx, by] = stack.pop();
            const key = (by << 16) | bx;

            if (visited.has(key)) continue;
            if (bx < 0 || bx >= bWidth || by < 0 || by >= bHeight) continue;

            const color = sampleColor(bx, by);

            // Check if we hit the border color
            if (stopRGB !== null) {
                if (color.r === stopRGB.r && color.g === stopRGB.g && color.b === stopRGB.b) {
                    continue;
                }
            }

            // When border color is specified: boundary fill (fill everything within border)
            // When no border color: flood fill (replace only matching start color)
            if (stopRGB === null) {
                if (color.r !== startColor.r || color.g !== startColor.g || color.b !== startColor.b) {
                    continue;
                }
            } else {
                // Skip pixels already filled
                if (color.r === fillRGB.r && color.g === fillRGB.g && color.b === fillRGB.b) {
                    continue;
                }
            }

            // Fill BASIC pixel block
            fillBlock(bx, by, fillRGB);

            visited.add(key);

            // Add neighbors (in BASIC pixel coordinates)
            stack.push([bx + 1, by]);
            stack.push([bx - 1, by]);
            stack.push([bx, by + 1]);
            stack.push([bx, by - 1]);
        }

        this.ctx.putImageData(imageData, 0, 0);
    }
    
    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    }
    
    drawText(x, y, text, color) {
        if (this.graphicsMode === 0) return;

        const res = this.pmodeResolutions[this.graphicsMode];
        const textColor = this.colors[color % this.colors.length];

        // Render using a small pixel font scaled to BASIC pixel size.
        // Each character is 4 BASIC pixels wide, 6 tall (fits CoCo style).
        const pw = res.pixelWidth;
        const ph = res.pixelHeight;
        const charW = 4;  // BASIC pixels per glyph width
        const charStep = 5; // BASIC pixels per character cell (4 + 1 spacing)
        const charH = 6;  // BASIC pixels per character height

        this.ctx.fillStyle = textColor;

        for (let ci = 0; ci < text.length; ci++) {
            const ch = text.charCodeAt(ci);
            const glyph = GPRINT_FONT[ch] || GPRINT_FONT[63]; // '?' fallback
            for (let row = 0; row < glyph.length; row++) {
                const bits = glyph[row];
                for (let col = 0; col < charW; col++) {
                    if (bits & (1 << (charW - 1 - col))) {
                        const px = (x + ci * charStep + col) * pw;
                        const py = (y + row) * ph;
                        this.ctx.fillRect(px, py, pw, ph);
                    }
                }
            }
        }
    }

    getGraphics(x1, y1, x2, y2, arrayName) {
        if (this.graphicsMode === 0) return;
        
        const res = this.pmodeResolutions[this.graphicsMode];
        const imageData = this.ctx.getImageData(
            Math.min(x1, x2) * res.pixelWidth,
            Math.min(y1, y2) * res.pixelHeight,
            (Math.abs(x2 - x1) + 1) * res.pixelWidth,
            (Math.abs(y2 - y1) + 1) * res.pixelHeight
        );
        
        this.spriteStorage[arrayName] = imageData;
        console.log(`GET graphics stored in array ${arrayName}`);
    }
    
    putGraphics(x, y, arrayName, action = 'pset', data = null) {
        if (this.graphicsMode === 0) return;
        
        const res = this.pmodeResolutions[this.graphicsMode];
        const sprite = this.spriteStorage[arrayName];
        
        if (sprite) {
            // Apply the sprite with the specified action
            if (action.toLowerCase() === 'pset') {
                this.ctx.putImageData(sprite, x * res.pixelWidth, y * res.pixelHeight);
            } else {
                // For other actions (OR, AND, XOR), we'd need pixel manipulation
                // For now, just use PSET
                this.ctx.putImageData(sprite, x * res.pixelWidth, y * res.pixelHeight);
            }
            console.log(`PUT array ${arrayName} at (${x},${y}) with action ${action}`);
        }
    }
    
    executeDraw(commands) {
        if (this.graphicsMode === 0) return;
        
        // Parse and execute DRAW commands
        // This is a simplified implementation
        console.log(`DRAW commands: ${commands}`);
        
        // Reset to center for demo
        this.drawX = 128;
        this.drawY = 96;
        
        // Simple command parser (would need full implementation)
        for (let cmd of commands) {
            switch (cmd.toUpperCase()) {
                case 'U': this.drawY -= 10; break;
                case 'D': this.drawY += 10; break;
                case 'L': this.drawX -= 10; break;
                case 'R': this.drawX += 10; break;
            }
            this.pset(this.drawX, this.drawY);
        }
    }
    
    saveState() {
        // Save canvas content as image data
        const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
        
        return {
            imageData: imageData,
            graphicsMode: this.graphicsMode,
            screenMode: this.screenMode,
            currentColor: this.currentColor,
            drawX: this.drawX,
            drawY: this.drawY
        };
    }
    
    restoreState(state) {
        if (!state) {
            // Clear canvas and reset to defaults for new tab
            this.ctx.fillStyle = '#000000';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            this.graphicsMode = 0;
            this.screenMode = 0;
            this.currentColor = 1;
            this.drawX = 128;
            this.drawY = 96;
            return;
        }
        
        // Restore canvas content
        this.ctx.putImageData(state.imageData, 0, 0);
        
        // Restore graphics state
        this.graphicsMode = state.graphicsMode;
        this.screenMode = state.screenMode;
        this.currentColor = state.currentColor;
        this.drawX = state.drawX;
        this.drawY = state.drawY;
    }
}

// Panel Resize Handler
class PanelResizer {
    constructor() {
        this.splitter = document.getElementById('panel-splitter');
        this.leftPanel = document.getElementById('text-panel');
        this.rightPanel = document.getElementById('graphics-panel');
        this.container = document.querySelector('.main-content');
        this.isResizing = false;
        
        this.init();
    }
    
    init() {
        this.splitter.addEventListener('mousedown', this.startResize.bind(this));
        document.addEventListener('mousemove', this.resize.bind(this));
        document.addEventListener('mouseup', this.stopResize.bind(this));
        
        // Load saved panel sizes
        this.loadPanelSizes();
    }
    
    startResize(e) {
        this.isResizing = true;
        this.startX = e.clientX;
        this.startLeftWidth = this.leftPanel.offsetWidth;
        this.splitter.style.cursor = 'col-resize';
        document.body.style.cursor = 'col-resize';
        e.preventDefault();
    }
    
    resize(e) {
        if (!this.isResizing) return;
        
        const diff = e.clientX - this.startX;
        const newLeftWidth = this.startLeftWidth + diff;
        const containerWidth = this.container.offsetWidth;
        
        // Enforce minimum panel widths
        const minWidth = 300;
        const maxWidth = containerWidth - minWidth - 6; // 6px for splitter
        
        if (newLeftWidth >= minWidth && newLeftWidth <= maxWidth) {
            const leftFlex = newLeftWidth / containerWidth;
            const rightFlex = 1 - leftFlex;
            
            this.leftPanel.style.flex = leftFlex;
            this.rightPanel.style.flex = rightFlex;
            
            // Save panel sizes
            this.savePanelSizes(leftFlex, rightFlex);
        }
    }
    
    stopResize() {
        this.isResizing = false;
        this.splitter.style.cursor = 'col-resize';
        document.body.style.cursor = 'default';
    }
    
    savePanelSizes(leftFlex, rightFlex) {
        localStorage.setItem('dualMonitor.panelSizes', JSON.stringify({
            left: leftFlex,
            right: rightFlex
        }));
    }
    
    loadPanelSizes() {
        const saved = localStorage.getItem('dualMonitor.panelSizes');
        if (saved) {
            const sizes = JSON.parse(saved);
            this.leftPanel.style.flex = sizes.left;
            this.rightPanel.style.flex = sizes.right;
        }
    }
}

// Program Tab Manager
class TabManager {
    constructor(emulator) {
        this.emulator = emulator;
        this.tabs = new Map();
        this.activeTabId = 'main';
        this.tabCounter = 1;
        this.tabResumeTimer = null; // Timer for tab resume after switching
        
        this.init();
    }
    
    init() {
        // Initialize main tab
        this.tabs.set('main', {
            id: 'main',
            title: 'Main',
            program: {},
            variables: {},
            isDirty: false,
            hasContent: true
        });
        
        // Setup event handlers
        document.getElementById('btn-add-tab').addEventListener('click', async (e) => {
            // Only respond to actual mouse clicks, not keyboard events
            if (e.detail === 0) return; // detail === 0 means keyboard activation
            await this.addTab();
        });
        
        // Handle tab clicks
        document.getElementById('tabs-container').addEventListener('click', async (e) => {
            if (e.target.classList.contains('tab') || e.target.parentElement.classList.contains('tab')) {
                const tab = e.target.closest('.tab');
                if (tab) {
                    await this.switchTab(tab.dataset.tabId);
                }
            }
            
            if (e.target.classList.contains('tab-close')) {
                e.stopPropagation();
                const tab = e.target.parentElement;
                await this.closeTab(tab.dataset.tabId);
            }
        });
    }
    
    async addTab() {
        const tabId = `prog${this.tabCounter++}`;
        const tabData = {
            id: tabId,
            title: `Program ${this.tabCounter}`,
            program: {},
            variables: {},
            isDirty: false,
            hasContent: false
        };
        
        this.tabs.set(tabId, tabData);
        
        // Create tab element
        const tabElement = document.createElement('div');
        tabElement.className = 'tab';
        tabElement.dataset.tabId = tabId;
        tabElement.innerHTML = `
            <span class="tab-title">${tabData.title}</span>
            <button class="tab-close">×</button>
        `;
        
        // Insert before the add button
        const addButton = document.getElementById('btn-add-tab');
        addButton.parentElement.insertBefore(tabElement, addButton);
        
        await this.switchTab(tabId);
    }
    
    async switchTab(tabId) {
        if (!this.tabs.has(tabId)) return;
        if (tabId === this.activeTabId) return;
        
        const previousTabId = this.activeTabId;
        
        // Step 1: Pause any running program in the current tab
        if (previousTabId) {
            await this.pauseTabForSwitch(previousTabId);
            this.saveTabState(previousTabId);
        }
        
        // Step 2: Update active tab and UI
        this.activeTabId = tabId;
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tabId === tabId);
        });
        
        // Step 3: Load new tab state
        this.loadTabState(tabId);
        
        // Step 4: Handle fresh tab or restore existing tab
        const tabData = this.tabs.get(tabId);
        if (!tabData.hasContent) {
            // Fresh tab - clear displays and show prompt
            this.emulator.displayManager.textDisplay.clearScreen();
            this.emulator.displayManager.textDisplay.showPrompt();
            this.emulator.displayManager.graphicsDisplay.restoreState(null);
            tabData.hasContent = true;
        }
        
        // Step 5: Notify server and resume if needed
        this.emulator.socket.emit('switch_tab', { tabId });
        await this.resumeTabAfterSwitch(tabId);
    }
    
    pauseTabForSwitch(tabId) {
        return new Promise((resolve) => {
            // Cancel any active auto-yield pause timer to prevent it from
            // firing continue_execution to the wrong tab after the switch
            if (this.emulator.pauseTimer) {
                clearTimeout(this.emulator.pauseTimer);
                this.emulator.pauseTimer = null;
            }

            // Store the tab's paused state
            const tabData = this.tabs.get(tabId);
            if (tabData) {
                tabData.wasPausedForSwitch = false;
                
                // Send pause request to server
                this.emulator.socket.emit('pause_for_tab_switch', { tabId });
                
                // Listen for pause confirmation
                const handlePauseResponse = (response) => {
                    this.emulator.socket.off('tab_switch_paused', handlePauseResponse);
                    tabData.wasPausedForSwitch = response.wasRunning || false;
                    resolve();
                };
                
                this.emulator.socket.on('tab_switch_paused', handlePauseResponse);
                
                // Fallback timeout
                setTimeout(() => {
                    this.emulator.socket.off('tab_switch_paused', handlePauseResponse);
                    resolve();
                }, 100);
            } else {
                resolve();
            }
        });
    }
    
    async resumeTabAfterSwitch(tabId) {
        const tabData = this.tabs.get(tabId);
        if (tabData && tabData.wasPausedForSwitch) {
            // Small delay to ensure tab switch is complete
            this.tabResumeTimer = setTimeout(() => {
                this.tabResumeTimer = null;
                this.emulator.socket.emit('resume_from_tab_switch', { tabId });
            }, 50);
        }
    }
    
    async closeTab(tabId) {
        if (tabId === 'main') return; // Can't close main tab
        
        const tabData = this.tabs.get(tabId);
        if (tabData && tabData.isDirty) {
            if (!confirm(`Tab "${tabData.title}" has unsaved changes. Close anyway?`)) {
                return;
            }
        }
        
        // Cancel any pending tab resume timer for this tab
        if (this.tabResumeTimer) {
            clearTimeout(this.tabResumeTimer);
            this.tabResumeTimer = null;
        }

        // If closing the active tab, pause any running program first
        if (this.activeTabId === tabId) {
            await this.pauseTabForSwitch(tabId);
        }

        // Remove tab
        this.tabs.delete(tabId);
        document.querySelector(`[data-tab-id="${tabId}"]`).remove();
        
        // Switch to main tab if this was active
        if (this.activeTabId === tabId) {
            await this.switchTab('main');
        }
    }
    
    saveTabState(tabId) {
        const tabData = this.tabs.get(tabId);
        if (!tabData) return;
        
        // Save display state (terminal content)
        tabData.displayState = this.emulator.displayManager.textDisplay.saveState();
        
        // Save graphics display state
        tabData.graphicsState = this.emulator.displayManager.graphicsDisplay.saveState();
        
        // Request current state from emulator
        this.emulator.socket.emit('get_state', { tabId }, (state) => {
            tabData.program = state.program || {};
            tabData.variables = state.variables || {};
        });
    }
    
    loadTabState(tabId) {
        const tabData = this.tabs.get(tabId);
        if (!tabData) return;
        
        // Restore display state (terminal content)
        if (tabData.displayState) {
            this.emulator.displayManager.textDisplay.restoreState(tabData.displayState);
        }
        
        // Restore graphics display state
        this.emulator.displayManager.graphicsDisplay.restoreState(tabData.graphicsState);
        
        // Send state to emulator
        this.emulator.socket.emit('set_state', {
            tabId,
            program: tabData.program,
            variables: tabData.variables
        });
    }
    
    markDirty(isDirty = true) {
        const tabData = this.tabs.get(this.activeTabId);
        if (tabData) {
            tabData.isDirty = isDirty;
            // Update UI indicator if needed
        }
    }
}

// Main Dual Monitor Emulator
class DualMonitorEmulator {
    constructor() {
        this.displayManager = new DisplayManager();
        this.audio = new CoCoAudio();
        
        // Test if Socket.IO is available
        if (typeof io === 'undefined') {
            console.error('Socket.IO library not loaded!');
            document.getElementById('program-status').textContent = 'Socket.IO Error';
            return;
        }
        
        console.log('Initializing Socket.IO connection...');
        this.socket = io();
        this.replContainer = document.getElementById('repl-container');
        this.waitingForInput = false;
        this.currentInputVariable = null;
        this.panelResizer = null;
        this.tabManager = null;
        this.sessionId = null;  // Store session ID from server
        
        this.initialize();
    }
    
    initialize() {
        // Initialize displays
        this.displayManager.initialize();

        // Wire file completion for LOAD/SAVE/KILL tab completion
        const socket = this.socket;
        this.displayManager.textDisplay.onRequestFiles = (callback) => {
            socket.emit('list_files');
            socket.once('file_list', (data) => callback(data.files));
        };

        // Initialize panel resizer
        this.panelResizer = new PanelResizer();
        
        // Initialize tab manager
        this.tabManager = new TabManager(this);
        
        // Setup Socket.IO handlers
        this.setupSocketHandlers();
        
        // Setup UI event handlers
        this.setupUIHandlers();
        
        // Load preferences
        this.loadPreferences();
        
        // Focus REPL container for keyboard input
        this.replContainer.focus();
    }
    
    setupSocketHandlers() {
        // Set up session ID handler FIRST, before connection
        this.socket.on('session_id', (data) => {
            this.sessionId = data.session_id;
            console.log('Session ID received:', this.sessionId);
            
            // Update status
            document.getElementById('program-status').textContent = 'Session Ready';
            
            // Clear the connecting message and show welcome
            this.displayManager.textDisplay.clearScreen();
            this.displayManager.textDisplay.printText('BASICOCO V1.0\n');
            this.displayManager.textDisplay.printText('Type BASIC commands or programs. Type HELP for assistance.\n\n');
            
            // Show initial prompt now that we're ready
            this.displayManager.textDisplay.showPrompt();
        });
        
        this.socket.on('connect', () => {
            console.log('Socket.IO connected successfully to server');
            console.log('Connected to BasiCoCo');
            document.getElementById('program-status').textContent = 'Connected';
            console.log('Waiting for session ID...');
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('Socket.IO connection error:', error);
            document.getElementById('program-status').textContent = 'Connection Error';
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            document.getElementById('program-status').textContent = 'Disconnected';
            this.sessionId = null;
        });
        
        this.socket.on('output', (data) => {
            this.handleOutput(data);
        });
        
    }
    
    setupUIHandlers() {
        // Track if a program is running
        this.programRunning = false;
        
        // Global keypress forwarding for INKEY$ (when program is running)
        // Use keydown instead of keypress (keypress is deprecated)
        document.addEventListener('keydown', (e) => {
            // Only forward printable characters when a program is running
            // and we're not waiting for input
            if (this.programRunning && 
                !this.displayManager.textDisplay.waitingForInput &&
                e.key.length === 1 && 
                !e.ctrlKey && !e.altKey && !e.metaKey) {
                console.log('Key detected for INKEY$:', e.key);
                
                // Send keypress to server for INKEY$ buffer
                this.socket.emit('keypress', {
                    key: e.key,
                    session_id: this.sessionId,
                    tabId: this.activeTabId  // Fixed: use tabId not tab
                });
                console.log('Sent key to server:', e.key);
            }
        }, true);  // Use capture phase to get event before other handlers

        // REPL keyboard input
        this.replContainer.addEventListener('keydown', (e) => {
            // Handle Ctrl+C interrupt
            if (e.ctrlKey && (e.key === 'c' || e.key === 'C')) {
                this.breakExecution();
                e.preventDefault();
                return;
            }

            // Scroll-back: Shift+PageUp / Shift+PageDown
            if (e.shiftKey && e.key === 'PageUp') {
                this.displayManager.textDisplay.scrollBack(this.displayManager.textDisplay.rows - 1);
                e.preventDefault();
                return;
            }
            if (e.shiftKey && e.key === 'PageDown') {
                this.displayManager.textDisplay.scrollForward(this.displayManager.textDisplay.rows - 1);
                e.preventDefault();
                return;
            }

            // Handle Emacs/readline key bindings
            if (e.ctrlKey) {
                let handled = this.displayManager.textDisplay.handleEmacsKeybinding(e.key);
                if (handled) {
                    e.preventDefault();
                    return;
                }
            }

            this.displayManager.textDisplay.handleKeyInput(e.key, (type, value) => {
                if (type === 'command') {
                    this.executeCommand(value);
                } else if (type === 'input') {
                    this.handleInputResponse(value);
                }
            });
            e.preventDefault(); // Prevent default browser behavior
        });

        // Mouse wheel scroll-back
        this.replContainer.addEventListener('wheel', (e) => {
            const td = this.displayManager.textDisplay;
            const lines = Math.ceil(Math.abs(e.deltaY) / 30);
            if (e.deltaY < 0) {
                td.scrollBack(lines);
            } else {
                td.scrollForward(lines);
            }
            e.preventDefault();
        });
        
        // Focus REPL when clicked
        this.replContainer.addEventListener('click', () => {
            this.replContainer.focus();
        });
        
        // Clear buttons
        document.getElementById('btn-clear-text').addEventListener('click', () => {
            this.displayManager.textDisplay.clearScreen();
        });
        
        document.getElementById('btn-clear-graphics').addEventListener('click', () => {
            this.displayManager.graphicsDisplay.clearGraphics();
        });
        
        // Export buttons
        document.getElementById('btn-export-png').addEventListener('click', () => {
            this.exportGraphics('png');
        });
        
        document.getElementById('btn-export-svg').addEventListener('click', () => {
            this.exportGraphics('svg');
        });
        
        // Help panel toggle
        document.getElementById('help-toggle').addEventListener('click', () => {
            const panel = document.getElementById('help-panel');
            const toggle = document.getElementById('help-toggle');
            
            panel.classList.toggle('collapsed');
            
            if (panel.classList.contains('collapsed')) {
                toggle.innerHTML = '<span>Quick Help ▲ Click to expand</span>';
            } else {
                toggle.innerHTML = '<span>Quick Help ▼ Click to collapse</span>';
            }
        });
        
        // Preferences
        document.getElementById('btn-preferences').addEventListener('click', () => {
            document.getElementById('preferences-modal').style.display = 'flex';
        });
        
        document.getElementById('btn-close-preferences').addEventListener('click', () => {
            document.getElementById('preferences-modal').style.display = 'none';
        });
        
        document.getElementById('btn-save-preferences').addEventListener('click', () => {
            this.savePreferences();
            document.getElementById('preferences-modal').style.display = 'none';
        });
        
        document.getElementById('btn-reset-preferences').addEventListener('click', () => {
            this.resetPreferences();
        });
        
        // Session management
        document.getElementById('btn-save-session').addEventListener('click', () => {
            this.saveSession();
        });
        
        // Copy text button
        document.getElementById('btn-copy-text').addEventListener('click', () => {
            this.copyTextDisplay();
        });
        
        // Track mouse position for graphics info
        document.getElementById('graphics-display').addEventListener('mousemove', (e) => {
            const rect = e.target.getBoundingClientRect();
            const res = this.displayManager.graphicsDisplay.pmodeResolutions[
                this.displayManager.graphicsDisplay.graphicsMode
            ];
            
            if (res && this.displayManager.graphicsDisplay.graphicsMode > 0) {
                const x = Math.floor((e.clientX - rect.left) / rect.width * res.width);
                const y = Math.floor((e.clientY - rect.top) / rect.height * res.height);
                document.getElementById('graphics-coords').textContent = `X: ${x}, Y: ${y}`;
            }
        });
    }
    
    executeCommand(command) {
        // Check if we have a session ID
        if (!this.sessionId) {
            console.error('No session ID available, cannot execute command:', command);
            this.displayManager.textDisplay.printText('ERROR: Not connected to server\n');
            this.displayManager.textDisplay.showPrompt();
            return;
        }
        
        console.log('Executing command:', command, 'with session:', this.sessionId);
        
        // Track if RUN command is starting
        if (command.trim().toUpperCase() === 'RUN') {
            this.programRunning = true;
            console.log('Program started running');
        }
        
        // Send to server
        this.socket.emit('execute_command', { 
            command: command,
            tabId: this.tabManager.activeTabId 
        });
        
        // Mark tab as dirty if it's a program line
        if (/^\d+/.test(command)) {
            this.tabManager.markDirty(true);
        }
    }
    
    handleInputResponse(value) {
        // Send input response to server
        this.socket.emit('input_response', {
            variable: this.currentInputVariable,
            value: value,
            tabId: this.tabManager.activeTabId
        });
        
        this.currentInputVariable = null;
    }
    
    breakExecution() {
        // Cancel any pending pause timers to prevent stray continue_execution calls
        if (this.pauseTimer) {
            clearTimeout(this.pauseTimer);
            this.pauseTimer = null;
        }
        
        // Cancel any pending tab resume timers to prevent stray resume_from_tab_switch calls
        if (this.tabManager.tabResumeTimer) {
            clearTimeout(this.tabManager.tabResumeTimer);
            this.tabManager.tabResumeTimer = null;
        }
        
        // Send break signal to server - let server decide what response to send
        // Server will send appropriate output and command_complete events
        this.socket.emit('break_execution', { tabId: this.tabManager.activeTabId });
        
        // Reset local input state immediately (safe to do)
        this.waitingForInput = false;
        this.currentInputVariable = null;
    }
    
    handleOutput(outputArray) {
        this._processOutputFrom(outputArray, 0);
    }

    _processOutputFrom(outputArray, startIndex) {
        for (let i = startIndex; i < outputArray.length; i++) {
            const output = outputArray[i];
            // Route output to appropriate display
            this.displayManager.routeOutput(output);

            // Handle special cases
            switch (output.type) {
                case 'sound':
                    this.audio.playSound(output.frequency, output.duration);
                    break;
                case 'input_request':
                    this.handleInputRequest(output);
                    return; // Stop processing — wait for user input
                case 'pause':
                    this.handlePause(output, outputArray, i + 1);
                    return; // Stop processing — resume after pause
                case 'command_complete':
                    document.getElementById('program-status').textContent = 'Ready';
                    this.programRunning = false;
                    console.log('Program stopped');
                    this.displayManager.textDisplay.showPrompt();
                    break;
            }
        }
    }
    
    handlePause(pauseCommand, remainingArray, remainingIndex) {
        // Handle PAUSE command - wait for specified duration then continue
        const duration = (pauseCommand.duration !== undefined && pauseCommand.duration !== null)
            ? pauseCommand.duration : 1.0; // Default 1 second if not specified

        // Show pause status (skip for short auto-yield pauses)
        if (duration > 0.1) {
            document.getElementById('program-status').textContent = `Pausing (${duration}s)...`;
        }

        // Clear any existing pause timer
        if (this.pauseTimer) {
            clearTimeout(this.pauseTimer);
        }

        // Wait for the specified duration, then continue
        this.pauseTimer = setTimeout(() => {
            if (this.pauseTimer === null) return; // cancelled
            this.pauseTimer = null;
            if (remainingArray && remainingIndex < remainingArray.length) {
                this._processOutputFrom(remainingArray, remainingIndex);
            } else {
                this.socket.emit('continue_execution', { tabId: this.tabManager.activeTabId });
                document.getElementById('program-status').textContent = 'Running...';
            }
        }, duration * 1000);
    }
    
    handleInputRequest(request) {
        this.waitingForInput = true;
        this.currentInputVariable = request.variable;
        
        // Show input prompt in the unified REPL
        this.displayManager.textDisplay.showInputPrompt(request.prompt);
        
        // Ensure REPL container has focus
        this.replContainer.focus();
    }
    
    exportGraphics(format) {
        const canvas = document.getElementById('graphics-display');
        
        if (format === 'png') {
            canvas.toBlob((blob) => {
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `trs80-graphics-${Date.now()}.png`;
                a.click();
                URL.revokeObjectURL(url);
            });
        } else if (format === 'svg') {
            // For SVG, we'd need to recreate the graphics as vector
            // This is a placeholder for future implementation
            alert('SVG export coming soon!');
        }
    }
    
    copyTextDisplay() {
        // Get text content from canvas (would need OCR or text tracking)
        // For now, just copy a message
        navigator.clipboard.writeText('Text display content copied!');
        
        // Show feedback
        const btn = document.getElementById('btn-copy-text');
        const originalText = btn.textContent;
        btn.textContent = 'Copied!';
        setTimeout(() => {
            btn.textContent = originalText;
        }, 1000);
    }
    
    saveSession() {
        const session = {
            tabs: Array.from(this.tabManager.tabs.values()),
            activeTab: this.tabManager.activeTabId,
            preferences: this.getPreferences(),
            timestamp: Date.now()
        };
        
        localStorage.setItem('dualMonitor.session', JSON.stringify(session));
        
        // Show feedback
        document.getElementById('program-status').textContent = 'Session saved';
        setTimeout(() => {
            document.getElementById('program-status').textContent = 'Ready';
        }, 2000);
    }
    
    loadSession() {
        const saved = localStorage.getItem('dualMonitor.session');
        if (saved) {
            const session = JSON.parse(saved);
            // Restore tabs and state
            // Implementation would restore all tab states
        }
    }
    
    getPreferences() {
        return {
            layout: document.getElementById('pref-layout').value,
            textColor: document.getElementById('pref-text-color').value,
            crtEffect: document.getElementById('pref-crt-effect').checked,
            autoSave: document.getElementById('pref-auto-save').checked
        };
    }
    
    savePreferences() {
        const prefs = this.getPreferences();
        localStorage.setItem('dualMonitor.preferences', JSON.stringify(prefs));
        this.applyPreferences(prefs);
    }
    
    loadPreferences() {
        const saved = localStorage.getItem('dualMonitor.preferences');
        if (saved) {
            const prefs = JSON.parse(saved);
            this.applyPreferences(prefs);
        }
    }
    
    applyPreferences(prefs) {
        // Apply layout
        if (prefs.layout === 'vertical') {
            document.querySelector('.main-content').style.flexDirection = 'column';
        } else {
            document.querySelector('.main-content').style.flexDirection = 'row';
        }
        
        // Apply text color
        const colorMap = {
            'green': '#00ff00',
            'amber': '#ffb000',
            'white': '#ffffff'
        };
        
        if (colorMap[prefs.textColor]) {
            this.displayManager.textDisplay.textColor = colorMap[prefs.textColor];
            document.documentElement.style.setProperty('--text-green', colorMap[prefs.textColor]);
        }
        
        // Apply CRT effect
        const screens = document.querySelectorAll('.screen-container');
        screens.forEach(screen => {
            if (prefs.crtEffect) {
                screen.classList.add('crt-effect');
            } else {
                screen.classList.remove('crt-effect');
            }
        });
        
        // Set form values
        document.getElementById('pref-layout').value = prefs.layout || 'horizontal';
        document.getElementById('pref-text-color').value = prefs.textColor || 'green';
        document.getElementById('pref-crt-effect').checked = prefs.crtEffect !== false;
        document.getElementById('pref-auto-save').checked = prefs.autoSave !== false;
    }
    
    resetPreferences() {
        localStorage.removeItem('dualMonitor.preferences');
        this.applyPreferences({
            layout: 'horizontal',
            textColor: 'green',
            crtEffect: true,
            autoSave: true
        });
        this.savePreferences();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.dualMonitor = new DualMonitorEmulator();
    
    // Auto-save session periodically if enabled
    setInterval(() => {
        if (document.getElementById('pref-auto-save').checked) {
            window.dualMonitor.saveSession();
        }
    }, 60000); // Every minute
});