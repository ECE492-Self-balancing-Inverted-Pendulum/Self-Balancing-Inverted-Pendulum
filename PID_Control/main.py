#!/usr/bin/env python3
"""
Self-Balancing Robot Main Program

This is the main entry point for the self-balancing robot application.
It provides a menu-driven interface to access different modes of operation
including balancing, motor testing, parameter tuning, and diagnostics.

The program integrates several components:
- IMU sensor reading and filtering
- PID control for balance
- Motor control for movement
- Web-based dashboard for real-time monitoring and tuning
- Configuration management

Features:
- Multiple operation modes accessible through a simple menu
- Self-balancing with real-time parameter tuning
- IMU diagnostics and tuning
- Motor testing
- Web interface for remote monitoring and control

Usage:
    Simply run this file to start the application:
        python main.py
    
    Then follow the on-screen menu to select the desired operation mode.
"""

# Standard library imports
import time
import threading
import select
import sys
import tty
import termios
import socket

# Component imports
from motorController import MotorControl, DualMotorControl
from IMU_reader import IMUReader
from config import CONFIG, HARDWARE_CONFIG
from balance_controller import BalanceController
from tuning import PIDTuner
from pid_controller import PIDController

# Check which import method works for the web server
try:
    # First try to import from the webpage package
    import webpage
    # Load the functions we need (lazy loading)
    start_server = webpage.start_server
    stop_server = webpage.stop_server
    add_data_point = webpage.add_data_point
    set_pid_params = webpage.set_pid_params
    set_update_callback = webpage.set_update_callback
    update_pid_params = webpage.update_pid_params
    print("Successfully imported webpage package")
except ImportError:
    try:
        # Fall back to direct import if package doesn't work
        import web_server
        # Load the functions we need
        start_server = web_server.start_server
        stop_server = web_server.stop_server
        add_data_point = web_server.add_data_point
        set_pid_params = web_server.set_pid_params
        set_update_callback = web_server.set_update_callback
        update_pid_params = web_server.update_pid_params
        print("Successfully imported web_server module")
    except ImportError:
        # Define dummy functions if neither import works
        print("Warning: Web dashboard functionality not available - missing modules")
        def start_server(*args, **kwargs): print("Web server not available")
        def stop_server(): pass
        def add_data_point(*args, **kwargs): pass
        def set_pid_params(*args, **kwargs): pass
        def set_update_callback(*args): pass
        def update_pid_params(*args): pass

# Global IMU reference for testing functions
IMU = None

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def input_available():
    """Check if input is available without blocking."""
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

# -----------------------------------------------------------------------------
# Mode Implementations
# -----------------------------------------------------------------------------

def runtime_parameter_tuning(pid_tuner, balance_controller):
    """
    Self-balancing mode with web dashboard for parameter tuning.
    Shows minimal output in the terminal while allowing parameter tuning via web interface.
    """
    # Import here to avoid circular imports
    from config import CONFIG, load_config, save_config
    
    print("\nSelf-Balancing Mode with Web Dashboard")
    
    # Get local IP address for easier connection
    local_ip = get_local_ip()
    server_port = 8080
    print(f"Web dashboard: http://{local_ip}:{server_port}")
    
    # Ensure we're using the latest config
    load_config()
    
    # Start the web server
    try:
        start_server(port=server_port)
        print("Web dashboard running")
        print("Connect to the web interface to see real-time data")
        print("Press 'Q' to return to menu")
    except Exception as e:
        print(f"Error starting server: {e}")
        return
    
    # Initialize web interface with parameters from config file
    # Note: set_pid_params still uses positional args (kp, ki, kd, target_angle)
    # but internally it will map to the correct parameter names
    set_pid_params(
        CONFIG['P_GAIN'],
        CONFIG['I_GAIN'],
        CONFIG['D_GAIN'],
        0.0  # Target angle is always 0 for balancing
    )
    
    # Update controller with latest config values
    balance_controller.update_from_config(CONFIG)
    
    # Set up callback for parameter updates
    def params_update_callback(params):
        # First, update the config file (source of truth)
        # This correctly maps the frontend parameters to CONFIG keys
        if 'kp' in params:
            CONFIG['P_GAIN'] = params['kp']
        if 'ki' in params:
            CONFIG['I_GAIN'] = params['ki']
        if 'kd' in params:
            CONFIG['D_GAIN'] = params['kd']
        if 'alpha' in params:
            CONFIG['IMU_FILTER_ALPHA'] = params['alpha']
        if 'sample_time' in params:
            # Convert from milliseconds (web interface) to seconds (controller)
            CONFIG['SAMPLE_TIME'] = params['sample_time'] / 1000.0
            # Ensure it's within reasonable bounds
            if CONFIG['SAMPLE_TIME'] > 1.0:  # More than 1 second is likely an error
                print(f"Warning: Sample time value suspiciously large ({CONFIG['SAMPLE_TIME']}), defaulting to 0.01")
                CONFIG['SAMPLE_TIME'] = 0.01
        if 'deadband' in params:
            CONFIG['MOTOR_DEADBAND'] = params['deadband']
        if 'max_speed' in params:
            CONFIG['MAX_MOTOR_SPEED'] = params['max_speed']
        if 'zero_threshold' in params:
            CONFIG['ZERO_THRESHOLD'] = params['zero_threshold']
        
        # Save config to file
        save_config(CONFIG)
        
        # Update the controller with new config
        balance_controller.update_from_config(CONFIG)
    
    # Register the callback
    set_update_callback(params_update_callback)
    
    # Create debug callback function
    def debug_callback(debug_info):
        # Extract data
        roll = debug_info['roll']
        output = debug_info['output']
        motor_output = debug_info.get('motor_output', abs(output))
        pid_info = debug_info['pid']
        
        # Send data to web dashboard only, no terminal output
        add_data_point(
            actual_angle=roll,
            target_angle=0.0,
            error=-roll,  # Error is target (0) - actual
            p_term=pid_info['p_term'],
            i_term=pid_info['i_term'],
            d_term=pid_info['d_term'],
            pid_output=output,
            motor_output=motor_output
        )
    
    # Start balancing with debug display
    balance_controller.start_balancing(debug_callback)
    
    # Clean up when done
    print("\nStopping web server...")
    stop_server()
    print("Returned to main menu.")

def get_local_ip():
    """Get local IP address for display purposes."""
    try:
        # Create a socket to determine the IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

# -----------------------------------------------------------------------------
# Main Application
# -----------------------------------------------------------------------------

def main():
    """
    Main function with menu for different modes.
    
    Example:
        # Run the application
        main()
    """
    # Initialize IMU with configuration from CONFIG
    # This compensates for the orientation of the IMU (upside-down or normal)
    imu = IMUReader(
        alpha=CONFIG.get('IMU_FILTER_ALPHA', 0.3),
        upside_down=CONFIG.get('IMU_UPSIDE_DOWN', True)
    )
    
    # Initialize motor control - Now using DualMotorControl for both motors
    motors = DualMotorControl(
        motor_a_in1=HARDWARE_CONFIG['MOTOR_A_IN1_PIN'],
        motor_a_in2=HARDWARE_CONFIG['MOTOR_A_IN2_PIN'],
        motor_b_in1=HARDWARE_CONFIG['MOTOR_B_IN1_PIN'],
        motor_b_in2=HARDWARE_CONFIG['MOTOR_B_IN2_PIN']
    )
    
    # Create balance controller and PID tuner
    balance_controller = BalanceController(imu, motors, CONFIG)
    pid_tuner = PIDTuner(CONFIG)
    
    # Make IMU accessible to test functions
    global IMU
    IMU = imu
    
    # Define a function to print the menu to avoid code duplication
    def print_menu():
        print("\nSelf-Balancing Robot Control System")
        print("--------------------------------------")
        print("Using dual motors for better stability and control")
        print("Choose an option:")
        print("1. Start Self-Balancing Mode")
        print("2. Motor Test Mode")
        print("3. Full Parameter Tuning")
        print("4. Quick PID Tuning")
        print("5. Runtime Parameter Tuning")
        print("6. IMU Tuning Mode")
        print("Q. Quit Program")
    
    # Print menu the first time
    print_menu()
    
    try:
        while True:
            print("\nEnter choice [1-6, q]: ", end='', flush=True)
            choice = input().lower()
            
            if choice == '1':
                # Start the self-balancing mode - no web interface
                try:
                    balance_controller.start_balancing(debug_callback=None)
                except KeyboardInterrupt:
                    print("\nBalancing interrupted by user.")
                # Reprint menu after returning from submenu
                print_menu()
                    
            elif choice == '2':
                motors.dual_motor_test()
                # Reprint menu after returning from submenu
                print_menu()
                
            elif choice == '3':
                # Update config with tuned parameters
                pid_tuner.tune_parameters()
                # Update the balance controller with the new configuration
                balance_controller = BalanceController(imu, motors, CONFIG)
                # Reprint menu after returning from submenu
                print_menu()
                
            elif choice == '4':
                # Quick tuning of just the P, I, and D gains
                pid_tuner.tune_specific_parameters(['P_GAIN', 'I_GAIN', 'D_GAIN', 'IMU_FILTER_ALPHA', 'DIRECTION_CHANGE_BOOST'])
                # Update the balance controller with the new configuration
                balance_controller = BalanceController(imu, motors, CONFIG)
                # Reprint menu after returning from submenu
                print_menu()
                
            elif choice == '5':
                runtime_parameter_tuning(pid_tuner, balance_controller)
                # Reprint menu after returning from submenu
                print_menu()
                
            elif choice == '6':
                imu.imu_tuning_mode()
                # Reprint menu after returning from submenu
                print_menu()
                
            elif choice == 'q':
                print("Exiting program...")
                motors.cleanup()
                break
                
            else:
                # If invalid option selected, reprint the menu
                print("\nInvalid option. Please try again.")
                print_menu()
    except KeyboardInterrupt:
        print("\nProgram interrupted.")
    finally:
        try:
            motors.cleanup()
            stop_server()  # Ensure web server is stopped when exiting
        except:
            pass
        print("Goodbye!")

# -----------------------------------------------------------------------------
# Application Entry Point
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    main()
