// Global objects for charts and configuration
let angleChart;
let pidTermsChart;
let pidData = {
    time: [],
    actual_angle: [],
    target_angle: [],
    pid_error: [],
    p_term: [],
    i_term: [],
    d_term: [],
    pid_output: []  // Add this field to store PID output
};

// Configuration
const config = {
    timeWindow: 30, // seconds to display
    updateInterval: 500, // ms between updates
    connected: true
};

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initCharts();
    setupEventListeners();
    
    // Set global data interval
    window.dataIntervalActive = true;
    window.dataInterval = setInterval(fetchData, config.updateInterval);
    
    // Initialize UI elements
    document.getElementById('updateIntervalValue').innerText = config.updateInterval + "ms";
    document.getElementById('updateIntervalSlider').value = config.updateInterval;
    document.getElementById('csvLoggingCheckbox').checked = false;
    
    fetchConfig();
});

function initCharts() {
    const angleCtx = document.getElementById('angleChart').getContext('2d');
    const pidTermsCtx = document.getElementById('pidTermsChart').getContext('2d');
    
    // Chart for angles
    angleChart = new Chart(angleCtx, {
        type: 'line',
        data: {
            datasets: [{
                label: 'Actual Angle',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1,
                pointRadius: 0
            }, {
                label: 'Target Angle',
                data: [],
                borderColor: 'rgb(255, 159, 64)',
                tension: 0.1,
                pointRadius: 0
            }, {
                label: 'PID Error',
                data: [],
                borderColor: 'rgb(255, 99, 132)',
                tension: 0.1,
                pointRadius: 0
            }]
        },
        options: {
            animation: false,
            scales: {
                x: {
                    type: 'linear',
                    title: {
                        display: true,
                        text: 'Time (s)'
                    },
                    min: 0,
                    max: config.timeWindow
                },
                y: {
                    title: {
                        display: true,
                        text: 'Angle (degrees)'
                    }
                }
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
            },
            responsive: true,
            maintainAspectRatio: false
        }
    });
    
    // Chart for PID terms
    pidTermsChart = new Chart(pidTermsCtx, {
        type: 'line',
        data: {
            datasets: [{
                label: 'P Term',
                data: [],
                borderColor: 'rgb(255, 99, 132)',
                tension: 0.1,
                pointRadius: 0
            }, {
                label: 'I Term',
                data: [],
                borderColor: 'rgb(54, 162, 235)',
                tension: 0.1,
                pointRadius: 0
            }, {
                label: 'D Term',
                data: [],
                borderColor: 'rgb(255, 205, 86)',
                tension: 0.1,
                pointRadius: 0
            }, {
                label: 'PID Output',
                data: [],
                borderColor: 'rgb(153, 102, 255)',
                tension: 0.1,
                pointRadius: 0
            }]
        },
        options: {
            animation: false,
            scales: {
                x: {
                    type: 'linear',
                    title: {
                        display: true,
                        text: 'Time (s)'
                    },
                    min: 0,
                    max: config.timeWindow
                },
                y: {
                    title: {
                        display: true,
                        text: 'Value'
                    }
                }
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
            },
            responsive: true,
            maintainAspectRatio: false
        }
    });
    
    updateConnectionStatus(true);
}

function updateCharts() {
    if (pidData.time.length === 0) return;
    
    // Convert time to relative seconds starting from 0
    const startTime = pidData.time[0];
    const relativeTime = pidData.time.map(t => (t - startTime));
    
    // Determine max time for proper window display
    const maxTime = relativeTime[relativeTime.length - 1];
    let minTime = Math.max(0, maxTime - config.timeWindow);
    
    // Always ensure data starts from 0
    if (maxTime < config.timeWindow) {
        minTime = 0;
    }
    
    // Update x-axis range for both charts to ensure data scrolls from left to right
    angleChart.options.scales.x.min = minTime;
    angleChart.options.scales.x.max = minTime + config.timeWindow;
    pidTermsChart.options.scales.x.min = minTime;
    pidTermsChart.options.scales.x.max = minTime + config.timeWindow;
    
    // Combine time and data for chart format
    const angleData = [
        combineTimeAndValue(relativeTime, pidData.actual_angle),
        combineTimeAndValue(relativeTime, pidData.target_angle),
        combineTimeAndValue(relativeTime, pidData.pid_error)
    ];
    
    const pidTermsData = [
        combineTimeAndValue(relativeTime, pidData.p_term),
        combineTimeAndValue(relativeTime, pidData.i_term),
        combineTimeAndValue(relativeTime, pidData.d_term),
        combineTimeAndValue(relativeTime, pidData.pid_output || Array(pidData.time.length).fill(0)) // Add PID output dataset
    ];
    
    // Update datasets for angle chart
    for (let i = 0; i < angleData.length; i++) {
        angleChart.data.datasets[i].data = angleData[i];
    }
    
    // Update datasets for PID terms chart
    for (let i = 0; i < pidTermsData.length; i++) {
        pidTermsChart.data.datasets[i].data = pidTermsData[i];
    }
    
    // Update the charts
    angleChart.update();
    pidTermsChart.update();
    
    // Update connection status
    updateConnectionStatus(config.connected);
}

function combineTimeAndValue(timeArray, valueArray) {
    return timeArray.map((t, i) => ({ x: t, y: valueArray[i] }));
}

function fetchData() {
    fetch('/api/pid_data')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data && data.time) {
                // Ensure all expected fields exist to prevent errors
                data.pid_output = data.pid_output || [];
                
                // Update global data
                pidData = data;
                
                // Update charts with new data
                updateCharts();
                
                // Set connection status to true
                config.connected = true;
            }
        })
        .catch(error => {
            console.error('Error fetching PID data:', error);
            config.connected = false;
            updateConnectionStatus(false);
        })
        .finally(() => {
            // Ensure data polling continues
            if (!window.dataIntervalActive) {
                window.dataIntervalActive = true;
                window.dataInterval = setInterval(fetchData, config.updateInterval);
            }
        });
}

function fetchConfig() {
    fetch('/api/config')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.updateInterval) {
                config.updateInterval = data.updateInterval;
                document.getElementById('updateIntervalValue').innerText = config.updateInterval + "ms";
                document.getElementById('updateIntervalSlider').value = config.updateInterval;
            }
            if (data.hasOwnProperty('csvLogging')) {
                document.getElementById('csvLoggingCheckbox').checked = data.csvLogging;
            }
        })
        .catch(error => {
            console.error('Error fetching config:', error);
        });
}

function updateConnectionStatus(connected) {
    const statusElement = document.getElementById('connectionStatus');
    if (statusElement) {
        if (connected) {
            statusElement.textContent = "Connected";
            statusElement.className = "badge bg-success";
        } else {
            statusElement.textContent = "Disconnected";
            statusElement.className = "badge bg-danger";
        }
    }
}

function setupEventListeners() {
    // Active button state
    const navBtns = document.querySelectorAll('.nav-link');
    navBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            navBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    // Server config updates
    const updateIntervalSlider = document.getElementById('updateIntervalSlider');
    if (updateIntervalSlider) {
        updateIntervalSlider.addEventListener('input', function() {
            document.getElementById('updateIntervalValue').innerText = this.value + "ms";
        });
        
        updateIntervalSlider.addEventListener('change', function() {
            config.updateInterval = parseInt(this.value);
            
            // Clear and restart interval with new rate
            clearInterval(window.dataInterval);
            window.dataInterval = setInterval(fetchData, config.updateInterval);
            
            // Update server config
            fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    updateInterval: config.updateInterval
                })
            }).catch(error => console.error('Error updating config:', error));
        });
    }
    
    const csvLoggingCheckbox = document.getElementById('csvLoggingCheckbox');
    if (csvLoggingCheckbox) {
        csvLoggingCheckbox.addEventListener('change', function() {
            fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    csvLogging: this.checked
                })
            }).catch(error => console.error('Error updating config:', error));
        });
    }
    
    // Restart PID controller
    const restartPIDBtn = document.getElementById('restartPID');
    if (restartPIDBtn) {
        restartPIDBtn.addEventListener('click', function() {
            fetch('/api/restart_pid', {
                method: 'POST'
            }).then(response => {
                if (response.ok) {
                    alert('PID Controller restarted successfully');
                } else {
                    throw new Error('Failed to restart PID Controller');
                }
            }).catch(error => {
                console.error('Error:', error);
                alert('Error restarting PID Controller: ' + error.message);
            });
        });
    }
} 