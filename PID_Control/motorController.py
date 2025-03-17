"""
Motor Controller Module for Self-Balancing Robot

This module provides classes for controlling DC motors through GPIO pins on a Raspberry Pi.
It offers both single and dual motor control with common interfaces.

Modified to work on non-Raspberry Pi systems with a mock GPIO implementation.
"""

import time
import sys

# Try to import RPi.GPIO module, or create a mock if not available
try:
    import RPi.GPIO as GPIO
    USING_REAL_GPIO = True
except ImportError:
    # Create a mock GPIO module for testing on non-Raspberry Pi systems
    print("RPi.GPIO not available, using mock implementation for testing")
    USING_REAL_GPIO = False
    
    # Mock GPIO module
    class MockGPIO:
        OUT = 1
        IN = 0
        BCM = 1
        BOARD = 0
        
        @staticmethod
        def setmode(mode):
            print(f"[MOCK] GPIO.setmode({mode})")
        
        @staticmethod
        def setup(pin, mode):
            print(f"[MOCK] GPIO.setup({pin}, {mode})")
        
        @staticmethod
        def output(pin, value):
            print(f"[MOCK] GPIO.output({pin}, {value})")
        
        @staticmethod
        def cleanup():
            print("[MOCK] GPIO.cleanup()")
    
    # Mock PWM class
    class MockPWM:
        def __init__(self, pin, freq):
            self.pin = pin
            self.freq = freq
            self.dc = 0
            print(f"[MOCK] PWM initialized on pin {pin} with frequency {freq}Hz")
        
        def start(self, dc):
            self.dc = dc
            print(f"[MOCK] PWM started with duty cycle {dc}%")
        
        def ChangeDutyCycle(self, dc):
            self.dc = dc
            print(f"[MOCK] PWM duty cycle changed to {dc}%")
        
        def stop(self):
            print(f"[MOCK] PWM stopped on pin {self.pin}")
    
    # Set up mock GPIO
    GPIO = MockGPIO
    GPIO.PWM = MockPWM

class MotorControl:
    """
    A simple motor control class for PWM-based DC motors using a motor driver.
    """

    def __init__(self, in1, in2, pwm_freq=1000):
        """
        Initializes the motor controller.

        :param in1: GPIO pin for motor IN1
        :param in2: GPIO pin for motor IN2
        :param pwm_freq: PWM frequency in Hz
        """
        self.in1_pin = in1
        self.in2_pin = in2
        self.pwm_freq = pwm_freq

        # Set up GPIO pins
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.in1_pin, GPIO.OUT)
        GPIO.setup(self.in2_pin, GPIO.OUT)

        # Set up PWM
        self.pwm1 = GPIO.PWM(self.in1_pin, self.pwm_freq)
        self.pwm2 = GPIO.PWM(self.in2_pin, self.pwm_freq)
        self.pwm1.start(0)
        self.pwm2.start(0)

        print(f"Motor controller initialized on pins {in1}, {in2}")

    def set_motor_speed(self, speed, direction):
        """
        Set the speed and direction of the motor.

        :param speed: Speed percentage (0-100)
        :param direction: 'clockwise' or 'counterclockwise'
        """
        # Ensure speed is within bounds
        speed = max(0, min(100, speed))
        
        if direction == "clockwise":
            self.pwm1.ChangeDutyCycle(speed)
            self.pwm2.ChangeDutyCycle(0)
        elif direction == "counterclockwise":
            self.pwm1.ChangeDutyCycle(0)
            self.pwm2.ChangeDutyCycle(speed)
        else:
            self.stop_motor()
            
        return (speed, direction)

    def stop_motor(self):
        """Stop the motor."""
        self.pwm1.ChangeDutyCycle(0)
        self.pwm2.ChangeDutyCycle(0)

    def cleanup(self):
        """Clean up GPIO resources."""
        self.stop_motor()
        self.pwm1.stop()
        self.pwm2.stop()
        # Don't call GPIO.cleanup() here since it might be shared with other components

class DualMotorControl:
    """
    Controls two DC motors for differential drive.
    """

    def __init__(self, motor_a_in1, motor_a_in2, motor_b_in1, motor_b_in2, pwm_freq=1000):
        """
        Initialize the dual motor controller.

        :param motor_a_in1: GPIO pin for motor A IN1
        :param motor_a_in2: GPIO pin for motor A IN2
        :param motor_b_in1: GPIO pin for motor B IN1
        :param motor_b_in2: GPIO pin for motor B IN2
        :param pwm_freq: PWM frequency in Hz
        """
        # Create two motor control instances
        self.motor_a = MotorControl(motor_a_in1, motor_a_in2, pwm_freq)
        self.motor_b = MotorControl(motor_b_in1, motor_b_in2, pwm_freq)
        
        print(f"Dual motor controller initialized")

    def set_motors_speed(self, speed, direction):
        """
        Set both motors to the same speed and direction.

        :param speed: Speed percentage (0-100)
        :param direction: 'clockwise' or 'counterclockwise'
        """
        self.motor_a.set_motor_speed(speed, direction)
        self.motor_b.set_motor_speed(speed, direction)
        
        return (speed, direction)

    def set_individual_speeds(self, speed_a, direction_a, speed_b, direction_b):
        """
        Set each motor to different speeds and directions.

        :param speed_a: Speed percentage for motor A (0-100)
        :param direction_a: Direction for motor A ('clockwise' or 'counterclockwise')
        :param speed_b: Speed percentage for motor B (0-100)
        :param direction_b: Direction for motor B ('clockwise' or 'counterclockwise')
        """
        self.motor_a.set_motor_speed(speed_a, direction_a)
        self.motor_b.set_motor_speed(speed_b, direction_b)

    def stop_motors(self):
        """Stop both motors."""
        self.motor_a.stop_motor()
        self.motor_b.stop_motor()

    def cleanup(self):
        """Clean up GPIO resources for both motors."""
        self.motor_a.cleanup()
        self.motor_b.cleanup()
        print("Dual motor controller cleaned up")

    def dual_motor_test(self):
        """Test both motors with a simple sequence."""
        print("\nDual Motor Test")
        print("Testing both motors. Press Ctrl+C to stop.")

        try:
            # Test sequence for both motors together
            print("Testing both motors forward (clockwise)...")
            self.set_motors_speed(70, "clockwise")
            time.sleep(2)
            
            print("Stopping motors...")
            self.stop_motors()
            time.sleep(1)
            
            print("Testing both motors backward (counterclockwise)...")
            self.set_motors_speed(70, "counterclockwise")
            time.sleep(2)
            
            print("Stopping motors...")
            self.stop_motors()
            time.sleep(1)
            
            # Individual motor tests
            print("Testing motor A only...")
            self.set_individual_speeds(70, "clockwise", 0, "clockwise")
            time.sleep(2)
            
            print("Testing motor B only...")
            self.set_individual_speeds(0, "clockwise", 70, "clockwise")
            time.sleep(2)
            
            # Differential drive test
            print("Testing differential drive (spin in place)...")
            self.set_individual_speeds(70, "clockwise", 70, "counterclockwise")
            time.sleep(2)
            
            print("Test complete, stopping motors.")
            self.stop_motors()
            
        except KeyboardInterrupt:
            print("\nTest interrupted by user.")
        finally:
            self.stop_motors()
            print("Motors stopped.") 