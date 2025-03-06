import RPi.GPIO as GPIO
import time
import threading

# Use BCM pin numbering
GPIO.setmode(GPIO.BCM)

# Define motor control pins (both PWM capable)
IN1 = 13  # Motor direction and PWM speed control
IN2 = 19  # Motor direction and PWM speed control
ENCODER_A = 17  # Encoder signal A input
ENCODER_B = 27  # Encoder signal B input

# Set up GPIOs as output
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(ENCODER_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Encoder A input with pull-up
GPIO.setup(ENCODER_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Encoder B input with pull-up

# Set up PWM on both pins (1 kHz frequency)
pwm1 = GPIO.PWM(IN1, 1000)
pwm2 = GPIO.PWM(IN2, 1000)

# Start both PWM signals at 0% duty cycle (motor stopped)
pwm1.start(0)
pwm2.start(0)

# Variables for RPM calculation
pulse_count = 0
rpm = 0
CPR = 1024  # Counts per revolution

# Callback function for encoder pulses
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
        time.sleep(0.05)  # Measure for 1 second
        rpm = (pulse_count / CPR) * 1200  # RPM calculation
        print(f"                            RPM: {rpm}")

# Start RPM measurement thread
rpm_thread = threading.Thread(target=measure_rpm, daemon=True)
rpm_thread.start()

# Function to set motor speed and direction
def set_motor_speed(speed, direction):
    """
    Set motor speed and direction using PWM.

    speed: 0 to 100 (percentage)
    direction: 'clockwise' or 'counterclockwise'
    """
    if direction == "clockwise":
        pwm1.ChangeDutyCycle(speed)  # PWM on IN1
        pwm2.ChangeDutyCycle(0)      # IN2 off
    elif direction == "counterclockwise":
        pwm1.ChangeDutyCycle(0)      # IN1 off
        pwm2.ChangeDutyCycle(speed)  # PWM on IN2
    elif direction == "brake":
        pwm1.ChangeDutyCycle(80)
        pwm2.ChangeDutyCycle(80)
    else:
        pwm1.ChangeDutyCycle(0)  # Stop motor
        pwm2.ChangeDutyCycle(0)  # Stop motor

try:
    for _ in range(3):  # Repeat cycle three times
        # Rotate motor clockwise at 75% speed
        print("\nRunning Motor at clockwise")
        set_motor_speed(75, "clockwise")
        time.sleep(0.2)

        # Stop the motor
        print("\nBraking Motor")
        set_motor_speed(0, "brake")
        time.sleep(0.01)

        # Rotate motor counterclockwise at 75% speed
        print("\nRunning Motor at counterclockwise")
        set_motor_speed(75, "counterclockwise")
        time.sleep(0.2)

        print("\nBraking Motor")
        set_motor_speed(0, "brake")
        time.sleep(0.01)

finally:
    print("\nStopping Motor")
    set_motor_speed(0, "stop")
    time.sleep(1)

    print("\nCleaning up GPIO...")
    pwm1.stop()
    pwm2.stop()
    GPIO.cleanup()

