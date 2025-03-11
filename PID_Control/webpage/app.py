"""
Flask application setup for the PID controller web dashboard.
"""
import os
import json
import csv
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, request

# Global variables to store PID data
pid_data = {
    'time': [],
    'actual_angle': [],
    'target_angle': [],
    'pid_error': [],
    'p_term': [],
    'i_term': [],
    'd_term': [],
    'pid_output': []  # Add pid_output to store the final PID controller output
}

# Configuration
config = {
    'updateInterval': 500,  # ms
    'csvLogging': False,
    'callback': None
}

# PID parameters
pid_params = {
    'kp': 0.0,
    'ki': 0.0,
    'kd': 0.0,
    'target_angle': 0.0
}

# CSV logging
csv_file = None
csv_writer = None

def create_app():
    """
    Create and configure the Flask application
    
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/api/pid_data')
    def get_pid_data():
        return jsonify(pid_data)
    
    @app.route('/api/config', methods=['GET', 'POST'])
    def handle_config():
        if request.method == 'POST':
            data = request.json
            if 'updateInterval' in data:
                config['updateInterval'] = data['updateInterval']
            if 'csvLogging' in data:
                config['csvLogging'] = data['csvLogging']
                if data['csvLogging']:
                    start_csv_logging()
                else:
                    stop_csv_logging()
            return jsonify({'status': 'success'})
        else:
            return jsonify({
                'updateInterval': config['updateInterval'],
                'csvLogging': config['csvLogging']
            })
    
    @app.route('/api/pid_params', methods=['GET', 'POST'])
    def handle_pid_params():
        if request.method == 'POST':
            data = request.json
            # Update pid_params with values from the request
            for key in ['kp', 'ki', 'kd', 'target_angle']:
                if key in data:
                    pid_params[key] = data[key]
            
            # Call callback if provided (to update the actual PID controller)
            if config['callback']:
                config['callback'](pid_params)
                
            return jsonify({'status': 'success'})
        else:
            return jsonify(pid_params)
    
    @app.route('/api/restart_pid', methods=['POST'])
    def restart_pid():
        # This endpoint is for restarting the PID controller
        # The actual restart is handled by the main application
        return jsonify({'status': 'success'})
    
    # Add a catch-all route for old API paths to maintain compatibility
    @app.route('/data')
    def get_data_legacy():
        # Redirect old API endpoint to new one
        return get_pid_data()
    
    @app.route('/pid_params', methods=['GET', 'POST'])
    def handle_params_legacy():
        # Redirect old API endpoint to new one
        return handle_pid_params()
    
    @app.route('/restart_pid', methods=['POST'])
    def restart_pid_legacy():
        # Redirect old API endpoint to new one
        return restart_pid()
    
    @app.route('/config', methods=['GET', 'POST'])
    def handle_config_legacy():
        # Redirect old API endpoint to new one
        return handle_config()
    
    @app.errorhandler(Exception)
    def handle_error(e):
        print(f"Error in Flask app: {e}")
        return jsonify({"error": str(e)}), 500
    
    return app 

def add_data_point(actual_angle, target_angle, error, p_term, i_term, d_term, pid_output=0):
    """Add a data point to the PID data store"""
    current_time = time.time()
    
    # Add the data point
    pid_data['time'].append(current_time)
    pid_data['actual_angle'].append(actual_angle)
    pid_data['target_angle'].append(target_angle)
    pid_data['pid_error'].append(error)
    pid_data['p_term'].append(p_term)
    pid_data['i_term'].append(i_term)
    pid_data['d_term'].append(d_term)
    pid_data['pid_output'].append(pid_output)  # Store the PID output
    
    # Trim data if it gets too large (keep last 1000 points)
    if len(pid_data['time']) > 1000:
        for key in pid_data:
            pid_data[key] = pid_data[key][-1000:]
    
    # Log to CSV if enabled
    if config['csvLogging'] and csv_writer:
        try:
            csv_writer.writerow([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                current_time,
                actual_angle,
                target_angle,
                error,
                p_term,
                i_term,
                d_term,
                pid_output  # Include PID output in CSV
            ])
        except Exception as e:
            print(f"Error writing to CSV: {e}")

def start_csv_logging():
    """Start logging PID data to a CSV file"""
    global csv_file, csv_writer
    try:
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        log_filename = f"logs/pid_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        csv_file = open(log_filename, 'w', newline='')
        csv_writer = csv.writer(csv_file)
        
        # Write header
        csv_writer.writerow([
            'Timestamp', 'Time', 'Actual Angle', 'Target Angle', 
            'Error', 'P Term', 'I Term', 'D Term', 'PID Output'  # Add PID Output to header
        ])
        
        print(f"CSV logging started: {log_filename}")
        return True
    except Exception as e:
        print(f"Error starting CSV logging: {e}")
        return False

def stop_csv_logging():
    """Stop logging PID data to CSV"""
    global csv_file, csv_writer
    try:
        if csv_file:
            csv_file.close()
            csv_file = None
            csv_writer = None
            print("CSV logging stopped")
            return True
    except Exception as e:
        print(f"Error stopping CSV logging: {e}")
        return False

def set_pid_params(kp, ki, kd, target_angle):
    """Set the PID parameters"""
    pid_params['kp'] = kp
    pid_params['ki'] = ki
    pid_params['kd'] = kd
    pid_params['target_angle'] = target_angle

def update_pid_params(params_dict):
    """Update PID parameters from a dictionary"""
    for key, value in params_dict.items():
        if key in pid_params:
            pid_params[key] = value

def set_update_callback(callback):
    """Set a callback function for when PID parameters are updated via the web interface"""
    config['callback'] = callback 