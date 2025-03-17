"""
PID Controller Web Dashboard

This package provides a web-based interface for visualizing and tuning 
a PID controller in real-time.
"""

import logging
import time
import threading

# Configure logging specifically for the compatibility layer
logger = logging.getLogger('pid_web_compatibility')

# Define module-level variables that will be populated by the web server module
PID_PARAMS = {'P_GAIN': 0.0, 'I_GAIN': 0.0, 'D_GAIN': 0.0, 'target_angle': 0.0, 'ZERO_THRESHOLD': 0.1}
CONFIG = {}
_update_callback = None
_web_server_module = None

# Functions that will be provided by the web server module
def _import_web_server():
    """Import the web server module on demand to avoid circular imports"""
    global _web_server_module
    if _web_server_module is None:
        try:
            from . import web_server as ws
            _web_server_module = ws
            # Update our module variables with the ones from web_server
            global PID_PARAMS, CONFIG
            PID_PARAMS.update(ws.PID_PARAMS)
            CONFIG.update(ws.CONFIG)
        except ImportError as e:
            logger.error(f"Error importing web_server: {e}")
            return None
    return _web_server_module

def start_server(host='0.0.0.0', port=8080, debug=False):
    """
    Start the web server on the specified host and port
    
    Args:
        host: Host address to bind to
        port: Port to listen on
        debug: Whether to run in debug mode
    """
    ws = _import_web_server()
    if ws is None:
        logger.error("Web server module not available")
        return
    
    return ws.start_server(host=host, port=port, debug=debug)

def stop_server():
    """Stop the web server"""
    ws = _import_web_server()
    if ws is None:
        logger.error("Web server module not available")
        return
    
    return ws.stop_server()

def is_server_running():
    """Check if the server is running"""
    ws = _import_web_server()
    if ws is None:
        logger.error("Web server module not available")
        return False
    
    return ws.is_server_running()

def save_pid_params():
    """Save PID parameters to file"""
    ws = _import_web_server()
    if ws is None:
        logger.error("Web server module not available")
        return
    
    return ws.save_pid_params()

def set_pid_params(kp, ki, kd, target_angle):
    """
    Set PID parameters
    
    Args:
        kp: Proportional gain
        ki: Integral gain
        kd: Derivative gain
        target_angle: Target angle setpoint
    """
    try:
        ws = _import_web_server()
        if ws is None:
            # Still update our local copy even if web_server is not available
            PID_PARAMS['P_GAIN'] = float(kp)
            PID_PARAMS['I_GAIN'] = float(ki)
            PID_PARAMS['D_GAIN'] = float(kd)
            PID_PARAMS['target_angle'] = float(target_angle)
            return
        
        ws.PID_PARAMS['P_GAIN'] = float(kp)
        ws.PID_PARAMS['I_GAIN'] = float(ki)
        ws.PID_PARAMS['D_GAIN'] = float(kd)
        ws.PID_PARAMS['target_angle'] = float(target_angle)
        ws.save_pid_params()
    except Exception as e:
        logger.error(f"Error in set_pid_params: {e}")

def update_pid_params(params_dict):
    """
    Update PID parameters from a dictionary
    
    Args:
        params_dict: Dictionary containing parameter key-value pairs
    """
    try:
        ws = _import_web_server()
        
        # Parameter name mapping from frontend to backend
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
        
        if ws is None:
            # Still update our local copy even if web_server is not available
            for key, value in params_dict.items():
                # Map frontend key to backend key if needed
                backend_key = param_mapping.get(key, key)
                if backend_key in PID_PARAMS:
                    PID_PARAMS[backend_key] = float(value)
            return
        
        for key, value in params_dict.items():
            # Map frontend key to backend key if needed
            backend_key = param_mapping.get(key, key)
            if backend_key in ws.PID_PARAMS:
                ws.PID_PARAMS[backend_key] = float(value)
        ws.save_pid_params()
    except Exception as e:
        logger.error(f"Error in update_pid_params: {e}")

def set_update_callback(callback):
    """
    Set a callback function to be called when parameters are updated via the web interface.
    
    The callback will be called with a dictionary of updated parameters.
    
    Args:
        callback: Function to be called when parameters are updated
    """
    # Store the callback for use when parameters are updated
    global _update_callback
    _update_callback = callback
    logger.info("Parameter update callback registered")

def trigger_update_callback(params):
    """
    Trigger the update callback with the provided parameters.
    
    Args:
        params: Dictionary of parameters to pass to the callback
    """
    if _update_callback and callable(_update_callback):
        try:
            _update_callback(params)
            logger.info("Parameter update callback triggered")
        except Exception as e:
            logger.error(f"Error in parameter update callback: {e}")

def add_data_point(actual_angle, target_angle, error, p_term, i_term, d_term, pid_output=0, motor_output=None):
    """
    Add a data point with auto-generated timestamp
    
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
        ws = _import_web_server()
        if ws is None:
            logger.error("Web server module not available, cannot add data point")
            return
        
        timestamp = time.time()
        # Use motor_output if provided, otherwise default to abs(pid_output)
        motor_out = motor_output if motor_output is not None else abs(pid_output)
        ws.add_data_point(
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

__all__ = [
    'start_server',
    'stop_server',
    'add_data_point',
    'set_pid_params',
    'update_pid_params',
    'set_update_callback',
    'trigger_update_callback',
    'is_server_running',
    'PID_PARAMS'
] 