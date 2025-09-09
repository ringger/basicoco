#!/bin/bash

# TRS-80 BASIC Emulator Server Log Monitor
# This script monitors the server logs in real-time

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
LATEST_LOG="$LOG_DIR/server_latest.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== TRS-80 Server Log Monitor ===${NC}"

# Check if logs directory exists
if [ ! -d "$LOG_DIR" ]; then
    echo -e "${RED}Error: Log directory not found at $LOG_DIR${NC}"
    echo "Please start the server first using: ./start_server_with_logging.sh"
    exit 1
fi

# Check if latest log exists
if [ ! -f "$LATEST_LOG" ]; then
    echo -e "${YELLOW}Warning: Latest log file not found${NC}"
    echo "Looking for most recent log file..."
    
    # Find the most recent log file
    RECENT_LOG=$(find "$LOG_DIR" -name "server_*.log" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
    
    if [ -z "$RECENT_LOG" ]; then
        echo -e "${RED}Error: No server log files found in $LOG_DIR${NC}"
        echo "Please start the server first using: ./start_server_with_logging.sh"
        exit 1
    else
        echo -e "${GREEN}Found recent log: $RECENT_LOG${NC}"
        LATEST_LOG="$RECENT_LOG"
    fi
fi

echo "Monitoring log file: $LATEST_LOG"
echo -e "${YELLOW}Press Ctrl+C to stop monitoring${NC}"
echo ""

# Add some visual separation
echo -e "${BLUE}==================== SERVER OUTPUT ====================${NC}"

# Follow the log file
tail -f "$LATEST_LOG"