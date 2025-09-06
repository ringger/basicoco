class CoCoDisplay {
    constructor() {
        this.canvas = document.getElementById('display');
        this.ctx = this.canvas.getContext('2d');
        this.cursor = document.getElementById('cursor');
        
        // Text mode properties
        this.charWidth = 16;
        this.charHeight = 24;
        this.cols = 32;
        this.rows = 16;
        this.currentRow = 0;
        this.currentCol = 0;
        
        // Graphics mode properties
        this.graphicsMode = 0; // 0 = text, 1-4 = PMODE
        this.screenMode = 1;
        this.currentDrawColor = 1;
        
        // Colors (TRS-80 Color Computer palette)
        this.colors = [
            '#000000', // 0 - black
            '#00ff00', // 1 - green
            '#ffff00', // 2 - yellow  
            '#0000ff', // 3 - blue
            '#ff0000', // 4 - red
            '#ffaa88', // 5 - buff
            '#00ffff', // 6 - cyan
            '#ff00ff', // 7 - magenta
            '#ff8800'  // 8 - orange
        ];
        
        this.currentColor = this.colors[1]; // green
        this.backgroundColor = this.colors[0]; // black
        
        // PMODE resolutions
        this.pmodeResolutions = {
            0: { width: 32, height: 16, pixelWidth: 16, pixelHeight: 24 }, // text mode
            1: { width: 128, height: 96, pixelWidth: 4, pixelHeight: 4 },
            2: { width: 128, height: 96, pixelWidth: 4, pixelHeight: 4 },
            3: { width: 128, height: 192, pixelWidth: 4, pixelHeight: 2 },
            4: { width: 256, height: 192, pixelWidth: 2, pixelHeight: 2 }
        };
        
        this.initDisplay();
        this.updateCursor();
    }
    
    initDisplay() {
        this.ctx.fillStyle = this.backgroundColor;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.font = '20px "Courier New", monospace';
        this.ctx.textBaseline = 'top';
    }
    
    clearScreen() {
        this.ctx.fillStyle = this.backgroundColor;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        this.currentRow = 0;
        this.currentCol = 0;
        this.updateCursor();
    }
    
    printText(text) {
        this.ctx.fillStyle = this.currentColor;
        
        for (let char of text) {
            if (char === '\n' || this.currentCol >= this.cols) {
                this.newLine();
                if (char === '\n') continue;
            }
            
            this.ctx.fillText(
                char, 
                this.currentCol * this.charWidth, 
                this.currentRow * this.charHeight
            );
            
            this.currentCol++;
        }
        
        this.updateCursor();
    }
    
    newLine() {
        this.currentCol = 0;
        this.currentRow++;
        
        if (this.currentRow >= this.rows) {
            this.scrollUp();
            this.currentRow = this.rows - 1;
        }
    }
    
    scrollUp() {
        const imageData = this.ctx.getImageData(0, this.charHeight, this.canvas.width, this.canvas.height - this.charHeight);
        this.ctx.fillStyle = this.backgroundColor;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.putImageData(imageData, 0, 0);
    }
    
    updateCursor() {
        if (this.graphicsMode === 0) {
            this.cursor.style.left = (this.currentCol * this.charWidth) + 'px';
            this.cursor.style.top = (this.currentRow * this.charHeight) + 'px';
            this.cursor.style.display = 'block';
        } else {
            this.cursor.style.display = 'none';
        }
    }
    
    setPmode(mode, page = 1) {
        this.graphicsMode = mode;
        this.clearScreen();
        
        if (mode > 0) {
            const res = this.pmodeResolutions[mode];
            console.log(`PMODE ${mode}: ${res.width}x${res.height} graphics`);
        } else {
            console.log('Text mode');
        }
        
        this.updateCursor();
    }
    
    setScreen(mode) {
        this.screenMode = mode;
        // Update color palette based on screen mode if needed
        console.log(`SCREEN ${mode}`);
    }
    
    setColor(fg, bg) {
        if (fg !== null && fg >= 0 && fg < this.colors.length) {
            this.currentColor = this.colors[fg];
            this.currentDrawColor = fg;
        }
        if (bg !== null && bg >= 0 && bg < this.colors.length) {
            this.backgroundColor = this.colors[bg];
            this.clearScreen();
        }
    }
    
    clearGraphics() {
        this.ctx.fillStyle = this.backgroundColor;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }
    
    pset(x, y, color = null) {
        if (this.graphicsMode === 0) return; // Only in graphics mode
        
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
        this.pset(x, y, 0); // Set to background color (black)
    }
    
    drawLine(x1, y1, x2, y2, color = null) {
        if (this.graphicsMode === 0) return; // Only in graphics mode
        
        const res = this.pmodeResolutions[this.graphicsMode];
        const lineColor = color !== null ? this.colors[color % this.colors.length] : this.currentColor;
        
        this.ctx.strokeStyle = lineColor;
        this.ctx.lineWidth = res.pixelWidth;
        this.ctx.beginPath();
        this.ctx.moveTo(x1 * res.pixelWidth + res.pixelWidth/2, y1 * res.pixelHeight + res.pixelHeight/2);
        this.ctx.lineTo(x2 * res.pixelWidth + res.pixelWidth/2, y2 * res.pixelHeight + res.pixelHeight/2);
        this.ctx.stroke();
    }
    
    drawCircle(x, y, radius, color = null) {
        if (this.graphicsMode === 0) return; // Only in graphics mode
        
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
    
    getGraphics(x1, y1, x2, y2, arrayName) {
        // GET (x1,y1)-(x2,y2), array_name
        // In a real implementation, this would capture the pixel data
        // For our simulation, we'll just acknowledge the operation
        console.log(`GET graphics from (${x1},${y1}) to (${x2},${y2}) into array ${arrayName}`);
        
        // In graphics mode, we would capture the actual pixel data here
        if (this.graphicsMode > 0) {
            const res = this.pmodeResolutions[this.graphicsMode];
            const imageData = this.ctx.getImageData(
                Math.min(x1, x2) * res.pixelWidth,
                Math.min(y1, y2) * res.pixelHeight,
                (Math.abs(x2 - x1) + 1) * res.pixelWidth,
                (Math.abs(y2 - y1) + 1) * res.pixelHeight
            );
            // Store the image data for later PUT operations
            this[`array_${arrayName}`] = imageData;
        }
    }
    
    putGraphics(x, y, arrayName, action, data) {
        // PUT (x,y), array_name [,action]
        // Display the stored graphics data at the specified position
        console.log(`PUT array ${arrayName} at (${x},${y}) with action ${action}`);
        
        if (this.graphicsMode > 0 && this[`array_${arrayName}`]) {
            const res = this.pmodeResolutions[this.graphicsMode];
            
            // For our simulation, draw a representation of the stored data
            // In a real implementation, this would restore actual pixel data
            if (data && Array.isArray(data)) {
                for (let row = 0; row < data.length; row++) {
                    for (let col = 0; col < data[row].length; col++) {
                        const pixel = data[row][col];
                        const pixelX = x + col;
                        const pixelY = y + row;
                        
                        // Apply the action (PSET, PRESET, OR, AND, XOR)
                        switch (action.toLowerCase()) {
                            case 'pset':
                                this.pset(pixelX, pixelY, pixel.color);
                                break;
                            case 'preset':
                                this.preset(pixelX, pixelY);
                                break;
                            case 'or':
                            case 'and': 
                            case 'xor':
                                // For now, just use PSET for these operations
                                this.pset(pixelX, pixelY, pixel.color);
                                break;
                            default:
                                this.pset(pixelX, pixelY, pixel.color);
                        }
                    }
                }
            }
        }
    }
}

class CoCoEmulator {
    constructor() {
        this.display = new CoCoDisplay();
        this.audio = new CoCoAudio();
        this.socket = io();
        this.commandInput = document.getElementById('command-input');
        this.waitingForInput = false;
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        this.commandInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const command = this.commandInput.value.trim();
                if (command) {
                    this.executeCommand(command);
                    this.commandInput.value = '';
                }
            }
        });
        
        this.socket.on('output', (data) => {
            this.handleOutput(data);
        });
        
        this.socket.on('connect', () => {
            console.log('Connected to TRS-80 Color Computer');
        });
    }
    
    executeCommand(command) {
        this.socket.emit('execute_command', { command: command });
    }
    
    handleOutput(outputArray) {
        for (let output of outputArray) {
            switch (output.type) {
                case 'text':
                    this.display.printText(output.text + '\n');
                    break;
                case 'clear_screen':
                    this.display.clearScreen();
                    break;
                case 'clear_graphics':
                    this.display.clearGraphics();
                    break;
                case 'set_pmode':
                    this.display.setPmode(output.mode, output.page);
                    break;
                case 'set_screen':
                    this.display.setScreen(output.mode);
                    break;
                case 'set_color':
                    this.display.setColor(output.fg, output.bg);
                    break;
                case 'pset':
                    this.display.pset(output.x, output.y, output.color);
                    break;
                case 'preset':
                    this.display.preset(output.x, output.y);
                    break;
                case 'line':
                    this.display.drawLine(output.x1, output.y1, output.x2, output.y2, output.color);
                    break;
                case 'circle':
                    this.display.drawCircle(output.x, output.y, output.radius, output.color);
                    break;
                case 'sound':
                    this.audio.playSound(output.frequency, output.duration);
                    break;
                case 'get':
                    this.display.getGraphics(output.x1, output.y1, output.x2, output.y2, output.array);
                    break;
                case 'put':
                    this.display.putGraphics(output.x, output.y, output.array, output.action, output.data);
                    break;
                case 'error':
                    this.display.printText(output.message + '\n');
                    break;
                case 'input_request':
                    this.handleInputRequest(output);
                    break;
                default:
                    console.log('Unknown output type:', output);
            }
        }
    }
    
    handleInputRequest(request) {
        // Set flag to prevent INKEY$ from capturing keystrokes
        this.waitingForInput = true;
        
        // Display the prompt
        this.display.printText(request.prompt);
        
        // Show a visual cursor or input indicator
        const inputIndicator = document.createElement('span');
        inputIndicator.textContent = '_';
        inputIndicator.style.animation = 'blink 1s infinite';
        
        // Create a temporary input field to capture keystrokes
        const inputBuffer = [];
        
        const handleKeyInput = (event) => {
            if (event.key === 'Enter') {
                // Submit the input
                const inputValue = inputBuffer.join('');
                this.display.printText(inputValue + '\n');
                
                // Send the input response to the server
                this.socket.emit('input_response', {
                    variable: request.variable,
                    value: inputValue
                });
                
                // Clean up
                this.waitingForInput = false;
                document.removeEventListener('keydown', handleKeyInput);
                if (inputIndicator.parentNode) {
                    inputIndicator.parentNode.removeChild(inputIndicator);
                }
            } else if (event.key === 'Backspace') {
                if (inputBuffer.length > 0) {
                    inputBuffer.pop();
                    // Update display by removing last character
                    const canvas = document.getElementById('screen');
                    const ctx = canvas.getContext('2d');
                    // Simple backspace - clear a character width
                    // This is basic - a full implementation would track cursor position
                }
            } else if (event.key.length === 1) {
                // Regular character
                inputBuffer.push(event.key.toUpperCase());
                this.display.printText(event.key.toUpperCase());
            }
        };
        
        // Add the input indicator to show we're waiting for input
        const textCanvas = document.getElementById('screen');
        textCanvas.appendChild(inputIndicator);
        
        // Focus and start listening for input
        document.addEventListener('keydown', handleKeyInput);
    }
}

// Initialize the emulator when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.coco = new CoCoEmulator();
    
    // Global keypress handler for INKEY$ function
    document.addEventListener('keydown', (event) => {
        // Don't capture keys if we're typing in the command input
        if (document.activeElement === document.getElementById('command-input')) {
            return;
        }
        
        // Don't capture keys if we're in an INPUT prompt
        if (window.coco.waitingForInput) {
            return;
        }
        
        // Send the keypress to the server for INKEY$ buffer
        if (event.key.length === 1 || event.key === 'Enter' || event.key === ' ') {
            let key = event.key;
            if (key === 'Enter') key = '\r';  // Convert Enter to carriage return for BASIC
            if (key === ' ') key = ' ';       // Space key
            
            window.coco.socket.emit('keypress', { key: key.toUpperCase() });
            
            // Prevent default behavior for captured keys
            event.preventDefault();
        }
    });
    
    // Focus the input field
    document.getElementById('command-input').focus();
});