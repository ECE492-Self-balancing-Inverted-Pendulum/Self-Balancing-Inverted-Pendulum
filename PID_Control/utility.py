"""
Utility Functions for the Self-Balancing Robot

This module contains utility functions that support the operation of the
self-balancing robot but are not core to its operation.

Functions:
- imu_tuning_mode: Interactive tool for tuning IMU filter settings
- motor_test_mode: Interactive tool for testing motor controls
"""

import time
import sys
import termios
import tty
import select
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
    
    # Get current alpha value from CONFIG directly
    current_alpha = CONFIG.get('IMU_FILTER_ALPHA', 0.2)
    
    print("\nCurrent alpha value:", current_alpha)
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
    
    # Save terminal settings to restore later
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        # Set terminal to raw mode
        tty.setraw(sys.stdin.fileno())
        
        running = True
        while running:
            # Get IMU data - this also updates the ALPHA value inside IMU
            imu_data = imu.get_imu_data()
            roll = imu_data['roll']
            angular_velocity = imu_data['angular_velocity']
            
            # Get current alpha value directly from CONFIG
            current_alpha = CONFIG.get('IMU_FILTER_ALPHA', 0.2)
            
            # Print data on the same line using \r
            sys.stdout.write(f"\rRoll: {roll:+6.2f}° | Angular Vel: {angular_velocity:+6.2f}°/s | Alpha: {current_alpha:.2f} | Upside-down: {imu.MOUNTED_UPSIDE_DOWN}")
            sys.stdout.flush()
            
            # Check if there's any input without blocking
            if select.select([sys.stdin], [], [], 0.1)[0]:
                # Read a single character
                user_input = sys.stdin.read(1)
                
                if user_input == 'q':
                    sys.stdout.write("\nExiting IMU tuning mode.")
                    sys.stdout.flush()
                    running = False
                
                elif user_input == '+':
                    new_alpha = min(current_alpha + 0.05, 0.95)
                    imu.set_alpha(new_alpha)
                    sys.stdout.write(f"\nIncreased alpha to {new_alpha:.2f}")
                    sys.stdout.flush()
                    
                    # Update the config
                    CONFIG['IMU_FILTER_ALPHA'] = new_alpha
                    save_config(CONFIG)
                
                elif user_input == '-':
                    new_alpha = max(current_alpha - 0.05, 0.05)
                    imu.set_alpha(new_alpha)
                    sys.stdout.write(f"\nDecreased alpha to {new_alpha:.2f}")
                    sys.stdout.flush()
                    
                    # Update the config
                    CONFIG['IMU_FILTER_ALPHA'] = new_alpha
                    save_config(CONFIG)
                
                elif user_input == 'r':
                    default_alpha = 0.2  # Default alpha value
                    imu.set_alpha(default_alpha)
                    sys.stdout.write(f"\nReset alpha to default ({default_alpha:.2f})")
                    sys.stdout.flush()
                    
                    # Update the config
                    CONFIG['IMU_FILTER_ALPHA'] = default_alpha
                    save_config(CONFIG)
                
                elif user_input == 't':
                    # Toggle the upside-down setting
                    imu.MOUNTED_UPSIDE_DOWN = not imu.MOUNTED_UPSIDE_DOWN
                    sys.stdout.write(f"\nToggled IMU orientation. Upside-down: {imu.MOUNTED_UPSIDE_DOWN}")
                    sys.stdout.flush()
                    
                    # Update the config
                    CONFIG['IMU_UPSIDE_DOWN'] = imu.MOUNTED_UPSIDE_DOWN
                    save_config(CONFIG)
                
                elif user_input == 'd':
                    current_alpha = CONFIG.get('IMU_FILTER_ALPHA', 0.2)
                    sys.stdout.write(f"\nCurrent settings: Alpha: {current_alpha:.2f}, Upside-down: {imu.MOUNTED_UPSIDE_DOWN}")
                    sys.stdout.flush()
                
                # Clear line after key press
                time.sleep(0.5)
                
            else:
                # Small delay if no input
                time.sleep(0.05)
    
    except KeyboardInterrupt:
        sys.stdout.write("\nIMU tuning mode interrupted.")
        sys.stdout.flush()
    
    finally:
        # Restore terminal settings
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
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
    has_dual_motors = hasattr(motor, 'set_motors_speed')
    
    # Current speed and direction
    current_speed = 0
    current_direction = "stop"
    
    running = True
    
    while running:
        # Simple input method without threading
        print("\nEnter command [w/s/p/space/q]: ", end='', flush=True)
        try:
            user_input = input().lower()
            
            if user_input == 'q':
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
                print("Moving forward")
            
            elif user_input == 's':
                # Move backward at 100% speed
                current_speed = 100
                current_direction = "counterclockwise"
                if has_dual_motors:
                    motor.set_motors_speed(current_speed, current_direction)
                else:
                    motor.set_motor_speed(current_speed, current_direction)
                print("Moving backward")
            
            elif user_input == ' ' or user_input == '':  # Space key or Enter
                # Stop motors
                current_speed = 0
                current_direction = "stop"
                if has_dual_motors:
                    motor.stop_motors()
                else:
                    motor.stop_motor()
                print("Motors stopped")
            
            elif user_input == 'p':
                # Prompt for custom PWM value
                print("Enter PWM value (-100 to 100): ", end='', flush=True)
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
                    
                    print("PWM value applied")
                except ValueError:
                    print("Invalid input. Please enter a number between -100 and 100.")
            
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
    print("Motor test mode exited. Motors stopped.")