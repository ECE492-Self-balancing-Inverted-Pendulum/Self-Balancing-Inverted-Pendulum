"""
Web Dashboard for Self-Balancing Robot

This module provides a simple web dashboard for the self-balancing robot,
displaying real-time angle data, target angle, and PID output.

It uses Flask for the web server and Socket.IO for real-time data transmission.
"""

import os
import json
import threading
import time
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO
from config import CONFIG, load_config

# Initialize Flask and SocketIO
app = Flask(__name__)
socketio = SocketIO(app)

# Global variables for data
latest_data = {
    'timestamp': 0,
    'angle': 0,
    'target_angle': 0,
    'output': 0
}

# Flag to track if the server is running
server_running = False
server_thread = None

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
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            margin-bottom: 20px;
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
        }
        .chart-container {
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            padding: 15px;
            margin-bottom: 20px;
            max-height: 400px; /* Control the height of the chart */
            width: 90%; /* Make chart smaller */
            margin: 0 auto 20px auto; /* Center the chart */
        }
        h2 {
            color: #555;
            margin-top: 0;
        }
        .chart-controls {
            text-align: center;
            margin-bottom: 20px;
        }
        button {
            margin: 0 5px;
            padding: 8px 15px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background: #45a049;
        }
    </style>
</head>
<body>
    <h1>PID Controller Dashboard
        <span class="status">Status: <span class="status-indicator">Connected</span></span>
    </h1>
    
    <div class="chart-container">
        <h2>Angle Data</h2>
        <canvas id="angleChart"></canvas>
    </div>
    
    <div class="chart-controls">
        <button id="reset-zoom">Reset Zoom</button>
    </div>
    
    <script>
        // Connect to Socket.IO server
        const socket = io();
        
        // Data arrays for chart
        const maxDataPoints = 100;
        const timeData = [];
        const angleData = [];
        const targetData = [];
        const outputData = [];
        
        // Initialize time counter
        let timeCounter = 0;
        
        // Create chart
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
                        tension: 0.2,
                        hidden: true
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
        
        // Reset zoom button
        document.getElementById('reset-zoom').addEventListener('click', function() {
            angleChart.resetZoom();
        });
        
        // Handle incoming data
        socket.on('update_data', function(data) {
            // Add new data
            timeCounter += 0.1;  // Approximate time (10Hz updates)
            timeData.push(timeCounter.toFixed(1));
            angleData.push(data.angle);
            targetData.push(data.target_angle);
            outputData.push(data.output / 10);  // Scale output to fit on same chart
            
            // Remove old data if we have too many points
            if (timeData.length > maxDataPoints) {
                timeData.shift();
                angleData.shift();
                targetData.shift();
                outputData.shift();
            }
            
            // Update chart
            angleChart.update('none'); // Use 'none' to disable animations for smoother updates
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
    return render_template_string(HTML_TEMPLATE)

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    # Send current data to newly connected client
    socketio.emit('update_data', latest_data, to=request.sid)

@socketio.on('request_initial_data')
def handle_initial_data_request():
    """Send initial data when requested by client."""
    socketio.emit('update_data', latest_data)

def send_data():
    """Send data to clients periodically."""
    global server_running
    print("Starting data broadcast thread...")
    
    # Send at least one data point even if there are no updates yet
    initial_data = latest_data.copy()
    initial_config = load_config()
    initial_data['target_angle'] = initial_config.get('SETPOINT', 0.0)
    socketio.emit('update_data', initial_data)
    
    data_points_sent = 0
    while server_running:
        try:
            # Load latest config to get target angle
            config = load_config()
            latest_data['target_angle'] = config.get('SETPOINT', 0.0)
            
            # Send latest data to all clients
            socketio.emit('update_data', latest_data)
            
            data_points_sent += 1
            if data_points_sent % 100 == 0:  # Log every 100 data points (approx. every 10 seconds)
                print(f"Sent {data_points_sent} data points to dashboard")
            
            # Sleep briefly
            socketio.sleep(0.1)
        except Exception as e:
            print(f"Error in send_data: {e}")
            socketio.sleep(1)  # Sleep longer on error

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
    
    # Start background thread for sending data
    socketio.start_background_task(send_data)
    
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
    print(f"Web dashboard server started successfully on port {port}")
    print(f"You can now connect to the dashboard from any browser on your network")

def stop_server():
    """Stop the web server."""
    global server_running
    server_running = False
    print("Web server stopping...")

def update_angle_data(roll, output):
    """
    Update the latest angle data.
    
    Args:
        roll: Current roll angle
        output: PID controller output
    """
    global latest_data
    latest_data['timestamp'] = time.time()
    latest_data['angle'] = roll
    latest_data['output'] = output

# For testing the server standalone
if __name__ == "__main__":
    start_server()
    print("Press Ctrl+C to stop")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_server() 