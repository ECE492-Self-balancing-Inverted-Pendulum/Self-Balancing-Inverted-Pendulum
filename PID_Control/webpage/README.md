# PID Controller Web Dashboard

This module provides a web-based interface for monitoring and tuning the self-balancing robot's PID controller in real-time.

## Features

- Real-time visualization of robot angle and PID terms
- Live parameter tuning with immediate feedback
- Data logging to CSV files
- Responsive design works on mobile devices
- Compatible with Raspberry Pi

## Setup

### Installation

On your Raspberry Pi, install the required dependencies:

```bash
# Activate your virtual environment if using one
source .venv/bin/activate  # Optional, if using venv

# Install required packages
pip install flask
```

### Running the Dashboard

The web dashboard starts automatically when using the runtime parameter tuning mode (option 5 in the main menu).

You can also start it programmatically:

```python
from webpage import start_server, stop_server

# Start the server (by default on port 5000)
start_server(port=5000)

# ... your code here ...

# Stop the server when done
stop_server()
```

### Accessing the Dashboard

Access the dashboard from any device on the same network by navigating to:

```
http://YOUR_RASPBERRY_PI_IP:5000
```

Replace `YOUR_RASPBERRY_PI_IP` with your Raspberry Pi's IP address.

## Troubleshooting

### Dashboard not loading

1. Check if Flask is installed correctly: `pip list | grep flask`
2. Ensure your Raspberry Pi's firewall allows connections on port 5000
3. Verify you're trying to access the correct IP address
4. Check if other services are using port 5000, and change the port if needed

### No data showing in charts

1. Make sure the PID controller is running
2. Check the console logs for errors
3. Verify the `debug_callback` function is being called in the balance controller

### Slow performance

1. Reduce the update interval (using the slider in the Settings panel)
2. Clear old data from the charts by restarting the PID controller
3. Make sure your Raspberry Pi isn't overheating (check CPU temperature)

## API Endpoints

The dashboard exposes the following API endpoints:

- `/api/pid_data` - GET: Returns current PID data
- `/api/pid_params` - GET/POST: Read or update PID parameters
- `/api/config` - GET/POST: Read or update dashboard configuration
- `/api/restart_pid` - POST: Restart the PID controller

## Dependencies

- Flask: Web server framework
- Chart.js: JavaScript charting library
- Bootstrap: CSS framework for responsive design

## Package Structure

The web dashboard is organized into the following modules:

- `__init__.py`: Package initialization that exports the main functions (`add_data_point`, `start_server`, `stop_server`) for external use.

- `app.py`: Flask application factory that creates and configures the web app with appropriate settings and routes.

- `config.py`: Contains all configuration settings, constants, and global state like data storage dictionaries and thread locks.

- `data_manager.py`: Handles all data operations including storage, filtering, and CSV logging. Maintains a circular buffer of PID data points.

- `routes.py`: Defines all API endpoints and URL routes for the web interface, including data retrieval and parameter updates.

- `server.py`: Manages starting and stopping the Flask server in a separate thread, ensuring it doesn't block the main application.

- `static_generator.py`: Dynamically generates and updates CSS, JavaScript and HTML template files for the web interface.

## Directory Structure

```
webpage/
├── __init__.py          # Package exports
├── app.py               # Flask app configuration
├── config.py            # Global settings
├── data_manager.py      # Data handling
├── routes.py            # API endpoints
├── server.py            # Server management
├── static_generator.py  # Static file generation
├── static/              # Static web assets
│   ├── css/             # Stylesheet files
│   │   └── styles.css   # Main CSS styles
│   └── js/              # JavaScript files
│       └── pid_chart.js # Chart rendering and data handling
└── templates/           # HTML templates
    └── index.html       # Main dashboard layout
```

## Technical Details

### Data Flow

1. `add_data_point()` receives data from the PID controller
2. Data is stored in memory buffers and optionally logged to CSV
3. The web client fetches data through API endpoints at `/data`
4. Chart.js visualizes the data on the client side

### Thread Safety

- All data access is protected with thread locks
- The Flask server runs in a separate daemon thread
- Communication between the main program and web server is done through shared data structures

### Configuration Management

- Web interface settings (time windows, update intervals, etc.) are stored in memory
- PID controller parameters are read from and written to the main config file
- Changes made through the web UI are immediately applied to the running controller

## Usage

```python
# Import the package
from webpage import start_server, stop_server, add_data_point

# Start the server
start_server(host='0.0.0.0', port=5000)

# Send data to the web interface
add_data_point(
    actual_angle=roll,
    target_angle=0.0, 
    pid_error=pid_error,
    p_term=p_term,
    i_term=i_term,
    d_term=d_term,
    pid_output=output
)

# Stop the server when done
stop_server()
```

## Web UI

The web interface is accessible at `http://<host>:<port>` and includes:

1. Angle chart showing actual, target, and error values
2. PID components chart showing P, I, D terms and output
3. Controls for adjusting time window, update interval, and data logging
4. Sliders for tuning PID parameters

## Development

To extend or modify the web dashboard:

1. Edit `static_generator.py` to update CSS or JavaScript
2. Modify `routes.py` to add new API endpoints
3. Update `data_manager.py` to change data handling

Run the server in debug mode for development:

```python
from webpage import start_server
start_server(debug=True)
``` 