import RPi.GPIO as GPIO
import time

# Motor Driver Pins
MOTOR_IN1 = 13  # PWM control pin
MOTOR_IN2 = 19  # Direction pin (LOW for one direction, HIGH for the other)

# Encoder Pins
ENCODER_A = 23  # Channel A
ENCODER_B = 24  # Channel B
CPR = 1024  # Counts Per Revolution

# PWM Frequency
PWM_FREQ = 1000  # 1 kHz

# GPIO setup
GPIO.setmode(GPIO.BCM)

# Motor Control Setup
GPIO.setup(MOTOR_IN1, GPIO.OUT)  # Set as PWM output
GPIO.setup(MOTOR_IN2, GPIO.OUT)  # Set as digital output

# Encoder Setup
GPIO.setup(ENCODER_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(ENCODER_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Setup PWM on MOTOR_IN1
pwm = GPIO.PWM(MOTOR_IN1, PWM_FREQ)  # Create PWM object
pwm.start(0)  # Start PWM at 0% duty cycle

# Variable to store encoder pulses
pulse_count = 0

# Callback function to count encoder pulses
def encoder_callback(channel):
    global pulse_count
    pulse_count += 1  # Increment pulse count on each rising edge

# Attach interrupt for encoder pulse counting
GPIO.add_event_detect(ENCODER_A, GPIO.RISING, callback=encoder_callback)

# Function to measure RPM
def measure_rpm(duration=1):
    global pulse_count
    pulse_count = 0  # Reset counter
    time.sleep(duration)  # Measure for 'duration' seconds
    rpm = (pulse_count * 60) / CPR  # Convert to RPM
    return rpm

# Function to run motor in a specific direction
def run_motor(direction, duration=5):
    print(f"\nRunning motor {'counterclockwise' if direction == 'CCW' else 'clockwise'} at 100% duty cycle...")

    # Ensure full stop before changing direction
    pwm.ChangeDutyCycle(0)
    time.sleep(2)

    # Set direction
    if direction == "CCW":
        GPIO.output(MOTOR_IN2, GPIO.LOW)
    else:
        GPIO.output(MOTOR_IN2, GPIO.HIGH)

    # Start motor at 100% duty cycle
    pwm.ChangeDutyCycle(100)
    time.sleep(2)  # Allow motor to stabilize

    # Measure RPM
    rpm = measure_rpm()
    print(f"{direction} RPM: {rpm:.2f}")

    # Stop motor
    print("\nStopping motor...")
    pwm.ChangeDutyCycle(0)
    time.sleep(2)  # Short delay before switching direction

try:
    for _ in range(2):  # Repeat cycle twice
        run_motor("CCW")
        run_motor("CW")

finally:
    print("\nCleaning up GPIO...")
    pwm.stop()
    GPIO.cleanup()

