#!/usr/bin/env python3
"""
Self-Balancing Robot Main Program

This is the main entry point for the self-balancing robot application.
It provides a menu-driven interface to access different modes of operation
including balancing, motor testing, parameter tuning, and diagnostics.

Features:
- Multiple operation modes accessible through a simple menu
- Self-balancing with real-time parameter tuning
- IMU diagnostics and tuning
- Motor testing
- Web dashboard for visualization

Usage:
    Simply run this file to start the application:
        python main.py
    
    Then follow the on-screen menu to select the desired operation mode.
"""

# Standard library imports
import time
import socket

# Component imports
from motorController import DualMotorControl
from IMU_reader import IMUReader
from config import CONFIG, HARDWARE_CONFIG
from balance_controller import BalanceController
from tuning import PIDTuner
from utility import imu_tuning_mode, motor_test_mode

# Import web dashboard functions
import web_dashboard

def get_local_ip():
    """Get local IP address for displaying web address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def web_dashboard_mode(balance_controller):
    """
    Run the self-balancing mode with web dashboard.
    
    Args:
        balance_controller: Balance controller instance
    """
    # Start the web server
    ip_address = get_local_ip()
    port = 8080
    web_dashboard.start_server(host='0.0.0.0', port=port)
    print(f"\nWeb dashboard available at: http://{ip_address}:{port}")
    print("Press Ctrl+C to stop balancing and return to menu")
    
    # Define a callback function for real-time data updates
    def dashboard_callback(debug_info):
        roll = debug_info['roll']
        output = debug_info['output']
        web_dashboard.update_angle_data(roll, output)
    
    try:
        # Start balancing with the dashboard callback
        balance_controller.start_balancing(debug_callback=dashboard_callback)
    except KeyboardInterrupt:
        print("\nWeb dashboard mode interrupted by user")
    finally:
        # Stop the web server
        web_dashboard.stop_server()

def main():
    """
    Main function with menu for different modes.
    """
    # Initialize IMU with configuration from CONFIG
    # This compensates for the orientation of the IMU (upside-down or normal)
    imu = IMUReader()
    
    # Initialize motor control - Using DualMotorControl for both motors
    motors = DualMotorControl(
        motor_a_in1=HARDWARE_CONFIG['MOTOR_A_IN1_PIN'],
        motor_a_in2=HARDWARE_CONFIG['MOTOR_A_IN2_PIN'],
        motor_b_in1=HARDWARE_CONFIG['MOTOR_B_IN1_PIN'],
        motor_b_in2=HARDWARE_CONFIG['MOTOR_B_IN2_PIN']
    )
    
    # Create balance controller and PID tuner
    balance_controller = BalanceController(imu, motors)
    pid_tuner = PIDTuner(CONFIG)
    
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
        print("5. IMU Tuning Mode")
        print("6. Self-balancing Mode with Web Dashboard")
        print("Q. Quit Program")
    
    # Print menu the first time
    print_menu()
    
    try:
        while True:
            print("\nEnter choice [1-6, q]: ", end='', flush=True)
            choice = input().lower()
            
            if choice == '1':
                # Start the self-balancing mode
                try:
                    balance_controller.start_balancing()
                except KeyboardInterrupt:
                    print("\nBalancing interrupted by user.")
                # Reprint menu after returning from submenu
                print_menu()
                    
            elif choice == '2':
                # Use the motor_test_mode from utility module
                motor_test_mode(motors)
                # Reprint menu after returning from submenu
                print_menu()
                
            elif choice == '3':
                # Update config with tuned parameters
                pid_tuner.tune_parameters()
                # Reprint menu after returning from submenu
                print_menu()
                
            elif choice == '4':
                # Quick tuning of just the P, I, and D gains
                pid_tuner.tune_specific_parameters(['P_GAIN', 'I_GAIN', 'D_GAIN', 'IMU_FILTER_ALPHA'])
                # Reprint menu after returning from submenu
                print_menu()
                
            elif choice == '5':
                # Call the imu_tuning_mode from utility module
                imu_tuning_mode(imu)
                # Reprint menu after returning from submenu
                print_menu()
                
            elif choice == '6':
                # Start the self-balancing mode with web dashboard
                web_dashboard_mode(balance_controller)
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
        motors.cleanup()
        print("Goodbye!")

# Application Entry Point
if __name__ == "__main__":
    main()
