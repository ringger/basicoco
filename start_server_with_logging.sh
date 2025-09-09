#!/bin/bash

# TRS-80 BASIC Emulator Server Startup Script with Logging
# This script starts the Flask server and logs all output for debugging

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/server_$(date +%Y%m%d_%H%M%S).log"
LATEST_LOG="$LOG_DIR/server_latest.log"
VENV_DIR="$SCRIPT_DIR/venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== TRS-80 BASIC Emulator Server Startup ===${NC}"
echo "Script directory: $SCRIPT_DIR"
echo "Log directory: $LOG_DIR"
echo "Log file: $LOG_FILE"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Change to the project directory
cd "$SCRIPT_DIR"
echo "Working directory: $(pwd)"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}Error: Virtual environment not found at $VENV_DIR${NC}"
    echo "Please create virtual environment first: python3 -m venv venv"
    exit 1
fi

# Check if Flask app exists
if [ ! -f "app.py" ]; then
    echo -e "${RED}Error: Flask app (app.py) not found in current directory${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# Verify Python and required packages
echo -e "${YELLOW}Checking Python environment...${NC}"
python --version
echo "Python executable: $(which python)"

# Check required packages
if ! python -c "import flask, flask_socketio" 2>/dev/null; then
    echo -e "${RED}Error: Required packages (flask, flask-socketio) not found${NC}"
    echo "Please install dependencies: pip install -r requirements.txt"
    exit 1
fi

# Set environment variables for better logging
export FLASK_ENV=development
export FLASK_DEBUG=1
export PYTHONUNBUFFERED=1

# Create log file with header
echo "=== TRS-80 BASIC Emulator Server Log ===" > "$LOG_FILE"
echo "Started at: $(date)" >> "$LOG_FILE"
echo "Working directory: $(pwd)" >> "$LOG_FILE"
echo "Python version: $(python --version)" >> "$LOG_FILE"
echo "Virtual environment: $VENV_DIR" >> "$LOG_FILE"
echo "=========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Create symlink to latest log
ln -sf "$LOG_FILE" "$LATEST_LOG"

echo -e "${GREEN}Starting Flask server...${NC}"
echo "Server output will be logged to: $LOG_FILE"
echo "You can monitor output with: tail -f $LATEST_LOG"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Function to handle cleanup on script exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down server...${NC}"
    echo "Server stopped at: $(date)" >> "$LOG_FILE"
    echo "Log saved to: $LOG_FILE"
}

# Set trap to handle cleanup
trap cleanup EXIT INT TERM

# Start the server with tee to log output
# Using stdbuf to ensure immediate output flushing
stdbuf -oL -eL python app.py 2>&1 | tee -a "$LOG_FILE"