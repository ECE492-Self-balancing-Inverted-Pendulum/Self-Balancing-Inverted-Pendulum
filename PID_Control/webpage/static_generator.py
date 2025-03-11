"""
Static file generator for the PID controller web dashboard.
Creates and updates CSS, JS, and template files.
"""
import os
from .config import CSS_DIR, JS_DIR, TEMPLATES_DIR

def setup_static_files():
    """
    Create the necessary static files for the web interface
    """
    create_css_files()
    create_js_files()
    create_templates()
    print("Static files set up successfully")

def create_css_files():
    """Create the CSS files needed for the web interface"""
    with open(os.path.join(CSS_DIR, 'styles.css'), 'w') as f:
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

def create_js_files():
    """Create the JavaScript files needed for the web interface"""
    with open(os.path.join(JS_DIR, 'pid_chart.js'), 'w') as f:
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
    // If no data, just return
    if (data.time.length === 0) {
        return;
    }

    // Calculate relative timestamps - start from 0 for first visible point
    let firstTime = data.time[0]; // First data point timestamp
    let relativeTimeData = data.time.map(t => t - firstTime);
    
    // Calculate the current range of data
    let maxTime = Math.max(...relativeTimeData);
    
    // Determine the visible window - always show most recent data
    // but start from beginning if we don't have enough data yet
    let minTime = 0;
    let visibleWindow = config.timeWindow;
    
    if (maxTime > config.timeWindow) {
        minTime = maxTime - config.timeWindow;
    } else {
        visibleWindow = Math.max(maxTime, 3); // At least 3 seconds window
    }
    
    // Update x-axis range - this ensures data scrolls from left to right
    angleChart.options.scales.x.min = minTime;
    angleChart.options.scales.x.max = minTime + visibleWindow;
    pidTermsChart.options.scales.x.min = minTime;
    pidTermsChart.options.scales.x.max = minTime + visibleWindow;
    
    // Update angle chart with the relative time data
    angleChart.data.datasets[0].data = combineData(relativeTimeData, data.actual_angle);
    angleChart.data.datasets[1].data = combineData(relativeTimeData, data.target_angle);
    angleChart.data.datasets[2].data = combineData(relativeTimeData, data.pid_error);
    
    // Update PID terms chart with the relative time data
    pidTermsChart.data.datasets[0].data = combineData(relativeTimeData, data.p_term);
    pidTermsChart.data.datasets[1].data = combineData(relativeTimeData, data.i_term);
    pidTermsChart.data.datasets[2].data = combineData(relativeTimeData, data.d_term);
    pidTermsChart.data.datasets[3].data = combineData(relativeTimeData, data.pid_output);
    
    // Update the charts
    angleChart.update();
    pidTermsChart.update();
    
    // Update connection status
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
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Only update if we have data
            if (data && Object.keys(data).length > 0 && data.time && data.time.length > 0) {
                updateCharts(data);
            }
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            config.isConnected = false;
            updateConnectionStatus();
        })
        .finally(() => {
            // Ensure we're always connected - if the interval was cleared for some reason
            if (!window.dataIntervalActive) {
                console.log("Restarting data polling interval");
                window.dataInterval = setInterval(fetchData, config.updateInterval);
                window.dataIntervalActive = true;
            }
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
        // Clear and restart the data interval with new rate
        clearInterval(window.dataInterval);
        window.dataInterval = setInterval(fetchData, config.updateInterval);
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
    window.dataIntervalActive = true;
    window.dataInterval = setInterval(fetchData, config.updateInterval);
    
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

def create_templates():
    """Create the HTML templates for the web interface"""
    with open(os.path.join(TEMPLATES_DIR, 'index.html'), 'w') as f:
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