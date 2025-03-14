// Global chart objects
let angleChart;
let pidTermsChart;

// Configuration
const config = {
    timeWindow: 10, // Time window to display in seconds
    updateInterval: 500, // Update interval in milliseconds
    connectionTimeout: 3000, // Timeout for connection status in milliseconds
    connected: false, // Connection status
};

// Initialize charts when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    
    // Set up update interval slider
    const updateIntervalSlider = document.getElementById('updateIntervalSlider');
    if (updateIntervalSlider) {
        updateIntervalSlider.value = config.updateInterval;
        document.getElementById('updateIntervalValue').textContent = `${config.updateInterval}ms`;
        
        updateIntervalSlider.addEventListener('input', function() {
            const value = parseInt(this.value);
            config.updateInterval = value;
            document.getElementById('updateIntervalValue').textContent = `${value}ms`;
        });
        
        updateIntervalSlider.addEventListener('change', function() {
            // Clear any existing interval
            if (window.dataInterval) {
                clearInterval(window.dataInterval);
                // Restart interval with new rate
                window.dataInterval = setInterval(fetchData, config.updateInterval);
            }
        });
    }
    
    // Set up CSV logging checkbox
    const csvLoggingCheckbox = document.getElementById('csvLoggingCheckbox');
    if (csvLoggingCheckbox) {
        fetch('/api/config')
            .then(response => response.json())
            .then(data => {
                csvLoggingCheckbox.checked = data.csv_logging;
            })
            .catch(error => console.error('Error fetching config:', error));
        
        csvLoggingCheckbox.addEventListener('change', function() {
            fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({csv_logging: this.checked})
            })
            .catch(error => console.error('Error updating CSV logging:', error));
        });
    }
    
    // Set up restart button
    const restartButton = document.getElementById('restartPID');
    if (restartButton) {
        restartButton.addEventListener('click', function() {
            if (confirm('Are you sure you want to restart the PID controller?')) {
                fetch('/api/restart', {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        showToast('PID controller restarted successfully', 'success');
                    } else {
                        showError('Failed to restart PID controller: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error restarting PID controller:', error);
                    showError('Failed to restart PID controller: ' + error.message);
                });
            }
        });
    }
    
    // Start data fetching
    window.dataIntervalActive = true;
    window.dataInterval = setInterval(fetchData, config.updateInterval);
    fetchData(); // Initial fetch
});

// Initialize charts
function initializeCharts() {
    const angleChartCanvas = document.getElementById('angleChart');
    const pidTermsChartCanvas = document.getElementById('pidTermsChart');
    
    if (!angleChartCanvas || !pidTermsChartCanvas) {
        console.error('Chart canvas elements not found');
        return;
    }
    
    // Initialize angle chart
    angleChart = new Chart(angleChartCanvas, {
        type: 'line',
        data: {
            datasets: [
                {
                    label: 'Actual Angle',
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    data: []
                },
                {
                    label: 'Target Angle',
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    borderDash: [5, 5],
                    data: []
                },
                {
                    label: 'PID Error',
                    borderColor: 'rgb(153, 102, 255)',
                    backgroundColor: 'rgba(153, 102, 255, 0.1)',
                    borderWidth: 1,
                    pointRadius: 0,
                    hidden: true,
                    data: []
                },
                {
                    label: 'PID Output',
                    borderColor: 'rgb(255, 159, 64)',
                    backgroundColor: 'rgba(255, 159, 64, 0.1)',
                    borderWidth: 1,
                    pointRadius: 0,
                    data: []
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            scales: {
                x: {
                    type: 'linear',
                    min: 0,
                    max: config.timeWindow,
                    title: {
                        display: true,
                        text: 'Time (s)'
                    },
                    ticks: {
                        stepSize: 1
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Angle (degrees)'
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                },
                zoom: {
                    pan: {
                        enabled: true,
                        mode: 'x'
                    },
                    zoom: {
                        wheel: {
                            enabled: true,
                        },
                        pinch: {
                            enabled: true
                        },
                        mode: 'x'
                    }
                }
            }
        }
    });
    
    // Initialize PID terms chart
    pidTermsChart = new Chart(pidTermsChartCanvas, {
        type: 'line',
        data: {
            datasets: [
                {
                    label: 'P Term',
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    data: []
                },
                {
                    label: 'I Term',
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    data: []
                },
                {
                    label: 'D Term',
                    borderColor: 'rgb(255, 206, 86)',
                    backgroundColor: 'rgba(255, 206, 86, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    data: []
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            scales: {
                x: {
                    type: 'linear',
                    min: 0,
                    max: config.timeWindow,
                    title: {
                        display: true,
                        text: 'Time (s)'
                    },
                    ticks: {
                        stepSize: 1
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
                    position: 'top',
                },
                zoom: {
                    pan: {
                        enabled: true,
                        mode: 'x'
                    },
                    zoom: {
                        wheel: {
                            enabled: true,
                        },
                        pinch: {
                            enabled: true
                        },
                        mode: 'x'
                    }
                }
            }
        }
    });
}

// Fetch data from the server
function fetchData() {
    if (!angleChart || !pidTermsChart) {
        console.error('Charts not initialized');
        return;
    }
    
    fetch('/api/data')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data && Array.isArray(data.data) && data.data.length > 0) {
                updateCharts(data.data);
                updateConnectionStatus(true);
            } else {
                console.warn('No data received or empty data array');
                updateConnectionStatus(false);
            }
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            updateConnectionStatus(false);
        });
}

// Update the charts with new data
function updateCharts(data) {
    if (!data || data.length === 0 || !angleChart || !pidTermsChart) {
        return;
    }
    
    // Get timestamps and make them relative to the first data point
    const timestamps = data.map(item => parseFloat(item.timestamp));
    const firstTimestamp = timestamps[0];
    const relativeTimestamps = timestamps.map(t => parseFloat((t - firstTimestamp).toFixed(2)));
    
    // Extract data values
    const actualAngles = data.map(item => parseFloat(item.actual_angle));
    const targetAngles = data.map(item => parseFloat(item.target_angle));
    const pidErrors = data.map(item => parseFloat(item.pid_error));
    const pidOutputs = data.map(item => parseFloat(item.pid_output));
    const pTerms = data.map(item => parseFloat(item.p_term));
    const iTerms = data.map(item => parseFloat(item.i_term));
    const dTerms = data.map(item => parseFloat(item.d_term));
    
    // Create dataset points
    const angleDataActual = combineTimeAndValues(relativeTimestamps, actualAngles);
    const angleDataTarget = combineTimeAndValues(relativeTimestamps, targetAngles);
    const angleDataError = combineTimeAndValues(relativeTimestamps, pidErrors);
    const angleDataOutput = combineTimeAndValues(relativeTimestamps, pidOutputs);
    const pidDataP = combineTimeAndValues(relativeTimestamps, pTerms);
    const pidDataI = combineTimeAndValues(relativeTimestamps, iTerms);
    const pidDataD = combineTimeAndValues(relativeTimestamps, dTerms);
    
    // Calculate the visible time window
    const maxTime = Math.max(...relativeTimestamps);
    const visibleMin = Math.max(0, maxTime - config.timeWindow);
    const visibleMax = maxTime > config.timeWindow ? maxTime : config.timeWindow;
    
    // Update the charts
    angleChart.data.datasets[0].data = angleDataActual;
    angleChart.data.datasets[1].data = angleDataTarget;
    angleChart.data.datasets[2].data = angleDataError;
    angleChart.data.datasets[3].data = angleDataOutput;
    
    pidTermsChart.data.datasets[0].data = pidDataP;
    pidTermsChart.data.datasets[1].data = pidDataI;
    pidTermsChart.data.datasets[2].data = pidDataD;
    
    // Update x-axis range to ensure data scrolls from right
    angleChart.options.scales.x.min = visibleMin;
    angleChart.options.scales.x.max = visibleMax;
    pidTermsChart.options.scales.x.min = visibleMin;
    pidTermsChart.options.scales.x.max = visibleMax;
    
    // Update the charts
    angleChart.update();
    pidTermsChart.update();
}

// Combine time and value arrays into point objects for Chart.js
function combineTimeAndValues(times, values) {
    return times.map((time, index) => ({
        x: time,
        y: values[index]
    }));
}

// Update connection status indicator
function updateConnectionStatus(isConnected) {
    const statusElement = document.getElementById('connectionStatus');
    if (!statusElement) return;
    
    if (isConnected !== config.connected) {
        config.connected = isConnected;
        
        if (isConnected) {
            statusElement.textContent = 'Connected';
            statusElement.className = 'connection-badge bg-success text-white';
        } else {
            statusElement.textContent = 'Disconnected';
            statusElement.className = 'connection-badge bg-danger text-white';
        }
    }
}

// If showToast is not defined elsewhere (we defined it in the HTML)
if (typeof showToast === 'undefined') {
    window.showToast = function(message, type = 'success') {
        console.log(`Toast (${type}): ${message}`);
    };
}

// If showError is not defined elsewhere (we defined it in the HTML)
if (typeof showError === 'undefined') {
    window.showError = function(message) {
        console.error(`Error: ${message}`);
    };
} 