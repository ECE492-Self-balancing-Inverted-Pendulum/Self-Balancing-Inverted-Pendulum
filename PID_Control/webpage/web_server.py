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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pid_web_server')

# Global variables
PID_DATA = []
CONFIG = {
    'update_interval': 500,  # milliseconds
    'csv_logging': False,
    'time_window': 10,  # seconds
    'max_data_points': 1000,  # Maximum number of data points to store
    'pid_config_file': 'pid_config.json'
}
PID_PARAMS = {
    'kp': 1.0,
    'ki': 0.1,
    'kd': 0.01,
    'target_angle': 0.0
}
CSV_FILE = None
CSV_WRITER = None
SERVER_INSTANCE = None
SERVER_STARTED = False
LOCK = threading.Lock()

# Create Flask app
app = Flask(__name__, static_folder='static')

# Load PID parameters from file if it exists
def load_pid_params():
    global PID_PARAMS
    try:
        if os.path.exists(CONFIG['pid_config_file']):
            with open(CONFIG['pid_config_file'], 'r') as f:
                loaded_params = json.load(f)
                logger.info(f"Loaded PID parameters: {loaded_params}")
                PID_PARAMS.update(loaded_params)
    except Exception as e:
        logger.error(f"Error loading PID parameters: {e}")

# Save PID parameters to file
def save_pid_params():
    try:
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
        return jsonify(PID_PARAMS)
    except Exception as e:
        logger.error(f"Error getting PID parameters: {e}")
        return jsonify({"error": str(e)}), 500

# API endpoint to update PID parameters
@app.route('/api/pid_params', methods=['POST'])
def update_pid_params():
    try:
        data = request.json
        
        # Update the parameters
        for key in ['kp', 'ki', 'kd', 'target_angle']:
            if key in data:
                PID_PARAMS[key] = float(data[key])
        
        logger.info(f"Updated PID parameters: {PID_PARAMS}")
        
        # Save to file
        save_pid_params()
        
        # Return the updated parameters
        return jsonify(PID_PARAMS)
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
    try:
        return send_from_directory('static', path)
    except Exception as e:
        logger.error(f"Error serving static file: {e}")
        return jsonify({"error": str(e)}), 500

# Add a new data point
def add_data_point(timestamp, actual_angle, target_angle, pid_error, p_term, i_term, d_term, pid_output):
    with LOCK:
        # Create the data point
        data_point = {
            "timestamp": timestamp,
            "actual_angle": actual_angle,
            "target_angle": target_angle,
            "pid_error": pid_error,
            "p_term": p_term,
            "i_term": i_term,
            "d_term": d_term,
            "pid_output": pid_output
        }
        
        # Add to the data array
        PID_DATA.append(data_point)
        
        # Trim the data if it exceeds the maximum
        if len(PID_DATA) > CONFIG['max_data_points']:
            PID_DATA.pop(0)
        
        # Log to CSV if enabled
        if CONFIG['csv_logging'] and CSV_WRITER:
            try:
                CSV_WRITER.writerow([
                    timestamp, actual_angle, target_angle, pid_error, 
                    p_term, i_term, d_term, pid_output
                ])
                CSV_FILE.flush()
            except Exception as e:
                logger.error(f"Error logging to CSV: {e}")

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
                'p_term', 'i_term', 'd_term', 'pid_output'
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
            stop_csv_logging()
            SERVER_STARTED = False
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
        
        # Start the server in a separate thread
        SERVER_STARTED = True
        if not debug:
            SERVER_INSTANCE = threading.Thread(
                target=lambda: app.run(host=host, port=port, debug=debug, use_reloader=False),
                daemon=True
            )
            SERVER_INSTANCE.start()
            logger.info(f"Server started on http://{host}:{port}/")
        else:
            # For debug mode, run in main thread
            logger.info(f"Starting server in debug mode on http://{host}:{port}/")
            app.run(host=host, port=port, debug=debug, use_reloader=False)
    except Exception as e:
        SERVER_STARTED = False
        logger.error(f"Error starting server: {e}")
        raise

# Stop the web server
def stop_server():
    global SERVER_STARTED
    
    if not SERVER_STARTED:
        logger.warning("Server is not running")
        return
    
    try:
        shutdown_server()
        logger.info("Server stopped")
    except Exception as e:
        logger.error(f"Error stopping server: {e}")

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