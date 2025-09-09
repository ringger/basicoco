from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from emulator.core import CoCoBasic

app = Flask(__name__)
app.config['SECRET_KEY'] = 'trs80-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Output callback for real-time streaming
def output_callback(output):
    """Emit output to all connected clients in real-time"""
    # Note: This callback isn't working properly in WebSocket context
    # Real-time streaming is handled in handle_command instead
    pass

# Global BASIC interpreter instance with streaming callback
basic = CoCoBasic(output_callback=output_callback)

@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('execute_command')
def handle_command(data):
    command = data.get('command', '')
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
            output = basic.execute_command(command)
            emit('output', output)
            
            # Only send completion signal if command actually finished (no pause or input request)
            has_pause = any(item.get('type') == 'pause' for item in output)
            has_input_request = any(item.get('type') == 'input_request' for item in output)
            if not has_pause and not has_input_request:
                emit('output', [{'type': 'command_complete'}])
                
        except Exception as e:
            emit('output', [{'type': 'error', 'message': f'Error: {str(e)}'}])

@socketio.on('input_response')
def handle_input_response(data):
    variable = data.get('variable', '')
    value = data.get('value', '')
    
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
    key = data.get('key', '')
    # Add the key to the keyboard buffer for INKEY$ function
    basic.keyboard_buffer.append(key)

@socketio.on('continue_execution')
def handle_continue_execution():
    """Continue program execution after a pause."""
    try:
        # Continue execution from where we left off
        if basic.program_counter:
            output = basic.continue_program_execution()
            emit('output', output)
            
            # Only send completion signal if program actually finished and no pause
            # (program_counter becomes None when program completes)
            has_pause = any(item.get('type') == 'pause' for item in output)
            if not has_pause and basic.program_counter is None:
                emit('output', [{'type': 'command_complete'}])
    except Exception as e:
        emit('output', [{'type': 'error', 'message': f'Continue execution error: {str(e)}'}])

@socketio.on('connect')
def on_connect():
    print('Client connected')

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)