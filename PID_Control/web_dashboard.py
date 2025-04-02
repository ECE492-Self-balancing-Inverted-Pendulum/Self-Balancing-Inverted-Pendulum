"""
Web Dashboard for Self-Balancing Robot

This module provides a web dashboard for the self-balancing robot,
displaying real-time angle data, target angle, and PID output.
It also allows for adjusting PID parameters and target angle.

It uses Flask for the web server and Socket.IO for real-time data transmission.
"""

import os
import json
import threading
import time
import numpy as np
from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO
from config import load_config, save_config

# Initialize Flask and SocketIO
app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading')

# Global variables for data
latest_data = {
    'timestamp': time.time(),
    'angle': 0,
    'target_angle': 0,
    'output': 0,
    'pid': {
        'p_term': 0,
        'i_term': 0,
        'd_term': 0
    }
}

# Flag to track if the server is running
server_running = False
server_thread = None

# Helper function to convert NumPy values to Python types
def convert_numpy_to_python(obj):
    """Convert NumPy types to standard Python types for JSON serialization."""
    if isinstance(obj, (np.integer, np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy_to_python(v) for k, v in obj.items()}
    elif isinstance(obj, list) or isinstance(obj, tuple):
        return [convert_numpy_to_python(i) for i in obj]
    else:
        return obj

# HTML template with JavaScript for the dashboard
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PID Controller Dashboard</title>
    <script src="https://cdn.socket.io/4.6.0/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/hammerjs@2.0.8"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@1.2.1"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
            margin: 0;
        }
        h1 {
            color: #333;
            margin-bottom: 20px;
            font-size: 28px;
            font-weight: 500;
            display: inline-block;
        }
        .status {
            float: right;
            font-size: 16px;
            margin-top: 10px;
        }
        .status-indicator {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 15px;
            background-color: #4CAF50;
            color: white;
            font-weight: 500;
        }
        .chart-container {
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            padding: 20px;
            margin-bottom: 20px;
            width: 100%;
            height: 350px;
        }
        .pid-chart-container {
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            padding: 20px;
            margin-bottom: 20px;
            width: 100%;
            height: 300px;
        }
        h2 {
            color: #555;
            margin-top: 0;
            margin-bottom: 15px;
            font-size: 20px;
            font-weight: 500;
        }
        .chart-controls {
            text-align: center;
            margin-top: 15px;
        }
        .control-panel {
            display: grid;
            grid-template-columns: 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        @media (min-width: 768px) {
            .control-panel {
                grid-template-columns: 1fr 1fr;
            }
        }
        .pid-controls, .target-controls {
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            padding: 20px;
        }
        .pid-parameter {
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }
        .pid-parameter label {
            width: 80px;
            font-weight: 500;
        }
        .pid-parameter input {
            flex: 1;
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
        }
        .target-angle-display {
            margin-bottom: 15px;
            font-size: 18px;
        }
        .target-angle-buttons {
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
        }
        .direction-button {
            flex: 1;
            margin: 0 5px;
            padding: 10px;
            background-color: #2196F3;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.2s;
        }
        .direction-button:hover {
            background-color: #0b7dda;
        }
        #reset-target {
            background-color: #ff9800;
        }
        #reset-target:hover {
            background-color: #e68a00;
        }
        .manual-target {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 10px;
            margin-top: 15px;
        }
        .manual-target label {
            width: 100%;
            font-weight: 500;
        }
        .manual-target input {
            flex: 1;
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
        }
        .action-button {
            padding: 10px 15px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.2s;
        }
        .action-button:hover {
            background-color: #45a049;
        }
        button {
            padding: 8px 15px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.2s;
        }
        button:hover {
            background: #45a049;
        }
        footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            color: #777;
        }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid #e0e0e0;
        }
    </style>
</head>
<body>
    <header>
        <h1>PID Controller Dashboard</h1>
        <div class="status">Status: <span id="connection-status" class="status-indicator">Connected</span></div>
    </header>
    
    <div class="chart-container">
        <h2>Angle Data</h2>
        <canvas id="angleChart"></canvas>
    </div>
    
    <div class="chart-controls">
        <button id="reset-zoom">Reset Zoom</button>
    </div>
    
    <div class="pid-chart-container">
        <h2>PID Components</h2>
        <canvas id="pidComponentsChart"></canvas>
    </div>
    
    <div class="control-panel">
        <div class="pid-controls">
            <h2>PID Parameters</h2>
            <div class="pid-parameter">
                <label for="p-gain">P Gain:</label>
                <input type="number" id="p-gain" value="{{ p_gain }}" step="0.1" min="0" max="20">
            </div>
            <div class="pid-parameter">
                <label for="i-gain">I Gain:</label>
                <input type="number" id="i-gain" value="{{ i_gain }}" step="0.05" min="0" max="5">
            </div>
            <div class="pid-parameter">
                <label for="d-gain">D Gain:</label>
                <input type="number" id="d-gain" value="{{ d_gain }}" step="0.1" min="0" max="10">
            </div>
            <button id="update-pid" class="action-button">Update PID Parameters</button>
        </div>

        <div class="target-controls">
            <h2>Target Angle Control</h2>
            <div class="target-angle-display">
                <span>Current Target Angle: <span id="current-target">{{ target_angle }}</span>°</span>
            </div>
            <div class="target-angle-buttons">
                <button id="forward" class="direction-button">Forward</button>
                <button id="reset-target" class="direction-button">Reset</button>
                <button id="backward" class="direction-button">Backward</button>
            </div>
            <div class="manual-target">
                <label for="target-angle">Set Target Angle:</label>
                <input type="number" id="target-angle" value="{{ target_angle }}" step="0.5" min="-10" max="10">
                <button id="set-target" class="action-button">Set</button>
            </div>
        </div>
    </div>
    
    <footer>
        <p>Self-Balancing Robot Control System</p>
    </footer>
    
    <script>
        // Connect to Socket.IO server
        const socket = io();
        
        // Data arrays for angle chart
        const maxDataPoints = 100;
        const timeData = [];
        const angleData = [];
        const targetData = [];
        const outputData = [];
        
        // Data arrays for PID components chart
        const pidTimeData = [];
        const pTermData = [];
        const iTermData = [];
        const dTermData = [];
        
        // Initialize time counter
        let timeCounter = 0;
        
        // Connection status management
        socket.on('connect', function() {
            document.getElementById('connection-status').textContent = 'Connected';
            document.getElementById('connection-status').style.backgroundColor = '#4CAF50';
        });
        
        socket.on('disconnect', function() {
            document.getElementById('connection-status').textContent = 'Disconnected';
            document.getElementById('connection-status').style.backgroundColor = '#f44336';
        });
        
        // Create angle chart
        const ctx = document.getElementById('angleChart').getContext('2d');
        const angleChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: timeData,
                datasets: [
                    {
                        label: 'Actual Angle',
                        data: angleData,
                        borderColor: 'rgb(75, 192, 192)',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.2
                    },
                    {
                        label: 'Target Angle',
                        data: targetData,
                        borderColor: 'rgb(255, 99, 132)',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0
                    },
                    {
                        label: 'PID Output',
                        data: outputData,
                        borderColor: 'rgb(255, 159, 64)',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Time (s)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Angle (degrees)'
                        }
                    }
                },
                animation: {
                    duration: 0
                },
                plugins: {
                    zoom: {
                        pan: {
                            enabled: true,
                            mode: 'xy'
                        },
                        zoom: {
                            wheel: {
                                enabled: true
                            },
                            pinch: {
                                enabled: true
                            },
                            mode: 'xy'
                        }
                    }
                }
            }
        });
        
        // Create PID components chart
        const pidCtx = document.getElementById('pidComponentsChart').getContext('2d');
        const pidChart = new Chart(pidCtx, {
            type: 'line',
            data: {
                labels: pidTimeData,
                datasets: [
                    {
                        label: 'P Term',
                        data: pTermData,
                        borderColor: 'rgb(255, 99, 132)',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.1
                    },
                    {
                        label: 'I Term',
                        data: iTermData,
                        borderColor: 'rgb(54, 162, 235)',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.1
                    },
                    {
                        label: 'D Term',
                        data: dTermData,
                        borderColor: 'rgb(255, 206, 86)',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Time (s)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'PID Terms'
                        }
                    }
                },
                animation: {
                    duration: 0
                }
            }
        });
        
        // Reset zoom button
        document.getElementById('reset-zoom').addEventListener('click', function() {
            angleChart.resetZoom();
        });
        
        // Update PID parameters button
        document.getElementById('update-pid').addEventListener('click', function() {
            const pGain = parseFloat(document.getElementById('p-gain').value);
            const iGain = parseFloat(document.getElementById('i-gain').value);
            const dGain = parseFloat(document.getElementById('d-gain').value);
            
            // Send PID parameter update to server
            socket.emit('update_pid', {
                p_gain: pGain,
                i_gain: iGain,
                d_gain: dGain
            });
        });
        
        // Target angle control buttons
        document.getElementById('forward').addEventListener('click', function() {
            const currentTarget = parseFloat(document.getElementById('current-target').textContent);
            const newTarget = Math.min(currentTarget + 1, 10);
            updateTargetAngle(newTarget);
        });
        
        document.getElementById('backward').addEventListener('click', function() {
            const currentTarget = parseFloat(document.getElementById('current-target').textContent);
            const newTarget = Math.max(currentTarget - 1, -10);
            updateTargetAngle(newTarget);
        });
        
        document.getElementById('reset-target').addEventListener('click', function() {
            updateTargetAngle(0);
        });
        
        document.getElementById('set-target').addEventListener('click', function() {
            const targetAngle = parseFloat(document.getElementById('target-angle').value);
            updateTargetAngle(targetAngle);
        });
        
        function updateTargetAngle(angle) {
            // Send target angle update to server
            socket.emit('update_target_angle', {
                angle: angle
            });
        }
        
        // Handle incoming data
        socket.on('update_data', function(data) {
            // Update target angle display
            document.getElementById('current-target').textContent = data.target_angle.toFixed(1);
            document.getElementById('target-angle').value = data.target_angle.toFixed(1);
            
            // Add new data to angle chart
            timeCounter += 0.1;  // Approximate time (10Hz updates)
            timeData.push(timeCounter.toFixed(1));
            angleData.push(data.angle);
            targetData.push(data.target_angle);
            outputData.push(data.output / 10);  // Scale output to fit on same chart
            
            // Add new data to PID components chart
            pidTimeData.push(timeCounter.toFixed(1));
            pTermData.push(data.pid.p_term);
            iTermData.push(data.pid.i_term);
            dTermData.push(data.pid.d_term);
            
            // Remove old data if we have too many points
            if (timeData.length > maxDataPoints) {
                timeData.shift();
                angleData.shift();
                targetData.shift();
                outputData.shift();
                
                pidTimeData.shift();
                pTermData.shift();
                iTermData.shift();
                dTermData.shift();
            }
            
            // Update charts
            angleChart.update('none'); // Use 'none' to disable animations for smoother updates
            pidChart.update('none');
        });
        
        // Handle PID parameter updates
        socket.on('pid_updated', function(data) {
            document.getElementById('p-gain').value = data.p_gain;
            document.getElementById('i-gain').value = data.i_gain;
            document.getElementById('d-gain').value = data.d_gain;
        });
        
        // Send a message to request any available data immediately
        socket.emit('request_initial_data');
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Render the dashboard page."""
    config = load_config()
    return render_template_string(HTML_TEMPLATE, 
                                 p_gain=config.get('P_GAIN', 0),
                                 i_gain=config.get('I_GAIN', 0),
                                 d_gain=config.get('D_GAIN', 0),
                                 target_angle=config.get('SETPOINT', 0))

@socketio.on('connect')
def handle_connect(auth=None):
    """Handle client connection."""
    # Send current data to newly connected client
    data_to_send = convert_numpy_to_python(latest_data)
    socketio.emit('update_data', data_to_send, to=request.sid)
    
    # Also send current PID parameters
    config = load_config()
    socketio.emit('pid_updated', {
        'p_gain': config.get('P_GAIN', 0),
        'i_gain': config.get('I_GAIN', 0),
        'd_gain': config.get('D_GAIN', 0)
    }, to=request.sid)

@socketio.on('request_initial_data')
def handle_initial_data_request():
    """Send initial data when requested by client."""
    data_to_send = convert_numpy_to_python(latest_data)
    socketio.emit('update_data', data_to_send)

@socketio.on('update_pid')
def handle_pid_update(data):
    """Handle PID parameter update."""
    try:
        # Update config
        config = load_config()
        if 'p_gain' in data:
            config['P_GAIN'] = float(data['p_gain'])
        if 'i_gain' in data:
            config['I_GAIN'] = float(data['i_gain'])
        if 'd_gain' in data:
            config['D_GAIN'] = float(data['d_gain'])
        
        # Save config
        save_config(config)
        
        # Broadcast the updated parameters to all clients
        socketio.emit('pid_updated', {
            'p_gain': config.get('P_GAIN', 0),
            'i_gain': config.get('I_GAIN', 0),
            'd_gain': config.get('D_GAIN', 0)
        })
        
        return {'success': True}
    except Exception as e:
        print(f"Error updating PID parameters: {e}")
        return {'success': False, 'error': str(e)}

@socketio.on('update_target_angle')
def handle_target_angle_update(data):
    """Handle target angle update."""
    try:
        # Update config
        angle = float(data['angle'])
        config = load_config()
        config['SETPOINT'] = angle
        save_config(config)
        
        # Update latest data
        latest_data['target_angle'] = angle
        
        return {'success': True}
    except Exception as e:
        print(f"Error updating target angle: {e}")
        return {'success': False, 'error': str(e)}

def send_data():
    """Send data to clients periodically."""
    global server_running
    
    # Initial data point
    initial_config = load_config()
    latest_data['target_angle'] = initial_config.get('SETPOINT', 0.0)
    data_to_send = convert_numpy_to_python(latest_data)
    socketio.emit('update_data', data_to_send)
    
    while server_running:
        try:
            # Load latest config to get target angle
            config = load_config()
            latest_data['target_angle'] = config.get('SETPOINT', 0.0)
            
            # Convert any NumPy types to standard Python types for JSON serialization
            data_to_send = convert_numpy_to_python(latest_data)
            
            # Send latest data to all clients
            socketio.emit('update_data', data_to_send)
            
            # Sleep briefly
            time.sleep(0.1)  # 10Hz update rate
        except Exception as e:
            print(f"Error in send_data: {e}")
            time.sleep(1)  # Sleep longer on error

def start_server(host='0.0.0.0', port=8080):
    """
    Start the web server in a background thread.
    
    Args:
        host: Host address to bind to
        port: Port to listen on
    """
    global server_running, server_thread
    
    if server_running:
        print("Server already running")
        return
    
    server_running = True
    
    # Initialize data with current config values
    config = load_config()
    latest_data['target_angle'] = config.get('SETPOINT', 0.0)
    
    # Start data sending thread
    data_thread = threading.Thread(target=send_data, daemon=True)
    data_thread.start()
    
    # Start server in a separate thread
    server_thread = threading.Thread(
        target=socketio.run,
        args=(app,),
        kwargs={
            'host': host, 
            'port': port, 
            'debug': False,
            'use_reloader': False,
            'allow_unsafe_werkzeug': True  # For newer Flask versions
        }
    )
    server_thread.daemon = True
    server_thread.start()
    print(f"Web dashboard server started on port {port}")

def stop_server():
    """Stop the web server."""
    global server_running
    server_running = False
    print("Web server stopping...")

def update_angle_data(roll, output, angular_velocity=0):
    """
    Update the latest angle data.
    
    Args:
        roll: Current roll angle in degrees
        output: PID controller output
        angular_velocity: Angular velocity in degrees per second (optional)
    """
    global latest_data
    
    # Get PID components from PIDController if available
    config = load_config()
    
    # Convert any NumPy types to standard Python types
    roll = float(roll) if roll is not None else 0.0
    output = float(output) if output is not None else 0.0
    angular_velocity = float(angular_velocity) if angular_velocity is not None else 0.0
    
    # Update latest data
    latest_data.update({
        'timestamp': float(time.time()),
        'angle': roll,
        'output': output,
        'pid': {
            'p_term': float(config.get('P_GAIN', 0) * roll),  # Approximate P term
            'i_term': 0.0,  # We don't have access to I term directly
            'd_term': float(config.get('D_GAIN', 0) * angular_velocity)  # Approximate D term
        }
    })

# For testing the server standalone
if __name__ == "__main__":
    start_server()
    print("Press Ctrl+C to stop")
    try:
        import random
        while True:
            # Simulate random data for testing
            angle = random.uniform(-10, 10)
            velocity = random.uniform(-20, 20)
            output = random.uniform(-100, 100)
            update_angle_data(angle, output, velocity)
            time.sleep(0.2)
    except KeyboardInterrupt:
        stop_server()
        print("Server stopped") 