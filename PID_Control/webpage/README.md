# PID Controller Web Dashboard

A simplified web-based dashboard for monitoring and controlling a PID controller for a self-balancing robot.

## Features

- Real-time visualization of robot angle and PID terms
- Vertically stacked charts for better readability
- Live parameter tuning with immediate feedback
- Data logging to CSV
- Mobile-friendly responsive design
- Clean, single-file server implementation for simplicity

## Architecture

The web dashboard consists of just a few files for simplicity:

- `web_server.py`: Single-file server implementation that handles all backend functionality
- `templates/index.html`: The main HTML template with responsive layout
- `static/js/pid_chart.js`: JavaScript for chart rendering and data handling

## Setup

### Installation

1. Ensure you have the required dependencies:
   ```
   pip install flask
   ```

2. Make sure your project includes the `webpage` directory in your main project folder.

### Running the Dashboard

#### Automatic Mode

The dashboard can start automatically when your main robot program runs:

```python
from webpage.web_server import start_server, stop_server, add_data_point

# Start the web server
start_server(host='0.0.0.0', port=5000)

# In your main loop, add data points
add_data_point(
    timestamp=time.time(),
    actual_angle=sensor_angle,
    target_angle=0.0,
    pid_error=error,
    p_term=p_component,
    i_term=i_component,
    d_term=d_component,
    pid_output=output
)

# When exiting, stop the server
stop_server()
```

#### Manual Mode

You can also run the web server directly:

```
python -m webpage.web_server
```

### Accessing the Dashboard

Open a web browser and go to:
- Local access: `http://localhost:5000`
- Remote access (from another device): `http://<raspberry-pi-ip>:5000`

## Troubleshooting

### Dashboard Not Loading
- Check that the server is running (`is_server_running()` function)
- Verify that you can access the Pi's IP address from your device
- Check console log for errors

### No Data Showing in Charts
- Ensure your main loop is calling `add_data_point()` regularly
- Check the server console logs for data processing errors

### Slow Performance
- Reduce the update interval in the dashboard settings
- If running on Raspberry Pi Zero, consider reducing the maximum data points stored

## API Endpoints

- `/api/data` - GET: Retrieve all PID data points
- `/api/pid_params` - GET/POST: Get or update PID parameters
- `/api/config` - GET/POST: Get or update dashboard configuration
- `/api/restart` - POST: Restart the PID controller

## Parameters

The dashboard allows you to tune these PID parameters:
- KP (Proportional Gain)
- KI (Integral Gain)
- KD (Derivative Gain)
- Target Angle

All changes to parameters are automatically saved to a JSON file (`robot_config.json`) and will be reloaded when the server restarts. 