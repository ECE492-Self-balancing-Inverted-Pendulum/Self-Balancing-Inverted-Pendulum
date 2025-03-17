#!/usr/bin/env python3
import os
import json
import time
import logging
import threading
import csv
import signal
import atexit
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_from_directory
import sys
from logging import FileHandler
import socket

# Set Flask's built-in logger to only show errors
import logging
from logging import FileHandler

# Configure custom logging to file instead of console
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'web_server.log')

# Configure our logger to use a file handler for detailed logs
logging.basicConfig(
    level=logging.ERROR,  # Only show errors in console
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pid_web_server')

# Add a file handler for detailed logs
file_handler = FileHandler(log_file)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

# Silence Flask and Werkzeug loggers
logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('flask').setLevel(logging.ERROR)

# Don't output any Flask server startup messages
cli = sys.modules.get('flask.cli')
if cli is not None:
    cli.show_server_banner = lambda *args, **kwargs: None

# Global variables
PID_DATA = []
CONFIG = {
    'update_interval': 500,  # milliseconds
    'csv_logging': False,
    'time_window': 10,  # seconds
    'max_data_points': 1000,  # Maximum number of data points to store
    'pid_config_file': 'robot_config.json'
}
PID_PARAMS = {
    'P_GAIN': 1.0,
    'I_GAIN': 0.1,
    'D_GAIN': 0.01,
    'IMU_FILTER_ALPHA': 0.2,
    'SAMPLE_TIME': 10,
    'target_angle': 0.0,
    'MOTOR_DEADBAND': 10,
    'MAX_MOTOR_SPEED': 100,
    'ZERO_THRESHOLD': 0.1
}
CSV_FILE = None
CSV_WRITER = None
SERVER_INSTANCE = None
SERVER_STARTED = False
LOCK = threading.Lock()

# Create Flask app
app = Flask(__name__, static_folder='static')

# Import from the compatibility layer
try:
    # Instead of importing directly, we'll use a function to get the callback
    # This avoids circular imports
    _parent_module = None
    
    def trigger_update_callback(params):
        """
        Trigger the update callback from the parent module, if available.
        
        Args:
            params: Parameters to pass to the callback
        """
        global _parent_module
        if _parent_module is None:
            # Get the parent module on first call
            try:
                import sys
                # The parent module is 'webpage'
                _parent_module = sys.modules.get('webpage')
            except Exception as e:
                logger.error(f"Error getting parent module: {e}")
                return
        
        # Call the callback function if it exists in the parent module
        if _parent_module and hasattr(_parent_module, 'trigger_update_callback'):
            try:
                _parent_module.trigger_update_callback(params)
            except Exception as e:
                logger.error(f"Error calling trigger_update_callback: {e}")
        else:
            logger.warning("trigger_update_callback not available")
except ImportError:
    # Define a dummy function if the import fails
    def trigger_update_callback(params):
        logger.warning("trigger_update_callback not available")

# Load PID parameters from file if it exists
def load_pid_params():
    """Load PID parameters from robot_config.json if available"""
    try:
        robot_config_path = 'robot_config.json'
        if os.path.exists(robot_config_path):
            with open(robot_config_path, 'r') as f:
                robot_config = json.load(f)
                
            # Update PID parameters from robot config - using consistent naming
            PID_PARAMS['P_GAIN'] = robot_config.get('P_GAIN', PID_PARAMS['P_GAIN'])
            PID_PARAMS['I_GAIN'] = robot_config.get('I_GAIN', PID_PARAMS['I_GAIN'])
            PID_PARAMS['D_GAIN'] = robot_config.get('D_GAIN', PID_PARAMS['D_GAIN'])
            PID_PARAMS['IMU_FILTER_ALPHA'] = robot_config.get('IMU_FILTER_ALPHA', PID_PARAMS['IMU_FILTER_ALPHA'])
            # Convert seconds to milliseconds for the web interface
            PID_PARAMS['SAMPLE_TIME'] = int(robot_config.get('SAMPLE_TIME', 0.01) * 1000)
            PID_PARAMS['MOTOR_DEADBAND'] = robot_config.get('MOTOR_DEADBAND', PID_PARAMS['MOTOR_DEADBAND'])
            PID_PARAMS['MAX_MOTOR_SPEED'] = robot_config.get('MAX_MOTOR_SPEED', PID_PARAMS['MAX_MOTOR_SPEED'])
            PID_PARAMS['ZERO_THRESHOLD'] = robot_config.get('ZERO_THRESHOLD', PID_PARAMS['ZERO_THRESHOLD'])
            
            logger.info(f"Loaded PID parameters: {PID_PARAMS}")
            logger.info(f"Updated PID parameters from robot_config.json: {PID_PARAMS}")
    except Exception as e:
        logger.error(f"Error loading PID parameters from robot_config.json: {e}")

# Save PID parameters to file
def save_pid_params():
    """Save PID parameters to file with proper error handling and thread safety"""
    try:
        with LOCK:  # Use thread lock when accessing shared resources
            with open(CONFIG['pid_config_file'], 'w') as f:
                json.dump(PID_PARAMS, f, indent=4)
                logger.info(f"Saved PID parameters: {PID_PARAMS}")
    except Exception as e:
        logger.error(f"Error saving PID parameters: {e}")

# Route for the main dashboard
@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error serving index page: {e}")
        return jsonify({"error": str(e)}), 500

# API endpoint to get all PID data
@app.route('/api/data')
def get_data():
    try:
        with LOCK:
            return jsonify({"data": PID_DATA})
    except Exception as e:
        logger.error(f"Error getting PID data: {e}")
        return jsonify({"error": str(e)}), 500

# Legacy endpoint for backward compatibility
@app.route('/api/pid_data')
def get_pid_data_legacy():
    try:
        with LOCK:
            # Convert data to the old format for backward compatibility
            if not PID_DATA:
                return jsonify({})
                
            result = {
                "time": [],
                "actual_angle": [],
                "target_angle": [],
                "pid_error": [],
                "p_term": [],
                "i_term": [],
                "d_term": [],
                "pid_output": []
            }
            
            for point in PID_DATA:
                result["time"].append(point["timestamp"])
                result["actual_angle"].append(point["actual_angle"])
                result["target_angle"].append(point["target_angle"])
                result["pid_error"].append(point["pid_error"])
                result["p_term"].append(point["p_term"])
                result["i_term"].append(point["i_term"])
                result["d_term"].append(point["d_term"])
                result["pid_output"].append(point["pid_output"])
                
            return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting legacy PID data: {e}")
        return jsonify({"error": str(e)}), 500

# API endpoint to get configuration
@app.route('/api/config')
def get_config():
    try:
        return jsonify({
            "update_interval": CONFIG["update_interval"],
            "csv_logging": CONFIG["csv_logging"]
        })
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        return jsonify({"error": str(e)}), 500

# API endpoint to update configuration
@app.route('/api/config', methods=['POST'])
def update_config():
    try:
        data = request.json
        
        if 'update_interval' in data:
            CONFIG['update_interval'] = int(data['update_interval'])
            logger.info(f"Updated update_interval: {CONFIG['update_interval']}")
            
        if 'csv_logging' in data:
            enable_csv = bool(data['csv_logging'])
            if enable_csv != CONFIG['csv_logging']:
                CONFIG['csv_logging'] = enable_csv
                logger.info(f"Updated CSV logging: {CONFIG['csv_logging']}")
                
                # Start or stop CSV logging
                if CONFIG['csv_logging']:
                    start_csv_logging()
                else:
                    stop_csv_logging()
        
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return jsonify({"error": str(e)}), 500

# API endpoint to get PID parameters
@app.route('/api/pid_params')
def get_pid_params():
    try:
        # Create a response with frontend parameter names for backward compatibility
        frontend_names = {
            'P_GAIN': 'kp',
            'I_GAIN': 'ki',
            'D_GAIN': 'kd',
            'IMU_FILTER_ALPHA': 'alpha',
            'SAMPLE_TIME': 'sample_time',
            'MOTOR_DEADBAND': 'deadband',
            'MAX_MOTOR_SPEED': 'max_speed',
            'ZERO_THRESHOLD': 'zero_threshold'
        }
        
        response_data = {}
        for backend_key, frontend_key in frontend_names.items():
            if backend_key in PID_PARAMS:
                response_data[frontend_key] = PID_PARAMS[backend_key]
        
        # Add any other parameters not mapped
        for key in PID_PARAMS:
            if key not in frontend_names and not key.startswith('_'):
                response_data[key] = PID_PARAMS[key]
        
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error getting PID parameters: {e}")
        return jsonify({"error": str(e)}), 500

# API endpoint to update PID parameters
@app.route('/api/pid_params', methods=['POST'])
def update_pid_params():
    try:
        data = request.json
        
        # Update the parameters with thread safety
        with LOCK:
            # Create a mapping for legacy frontend parameter names to backend names
            param_mapping = {
                'kp': 'P_GAIN', 
                'ki': 'I_GAIN', 
                'kd': 'D_GAIN',
                'alpha': 'IMU_FILTER_ALPHA',
                'sample_time': 'SAMPLE_TIME',
                'deadband': 'MOTOR_DEADBAND',
                'max_speed': 'MAX_MOTOR_SPEED',
                'zero_threshold': 'ZERO_THRESHOLD'
            }
            
            # Validate parameters before updating
            for key in ['kp', 'ki', 'kd', 'alpha', 'sample_time', 'deadband', 'max_speed', 'zero_threshold']:
                if key in data:
                    try:
                        # Convert to float and validate ranges
                        value = float(data[key])
                        
                        # Validate based on the key
                        if key in ['kp', 'ki', 'kd'] and value < 0:
                            return jsonify({"error": f"Parameter {key} cannot be negative"}), 400
                        elif key == 'alpha' and (value < 0.05 or value > 0.95):
                            return jsonify({"error": "Alpha must be between 0.05 and 0.95"}), 400
                        elif key == 'sample_time' and (value < 5 or value > 20):
                            return jsonify({"error": "Sample time must be between 5 and 20 milliseconds"}), 400
                        elif key == 'deadband' and (value < 0 or value > 60):
                            return jsonify({"error": "Deadband must be between 0 and 60"}), 400
                        elif key == 'max_speed' and (value < 60 or value > 100):
                            return jsonify({"error": "Max speed must be between 60 and 100"}), 400
                        elif key == 'zero_threshold' and (value < 0.01 or value > 1.0):
                            return jsonify({"error": "Zero threshold must be between 0.01 and 1.0"}), 400
                        
                        # Update the parameter using the mapped key
                        backend_key = param_mapping.get(key, key)
                        PID_PARAMS[backend_key] = value
                    except ValueError:
                        return jsonify({"error": f"Invalid value for {key}"}), 400
        
        logger.info(f"Updated PID parameters: {PID_PARAMS}")
        
        # Save to PID config file
        save_pid_params()
        
        # Also update the robot_config.json file directly - no translation needed now
        try:
            robot_config_path = 'robot_config.json'
            if os.path.exists(robot_config_path):
                # Load current robot config
                with open(robot_config_path, 'r') as f:
                    robot_config = json.load(f)
                
                # Update parameters - use direct mapping
                for backend_key, value in PID_PARAMS.items():
                    # Only update keys that are in the robot_config
                    if backend_key in robot_config:
                        # Convert sample time from ms to seconds
                        if backend_key == 'SAMPLE_TIME':
                            robot_config[backend_key] = value / 1000.0
                        else:
                            robot_config[backend_key] = value
                
                # Save updated robot config
                with open(robot_config_path, 'w') as f:
                    json.dump(robot_config, f, indent=4)
                    
                logger.info(f"Updated robot_config.json with PID parameters")
                
                # Convert back to frontend parameter names for the callback
                frontend_data = {}
                for frontend_key, backend_key in param_mapping.items():
                    if backend_key in PID_PARAMS:
                        frontend_data[frontend_key] = PID_PARAMS[backend_key]
                
                # Trigger the update callback to apply changes in real-time
                trigger_update_callback(frontend_data)
        except Exception as e:
            logger.error(f"Error updating robot_config.json: {e}")
        
        # Convert to frontend format for response
        response_data = {}
        for frontend_key, backend_key in param_mapping.items():
            if backend_key in PID_PARAMS:
                response_data[frontend_key] = PID_PARAMS[backend_key]
        
        # Include any other parameters 
        for key in PID_PARAMS:
            if key not in param_mapping.values():
                response_data[key] = PID_PARAMS[key]
                
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error updating PID parameters: {e}")
        return jsonify({"error": str(e)}), 500

# API endpoint to restart the PID controller
@app.route('/api/restart', methods=['POST'])
def restart_pid():
    try:
        # This would normally call your PID controller restart function
        # For now, just log the request
        logger.info("Restart PID controller requested")
        
        # Here you would call your actual restart function
        # For example: pid_controller.restart()
        
        return jsonify({"status": "success", "message": "PID controller restarted"})
    except Exception as e:
        logger.error(f"Error restarting PID controller: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Serve static files
@app.route('/static/<path:path>')
def serve_static(path):
    """
    Serve static files with proper caching headers and error handling
    
    Args:
        path: Relative path to the static file
    """
    try:
        # Determine content type based on file extension
        content_type = None
        if path.endswith('.js'):
            content_type = 'application/javascript'
        elif path.endswith('.css'):
            content_type = 'text/css'
        elif path.endswith('.png'):
            content_type = 'image/png'
        elif path.endswith('.jpg') or path.endswith('.jpeg'):
            content_type = 'image/jpeg'
        
        # Add appropriate headers when applicable
        headers = {}
        if content_type:
            headers['Content-Type'] = content_type
            
        # Add caching headers for improved performance
        headers['Cache-Control'] = 'public, max-age=86400'  # Cache for 24 hours
            
        return send_from_directory('static', path, headers=headers)
    except Exception as e:
        logger.error(f"Error serving static file {path}: {e}")
        return jsonify({"error": f"File not found: {path}"}), 404

# Add a new data point
def add_data_point(timestamp, actual_angle, target_angle, pid_error, p_term, i_term, d_term, pid_output, motor_output=None):
    """
    Add a new data point to the PID data store with thread safety and data validation.
    
    Args:
        timestamp: Current time in seconds since epoch
        actual_angle: Measured angle from the IMU
        target_angle: Desired angle setpoint
        pid_error: Error between target and actual angle
        p_term: Proportional term calculated by PID controller
        i_term: Integral term calculated by PID controller
        d_term: Derivative term calculated by PID controller
        pid_output: Overall PID controller output
        motor_output: Optional motor output percentage (defaults to abs(pid_output) if not provided)
    """
    with LOCK:
        try:
            # Validate inputs - convert to floats and handle potential errors
            try:
                timestamp = float(timestamp)
                actual_angle = float(actual_angle)
                target_angle = float(target_angle)
                pid_error = float(pid_error)
                p_term = float(p_term)
                i_term = float(i_term) 
                d_term = float(d_term)
                pid_output = float(pid_output)
                
                # If motor_output is not provided, calculate it from pid_output
                if motor_output is None:
                    motor_output = min(100, abs(float(pid_output)))
                else:
                    motor_output = float(motor_output)
            except (ValueError, TypeError) as e:
                logger.warning(f"Data point validation error: {e}")
                return
                
            # Create the data point
            data_point = {
                "timestamp": timestamp,
                "actual_angle": actual_angle,
                "target_angle": target_angle,
                "pid_error": pid_error,
                "p_term": p_term,
                "i_term": i_term,
                "d_term": d_term,
                "pid_output": pid_output,
                "motor_output": motor_output
            }
            
            # Add to the data array
            PID_DATA.append(data_point)
            
            # Trim the data if it exceeds the maximum - remove multiple points if needed
            # to avoid frequent trimming operations
            if len(PID_DATA) > CONFIG['max_data_points']:
                # Remove the oldest 10% of data points when limit is reached
                points_to_remove = max(1, int(CONFIG['max_data_points'] * 0.1))
                PID_DATA[:points_to_remove] = []
            
            # Log to CSV if enabled
            if CONFIG['csv_logging'] and CSV_WRITER:
                try:
                    CSV_WRITER.writerow([
                        timestamp, actual_angle, target_angle, pid_error, 
                        p_term, i_term, d_term, pid_output, motor_output
                    ])
                    CSV_FILE.flush()
                except Exception as e:
                    logger.error(f"Error logging to CSV: {e}")
        except Exception as e:
            logger.error(f"Error adding data point: {e}")

# Start CSV logging
def start_csv_logging():
    global CSV_FILE, CSV_WRITER
    try:
        if CSV_FILE is None:
            # Create logs directory if it doesn't exist
            os.makedirs('logs', exist_ok=True)
            
            # Create a new CSV file with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_path = f'logs/pid_data_{timestamp}.csv'
            
            CSV_FILE = open(csv_path, 'w', newline='')
            CSV_WRITER = csv.writer(CSV_FILE)
            
            # Write header
            CSV_WRITER.writerow([
                'timestamp', 'actual_angle', 'target_angle', 'pid_error',
                'p_term', 'i_term', 'd_term', 'pid_output', 'motor_output'
            ])
            
            logger.info(f"Started CSV logging to {csv_path}")
    except Exception as e:
        logger.error(f"Error starting CSV logging: {e}")
        CONFIG['csv_logging'] = False

# Stop CSV logging
def stop_csv_logging():
    global CSV_FILE, CSV_WRITER
    try:
        if CSV_FILE:
            CSV_FILE.close()
            CSV_FILE = None
            CSV_WRITER = None
            logger.info("Stopped CSV logging")
    except Exception as e:
        logger.error(f"Error stopping CSV logging: {e}")

# Clean shutdown
def shutdown_server():
    global SERVER_STARTED
    try:
        if SERVER_STARTED:
            logger.info("Shutting down server...")
            # Stop CSV logging
            stop_csv_logging()
            
            # Final save of parameters
            if os.path.exists(CONFIG['pid_config_file']):
                save_pid_params()
                
            # Clear any in-memory data that's no longer needed
            with LOCK:
                PID_DATA.clear()
                
            SERVER_STARTED = False
            logger.info("Server shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Start the web server
def start_server(host='0.0.0.0', port=5000, debug=False):
    global SERVER_INSTANCE, SERVER_STARTED
    
    # Don't start if already running
    if SERVER_STARTED:
        logger.warning("Server is already running")
        return
    
    try:
        # Load PID parameters from file
        load_pid_params()
        
        # Register clean shutdown
        atexit.register(shutdown_server)
        signal.signal(signal.SIGINT, lambda sig, frame: shutdown_server())
        
        # Get the actual IP address that others can use to connect
        actual_ip = "localhost"
        try:
            # This is a more reliable way to get the actual IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 1))  # Connect to Google's DNS
            actual_ip = s.getsockname()[0]
            s.close()
        except:
            # Fallback to hostname-based detection
            import socket
            hostname = socket.gethostname()
            try:
                actual_ip = socket.gethostbyname(hostname)
                if actual_ip.startswith('127.'):
                    # Try to find a non-loopback address
                    actual_ip = socket.gethostbyname(f"{hostname}.local")
            except:
                pass
        
        # Start the server in a separate thread
        SERVER_STARTED = True
        if not debug:
            SERVER_INSTANCE = threading.Thread(
                target=lambda: app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False),
                daemon=True
            )
            SERVER_INSTANCE.start()
            
            # Print a clean, simple message for the user
            print("\n✅ Web server started successfully!")
            print(f"📊 Access the dashboard at: http://{actual_ip}:{port}")
            print("─────────────────────────────────────────────────────")
            
            logger.info(f"Server started on http://{host}:{port}/")
        else:
            # For debug mode, run in main thread
            logger.info(f"Starting server in debug mode on http://{host}:{port}/")
            app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
    except Exception as e:
        SERVER_STARTED = False
        logger.error(f"Error starting server: {e}")
        print(f"\n❌ Could not start web server: {e}")
        print("Try using a different port (e.g., start_server(port=8080))")
        raise

# Stop the web server
def stop_server():
    global SERVER_STARTED, SERVER_INSTANCE
    
    if not SERVER_STARTED:
        logger.warning("Server is not running")
        return
    
    try:
        # Call shutdown handler without logging (quieter operation)
        try:
            if SERVER_STARTED:
                # Stop CSV logging
                stop_csv_logging()
                
                # Final save of parameters
                if os.path.exists(CONFIG['pid_config_file']):
                    with LOCK:
                        with open(CONFIG['pid_config_file'], 'w') as f:
                            json.dump(PID_PARAMS, f, indent=4)
                
                # Clear any in-memory data that's no longer needed
                with LOCK:
                    PID_DATA.clear()
                    
                SERVER_STARTED = False
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        # If server was started in a thread, wait for it to finish
        # This is best-effort since Flask doesn't have a clean shutdown mechanism
        # when running in a thread
        if SERVER_INSTANCE and SERVER_INSTANCE.is_alive():
            logger.info("Waiting for server thread to finish...")
            # Wait for a shorter time to avoid blocking
            SERVER_INSTANCE.join(timeout=0.5)
            
        SERVER_INSTANCE = None
        logger.info("Server stopped")
    except Exception as e:
        logger.error(f"Error stopping server: {e}")
    finally:
        SERVER_STARTED = False

# Check if server is running
def is_server_running():
    return SERVER_STARTED

# If this file is run directly, start the server
if __name__ == '__main__':
    try:
        start_server(debug=True)
    except KeyboardInterrupt:
        shutdown_server()
        logger.info("Server stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Server error: {e}") 