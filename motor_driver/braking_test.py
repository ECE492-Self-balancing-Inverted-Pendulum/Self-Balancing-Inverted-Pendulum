import time
import threading
import RPi.GPIO as GPIO
from lib.motorDriver import MotorControl

# Define motor control pins
IN1 = 13  # Motor direction and PWM speed control
IN2 = 19  # Motor direction and PWM speed control
ENCODER_A = 17  # Encoder signal A input
ENCODER_B = 27  # Encoder signal B input

# Encoder configuration
GPIO.setmode(GPIO.BCM)
GPIO.setup(ENCODER_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(ENCODER_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Initialize motor control
motor = MotorControl(IN1, IN2)

# Variables for RPM calculation
pulse_count = 0
rpm = 0
CPR = 1024  # Counts per revolution

# Encoder callback function
def encoder_callback(channel):
    global pulse_count
    pulse_count += 1

# Attach interrupt to encoder pin
GPIO.add_event_detect(ENCODER_A, GPIO.FALLING, callback=encoder_callback)

# Function to measure RPM
def measure_rpm():
    global pulse_count, rpm
    while True:
        pulse_count = 0  # Reset pulse count
        time.sleep(1)  # Measure for 1 second
        rpm = (pulse_count / CPR) * 60  # RPM calculation
        print(f"RPM: {rpm}")

# Start RPM measurement thread
rpm_thread = threading.Thread(target=measure_rpm, daemon=True)
rpm_thread.start()

# Motor operation
try:
    for _ in range(3):  # Repeat cycle three times
        print("\nRunning Motor at clockwise")
        motor.set_motor_speed(75, "clockwise")
        time.sleep(1)

        print("\nBraking Motor")
        motor.brake()

        print("\nRunning Motor at counterclockwise")
        motor.set_motor_speed(75, "counterclockwise")
        time.sleep(1)

        print("\nBraking Motor")
        motor.brake()

finally:
    print("\nStopping Motor")
    motor.stop_motor()

