"""
Data management for the PID controller web dashboard.
Handles data storage, processing, and CSV logging.
"""
import time
import csv
import os
from .config import PID_DATA, WEB_CONFIG, DATA_LOCK, CSV_FILE

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
    
    with DATA_LOCK:
        # Add new data
        PID_DATA['time'].append(current_time)
        PID_DATA['actual_angle'].append(actual_angle)
        PID_DATA['target_angle'].append(target_angle)
        PID_DATA['pid_error'].append(pid_error)
        PID_DATA['p_term'].append(p_term)
        PID_DATA['i_term'].append(i_term)
        PID_DATA['d_term'].append(d_term)
        PID_DATA['pid_output'].append(pid_output)
        
        # Trim data if it exceeds max_data_points
        if len(PID_DATA['time']) > PID_DATA['max_data_points']:
            for key in PID_DATA:
                if key != 'max_data_points':
                    PID_DATA[key] = PID_DATA[key][-PID_DATA['max_data_points']:]
        
        # Log to CSV if enabled
        if WEB_CONFIG.get('csv_logging', True):
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
    file_exists = os.path.isfile(CSV_FILE)
    
    try:
        with open(CSV_FILE, 'a', newline='') as file:
            writer = csv.writer(file)
            
            # Write header if the file doesn't exist
            if not file_exists:
                writer.writerow(['Timestamp', 'Actual Angle', 'Target Angle', 'PID Error', 
                                 'P Term', 'I Term', 'D Term', 'PID Output'])
            
            # Write data
            writer.writerow([timestamp, actual_angle, target_angle, pid_error, 
                             p_term, i_term, d_term, pid_output])
    except Exception as e:
        print(f"Error logging to CSV: {e}")

def clear_csv_file():
    """Clear the CSV file"""
    try:
        with open(CSV_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp', 'Actual Angle', 'Target Angle', 'PID Error', 
                             'P Term', 'I Term', 'D Term', 'PID Output'])
    except Exception as e:
        print(f"Error clearing CSV file: {e}")

def get_data_for_display():
    """
    Get data formatted for display, filtered by time window
    
    Returns:
        Dict containing filtered data arrays
    """
    with DATA_LOCK:
        # Calculate how many data points to return based on time window
        points_to_return = min(len(PID_DATA['time']), 
                              int(WEB_CONFIG['time_window'] * 10))  # Assuming 10Hz data rate
        
        if points_to_return == 0:
            return {
                'time': [],
                'actual_angle': [],
                'target_angle': [],
                'pid_error': [],
                'p_term': [],
                'i_term': [],
                'd_term': [],
                'pid_output': []
            }
        
        return {
            'time': PID_DATA['time'][-points_to_return:],
            'actual_angle': PID_DATA['actual_angle'][-points_to_return:],
            'target_angle': PID_DATA['target_angle'][-points_to_return:],
            'pid_error': PID_DATA['pid_error'][-points_to_return:],
            'p_term': PID_DATA['p_term'][-points_to_return:],
            'i_term': PID_DATA['i_term'][-points_to_return:],
            'd_term': PID_DATA['d_term'][-points_to_return:],
            'pid_output': PID_DATA['pid_output'][-points_to_return:]
        }

def clear_data():
    """Clear all stored data points"""
    with DATA_LOCK:
        for key in PID_DATA:
            if key != 'max_data_points':
                PID_DATA[key] = [] 