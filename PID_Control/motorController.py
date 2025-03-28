"""
Motor Controller Module for Self-Balancing Robot

This module provides classes for controlling DC motors through GPIO pins on a Raspberry Pi.
It offers both single and dual motor control with common interfaces.

"""

import time
import sys
import RPi.GPIO as GPIO

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
            self.pwm2.ChangeDutyCycle(speed)
        elif direction == "counterclockwise":
            self.pwm1.ChangeDutyCycle(speed)
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
