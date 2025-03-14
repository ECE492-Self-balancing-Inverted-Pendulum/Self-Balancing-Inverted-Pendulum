"""
PID Controller Web Dashboard

This package provides a web-based interface for visualizing and tuning 
a PID controller in real-time.
"""

import logging
import time

# Configure logging specifically for the compatibility layer
logger = logging.getLogger('pid_web_compatibility')

# Import from the web server implementation
try:
    from .web_server import (
        start_server,
        stop_server,
        add_data_point as new_add_data_point,
        is_server_running,
        PID_PARAMS,
        save_pid_params,
        CONFIG
    )
except ImportError as e:
    logger.error(f"Error importing from web_server: {e}")
    # Define fallback dummy functions if imports fail
    def start_server(*args, **kwargs): 
        logger.error("Web server module not available")
    def stop_server(): pass
    def new_add_data_point(*args, **kwargs): pass
    def is_server_running(): return False
    PID_PARAMS = {'kp': 0.0, 'ki': 0.0, 'kd': 0.0, 'target_angle': 0.0}
    def save_pid_params(): pass
    CONFIG = {}

# Backward compatibility functions with improved error handling
def set_pid_params(kp, ki, kd, target_angle):
    """
    Legacy function for backward compatibility - sets PID parameters
    
    Args:
        kp: Proportional gain
        ki: Integral gain
        kd: Derivative gain
        target_angle: Target angle setpoint
    """
    try:
        PID_PARAMS['kp'] = float(kp)
        PID_PARAMS['ki'] = float(ki)
        PID_PARAMS['kd'] = float(kd)
        PID_PARAMS['target_angle'] = float(target_angle)
        save_pid_params()
    except Exception as e:
        logger.error(f"Error in set_pid_params: {e}")

def update_pid_params(params_dict):
    """
    Legacy function for backward compatibility - updates PID parameters from a dictionary
    
    Args:
        params_dict: Dictionary containing parameter key-value pairs
    """
    try:
        for key, value in params_dict.items():
            if key in PID_PARAMS:
                PID_PARAMS[key] = float(value)
        save_pid_params()
    except Exception as e:
        logger.error(f"Error in update_pid_params: {e}")

def set_update_callback(callback):
    """
    Legacy function for backward compatibility - parameters are now saved to file automatically
    
    In the new implementation, this function is kept for API compatibility but doesn't
    directly use the callback. Parameter changes are persisted via JSON file.
    
    Args:
        callback: Function to be called when parameters are updated (ignored in new implementation)
    """
    # This function is kept for compatibility
    if callable(callback):
        # Store the callback in case we want to use it later
        global _update_callback
        _update_callback = callback
        logger.info("Parameter update callback registered (note: direct callbacks not used in new implementation)")

def add_data_point(actual_angle, target_angle, error, p_term, i_term, d_term, pid_output=0, motor_output=None):
    """
    Legacy function for backward compatibility - adds a data point with auto-generated timestamp
    
    Args:
        actual_angle: Measured angle from the IMU
        target_angle: Desired angle setpoint
        error: Error between target and actual angle
        p_term: Proportional term calculated by PID controller
        i_term: Integral term calculated by PID controller
        d_term: Derivative term calculated by PID controller
        pid_output: Overall PID controller output (default: 0)
        motor_output: Motor output percentage (default: None, will use abs(pid_output) if not provided)
    """
    try:
        timestamp = time.time()
        # Use motor_output if provided, otherwise default to abs(pid_output)
        motor_out = motor_output if motor_output is not None else abs(pid_output)
        new_add_data_point(
            timestamp=timestamp,
            actual_angle=actual_angle,
            target_angle=target_angle,
            pid_error=error,
            p_term=p_term,
            i_term=i_term,
            d_term=d_term,
            pid_output=pid_output,
            motor_output=motor_out
        )
    except Exception as e:
        logger.error(f"Error in add_data_point: {e}")

# Store a reference to the update callback if provided
_update_callback = None

__all__ = [
    'start_server',
    'stop_server',
    'add_data_point',
    'set_pid_params',
    'update_pid_params',
    'set_update_callback',
    'is_server_running',
    'PID_PARAMS'
] 