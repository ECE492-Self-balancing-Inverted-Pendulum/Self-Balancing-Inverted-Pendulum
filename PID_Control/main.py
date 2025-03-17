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
from webpage import start_server, stop_server, add_data_point, set_pid_params, update_pid_params, set_update_callback

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
    Shows real-time angle output in the terminal while allowing parameter tuning via web interface.
    """
    # Import here to avoid circular imports
    from config import CONFIG, load_config, save_config
    
    print("\n🤖 Self-Balancing Mode with Web Dashboard")
    print("Connect to the same WiFi network as the robot")
    
    # Get local IP address for easier connection
    local_ip = get_local_ip()
    server_port = 8080
    print(f"Web dashboard: http://{local_ip}:{server_port}")
    
    # Ensure we're using the latest config
    load_config()
    
    # Start the web server
    try:
        start_server(port=server_port)
        print("✅ Web dashboard running")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return
    
    # Initialize web interface with parameters from config file
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
        if 'kp' in params:
            CONFIG['P_GAIN'] = params['kp']
        if 'ki' in params:
            CONFIG['I_GAIN'] = params['ki']
        if 'kd' in params:
            CONFIG['D_GAIN'] = params['kd']
        if 'alpha' in params:
            CONFIG['IMU_FILTER_ALPHA'] = params['alpha']
        if 'sample_time' in params:
            CONFIG['SAMPLE_TIME'] = params['sample_time'] / 1000.0  # Convert ms to seconds
        if 'deadband' in params:
            CONFIG['MOTOR_DEADBAND'] = params['deadband']
        if 'max_speed' in params:
            CONFIG['MAX_MOTOR_SPEED'] = params['max_speed']
        
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
        
        # Initialize timestamp for output rate limiting
        if not hasattr(debug_callback, 'last_output_time'):
            debug_callback.last_output_time = 0
        
        # Display to terminal (rate-limited to every 200ms)
        current_time = time.time()
        if current_time - debug_callback.last_output_time > 0.2:
            # Clear line and write updated values
            sys.stdout.write("\r" + " " * 80)
            sys.stdout.write(f"\rAngle: {roll:6.2f}° | Output: {output:6.1f} | Motor: {motor_output:3.0f}% | P: {pid_info['p_term']:6.1f} | I: {pid_info['i_term']:6.1f} | D: {pid_info['d_term']:6.1f}")
            sys.stdout.flush()
            debug_callback.last_output_time = current_time
        
        # Send data to web dashboard
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
    
    print("Starting balancing. Press 'Q' to return to menu.")
    
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
        print("\n🤖 Self-Balancing Robot Control System")
        print("--------------------------------------")
        print("Using dual motors for better stability and control")
        print("Choose an option:")
        print("1. 🚀 Start Self-Balancing Mode")
        print("2. 🔌 Motor Test Mode")
        print("3. 🎛️ Full Parameter Tuning")
        print("4. 🔧 Quick PID Tuning")
        print("5. 📊 Runtime Parameter Tuning")
        print("6. 🧭 IMU Tuning Mode")
        print("Q. ❌ Quit Program")
    
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
