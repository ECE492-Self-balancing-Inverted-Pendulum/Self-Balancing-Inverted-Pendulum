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
    Simple mode to display IMU readings in the terminal.
    Press Ctrl+C to exit.
    
    Args:
        imu: IMU reader instance
    """
    print("\nIMU Reading Mode")
    print("-----------------")
    print("Displaying live IMU readings. Press Ctrl+C to exit.")
    print()
    
    try:
        while True:
            try:
                # Get IMU data
                data = imu.get_imu_data()
                roll = data.get('roll', 0)
                pitch = data.get('pitch', 0)  # Try to get pitch if available
                angular_velocity = data.get('angular_velocity', 0)
                
                # Print on a single line with carriage return
                output = f"\rRoll: {roll:+6.2f}° | "
                if 'pitch' in data:
                    output += f"Pitch: {pitch:+6.2f}° | "
                output += f"Angular Velocity: {angular_velocity:+6.2f}°/s"
                
                print(output, end='', flush=True)
                
            except Exception as e:
                print(f"\rIMU read error: {e}", end='', flush=True)
            
            # Simple delay
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\nIMU reading mode exited.")


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
    
    try:
        while sample_count < num_samples and time.time() - start_time < calibration_time:
            # Get raw IMU data - exactly as IMU_reader does
            accel_raw = imu.imu.acceleration
            gyro_raw = imu.imu.gyro
            
            # Convert gyro data from rad/s to deg/s - just like in IMU_reader
            gyro_deg = np.array(gyro_raw) * (180 / np.pi)
            
            # Important: we collect RAW data WITHOUT applying any calibration offsets
            # or orientation corrections, as IMU_reader will apply these itself
            
            # Add raw samples to our lists
            accel_samples_x.append(accel_raw[0])
            accel_samples_y.append(accel_raw[1])
            accel_samples_z.append(accel_raw[2])
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
        accel_offset_x = float(np.mean(accel_samples_x))
        accel_offset_y = float(np.mean(accel_samples_y))
        accel_offset_z = float(np.mean(accel_samples_z) - 9.81)  # Subtract gravity
        
        gyro_offset_x = float(np.mean(gyro_samples_x))
        gyro_offset_y = float(np.mean(gyro_samples_y))
        gyro_offset_z = float(np.mean(gyro_samples_z))
        
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
        
        # Create Python lists for the calibration offsets
        accel_offset = [float(accel_offset_x), float(accel_offset_y), float(accel_offset_z)]
        gyro_offset = [float(gyro_offset_x), float(gyro_offset_y), float(gyro_offset_z)]
        
        # Load the current config
        config = load_config()
        
        # Update the config with the new calibration values
        config['IMU_ACCEL_OFFSET'] = accel_offset
        config['IMU_GYRO_OFFSET'] = gyro_offset
        
        # Save the updated config
        save_config(config)
        
        # Verify the save worked
        verify_config = load_config()
        if 'IMU_ACCEL_OFFSET' in verify_config and 'IMU_GYRO_OFFSET' in verify_config:
            print("\nCalibration values saved successfully!")
            print(f"Accel offsets: {verify_config['IMU_ACCEL_OFFSET']}")
            print(f"Gyro offsets: {verify_config['IMU_GYRO_OFFSET']}")
            print("\nPlease restart the program for the new calibration to take effect.")
            return True
        else:
            print("\nError: Failed to save calibration values.")
            return False
    
    except Exception as e:
        print(f"\nError during calibration: {e}")
        print("Calibration failed. Please try again.")
        return False
 