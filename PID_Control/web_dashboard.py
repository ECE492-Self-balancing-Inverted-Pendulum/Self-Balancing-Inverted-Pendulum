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
import copy
from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO
from config import load_config, save_config, DEFAULT_CONFIG

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

# Use a lock for config file operations to prevent corruption
config_lock = threading.Lock()

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

# Safe config loading/saving functions
def safe_load_config():
    """Thread-safe config loading with fallback"""
    with config_lock:
        try:
            return load_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            return copy.deepcopy(DEFAULT_CONFIG)

def safe_save_config(config):
    """Thread-safe config saving"""
    with config_lock:
        try:
            save_config(config)
            print(f"✅ PID parameters updated and saved: P={config.get('P_GAIN')}, I={config.get('I_GAIN')}, D={config.get('D_GAIN')}")
            return True
        except Exception as e:
            print(f"❌ Error saving config: {e}, Type: {type(e)}, File: {CONFIG_FILE}")
            print(f"Config data attempted to save: {config}")
            return False

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
            height: 400px; /* Increased height by 15% */
        }
        .pid-chart-container {
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            padding: 20px;
            margin-bottom: 20px;
            width: 100%;
            height: 350px; /* Increased height by 15% */
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
            margin-bottom: 40px; /* Added space between charts and controls */
            padding-top: 15px; /* Add padding to move reset button down */
        }
        .control-panel {
            display: grid;
            grid-template-columns: 1fr;
            gap: 20px;
            margin-bottom: 20px;
            margin-top: 40px; /* Moved controls lower */
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
        /* Joystick style control */
        .joystick-container {
            position: relative;
            width: 200px;
            height: 200px;
            margin: 20px auto;
            background-color: #f0f0f0;
            border-radius: 50%;
            overflow: hidden;
            touch-action: none;
            box-shadow: inset 0 0 10px rgba(0,0,0,0.1), 0 4px 8px rgba(0,0,0,0.1);
        }
        .joystick-knob {
            position: absolute;
            width: 80px;
            height: 80px;
            background-color: #2196F3;
            border-radius: 50%;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            cursor: pointer;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            transition: background-color 0.2s;
        }
        .joystick-knob:hover {
            background-color: #0b7dda;
        }
        .joystick-center {
            position: absolute;
            width: 20px;
            height: 20px;
            background-color: #fff;
            border-radius: 50%;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            pointer-events: none;
        }
        .joystick-horizontal-line {
            position: absolute;
            width: 100%;
            height: 2px;
            background-color: rgba(0,0,0,0.1);
            top: 50%;
            left: 0;
        }
        .joystick-vertical-line {
            position: absolute;
            width: 2px;
            height: 100%;
            background-color: rgba(0,0,0,0.1);
            left: 50%;
            top: 0;
        }
        .joystick-background {
            position: absolute;
            width: 100%;
            height: 100%;
            background: radial-gradient(circle, #ffffff 0%, #e0e0e0 100%);
            border-radius: 50%;
        }
        .manual-target {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 10px;
            margin-top: 20px;
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
        .reset-button {
            display: block;
            margin: 10px auto;
            padding: 8px 20px;
            background-color: #ff9800;
            color: white;
        }
        .reset-button:hover {
            background-color: #e68a00;
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
        /* Add notification styles */
        .notification {
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            padding: 10px 20px;
            border-radius: 5px;
            color: white;
            font-weight: bold;
            z-index: 9999;
            opacity: 0;
            transition: opacity 0.3s;
        }
        .success-notification {
            background-color: #4CAF50;
        }
        .error-notification {
            background-color: #f44336;
        }
        /* Add joystick range control styles */
        .joystick-range-controls {
            margin-bottom: 15px;
            padding: 10px;
            background-color: #f9f9f9;
            border-radius: 5px;
            border: 1px solid #ddd;
        }
        .range-control {
            display: flex;
            align-items: center;
            margin-bottom: 8px;
        }
        .range-control label {
            width: 120px;
            font-weight: 500;
        }
        .range-control input {
            flex: 1;
            padding: 6px 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        .range-button {
            padding: 5px 10px;
            margin-top: 5px;
            background-color: #3498db;
            font-size: 12px;
        }
        .range-button:hover {
            background-color: #2980b9;
        }
    </style>
</head>
<body>
    <header>
        <h1>PID Controller Dashboard</h1>
        <div class="status">Status: <span id="connection-status" class="status-indicator">Connected</span></div>
    </header>
    
    <!-- Add notification element -->
    <div id="notification" class="notification"></div>
    
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
            
            <!-- Joystick range controls -->
            <div class="joystick-range-controls">
                <div class="range-control">
                    <label for="joystick-min">Joystick Min (°):</label>
                    <input type="number" id="joystick-min" value="-1.5" step="0.5" min="-10" max="0">
                </div>
                <div class="range-control">
                    <label for="joystick-max">Joystick Max (°):</label>
                    <input type="number" id="joystick-max" value="1.5" step="0.5" min="0" max="10">
                </div>
                <div class="range-control">
                    <label for="joystick-middle">Joystick Middle (°):</label>
                    <input type="number" id="joystick-middle" value="0" step="0.5" min="-5" max="5">
                </div>
                <button id="update-joystick-range" class="range-button">Update Range</button>
            </div>
            
            <!-- Joystick control for direction -->
            <div class="joystick-container" id="joystick">
                <div class="joystick-background"></div>
                <div class="joystick-horizontal-line"></div>
                <div class="joystick-vertical-line"></div>
                <div class="joystick-knob" id="joystick-knob"></div>
                <div class="joystick-center"></div>
            </div>
            
            <button id="reset-target" class="reset-button">Reset Target Angle</button>
            
            <div class="manual-target">
                <label for="target-angle">Set Target Angle:</label>
                <input type="number" id="target-angle" value="{{ target_angle }}" step="0.5" min="-5" max="5">
                <button id="set-target" class="action-button">Set</button>
            </div>
        </div>
    </div>
    
    <footer>
        <p>Self-Balancing Robot Control System</p>
    </footer>
    
    <script>
        // Add notification function
        function showNotification(message, isSuccess) {
            const notification = document.getElementById('notification');
            notification.textContent = message;
            notification.className = 'notification ' + (isSuccess ? 'success-notification' : 'error-notification');
            notification.style.opacity = 1;
            
            setTimeout(() => {
                notification.style.opacity = 0;
            }, 3000);
        }

        // Connect to Socket.IO server with reconnection options
        const socket = io({
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            timeout: 20000
        });
        
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
        
        // Throttle control to prevent too many updates
        let lastTargetUpdate = 0;
        const TARGET_UPDATE_INTERVAL = 100; // ms
        
        // Connection status management
        socket.on('connect', function() {
            document.getElementById('connection-status').textContent = 'Connected';
            document.getElementById('connection-status').style.backgroundColor = '#4CAF50';
            showNotification('Connected to server', true);
        });
        
        socket.on('disconnect', function() {
            document.getElementById('connection-status').textContent = 'Disconnected';
            document.getElementById('connection-status').style.backgroundColor = '#f44336';
            showNotification('Disconnected from server - attempting to reconnect...', false);
        });
        
        socket.on('reconnect', function(attemptNumber) {
            showNotification('Reconnected to server after ' + attemptNumber + ' attempts', true);
        });
        
        socket.on('reconnect_failed', function() {
            showNotification('Failed to reconnect to server after multiple attempts', false);
        });
        
        socket.on('error', function(error) {
            showNotification('Connection error: ' + error, false);
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
                        tension: 0.4, // Increased for smoother curves
                        pointRadius: 0 // No points, just lines
                    },
                    {
                        label: 'Target Angle',
                        data: targetData,
                        borderColor: 'rgb(255, 99, 132)',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0,
                        pointRadius: 0, // No points, just lines
                        spanGaps: true // Connect the line across any null values
                    },
                    {
                        label: 'PID Output',
                        data: outputData,
                        borderColor: 'rgb(255, 159, 64)',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.4, // Increased for smoother curves
                        pointRadius: 0 // No points, just lines
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
                    duration: 0 // No animation for real-time updates
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
                        tension: 0.3, // Smoother curves
                        pointRadius: 0 // No points
                    },
                    {
                        label: 'I Term',
                        data: iTermData,
                        borderColor: 'rgb(54, 162, 235)',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.3, // Smoother curves
                        pointRadius: 0 // No points
                    },
                    {
                        label: 'D Term',
                        data: dTermData,
                        borderColor: 'rgb(255, 206, 86)',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.3, // Smoother curves
                        pointRadius: 0 // No points
                    },
                    {
                        label: 'Zero Line',
                        data: Array(pidTimeData.length).fill(0), // Create an array of zeros
                        borderColor: 'rgba(100, 100, 100, 0.5)', // Gray, semi-transparent
                        borderWidth: 1,
                        borderDash: [5, 5], // Dotted line
                        fill: false,
                        tension: 0,
                        pointRadius: 0,
                        order: 4 // Draw below other datasets
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
                plugins: {
                    legend: {
                        labels: {
                            filter: function(item, chart) {
                                // Don't show Zero Line in legend
                                return item.text !== 'Zero Line';
                            }
                        }
                    }
                },
                animation: {
                    duration: 0 // No animation for real-time updates
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
            
            // Disable the button during update
            const button = document.getElementById('update-pid');
            button.disabled = true;
            button.textContent = 'Updating...';
            
            // Send PID parameter update to server
            socket.emit('update_pid', {
                p_gain: pGain,
                i_gain: iGain,
                d_gain: dGain
            }, function(response) {
                // Re-enable button with feedback
                button.disabled = false;
                if (response && response.success) {
                    button.textContent = 'Updated!';
                    showNotification('PID Parameters Updated Successfully!', true);
                    setTimeout(() => {
                        button.textContent = 'Update PID Parameters';
                    }, 1500);
                } else {
                    button.textContent = 'Update Failed';
                    showNotification('Failed to update PID parameters: ' + (response && response.error ? response.error : 'Unknown error'), false);
                    setTimeout(() => {
                        button.textContent = 'Update PID Parameters';
                    }, 1500);
                }
            });
        });
        
        // Joystick control
        const joystick = document.getElementById('joystick');
        const knob = document.getElementById('joystick-knob');
        let isDragging = false;
        let centerX = joystick.offsetWidth / 2;
        let centerY = joystick.offsetHeight / 2;
        const radius = joystick.offsetWidth / 2 - knob.offsetWidth / 2;
        
        // Joystick range settings (default values)
        let joystickMinAngle = -1.5;
        let joystickMaxAngle = 1.5;
        let joystickMiddleAngle = 0;
        
        // Update joystick range from inputs
        document.getElementById('update-joystick-range').addEventListener('click', function() {
            const minValue = parseFloat(document.getElementById('joystick-min').value);
            const maxValue = parseFloat(document.getElementById('joystick-max').value);
            const middleValue = parseFloat(document.getElementById('joystick-middle').value);
            
            // Validate inputs
            if (isNaN(minValue) || isNaN(maxValue) || isNaN(middleValue)) {
                showNotification('Please enter valid numbers for all values', false);
                return;
            }
            
            if (minValue >= maxValue) {
                showNotification('Min value must be less than max value', false);
                return;
            }
            
            if (middleValue < minValue || middleValue > maxValue) {
                showNotification('Middle value must be between min and max values', false);
                return;
            }
            
            // Update joystick range
            joystickMinAngle = minValue;
            joystickMaxAngle = maxValue;
            joystickMiddleAngle = middleValue;
            
            showNotification(`Joystick range updated: ${joystickMinAngle}° to ${joystickMaxAngle}°, middle: ${joystickMiddleAngle}°`, true);
        });
        
        // Initialize knob at center
        knob.style.left = `${centerX}px`;
        knob.style.top = `${centerY}px`;
        
        // Handle joystick events
        joystick.addEventListener('mousedown', startDrag);
        joystick.addEventListener('touchstart', startDrag);
        document.addEventListener('mousemove', drag);
        document.addEventListener('touchmove', drag);
        document.addEventListener('mouseup', endDrag);
        document.addEventListener('touchend', endDrag);
        
        function startDrag(e) {
            isDragging = true;
            drag(e);
        }
        
        function drag(e) {
            if (!isDragging) return;
            
            e.preventDefault();
            
            // Get position
            let clientX, clientY;
            if (e.type.startsWith('touch')) {
                clientX = e.touches[0].clientX;
                clientY = e.touches[0].clientY;
            } else {
                clientX = e.clientX;
                clientY = e.clientY;
            }
            
            // Get joystick position
            const rect = joystick.getBoundingClientRect();
            const joystickX = clientX - rect.left;
            const joystickY = clientY - rect.top;
            
            // Calculate distance from center
            const deltaX = joystickX - centerX;
            const deltaY = joystickY - centerY;
            const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
            
            // Normalize to radius
            let newX, newY;
            if (distance > radius) {
                // Limit to the edge of the joystick
                const angle = Math.atan2(deltaY, deltaX);
                newX = centerX + radius * Math.cos(angle);
                newY = centerY + radius * Math.sin(angle);
            } else {
                newX = joystickX;
                newY = joystickY;
            }
            
            // Update knob position
            knob.style.left = `${newX}px`;
            knob.style.top = `${newY}px`;
            
            // Calculate angle control value (only using Y-axis)
            // Map from -1 to 1 based on the Y position
            const normalizedY = ((newY - centerY) / radius) * -1;
            
            // Map the normalized Y position to the angle range:
            // When normalizedY is -1, output should be joystickMinAngle
            // When normalizedY is 0, output should be joystickMiddleAngle
            // When normalizedY is 1, output should be joystickMaxAngle
            let mappedAngle;
            if (normalizedY >= 0) {
                // Map from 0 to 1 to middleAngle to maxAngle
                mappedAngle = joystickMiddleAngle + normalizedY * (joystickMaxAngle - joystickMiddleAngle);
            } else {
                // Map from -1 to 0 to minAngle to middleAngle
                mappedAngle = joystickMiddleAngle + normalizedY * (joystickMiddleAngle - joystickMinAngle);
            }
            
            // Calculate X-axis value for wheel differential control
            // Normalize to -1 to 1 for wheel differential
            const normalizedX = ((newX - centerX) / radius);
            
            // Update target angle if enough time has passed
            const now = Date.now();
            if (now - lastTargetUpdate > TARGET_UPDATE_INTERVAL) {
                updateTargetAngle(mappedAngle, true);
                
                // Send wheel differential command based on X-axis
                updateWheelDifferential(normalizedX);
                
                lastTargetUpdate = now;
            }
        }
        
        function endDrag() {
            if (!isDragging) return;
            isDragging = false;
            
            // Animate back to center
            knob.style.transition = 'left 0.2s, top 0.2s';
            knob.style.left = `${centerX}px`;
            knob.style.top = `${centerY}px`;
            
            // Reset transition after animation
            setTimeout(() => {
                knob.style.transition = '';
            }, 200);
            
            // Reset target angle to the middle value instead of 0
            updateTargetAngle(joystickMiddleAngle, true);
            
            // Reset wheel differential
            updateWheelDifferential(0);
        }
        
        // Function to update wheel differential based on joystick X position
        function updateWheelDifferential(xValue) {
            // Only apply differential if significant movement
            if (Math.abs(xValue) < 0.05) {
                xValue = 0;
            }
            
            // Send wheel differential command to server
            socket.emit('update_wheel_differential', {
                value: xValue
            }, function(response) {
                if (response && !response.success) {
                    showNotification('Failed to update wheel differential: ' + 
                        (response.error ? response.error : 'Unknown error'), false);
                }
            });
        }
        
        // Reset target angle button
        document.getElementById('reset-target').addEventListener('click', function() {
            updateTargetAngle(joystickMiddleAngle, true);
        });
        
        document.getElementById('set-target').addEventListener('click', function() {
            const targetAngle = parseFloat(document.getElementById('target-angle').value);
            updateTargetAngle(targetAngle);
        });
        
        function updateTargetAngle(angle, fromJoystick = false) {
            // Limit angle based on source: joystick or manual input (-5 to 5 degrees)
            if (fromJoystick) {
                // Use the custom range for joystick
                angle = Math.max(joystickMinAngle, Math.min(joystickMaxAngle, angle));
            } else {
                // Keep the manual range as before
                angle = Math.max(-5, Math.min(5, angle));
            }
            
            // Round to 1 decimal place for display
            const roundedAngle = Math.round(angle * 10) / 10;
            
            // Update input field
            document.getElementById('target-angle').value = roundedAngle.toFixed(1);
            
            // Send target angle update to server
            socket.emit('update_target_angle', {
                angle: roundedAngle
            }, function(response) {
                if (response && response.success) {
                    showNotification('Target angle updated to ' + roundedAngle.toFixed(1) + '°', true);
                } else {
                    showNotification('Failed to update target angle: ' + (response && response.error ? response.error : 'Unknown error'), false);
                }
            });
        }
        
        // Handle incoming data
        socket.on('update_data', function(data) {
            // Update target angle display
            document.getElementById('current-target').textContent = data.target_angle.toFixed(1);
            
            // Add new data to angle chart
            timeCounter += 0.05;  // 20Hz updates (double the previous rate)
            timeData.push(timeCounter.toFixed(1));
            angleData.push(data.angle);
            
            // For target, use a fixed value rather than a time series
            // This creates a straight dotted line across the chart
            targetData.push(data.target_angle);
            
            // Scale output to fit better with angle scale
            outputData.push(data.output / 10);
            
            // Add new data to PID components chart
            pidTimeData.push(timeCounter.toFixed(1));
            pTermData.push(data.pid.p_term);
            iTermData.push(data.pid.i_term);
            dTermData.push(data.pid.d_term);
            
            // Ensure zero line dataset has same number of points
            if (pidChart.data.datasets[3]) {
                pidChart.data.datasets[3].data.push(0);
            }
            
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
                
                // Keep zero line dataset in sync
                if (pidChart.data.datasets[3]) {
                    pidChart.data.datasets[3].data.shift();
                }
            }
            
            // Update charts without animation for smooth real-time display
            angleChart.update('none');
            pidChart.update('none');
        });
        
        // Handle PID parameter updates
        socket.on('pid_updated', function(data) {
            document.getElementById('p-gain').value = data.p_gain;
            document.getElementById('i-gain').value = data.i_gain;
            document.getElementById('d-gain').value = data.d_gain;
        });
        
        // Handle window resize to update joystick dimensions
        window.addEventListener('resize', function() {
            centerX = joystick.offsetWidth / 2;
            centerY = joystick.offsetHeight / 2;
            knob.style.left = `${centerX}px`;
            knob.style.top = `${centerY}px`;
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
    config = safe_load_config()
    
    # Use target_angle if it exists, otherwise fall back to SETPOINT
    target_angle = config.get('target_angle', config.get('SETPOINT', 0))
    
    return render_template_string(HTML_TEMPLATE, 
                                 p_gain=config.get('P_GAIN', 0),
                                 i_gain=config.get('I_GAIN', 0),
                                 d_gain=config.get('D_GAIN', 0),
                                 target_angle=target_angle)

@socketio.on('connect')
def handle_connect(auth=None):
    """Handle client connection."""
    # Send current data to newly connected client
    data_to_send = convert_numpy_to_python(latest_data)
    socketio.emit('update_data', data_to_send, to=request.sid)
    
    # Also send current PID parameters
    config = safe_load_config()
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
        # Print received data for debugging
        print(f"Received PID update request: {data}")
        
        # Update config
        config = safe_load_config()
        print(f"Current config before update: P={config.get('P_GAIN')}, I={config.get('I_GAIN')}, D={config.get('D_GAIN')}")
        
        if 'p_gain' in data:
            config['P_GAIN'] = float(data['p_gain'])
        if 'i_gain' in data:
            config['I_GAIN'] = float(data['i_gain'])
        if 'd_gain' in data:
            config['D_GAIN'] = float(data['d_gain'])
        
        print(f"Updated config values: P={config.get('P_GAIN')}, I={config.get('I_GAIN')}, D={config.get('D_GAIN')}")
        
        # Save config
        success = safe_save_config(config)
        
        # Broadcast the updated parameters to all clients if saved successfully
        if success:
            socketio.emit('pid_updated', {
                'p_gain': config.get('P_GAIN', 0),
                'i_gain': config.get('I_GAIN', 0),
                'd_gain': config.get('D_GAIN', 0)
            })
            print("PID parameters successfully broadcast to all clients")
        else:
            print("Failed to save PID parameters - configuration not updated")
        
        return {'success': success}
    except Exception as e:
        print(f"❌ Error updating PID parameters: {e}, Type: {type(e)}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

@socketio.on('update_target_angle')
def handle_target_angle_update(data):
    """Handle target angle update."""
    try:
        # Update config
        angle = float(data['angle'])
        config = safe_load_config()
        # Use target_angle instead of SETPOINT to match the config file
        config['target_angle'] = angle
        success = safe_save_config(config)
        
        # Update latest data
        latest_data['target_angle'] = angle
        
        if success:
            print(f"✅ Target angle updated to: {angle}")
            return {'success': True}
        else:
            print(f"❌ Failed to update target angle to: {angle}")
            return {'success': False, 'error': 'Failed to save configuration'}
    except Exception as e:
        print(f"❌ Error updating target angle: {e}, Type: {type(e)}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

@socketio.on('update_wheel_differential')
def handle_wheel_differential(data):
    """Handle wheel differential control from joystick X-axis."""
    try:
        # Get the x-axis value (-1 to 1)
        x_value = float(data.get('value', 0))
        
        # Calculate differential power (25 PWM max)
        differential_power = abs(x_value) * 25
        
        # Determine which wheel gets the power based on direction
        if x_value > 0:
            # Positive X is right movement - apply to right wheel
            left_power = 0
            right_power = differential_power
        elif x_value < 0:
            # Negative X is left movement - apply to left wheel
            left_power = differential_power
            right_power = 0
        else:
            # Centered - no differential
            left_power = 0
            right_power = 0
        
        # Store values for debug/display
        latest_data['wheel_differential'] = {
            'x_value': x_value,
            'left_power': left_power,
            'right_power': right_power
        }
        
        # Update global variable to indicate differential control is active
        # This will be checked by the balance controller
        latest_data['differential_active'] = (left_power > 0 or right_power > 0)
        latest_data['left_wheel_power'] = left_power
        latest_data['right_wheel_power'] = right_power
        
        print(f"🎮 Wheel differential: x={x_value:.2f}, L={left_power:.1f}, R={right_power:.1f}")
        
        return {'success': True}
    except Exception as e:
        print(f"❌ Error updating wheel differential: {e}")
        return {'success': False, 'error': str(e)}

def send_data():
    """Send data to clients periodically."""
    global server_running
    
    # Initial data point
    initial_config = safe_load_config()
    latest_data['target_angle'] = initial_config.get('target_angle', 0.0)  # Use target_angle instead of SETPOINT
    data_to_send = convert_numpy_to_python(latest_data)
    socketio.emit('update_data', data_to_send)
    
    while server_running:
        try:
            # Load latest config to get target angle
            config = safe_load_config()
            latest_data['target_angle'] = config.get('target_angle', 0.0)  # Use target_angle instead of SETPOINT
            
            # Convert any NumPy types to standard Python types for JSON serialization
            data_to_send = convert_numpy_to_python(latest_data)
            
            # Send latest data to all clients
            socketio.emit('update_data', data_to_send)
            
            # Sleep briefly
            time.sleep(0.05)  
        except Exception as e:
            print(f"❌ Error in send_data: {e}, Type: {type(e)}")
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
    config = safe_load_config()
    latest_data['target_angle'] = config.get('target_angle', 0.0)  # Use target_angle instead of SETPOINT
    
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
    config = safe_load_config()
    
    # Convert any NumPy types to standard Python types
    roll = float(roll) if roll is not None else 0.0
    output = float(output) if output is not None else 0.0
    angular_velocity = float(angular_velocity) if angular_velocity is not None else 0.0
    
    # Track time delta for I term calculation
    current_time = time.time()
    dt = current_time - latest_data.get('timestamp', current_time)
    
    # Calculate error (target - current)
    error = latest_data.get('target_angle', 0) - roll
    
    # Approximate I term by accumulating error over time (if we have a previous i_term)
    if 'pid' in latest_data and 'i_term' in latest_data['pid']:
        # Get I gain from config
        i_gain = config.get('I_GAIN', 0.1)
        # Calculate I term based on accumulated error
        i_term = latest_data['pid']['i_term'] + (i_gain * error * dt)
        # Apply rudimentary anti-windup (limit the I term)
        max_i = config.get('MAX_I_TERM', 20.0)
        i_term = max(-max_i, min(i_term, max_i))
    else:
        # If no previous I term, start with a simple approximation
        i_term = config.get('I_GAIN', 0.1) * error
    
    # Calculate P and D terms
    p_term = float(config.get('P_GAIN', 0) * roll)
    d_term = float(config.get('D_GAIN', 0) * angular_velocity)
    
    # Update latest data
    latest_data.update({
        'timestamp': current_time,
        'angle': roll,
        'output': output,
        'pid': {
            'p_term': p_term,
            'i_term': i_term,
            'd_term': d_term
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
            time.sleep(0.1)
    except KeyboardInterrupt:
        stop_server()
        print("Server stopped") 