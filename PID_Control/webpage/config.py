"""
Configuration settings for the web dashboard.
"""
import os
import threading

# Global variables to store data
PID_DATA = {
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
WEB_CONFIG = {
    'time_window': 10,  # Default time window in seconds
    'update_interval': 200,  # Update interval in milliseconds
    'is_running': False,
    'csv_logging': True,
    'restart_requested': False
}

# Lock for thread-safe access to data
DATA_LOCK = threading.Lock()

# File paths
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')
CSS_DIR = os.path.join(STATIC_DIR, 'css')
JS_DIR = os.path.join(STATIC_DIR, 'js')
CSV_FILE = 'pid_data.csv'

# Ensure directories exist
for directory in [STATIC_DIR, TEMPLATES_DIR, CSS_DIR, JS_DIR]:
    os.makedirs(directory, exist_ok=True) 