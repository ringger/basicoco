from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from emulator.core import CoCoBasic

app = Flask(__name__)
app.config['SECRET_KEY'] = 'trs80-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Output callback for real-time streaming
def output_callback(output):
    """Emit output to all connected clients in real-time"""
    socketio.emit('output', output)

# Global BASIC interpreter instance with streaming callback
basic = CoCoBasic(output_callback=output_callback)

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
    else:
        # Execute immediate command
        try:
            output = basic.execute_command(command)
            emit('output', output)
        except Exception as e:
            emit('output', [{'type': 'error', 'message': f'Error: {str(e)}'}])

@socketio.on('input_response')
def handle_input_response(data):
    variable = data.get('variable', '')
    value = data.get('value', '')
    
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
        if basic.program_counter:
            basic.waiting_for_input = False
            output = basic.continue_execution()
            emit('output', output)
        
    except Exception as e:
        emit('output', [{'type': 'error', 'message': f'Input error: {str(e)}'}])

@socketio.on('keypress')
def handle_keypress(data):
    key = data.get('key', '')
    # Add the key to the keyboard buffer for INKEY$ function
    basic.keyboard_buffer.append(key)

@socketio.on('connect')
def on_connect():
    print('Client connected')

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)