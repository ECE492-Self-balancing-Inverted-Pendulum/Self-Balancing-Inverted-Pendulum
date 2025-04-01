"""
Utility Functions for the Self-Balancing Robot

This module contains utility functions that support the operation of the
self-balancing robot but are not core to its operation.

Functions:
- imu_tuning_mode: Interactive tool for tuning IMU filter settings
- motor_test_mode: Interactive tool for testing motor controls
- calibrate_imu: Calibrate IMU sensor when robot is at rest
"""

import time
import sys
import termios
import tty
import select
import numpy as np
import json

try:
    from config import save_config, load_config
    CONFIG = load_config()
except ImportError:
    CONFIG = {}
    print("Failed to load configuration.")

def imu_tuning_mode(imu):
    """
    Interactive mode for tuning IMU responsiveness.
    Displays IMU data on a single line and allows adjusting the Madgwick filter gain.
    
    Args:
        imu: IMUReader instance to tune
    
    Controls:
        +: Increase gain (more responsive)
        -: Decrease gain (smoother)
        r: Reset to default (0.8)
        t: Toggle IMU upside-down setting
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
    
    # Get current gain value
    current_gain = imu.ahrs.settings.gain
    
    print("\nCurrent filter gain:", current_gain)
    print("Higher gain = more responsive but may be less stable")
    print("Lower gain = more stable but slower to respond")
    print("\nCommands:")
    print("+: Increase gain by 0.05 (more responsive)")
    print("-: Decrease gain by 0.05 (smoother)")
    print("r: Reset to default (0.8)")
    print("t: Toggle IMU upside-down setting")
    print("q: Exit IMU tuning mode")
    print("\nPress any key at any time to use a command.")
    
    # Save terminal settings to restore later
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        # Set terminal to raw mode
        tty.setraw(sys.stdin.fileno())
        
        running = True
        while running:
            # Get IMU data
            imu_data = imu.get_imu_data()
            roll = imu_data['roll']
            angular_velocity = imu_data['angular_velocity']
            
            # Get current gain value
            current_gain = imu.ahrs.settings.gain
            
            # Print data on the same line using \r
            sys.stdout.write(f"\rRoll: {roll:+6.2f}° | Angular Vel: {angular_velocity:+6.2f}°/s | Gain: {current_gain:.2f} | Upside-down: {imu.upside_down}")
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
                    new_gain = min(current_gain + 0.05, 0.95)
                    imu.set_gain(new_gain)
                    sys.stdout.write(f"\nIncreased gain to {new_gain:.2f}")
                    sys.stdout.flush()
                
                elif user_input == '-':
                    new_gain = max(current_gain - 0.05, 0.05)
                    imu.set_gain(new_gain)
                    sys.stdout.write(f"\nDecreased gain to {new_gain:.2f}")
                    sys.stdout.flush()
                
                elif user_input == 'r':
                    default_gain = 0.8  # Default gain value
                    imu.set_gain(default_gain)
                    sys.stdout.write(f"\nReset gain to default ({default_gain:.2f})")
                    sys.stdout.flush()
                
                elif user_input == 't':
                    # Toggle the upside-down setting
                    imu.upside_down = not imu.upside_down
                    
                    # Update config
                    CONFIG['IMU_UPSIDE_DOWN'] = imu.upside_down
                    save_config(CONFIG)
                    
                    sys.stdout.write(f"\nToggled IMU orientation. Upside-down: {imu.upside_down}")
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

def calibrate_imu(imu):
    """
    Calibrate the IMU sensor by measuring offsets when robot is at rest.
    
    This function collects multiple samples of IMU data while the robot is stationary
    and uses them to calculate offsets for accelerometer and gyroscope.
    
    Args:
        imu: IMUReader instance to calibrate
    
    Returns:
        bool: True if calibration was successful, False otherwise
    """
    print("\nIMU Calibration Mode")
    print("--------------------")
    print("This mode will calibrate your IMU sensor for accurate readings.")
    print("Please follow these steps:")
    print("1. Place the robot on a flat, level surface")
    print("2. Make sure the robot is completely still")
    print("3. Keep the robot still during the entire calibration process (5 seconds)")
    
    # Ask user confirmation to start
    print("\nIs the robot still on a level surface? (y/n): ", end='', flush=True)
    response = input().lower()
    if response != 'y':
        print("Calibration cancelled.")
        return False
    
    print("\nStarting calibration. Keep the robot still...")
    print("Collecting data for 5 seconds...")
    
    # Collect multiple samples over 5 seconds
    accel_samples_x = []
    accel_samples_y = []
    accel_samples_z = []
    gyro_samples_x = []
    gyro_samples_y = []
    gyro_samples_z = []
    
    # Set the number of samples and duration
    num_samples = 100
    calibration_time = 5.0  # seconds
    
    start_time = time.time()
    sample_count = 0
    
    # Print a progress indicator
    sys.stdout.write("\nCalibrating: [" + " " * 20 + "] 0%")
    sys.stdout.flush()
    
    while sample_count < num_samples and time.time() - start_time < calibration_time:
        # Get raw IMU data
        raw_data = imu.imu.acceleration, imu.imu.gyro
        accel, gyro = raw_data
        
        # Add samples to our lists
        accel_samples_x.append(accel[0])
        accel_samples_y.append(accel[1])
        accel_samples_z.append(accel[2])
        
        # Convert gyro data from rad/s to deg/s
        gyro_deg = np.array(gyro) * (180 / np.pi)
        gyro_samples_x.append(gyro_deg[0])
        gyro_samples_y.append(gyro_deg[1])
        gyro_samples_z.append(gyro_deg[2])
        
        # Update progress bar every 5 samples
        if sample_count % 5 == 0:
            progress = int((sample_count / num_samples) * 20)
            percentage = int((sample_count / num_samples) * 100)
            sys.stdout.write(f"\rCalibrating: [" + "#" * progress + " " * (20 - progress) + f"] {percentage}%")
            sys.stdout.flush()
        
        sample_count += 1
        time.sleep(calibration_time / num_samples)
    
    # Complete the progress bar
    sys.stdout.write("\rCalibrating: [" + "#" * 20 + "] 100%")
    sys.stdout.flush()
    print("\nCalibration data collected!")
    
    # Calculate offsets based on averages
    accel_offset_x = np.mean(accel_samples_x)
    accel_offset_y = np.mean(accel_samples_y)
    accel_offset_z = np.mean(accel_samples_z) - 9.81  # Subtract gravity
    
    gyro_offset_x = np.mean(gyro_samples_x)
    gyro_offset_y = np.mean(gyro_samples_y)
    gyro_offset_z = np.mean(gyro_samples_z)
    
    # Display results
    print("\nCalibration Results:")
    print(f"Accelerometer offsets: X={accel_offset_x:.6f}, Y={accel_offset_y:.6f}, Z={accel_offset_z:.6f}")
    print(f"Gyroscope offsets: X={gyro_offset_x:.6f}, Y={gyro_offset_y:.6f}, Z={gyro_offset_z:.6f}")
    
    # Confirm saving the calibration
    print("\nDo you want to save these calibration values? (y/n): ", end='', flush=True)
    response = input().lower()
    if response != 'y':
        print("Calibration cancelled. Values not saved.")
        return False
    
    # Create arrays for the CONFIG dictionary
    accel_offset = [float(accel_offset_x), float(accel_offset_y), float(accel_offset_z)]
    gyro_offset = [float(gyro_offset_x), float(gyro_offset_y), float(gyro_offset_z)]
    
    # Save directly to CONFIG
    CONFIG['IMU_ACCEL_OFFSET'] = accel_offset
    CONFIG['IMU_GYRO_OFFSET'] = gyro_offset
    CONFIG['IMU_UPSIDE_DOWN'] = imu.upside_down
    
    
    # Save CONFIG
    save_config(CONFIG)
    
    print("\nCalibration values saved successfully to config!")
    print("Please restart the program for the new calibration to take effect.")
    
    return True
