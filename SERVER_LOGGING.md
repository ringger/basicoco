# Server Logging Scripts

These scripts help you run and monitor the BasiCoCo server with comprehensive logging for debugging purposes.

## Scripts

### `start_server_with_logging.sh`
Starts the Flask server with full logging to timestamped files.

**Features:**
- Activates virtual environment automatically
- Validates dependencies and environment
- Creates timestamped log files in `logs/` directory
- Creates `logs/server_latest.log` symlink for easy access
- Uses `tee` to show output on console AND save to file
- Handles graceful shutdown with Ctrl+C

**Usage:**
```bash
./start_server_with_logging.sh
```

### `monitor_server_logs.sh`
Monitors server logs in real-time using `tail -f`.

**Features:**
- Automatically finds the latest log file
- Real-time monitoring with `tail -f`
- Colored output for better readability
- Graceful handling if server isn't running

**Usage:**
```bash
# In a separate terminal window:
./monitor_server_logs.sh
```

## Workflow

1. **Terminal 1** - Start server with logging:
   ```bash
   ./start_server_with_logging.sh
   ```

2. **Terminal 2** - Monitor logs (optional, for debugging):
   ```bash
   ./monitor_server_logs.sh
   ```

3. **Terminal 3** - Run tests, CLI client, etc:
   ```bash
   source venv/bin/activate
   python tests/integration/test_websocket_completion_signals.py
   # or
   python cli_client.py
   ```

## Log Files

- **Location**: `logs/` directory
- **Format**: `server_YYYYMMDD_HHMMSS.log`
- **Latest**: `logs/server_latest.log` (symlink to most recent)
- **Content**: All server stdout/stderr including:
  - Flask startup messages
  - WebSocket connections/disconnections
  - Debug print statements
  - Error messages and tracebacks
  - Request/response logging

## Benefits

- **No more copy/paste**: All server output automatically logged
- **Timestamped logs**: Easy to correlate with test runs
- **Persistent history**: Logs saved even after server stops
- **Real-time monitoring**: `tail -f` shows live output
- **Clean separation**: Server in one terminal, monitoring in another

## Example Log Output

```
=== TRS-80 BASIC Emulator Server Log ===
Started at: Mon Sep  9 11:47:28 UTC 2025
Working directory: /path/to/trs80
Python version: Python 3.12.3
Virtual environment: /path/to/trs80/venv
=========================================

 * Serving Flask app 'app'
 * Debug mode: on
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://172.28.211.212:5000
Client connected
DEBUG: Input response for A = 42
DEBUG: basic.program_counter = (0, 0)
Client disconnected
```

This makes debugging much more efficient since you can see all server activity in real-time without manual copy/paste operations.