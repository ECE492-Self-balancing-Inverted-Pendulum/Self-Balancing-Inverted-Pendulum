"""
Utility Functions for the Self-Balancing Robot

This module contains utility functions that support the operation of the
self-balancing robot but are not core to its operation.

Functions:
- imu_tuning_mode: Interactive tool for tuning IMU filter settings
- motor_test_mode: Interactive tool for testing motor controls
"""

import time
from config import CONFIG, save_config

def imu_tuning_mode(imu):
    """
    Interactive mode for tuning IMU responsiveness.
    Displays IMU data on a single line and allows adjusting the alpha filter value.
    
    Args:
        imu: IMUReader instance to tune
    
    Controls:
        +: Increase alpha (more responsive)
        -: Decrease alpha (smoother)
        r: Reset to default (0.2)
        t: Toggle IMU upside-down setting
        d: Display current settings in detail
        q: Exit tuning mode
    
    Example:
        from utility import imu_tuning_mode
        from IMU_reader import IMUReader
        
        imu = IMUReader()
        imu_tuning_mode(imu)
    """
    print("\nIMU Tuning Mode")
    print("------------------")
    print("This mode allows you to adjust the IMU filter settings")
    print("to find the right balance between responsiveness and stability.")
    print("\nCurrent alpha value:", imu.ALPHA)
    print("Higher alpha = more responsive but noisier")
    print("Lower alpha = smoother but slower to respond")
    print("\nCommands:")
    print("+: Increase alpha by 0.05 (more responsive)")
    print("-: Decrease alpha by 0.05 (smoother)")
    print("r: Reset to default (0.2)")
    print("t: Toggle IMU upside-down setting")
    print("d: Display current values")
    print("q: Exit IMU tuning mode")
    print("\nPress any key at any time to use a command.")
    
    running = True
    
    while running:
        # Get IMU data
        imu_data = imu.get_imu_data()
        roll = imu_data['roll']
        angular_velocity = imu_data['angular_velocity']
        
        # Print data on the same line using \r
        print(f"\rRoll: {roll:+6.2f}° | Angular Vel: {angular_velocity:+6.2f}°/s | Alpha: {imu.ALPHA:.2f} | Upside-down: {imu.MOUNTED_UPSIDE_DOWN}", end='', flush=True)
        
        # Small delay to prevent flooding the terminal
        time.sleep(0.1)
        
        # Check for keypress - simple non-blocking approach
        try:
            # Wait for very short time for key input
            user_input = input_with_timeout(0.1)
            
            if user_input:
                if user_input == 'q':
                    print("\nExiting IMU tuning mode.")
                    running = False
                
                elif user_input == '+':
                    new_alpha = min(imu.ALPHA + 0.05, 0.95)
                    imu.set_alpha(new_alpha)
                    print(f"\nIncreased alpha to {imu.ALPHA:.2f}")
                    
                    # Update the config
                    CONFIG['IMU_FILTER_ALPHA'] = imu.ALPHA
                    save_config(CONFIG)
                
                elif user_input == '-':
                    new_alpha = max(imu.ALPHA - 0.05, 0.05)
                    imu.set_alpha(new_alpha)
                    print(f"\nDecreased alpha to {imu.ALPHA:.2f}")
                    
                    # Update the config
                    CONFIG['IMU_FILTER_ALPHA'] = imu.ALPHA
                    save_config(CONFIG)
                
                elif user_input == 'r':
                    default_alpha = 0.2  # Default alpha value
                    imu.set_alpha(default_alpha)
                    print(f"\nReset alpha to default ({default_alpha:.2f})")
                    
                    # Update the config
                    CONFIG['IMU_FILTER_ALPHA'] = imu.ALPHA
                    save_config(CONFIG)
                
                elif user_input == 't':
                    # Toggle the upside-down setting
                    imu.MOUNTED_UPSIDE_DOWN = not imu.MOUNTED_UPSIDE_DOWN
                    print(f"\nToggled IMU orientation. Upside-down: {imu.MOUNTED_UPSIDE_DOWN}")
                    
                    # Update the config
                    CONFIG['IMU_UPSIDE_DOWN'] = imu.MOUNTED_UPSIDE_DOWN
                    save_config(CONFIG)
                
                elif user_input == 'd':
                    print(f"\nCurrent settings: Alpha: {imu.ALPHA:.2f}, Upside-down: {imu.MOUNTED_UPSIDE_DOWN}")
        
        except KeyboardInterrupt:
            print("\nIMU tuning mode interrupted.")
            running = False
    
    print("\nIMU tuning mode exited.")


def motor_test_mode(motor):
    """
    Interactive mode for testing motor controls.
    Allows controlling motor speed with keyboard commands.
    
    Args:
        motor: Motor controller instance (single or dual)
    
    Controls:
        w: Move forward at 100% speed
        s: Move backward at 100% speed
        p: Enter custom PWM value (-100 to 100)
        space: Stop motors
        q: Exit motor test mode
    
    Example:
        from utility import motor_test_mode
        from motorController import DualMotorControl
        
        motors = DualMotorControl(...)
        motor_test_mode(motors)
    """
    print("\nMotor Test Mode")
    print("------------------")
    print("This mode allows you to test the motors.")
    print("\nCommands:")
    print("w: Move forward at 100% speed")
    print("s: Move backward at 100% speed")
    print("p: Enter custom PWM value (-100 to 100)")
    print("space: Stop motors")
    print("q: Exit motor test mode")
    
    # Check if we're using dual motors
    import inspect
    has_dual_motors = hasattr(motor, 'set_motors_speed')
    
    # Current speed and direction
    current_speed = 0
    current_direction = "stop"
    
    running = True
    
    while running:
        # Print current status
        print(f"\rMotor Status: {current_speed}% {current_direction}", end='', flush=True)
        
        # Check for keypress
        try:
            user_input = input_with_timeout(0.1)
            
            if user_input:
                if user_input == 'q':
                    print("\nExiting motor test mode.")
                    running = False
                    # Stop motors before exiting
                    if has_dual_motors:
                        motor.stop_motors()
                    else:
                        motor.stop_motor()
                
                elif user_input == 'w':
                    # Move forward at 100% speed
                    current_speed = 100
                    current_direction = "clockwise"
                    if has_dual_motors:
                        motor.set_motors_speed(current_speed, current_direction)
                    else:
                        motor.set_motor_speed(current_speed, current_direction)
                    print(f"\nMoving forward at {current_speed}% speed")
                
                elif user_input == 's':
                    # Move backward at 100% speed
                    current_speed = 100
                    current_direction = "counterclockwise"
                    if has_dual_motors:
                        motor.set_motors_speed(current_speed, current_direction)
                    else:
                        motor.set_motor_speed(current_speed, current_direction)
                    print(f"\nMoving backward at {current_speed}% speed")
                
                elif user_input == ' ':  # Space key
                    # Stop motors
                    current_speed = 0
                    current_direction = "stop"
                    if has_dual_motors:
                        motor.stop_motors()
                    else:
                        motor.stop_motor()
                    print("\nMotors stopped")
                
                elif user_input == 'p':
                    # Prompt for custom PWM value
                    print("\nEnter PWM value (-100 to 100): ", end='', flush=True)
                    try:
                        pwm_input = input().strip()
                        pwm_value = float(pwm_input)
                        
                        # Ensure value is within bounds
                        pwm_value = max(-100, min(100, pwm_value))
                        
                        # Set direction based on PWM value
                        if pwm_value > 0:
                            current_direction = "clockwise"
                            current_speed = pwm_value
                        elif pwm_value < 0:
                            current_direction = "counterclockwise"
                            current_speed = abs(pwm_value)
                        else:
                            current_direction = "stop"
                            current_speed = 0
                        
                        # Apply to motors
                        if current_direction == "stop":
                            if has_dual_motors:
                                motor.stop_motors()
                            else:
                                motor.stop_motor()
                        else:
                            if has_dual_motors:
                                motor.set_motors_speed(current_speed, current_direction)
                            else:
                                motor.set_motor_speed(current_speed, current_direction)
                        
                        print(f"\nSet motors to {current_speed}% {current_direction}")
                    except ValueError:
                        print("\nInvalid input. Please enter a number between -100 and 100.")
                
        except KeyboardInterrupt:
            print("\nMotor test mode interrupted.")
            running = False
            # Stop motors before exiting
            if has_dual_motors:
                motor.stop_motors()
            else:
                motor.stop_motor()
    
    # Ensure motors are stopped when exiting
    if has_dual_motors:
        motor.stop_motors()
    else:
        motor.stop_motor()
    print("\nMotor test mode exited. Motors stopped.")


def input_with_timeout(timeout):
    """
    Simple non-blocking input function that returns None if no input is available.
    This avoids using termios/tty while still allowing checking for keypresses.
    
    Args:
        timeout: Time to wait for input in seconds
    
    Returns:
        User input or None if no input available
    """
    import threading
    import queue
    
    input_queue = queue.Queue()
    
    def input_thread():
        try:
            text = input()
            input_queue.put(text)
        except:
            input_queue.put(None)
    
    # Start the input thread
    thread = threading.Thread(target=input_thread)
    thread.daemon = True
    thread.start()
    
    # Wait for specified timeout
    thread.join(timeout)
    
    # Check if we got input
    if not input_queue.empty():
        return input_queue.get()
    return None