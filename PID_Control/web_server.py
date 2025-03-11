from flask import Flask, render_template, jsonify, request
import threading
import time
import json
import os
import csv
import datetime
import numpy as np

# Global variables to store data
pid_data = {
    'time': [],
    'actual_angle': [],
    'target_angle': [],
    'pid_error': [],
    'p_term': [],
    'i_term': [],
    'd_term': [],
    'pid_output': [],
    'max_data_points': 300  # Keep 300 data points (30 seconds at 10Hz)
}

# Configuration settings that can be adjusted from web UI
web_config = {
    'time_window': 10,  # Default time window in seconds
    'update_interval': 200,  # Update interval in milliseconds
    'is_running': False,
    'csv_logging': True
}

# Lock for thread-safe access to data
data_lock = threading.Lock()

app = Flask(__name__)

# Ensure the static and templates directories exist
os.makedirs('static', exist_ok=True)
os.makedirs('templates', exist_ok=True)

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html', config=web_config)

@app.route('/data')
def get_data():
    """API endpoint to get the current PID data"""
    with data_lock:
        # Calculate how many data points to return based on time window
        points_to_return = min(len(pid_data['time']), 
                              int(web_config['time_window'] * 10))  # Assuming 10Hz data rate
        
        if points_to_return == 0:
            return jsonify({
                'time': [],
                'actual_angle': [],
                'target_angle': [],
                'pid_error': [],
                'p_term': [],
                'i_term': [],
                'd_term': [],
                'pid_output': []
            })
        
        return jsonify({
            'time': pid_data['time'][-points_to_return:],
            'actual_angle': pid_data['actual_angle'][-points_to_return:],
            'target_angle': pid_data['target_angle'][-points_to_return:],
            'pid_error': pid_data['pid_error'][-points_to_return:],
            'p_term': pid_data['p_term'][-points_to_return:],
            'i_term': pid_data['i_term'][-points_to_return:],
            'd_term': pid_data['d_term'][-points_to_return:],
            'pid_output': pid_data['pid_output'][-points_to_return:]
        })

@app.route('/config', methods=['GET', 'POST'])
def config():
    """API endpoint to get or update configuration"""
    global web_config
    
    if request.method == 'POST':
        data = request.get_json()
        with data_lock:
            if 'time_window' in data:
                web_config['time_window'] = int(data['time_window'])
            if 'update_interval' in data:
                web_config['update_interval'] = int(data['update_interval'])
            if 'csv_logging' in data:
                web_config['csv_logging'] = bool(data['csv_logging'])
        return jsonify({"status": "success"})
    else:
        return jsonify(web_config)

@app.route('/pid_params', methods=['GET', 'POST'])
def pid_params():
    """API endpoint to get or update PID parameters"""
    from config import CONFIG, save_config
    
    if request.method == 'POST':
        data = request.get_json()
        updated = False
        
        # Update the configuration
        if 'p_gain' in data:
            CONFIG['P_GAIN'] = float(data['p_gain'])
            updated = True
        if 'i_gain' in data:
            CONFIG['I_GAIN'] = float(data['i_gain'])
            updated = True
        if 'd_gain' in data:
            CONFIG['D_GAIN'] = float(data['d_gain'])
            updated = True
        if 'alpha' in data:
            CONFIG['IMU_FILTER_ALPHA'] = float(data['alpha'])
            updated = True
        if 'direction_change_boost' in data:
            CONFIG['DIRECTION_CHANGE_BOOST'] = float(data['direction_change_boost'])
            updated = True
        if 'sample_time' in data:
            CONFIG['SAMPLE_TIME'] = float(data['sample_time'])
            updated = True
            
        # Save the configuration if it was updated
        if updated:
            save_config(CONFIG)
            
        return jsonify({"status": "success"})
    else:
        from config import CONFIG
        # Return the current PID parameters
        return jsonify({
            'p_gain': CONFIG.get('P_GAIN', 0),
            'i_gain': CONFIG.get('I_GAIN', 0),
            'd_gain': CONFIG.get('D_GAIN', 0),
            'alpha': CONFIG.get('IMU_FILTER_ALPHA', 0.3),
            'direction_change_boost': CONFIG.get('DIRECTION_CHANGE_BOOST', 20.0),
            'sample_time': CONFIG.get('SAMPLE_TIME', 0.01)
        })

@app.route('/restart_pid', methods=['POST'])
def restart_pid():
    """API endpoint to restart the PID controller"""
    global pid_data
    
    # Notify the main thread to restart the PID controller
    web_config['restart_requested'] = True
    
    # Clear the data
    with data_lock:
        for key in pid_data:
            if key != 'max_data_points':
                pid_data[key] = []
    
    return jsonify({"status": "success"})

def add_data_point(actual_angle, target_angle, pid_error, p_term, i_term, d_term, pid_output):
    """
    Add a new data point to the data store
    
    Args:
        actual_angle: Current angle from the IMU
        target_angle: Target angle (setpoint)
        pid_error: Current error (target - actual)
        p_term: Proportional term
        i_term: Integral term
        d_term: Derivative term
        pid_output: Overall PID output
    """
    current_time = time.time()
    
    with data_lock:
        # Add new data
        pid_data['time'].append(current_time)
        pid_data['actual_angle'].append(actual_angle)
        pid_data['target_angle'].append(target_angle)
        pid_data['pid_error'].append(pid_error)
        pid_data['p_term'].append(p_term)
        pid_data['i_term'].append(i_term)
        pid_data['d_term'].append(d_term)
        pid_data['pid_output'].append(pid_output)
        
        # Trim data if it exceeds max_data_points
        if len(pid_data['time']) > pid_data['max_data_points']:
            for key in pid_data:
                if key != 'max_data_points':
                    pid_data[key] = pid_data[key][-pid_data['max_data_points']:]
        
        # Log to CSV if enabled
        if web_config.get('csv_logging', True):
            log_to_csv(current_time, actual_angle, target_angle, pid_error, 
                       p_term, i_term, d_term, pid_output)

def log_to_csv(timestamp, actual_angle, target_angle, pid_error, p_term, i_term, d_term, pid_output):
    """
    Log data to a CSV file
    
    Args:
        timestamp: Current time
        actual_angle: Current angle from the IMU
        target_angle: Target angle (setpoint)
        pid_error: Current error (target - actual)
        p_term: Proportional term
        i_term: Integral term
        d_term: Derivative term
        pid_output: Overall PID output
    """
    csv_file = 'pid_data.csv'
    file_exists = os.path.isfile(csv_file)
    
    with open(csv_file, 'a', newline='') as file:
        writer = csv.writer(file)
        
        # Write header if the file doesn't exist
        if not file_exists:
            writer.writerow(['Timestamp', 'Actual Angle', 'Target Angle', 'PID Error', 
                             'P Term', 'I Term', 'D Term', 'PID Output'])
        
        # Write data
        writer.writerow([timestamp, actual_angle, target_angle, pid_error, 
                         p_term, i_term, d_term, pid_output])

def clear_csv_file():
    """Clear the CSV file"""
    with open('pid_data.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Timestamp', 'Actual Angle', 'Target Angle', 'PID Error', 
                         'P Term', 'I Term', 'D Term', 'PID Output'])

def start_server(host='0.0.0.0', port=5000, debug=False):
    """
    Start the Flask server in a separate thread
    
    Args:
        host: Host address to bind to
        port: Port to listen on
        debug: Whether to run in debug mode
    """
    # Clear the CSV file
    clear_csv_file()
    
    # Start the server
    web_config['is_running'] = True
    threading.Thread(target=lambda: app.run(host=host, port=port, debug=debug, use_reloader=False)).start()
    print(f"Web server started at http://{host}:{port}")
    
def stop_server():
    """Stop the Flask server"""
    web_config['is_running'] = False
    
# Create the CSS and JS files
def create_static_files():
    """Create the static files needed for the web interface"""
    # Create styles.css
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    with open('static/css/styles.css', 'w') as f:
        f.write("""
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin: 0;
    padding: 0;
    background-color: #f8f9fa;
}

.navbar {
    background-color: #343a40;
    color: white;
}

.container {
    padding-top: 20px;
}

.card {
    margin-bottom: 20px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.card-header {
    background-color: #343a40;
    color: white;
    font-weight: bold;
}

.graph-container {
    height: 400px;
    width: 100%;
}

.parameter-slider {
    margin: 10px 0;
}

.slider-value {
    font-weight: bold;
    color: #343a40;
}

.btn-primary {
    background-color: #007bff;
}

.btn-danger {
    background-color: #dc3545;
}

.btn-success {
    background-color: #28a745;
}

.form-label {
    font-weight: bold;
}

#status-indicator {
    height: 15px;
    width: 15px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 5px;
}

.status-connected {
    background-color: #28a745;
}

.status-disconnected {
    background-color: #dc3545;
}
        """)
    
    # Create chart.js script
    with open('static/js/pid_chart.js', 'w') as f:
        f.write("""
// Global chart objects
let angleChart = null;
let pidTermsChart = null;

// Global configuration
const config = {
    timeWindow: 10,
    updateInterval: 200,
    csvLogging: true,
    isConnected: false,
    lastUpdateTime: 0
};

// Initialize the charts
function initCharts() {
    // Angle Chart
    const angleCtx = document.getElementById('angleChart').getContext('2d');
    angleChart = new Chart(angleCtx, {
        type: 'line',
        data: {
            datasets: [
                {
                    label: 'Actual Angle',
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    data: []
                },
                {
                    label: 'Target Angle',
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    data: []
                },
                {
                    label: 'PID Error',
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    data: []
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'linear',
                    display: true,
                    title: {
                        display: true,
                        text: 'Time (s)'
                    }
                },
                y: {
                    display: true,
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
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                legend: {
                    position: 'top',
                }
            }
        }
    });

    // PID Terms Chart
    const pidCtx = document.getElementById('pidTermsChart').getContext('2d');
    pidTermsChart = new Chart(pidCtx, {
        type: 'line',
        data: {
            datasets: [
                {
                    label: 'P Term',
                    borderColor: '#fd7e14',
                    backgroundColor: 'rgba(253, 126, 20, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    data: []
                },
                {
                    label: 'I Term',
                    borderColor: '#20c997',
                    backgroundColor: 'rgba(32, 201, 151, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    data: []
                },
                {
                    label: 'D Term',
                    borderColor: '#6f42c1',
                    backgroundColor: 'rgba(111, 66, 193, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    data: []
                },
                {
                    label: 'PID Output',
                    borderColor: '#17a2b8',
                    backgroundColor: 'rgba(23, 162, 184, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    data: []
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'linear',
                    display: true,
                    title: {
                        display: true,
                        text: 'Time (s)'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'PID Terms'
                    }
                }
            },
            animation: {
                duration: 0
            },
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                legend: {
                    position: 'top',
                }
            }
        }
    });
}

// Update the charts with new data
function updateCharts(data) {
    // Calculate the time window
    let now = data.time.length > 0 ? data.time[data.time.length - 1] : 0;
    let timeMin = now - config.timeWindow;
    
    // Process data with relative timestamps
    let relativeTimeData = data.time.map(t => t - timeMin);
    
    // Update angle chart
    angleChart.data.datasets[0].data = combineData(relativeTimeData, data.actual_angle);
    angleChart.data.datasets[1].data = combineData(relativeTimeData, data.target_angle);
    angleChart.data.datasets[2].data = combineData(relativeTimeData, data.pid_error);
    
    // Update PID terms chart
    pidTermsChart.data.datasets[0].data = combineData(relativeTimeData, data.p_term);
    pidTermsChart.data.datasets[1].data = combineData(relativeTimeData, data.i_term);
    pidTermsChart.data.datasets[2].data = combineData(relativeTimeData, data.d_term);
    pidTermsChart.data.datasets[3].data = combineData(relativeTimeData, data.pid_output);
    
    // Update x-axis range
    angleChart.options.scales.x.min = 0;
    angleChart.options.scales.x.max = config.timeWindow;
    pidTermsChart.options.scales.x.min = 0;
    pidTermsChart.options.scales.x.max = config.timeWindow;
    
    // Update the charts
    angleChart.update();
    pidTermsChart.update();
    
    // Update status
    config.isConnected = true;
    config.lastUpdateTime = Date.now();
    updateConnectionStatus();
}

// Helper function to combine time and value arrays into {x, y} format
function combineData(timeArray, valueArray) {
    return timeArray.map((t, i) => ({x: t, y: valueArray[i]}));
}

// Fetch data from the server
function fetchData() {
    fetch('/data')
        .then(response => response.json())
        .then(data => {
            updateCharts(data);
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            config.isConnected = false;
            updateConnectionStatus();
        });
}

// Update the connection status indicator
function updateConnectionStatus() {
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    
    if (config.isConnected) {
        statusIndicator.className = 'status-connected';
        statusText.textContent = 'Connected';
    } else {
        statusIndicator.className = 'status-disconnected';
        statusText.textContent = 'Disconnected';
    }
}

// Check if the connection is still active
function checkConnection() {
    if (Date.now() - config.lastUpdateTime > 5000) {
        config.isConnected = false;
        updateConnectionStatus();
    }
}

// Fetch the current PID parameters
function fetchPIDParameters() {
    fetch('/pid_params')
        .then(response => response.json())
        .then(data => {
            document.getElementById('pGain').value = data.p_gain;
            document.getElementById('pGainValue').textContent = data.p_gain.toFixed(2);
            
            document.getElementById('iGain').value = data.i_gain;
            document.getElementById('iGainValue').textContent = data.i_gain.toFixed(2);
            
            document.getElementById('dGain').value = data.d_gain;
            document.getElementById('dGainValue').textContent = data.d_gain.toFixed(2);
            
            document.getElementById('alpha').value = data.alpha;
            document.getElementById('alphaValue').textContent = data.alpha.toFixed(2);
            
            document.getElementById('directionChangeBoost').value = data.direction_change_boost;
            document.getElementById('directionChangeBoostValue').textContent = data.direction_change_boost.toFixed(2);
            
            document.getElementById('sampleTime').value = data.sample_time;
            document.getElementById('sampleTimeValue').textContent = data.sample_time.toFixed(3);
        })
        .catch(error => {
            console.error('Error fetching PID parameters:', error);
        });
}

// Update a PID parameter
function updatePIDParameter(parameter, value) {
    let data = {};
    data[parameter] = value;
    
    fetch('/pid_params', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        console.log('Parameter updated:', data);
    })
    .catch(error => {
        console.error('Error updating parameter:', error);
    });
}

// Update the configuration
function updateConfig() {
    fetch('/config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            time_window: config.timeWindow,
            update_interval: config.updateInterval,
            csv_logging: config.csvLogging
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Configuration updated:', data);
    })
    .catch(error => {
        console.error('Error updating configuration:', error);
    });
}

// Restart the PID controller
function restartPID() {
    fetch('/restart_pid', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        console.log('PID restarted:', data);
    })
    .catch(error => {
        console.error('Error restarting PID:', error);
    });
}

// Initialize everything when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the charts
    initCharts();
    
    // Fetch the initial PID parameters
    fetchPIDParameters();
    
    // Set up event listeners for the time window buttons
    document.querySelectorAll('.time-window-btn').forEach(button => {
        button.addEventListener('click', function() {
            const timeWindow = parseInt(this.dataset.window);
            config.timeWindow = timeWindow;
            
            // Update active button
            document.querySelectorAll('.time-window-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            this.classList.add('active');
            
            // Update server config
            updateConfig();
        });
    });
    
    // Set up event listeners for the update interval slider
    const updateIntervalSlider = document.getElementById('updateInterval');
    const updateIntervalValue = document.getElementById('updateIntervalValue');
    
    updateIntervalSlider.addEventListener('input', function() {
        config.updateInterval = parseInt(this.value);
        updateIntervalValue.textContent = this.value + 'ms';
    });
    
    updateIntervalSlider.addEventListener('change', function() {
        updateConfig();
        clearInterval(dataInterval);
        dataInterval = setInterval(fetchData, config.updateInterval);
    });
    
    // Set up event listeners for CSV logging
    const csvLoggingCheckbox = document.getElementById('csvLogging');
    csvLoggingCheckbox.addEventListener('change', function() {
        config.csvLogging = this.checked;
        updateConfig();
    });
    
    // Set up event listeners for the restart button
    document.getElementById('restartBtn').addEventListener('click', restartPID);
    
    // Set up event listeners for all PID parameter sliders
    document.querySelectorAll('.pid-slider').forEach(slider => {
        const valueElement = document.getElementById(slider.id + 'Value');
        
        slider.addEventListener('input', function() {
            valueElement.textContent = parseFloat(this.value).toFixed(
                slider.id === 'sampleTime' ? 3 : 2
            );
        });
        
        slider.addEventListener('change', function() {
            updatePIDParameter(slider.dataset.param, parseFloat(this.value));
        });
    });
    
    // Start the data update interval
    let dataInterval = setInterval(fetchData, config.updateInterval);
    
    // Start the connection check interval
    setInterval(checkConnection, 1000);
    
    // Set initial values based on config
    document.getElementById('updateInterval').value = config.updateInterval;
    document.getElementById('updateIntervalValue').textContent = config.updateInterval + 'ms';
    document.getElementById('csvLogging').checked = config.csvLogging;
    
    // Set the initial active time window button
    document.querySelector(`.time-window-btn[data-window="${config.timeWindow}"]`).classList.add('active');
});
        """)

# Create the HTML template
def create_templates():
    """Create the HTML templates for the web interface"""
    os.makedirs('templates', exist_ok=True)
    
    with open('templates/index.html', 'w') as f:
        f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PID Controller Dashboard</title>
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Custom CSS -->
    <link href="/static/css/styles.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container">
            <a class="navbar-brand" href="#">Self-Balancing Robot Dashboard</a>
            <div class="ms-auto">
                <span id="status-indicator" class="status-disconnected"></span>
                <span id="status-text">Disconnected</span>
            </div>
        </div>
    </nav>

    <div class="container">
        <div class="row">
            <!-- Angle Chart -->
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">Robot Angle</div>
                    <div class="card-body">
                        <div class="graph-container">
                            <canvas id="angleChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- PID Terms Chart -->
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">PID Components</div>
                    <div class="card-body">
                        <div class="graph-container">
                            <canvas id="pidTermsChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Graph Controls -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">Graph Controls</div>
                    <div class="card-body">
                        <div class="mb-3">
                            <label class="form-label">Time Window</label>
                            <div class="btn-group" role="group">
                                <button type="button" class="btn btn-outline-primary time-window-btn" data-window="3">3s</button>
                                <button type="button" class="btn btn-outline-primary time-window-btn" data-window="5">5s</button>
                                <button type="button" class="btn btn-outline-primary time-window-btn" data-window="10">10s</button>
                                <button type="button" class="btn btn-outline-primary time-window-btn" data-window="30">30s</button>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label for="updateInterval" class="form-label">Update Interval: <span id="updateIntervalValue">200ms</span></label>
                            <input type="range" class="form-range" id="updateInterval" min="100" max="1000" step="100" value="200">
                        </div>
                        
                        <div class="form-check mb-3">
                            <input class="form-check-input" type="checkbox" id="csvLogging" checked>
                            <label class="form-check-label" for="csvLogging">
                                Enable CSV Logging
                            </label>
                        </div>
                        
                        <button id="restartBtn" class="btn btn-danger">Restart PID Controller</button>
                    </div>
                </div>
            </div>
            
            <!-- PID Parameters -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">PID Parameters</div>
                    <div class="card-body">
                        <div class="mb-3">
                            <label for="pGain" class="form-label">P Gain: <span id="pGainValue">0.00</span></label>
                            <input type="range" class="form-range pid-slider" id="pGain" data-param="p_gain" min="0" max="50" step="0.1" value="0">
                        </div>
                        
                        <div class="mb-3">
                            <label for="iGain" class="form-label">I Gain: <span id="iGainValue">0.00</span></label>
                            <input type="range" class="form-range pid-slider" id="iGain" data-param="i_gain" min="0" max="10" step="0.1" value="0">
                        </div>
                        
                        <div class="mb-3">
                            <label for="dGain" class="form-label">D Gain: <span id="dGainValue">0.00</span></label>
                            <input type="range" class="form-range pid-slider" id="dGain" data-param="d_gain" min="0" max="20" step="0.1" value="0">
                        </div>
                        
                        <div class="mb-3">
                            <label for="alpha" class="form-label">IMU Filter Alpha: <span id="alphaValue">0.30</span></label>
                            <input type="range" class="form-range pid-slider" id="alpha" data-param="alpha" min="0.01" max="1.0" step="0.01" value="0.3">
                        </div>
                        
                        <div class="mb-3">
                            <label for="directionChangeBoost" class="form-label">Direction Change Boost: <span id="directionChangeBoostValue">20.00</span>%</label>
                            <input type="range" class="form-range pid-slider" id="directionChangeBoost" data-param="direction_change_boost" min="0" max="100" step="1" value="20">
                        </div>
                        
                        <div class="mb-3">
                            <label for="sampleTime" class="form-label">Sample Time: <span id="sampleTimeValue">0.010</span> sec</label>
                            <input type="range" class="form-range pid-slider" id="sampleTime" data-param="sample_time" min="0.001" max="0.05" step="0.001" value="0.01">
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Bootstrap & Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- Custom JS -->
    <script src="/static/js/pid_chart.js"></script>
</body>
</html>""")

# Call the functions to create the static files
create_static_files()
create_templates()

if __name__ == "__main__":
    start_server(debug=True) 