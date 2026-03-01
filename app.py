from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from emulator.core import CoCoBasic
import logging
import os
import uuid

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24).hex())
socketio = SocketIO(app, cors_allowed_origins="*")

# Session management for multiple tabs/programs
class SessionManager:
    def __init__(self):
        self.sessions = {}
    
    def get_session(self, session_id, tab_id='main'):
        """Get or create a session for the given session and tab IDs"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {}
        
        if tab_id not in self.sessions[session_id]:
            self.sessions[session_id][tab_id] = CoCoBasic()
        
        return self.sessions[session_id][tab_id]
    
    def remove_session(self, session_id):
        """Remove a session when client disconnects"""
        if session_id in self.sessions:
            del self.sessions[session_id]

# Global session manager
session_manager = SessionManager()

# Track client sessions
client_sessions = {}

@socketio.on('connect')
def handle_connect():
    """Handle client connection and assign session ID"""
    logger.debug("New client connecting: %s", request.sid)
    session_id = str(uuid.uuid4())
    client_sessions[request.sid] = session_id
    logger.debug("Client connected: %s with session %s", request.sid, session_id)
    emit('session_id', {'session_id': session_id})
    logger.debug("Session ID emitted successfully")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection and cleanup session"""
    if request.sid in client_sessions:
        session_id = client_sessions[request.sid]
        session_manager.remove_session(session_id)
        del client_sessions[request.sid]
        logger.debug("Client disconnected: %s", request.sid)

@app.route('/')
def index():
    """TRS-80 Color Computer BASIC Emulator"""
    return render_template('dual_monitor.html')

@app.route('/dual')
def dual_monitor():
    """Dual monitor interface (same as main route for backward compatibility)"""
    return render_template('dual_monitor.html')

@socketio.on('execute_command')
def handle_command(data):
    """Execute BASIC command with session and tab support"""
    command = data.get('command', '')
    tab_id = data.get('tabId', 'main')
    
    logger.debug("Executing command '%s' for client %s", command, request.sid)
    
    # Get session for this client
    session_id = client_sessions.get(request.sid)
    if not session_id:
        logger.warning("Session not found for client %s. Available sessions: %s", request.sid, list(client_sessions.keys()))
        emit('output', [{'type': 'error', 'message': 'Session not found'}])
        return
    
    logger.debug("Using session %s for tab %s", session_id, tab_id)
    
    # Get BASIC interpreter for this session/tab
    basic = session_manager.get_session(session_id, tab_id)
    
    line_num, code = basic.parse_line(command)
    
    if line_num is not None:
        # Store program line
        if code:
            basic.program[line_num] = code
            # Also expand into sub-lines for execution
            basic.expand_line_to_sublines(line_num, code)
        else:
            # Delete line if no code
            if line_num in basic.program:
                del basic.program[line_num]
            # Also remove from expanded program
            keys_to_remove = [key for key in basic.expanded_program.keys() if key[0] == line_num]
            for key in keys_to_remove:
                del basic.expanded_program[key]
        
        emit('output', [{'type': 'text', 'text': 'OK'}])
        emit('output', [{'type': 'command_complete'}])
    else:
        # Execute immediate command
        try:
            logger.debug("About to execute command: %s", command)
            output = basic.process_command(command)
            logger.debug("Command execution returned: %s", output)
            emit('output', output)
            
            # Only send completion signal if command actually finished (no pause or input request)
            has_pause = any(item.get('type') == 'pause' for item in output)
            has_input_request = any(item.get('type') == 'input_request' for item in output)
            if not has_pause and not has_input_request:
                emit('output', [{'type': 'command_complete'}])
                
        except Exception as e:
            logger.error("Command execution error: %s", e, exc_info=True)
            emit('output', [{'type': 'error', 'message': f'Error: {str(e)}'}])
            emit('output', [{'type': 'command_complete'}])

@socketio.on('input_response')
def handle_input_response(data):
    """Handle INPUT response with session support"""
    variable = data.get('variable', '')
    value = data.get('value', '')
    tab_id = data.get('tabId', 'main')
    
    # Get session for this client
    session_id = client_sessions.get(request.sid)
    if not session_id:
        emit('output', [{'type': 'error', 'message': 'Session not found'}])
        return
    
    # Get BASIC interpreter for this session/tab
    basic = session_manager.get_session(session_id, tab_id)
    
    # Handle special system variables
    if variable == '_kill_confirm':
        filename = data.get('filename', '')
        if filename:
            output = basic.process_kill_confirmation(value, filename)
            emit('output', output)
            # Send completion signal after KILL confirmation
            emit('output', [{'type': 'command_complete'}])
            return
        else:
            emit('output', [{'type': 'error', 'message': 'KILL confirmation error: no filename'}])
            # Send completion signal even for KILL errors
            emit('output', [{'type': 'command_complete'}])
            return
    
    # Process the input value and continue program execution
    try:
        # Store the input value in the variable
        if variable.endswith('$'):
            # String variable
            basic.variables[variable] = str(value)
        else:
            # Numeric variable - try to convert to number
            try:
                if '.' in value or 'E' in value.upper():
                    basic.variables[variable] = float(value)
                else:
                    basic.variables[variable] = int(value)
            except ValueError:
                # If conversion fails, treat as 0
                basic.variables[variable] = 0
        
        # Check if we're in multi-variable INPUT mode
        if hasattr(basic, 'input_variables') and basic.input_variables:
            basic.current_input_index += 1
            
            # Check if there are more variables to input
            if basic.current_input_index < len(basic.input_variables):
                # Request input for the next variable
                next_variable = basic.input_variables[basic.current_input_index]
                output = [{'type': 'input_request', 'prompt': basic.input_prompt, 'variable': next_variable}]
                emit('output', output)
                return
            else:
                # All variables have been input, clean up and continue
                basic.input_variables = None
                basic.input_prompt = None
                basic.current_input_index = 0
        
        # Continue execution from where we left off  
        if (hasattr(basic, 'program_counter') and basic.program_counter is not None and 
            basic.program_counter != (0, 0)):
            # We're in program execution - continue from where we paused for input
            basic.waiting_for_input = False
            output = basic.continue_program_execution()
            emit('output', output)
            
            # Only send completion signal if execution actually finished (no pause)
            has_pause = any(item.get('type') == 'pause' for item in output)
            if not has_pause and basic.program_counter is None:
                emit('output', [{'type': 'command_complete'}])
        else:
            # Direct INPUT command (not in program) - complete immediately
            emit('output', [{'type': 'command_complete'}])
        
    except Exception as e:
        emit('output', [{'type': 'error', 'message': f'Input error: {str(e)}'}])
        emit('output', [{'type': 'command_complete'}])

@socketio.on('keypress')
def handle_keypress(data):
    """Handle keypress for INKEY$ with session support"""
    key = data.get('key', '')
    tab_id = data.get('tabId', 'main')
    
    # Get session for this client
    session_id = client_sessions.get(request.sid)
    if not session_id:
        return
    
    # Get BASIC interpreter for this session/tab
    basic = session_manager.get_session(session_id, tab_id)
    
    # Add the key to the keyboard buffer for INKEY$ function
    basic.keyboard_buffer.append(key)

@socketio.on('pause_for_tab_switch')
def handle_pause_for_tab_switch(data):
    """Pause program execution for tab switching"""
    tab_id = data.get('tabId', 'main')
    
    # Get session for this client
    session_id = client_sessions.get(request.sid)
    if not session_id:
        emit('tab_switch_paused', {'success': False, 'error': 'Session not found'})
        return
    
    # Get BASIC interpreter for this session/tab
    basic = session_manager.get_session(session_id, tab_id)
    
    # Check if program is running and pause it
    was_running = basic.program_counter is not None
    if was_running:
        # Mark as paused for tab switch (we'll add this flag to the interpreter)
        basic.paused_for_tab_switch = True
    
    emit('tab_switch_paused', {'success': True, 'wasRunning': was_running})

@socketio.on('resume_from_tab_switch')
def handle_resume_from_tab_switch(data):
    """Resume program execution after returning to tab"""
    tab_id = data.get('tabId', 'main')
    
    # Get session for this client
    session_id = client_sessions.get(request.sid)
    if not session_id:
        emit('output', [{'type': 'error', 'message': 'Session not found'}])
        return
    
    # Get BASIC interpreter for this session/tab
    basic = session_manager.get_session(session_id, tab_id)
    
    # Resume if it was paused for tab switch
    if hasattr(basic, 'paused_for_tab_switch') and basic.paused_for_tab_switch:
        basic.paused_for_tab_switch = False
        if basic.program_counter:
            # Continue execution from where we left off
            output = basic.continue_program_execution()
            emit('output', output)
            
            # Check if program finished or paused
            has_pause = any(item.get('type') == 'pause' for item in output)
            if not has_pause and basic.program_counter is None:
                emit('output', [{'type': 'command_complete'}])

@socketio.on('switch_tab')
def handle_switch_tab(data):
    """Handle tab switching - ensure session exists for new tab"""
    tab_id = data.get('tabId', 'main')
    
    # Get session for this client
    session_id = client_sessions.get(request.sid)
    if not session_id:
        emit('output', [{'type': 'error', 'message': 'Session not found'}])
        return
    
    # Ensure session exists for this tab
    basic = session_manager.get_session(session_id, tab_id)
    
    # Send confirmation
    emit('tab_switched', {'tabId': tab_id})

@socketio.on('get_state')
def handle_get_state(data):
    """Get current state for a tab"""
    tab_id = data.get('tabId', 'main')
    
    # Get session for this client
    session_id = client_sessions.get(request.sid)
    if not session_id:
        return {'program': {}, 'variables': {}}
    
    # Get BASIC interpreter for this session/tab
    basic = session_manager.get_session(session_id, tab_id)
    
    return {
        'program': dict(basic.program),
        'variables': dict(basic.variables)
    }

@socketio.on('set_state')
def handle_set_state(data):
    """Set state for a tab"""
    tab_id = data.get('tabId', 'main')
    program = data.get('program', {})
    variables = data.get('variables', {})
    
    # Get session for this client
    session_id = client_sessions.get(request.sid)
    if not session_id:
        return
    
    # Get BASIC interpreter for this session/tab
    basic = session_manager.get_session(session_id, tab_id)
    
    # Set state
    basic.program = program
    basic.variables = variables
    
    # Expand program lines
    for line_num, code in program.items():
        basic.expand_line_to_sublines(int(line_num), code)

@socketio.on('continue_execution')
def handle_continue_execution(data=None):
    """Continue program execution after a pause."""
    try:
        # Get tab ID from data or default to 'main'
        tab_id = data.get('tabId', 'main') if data else 'main'
        
        # Get session for this client
        session_id = client_sessions.get(request.sid)
        if not session_id:
            emit('output', [{'type': 'error', 'message': 'Session not found'}])
            return
        
        # Get BASIC interpreter for this session/tab
        basic = session_manager.get_session(session_id, tab_id)
        
        # Continue execution from where we left off
        if basic.program_counter:
            output = basic.continue_program_execution()
            emit('output', output)
            
            # Only send completion signal if program actually finished and no pause
            # (program_counter becomes None when program completes)
            has_pause = any(item.get('type') == 'pause' for item in output)
            if not has_pause and basic.program_counter is None:
                emit('output', [{'type': 'command_complete'}])
        else:
            # Silently ignore stray continue_execution calls (likely from cancelled pause timers)
            # This prevents confusing error messages when Ctrl+C interrupts a pause
            logger.debug("Ignoring stray continue_execution call for session %s, tab %s", session_id, tab_id)
            emit('output', [{'type': 'command_complete'}])
    except Exception as e:
        logger.error("Continue execution error: %s", e, exc_info=True)
        emit('output', [{'type': 'error', 'message': f'Continue execution error: {str(e)}'}])

@socketio.on('break_execution')
def handle_break_execution(data=None):
    """Break program execution (Ctrl+C)"""
    try:
        # Get tab ID from data or default to 'main'
        tab_id = data.get('tabId', 'main') if data else 'main'
        
        # Get session for this client
        session_id = client_sessions.get(request.sid)
        if not session_id:
            emit('output', [{'type': 'error', 'message': 'Session not found'}])
            return
        
        # Get BASIC interpreter for this session/tab
        basic = session_manager.get_session(session_id, tab_id)
        
        # Check if there was actually a program running
        was_running = basic.program_counter is not None or basic.waiting_for_input
        
        # Break program execution (safe to do even if nothing is running)
        basic.program_counter = None
        basic.waiting_for_input = False
        if hasattr(basic, 'input_variables'):
            basic.input_variables = None
            basic.input_prompt = None
            basic.current_input_index = 0
        
        # Send appropriate response based on whether something was actually interrupted
        if was_running:
            logger.debug("Program execution interrupted with Ctrl+C for session %s, tab %s", session_id, tab_id)
            emit('output', [
                {'type': 'text', 'text': '^C'},
                {'type': 'text', 'text': 'BREAK'},
                {'type': 'command_complete'}
            ])
        else:
            # Nothing was running, just acknowledge the break signal silently
            # (Could optionally emit nothing, or a different response)
            emit('output', [{'type': 'command_complete'}])
        
    except Exception as e:
        logger.error("Break execution error: %s", e, exc_info=True)


if __name__ == '__main__':
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    socketio.run(app, debug=debug, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)