"""
Motor Controller Module for Self-Balancing Robot

This module provides classes for controlling DC motors through a motor driver
using PWM (Pulse Width Modulation). It supports both single and dual motor
configurations, making it suitable for various robot designs.

Key features:
- Single motor control with direction and speed adjustment
- Dual motor control with synchronized movement
- Individual control of dual motors for differential drive
- PWM-based speed control for smooth operation
- Proper GPIO cleanup to prevent pin conflicts

The motor controller translates the output from the PID controller into the
appropriate GPIO signals to control the motors, which physically balance the robot.
It handles details like motor direction, speed scaling, and motor driver interfacing.

Example Usage:
    # Single Motor Example
    from motorController import MotorControl
    
    # Initialize a single motor controller
    motor = MotorControl(in1=13, in2=19)
    
    # Run motor at 75% speed clockwise
    motor.set_motor_speed(75, "clockwise")
    
    # Stop the motor
    motor.stop_motor()
    
    # Clean up when done
    motor.cleanup()
    
    # Dual Motor Example
    from motorController import DualMotorControl
    
    # Initialize dual motors
    motors = DualMotorControl(
        motor_a_in1=12, motor_a_in2=18,
        motor_b_in1=13, motor_b_in2=19
    )
    
    # Run both motors forward
    motors.set_motors_speed(80, "clockwise")
    
    # Different directions (for turning)
    motors.set_individual_speeds(50, "clockwise", 50, "counterclockwise")
    
    # Stop both motors
    motors.stop_motors()
    
    # Clean up
    motors.cleanup()
"""

import RPi.GPIO as GPIO
import time
import sys

class MotorControl:
    """
    A simple motor control class for PWM-based DC motors using a motor driver.
    """

    def __init__(self, in1, in2, pwm_freq=1000):
        """
        Initializes the motor controller.

        :param in1: GPIO pin for motor IN1
        :param in2: GPIO pin for motor IN2
        :param pwm_freq: PWM frequency in Hz (default: 1000Hz)
        """
        GPIO.setwarnings(False)  # ✅ Disable "channel already in use" warning
        GPIO.setmode(GPIO.BCM)

        self.IN1 = in1
        self.IN2 = in2
        self.pwm_freq = pwm_freq

        GPIO.setup(self.IN1, GPIO.OUT)
        GPIO.setup(self.IN2, GPIO.OUT)

        self.pwm1 = GPIO.PWM(self.IN1, self.pwm_freq)
        self.pwm2 = GPIO.PWM(self.IN2, self.pwm_freq)
        self.pwm1.start(0)
        self.pwm2.start(0)

    def set_motor_speed(self, speed, direction):
        """
        Sets motor speed and direction.

        :param speed: Desired speed (0 to 100% PWM)
        :param direction: "clockwise" or "counterclockwise"
        """
        speed = max(0, min(100, speed))

        if direction not in ["clockwise", "counterclockwise", "stop"]:
            print("[ERROR] Invalid direction. Use 'clockwise', 'counterclockwise', or 'stop'.")
            return

        if direction == "clockwise":
            self.pwm1.ChangeDutyCycle(speed)
            self.pwm2.ChangeDutyCycle(0)
        elif direction == "counterclockwise":
            self.pwm1.ChangeDutyCycle(0)
            self.pwm2.ChangeDutyCycle(speed)
        elif direction == "stop":
            self.pwm1.ChangeDutyCycle(0)
            self.pwm2.ChangeDutyCycle(0)

    def stop_motor(self):
        """
        Stops the motor immediately.
        """
        self.set_motor_speed(0, "stop")

    def cleanup(self):
        """
        Cleans up GPIO settings.
        """
        self.stop_motor()
        self.pwm1.stop()
        self.pwm2.stop()
        GPIO.cleanup()
        print("[INFO] GPIO cleanup completed.")


class DualMotorControl:
    """
    Controller for two independent motor drivers, ensuring synchronized movement.
    Motor A and Motor B each have their own controller and pins.
    """
    
    def __init__(self, motor_a_in1, motor_a_in2, motor_b_in1, motor_b_in2, pwm_freq=1000):
        """
        Initializes both motor controllers with their respective pins.
        
        :param motor_a_in1: GPIO pin for Motor A IN1
        :param motor_a_in2: GPIO pin for Motor A IN2
        :param motor_b_in1: GPIO pin for Motor B IN1
        :param motor_b_in2: GPIO pin for Motor B IN2
        :param pwm_freq: PWM frequency in Hz (default: 1000Hz)
        """
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        
        # Create individual motor controllers
        self.motor_a = MotorControl(motor_a_in1, motor_a_in2, pwm_freq)
        self.motor_b = MotorControl(motor_b_in1, motor_b_in2, pwm_freq)
        
        print(f"[INFO] Dual motor controller initialized:")
        print(f"  - Motor A: IN1={motor_a_in1}, IN2={motor_a_in2}")
        print(f"  - Motor B: IN1={motor_b_in1}, IN2={motor_b_in2}")
    
    def set_motors_speed(self, speed, direction):
        """
        Sets both motors to the same speed and direction.
        
        :param speed: Desired speed (0 to 100% PWM)
        :param direction: "clockwise" or "counterclockwise"
        """
        # Set both motors to the same direction and speed
        self.motor_a.set_motor_speed(speed, direction)
        self.motor_b.set_motor_speed(speed, direction)
    
    def set_individual_speeds(self, speed_a, direction_a, speed_b, direction_b):
        """
        Sets each motor to different speeds and directions (use with caution).
        
        :param speed_a: Speed for Motor A (0 to 100%)
        :param direction_a: Direction for Motor A
        :param speed_b: Speed for Motor B (0 to 100%)
        :param direction_b: Direction for Motor B
        """
        self.motor_a.set_motor_speed(speed_a, direction_a)
        self.motor_b.set_motor_speed(speed_b, direction_b)
    
    def stop_motors(self):
        """
        Stops both motors immediately.
        """
        self.motor_a.stop_motor()
        self.motor_b.stop_motor()
    
    def cleanup(self):
        """
        Properly cleans up both motor controllers.
        """
        self.stop_motors()
        # Only call GPIO.cleanup() once, otherwise will generate errors
        self.motor_a.pwm1.stop()
        self.motor_a.pwm2.stop()
        self.motor_b.pwm1.stop()
        self.motor_b.pwm2.stop()
        GPIO.cleanup()
        print("[INFO] Dual motor controller cleaned up.")
        
    def dual_motor_test(self):
        """
        Test mode for independently testing both motors.
        
        Example:
            motors = DualMotorControl(
                motor_a_in1=12, motor_a_in2=18,
                motor_b_in1=13, motor_b_in2=19
            )
            motors.dual_motor_test()
        """
        print("\n🔌 Dual Motor Test Mode")
        print("----------------------")
        print("W: Both Motors Forward (100%)")
        print("S: Both Motors Reverse (100%)")
        print("A: Motor A Forward (100%)")
        print("D: Motor B Forward (100%)")
        print("Z: Motor A Reverse (100%)")
        print("X: Motor B Reverse (100%)")
        print("I: Get IMU Data")
        print("Q: Quit to Main Menu")
        print("-------------------------")
        
        # Initialize IMU instance once to avoid recreating it
        imu_instance = None
        try:
            # First, try to import from main
            try:
                from main import IMU
                if IMU is not None:
                    imu_instance = IMU
            except (ImportError, AttributeError):
                pass
                
            # If not found, create a new one
            if imu_instance is None:
                try:
                    from IMU_reader import IMUReader
                    imu_instance = IMUReader()
                except Exception as e:
                    print(f"Warning: IMU not available - {e}")
        except Exception as e:
            print(f"Warning: IMU initialization failed - {e}")
        
        try:
            while True:
                # Use sys.stdout.write to ensure the prompt appears on a clean line
                sys.stdout.write("\rEnter Command: ")
                sys.stdout.flush()
                
                # Use a single character read to get immediate response
                command = input().lower().strip()
                
                # Skip empty commands
                if not command:
                    continue
                
                if command == "w":
                    self.set_motors_speed(100, "clockwise")
                    print("Both motors running FORWARD at 100%")
                    
                elif command == "s":
                    self.set_motors_speed(100, "counterclockwise")
                    print("Both motors running REVERSE at 100%")
                    
                elif command == "a":
                    self.set_individual_speeds(100, "clockwise", 0, "stop")
                    print("Motor A running FORWARD at 100%")
                    
                elif command == "d":
                    self.set_individual_speeds(0, "stop", 100, "clockwise")
                    print("Motor B running FORWARD at 100%")
                    
                elif command == "z":
                    self.set_individual_speeds(100, "counterclockwise", 0, "stop")
                    print("Motor A running REVERSE at 100%")
                    
                elif command == "x":
                    self.set_individual_speeds(0, "stop", 100, "counterclockwise")
                    print("Motor B running REVERSE at 100%")
                    
                elif command == "i":
                    # Use the already initialized IMU instance
                    if imu_instance:
                        try:
                            imu_data = imu_instance.get_imu_data()
                            print(f"Roll: {imu_data['roll']:.2f}° | Angular Velocity: {imu_data['angular_velocity']:.2f}°/s")
                        except Exception as e:
                            print(f"Error getting IMU data: {e}")
                    else:
                        print("IMU not available")
                    
                elif command == "q":
                    print("Exiting dual motor test mode...")
                    self.stop_motors()
                    break
                    
                else:
                    print(f"Unknown command: '{command}'")
                
        except KeyboardInterrupt:
            print("\nTest interrupted.")
            self.stop_motors()
        finally:
            # Make sure motors are stopped when exiting
            self.stop_motors()


# Example usage
if __name__ == "__main__":
    # Example using single motor
    # motor = MotorControl(in1=13, in2=19)
    
    # Example using dual motors
    dual_motor = DualMotorControl(
        motor_a_in1=12, motor_a_in2=18,  # Motor A pins
        motor_b_in1=13, motor_b_in2=19   # Motor B pins
    )
    
    try:
        print("Running both motors forward at 50%...")
        dual_motor.set_motors_speed(50, "clockwise")
        time.sleep(3)
        
        print("Running both motors forward at 100%...")
        dual_motor.set_motors_speed(100, "clockwise")
        time.sleep(3)
        
        print("Stopping motors...")
        dual_motor.stop_motors()
    except KeyboardInterrupt:
        print("\nStopping motors.")
    finally:
        dual_motor.cleanup()

