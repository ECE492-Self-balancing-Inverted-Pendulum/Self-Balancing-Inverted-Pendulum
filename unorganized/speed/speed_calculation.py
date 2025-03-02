import RPi.GPIO as GPIO
import time
import math

# Use BCM pin numbering
GPIO.setmode(GPIO.BCM)

# Motor Control Pins (PWM)
IN1 = 13  # Motor direction and PWM speed control
IN2 = 19  # Motor direction and PWM speed control

# Encoder Pins (Quadrature A & B)
ENCODER_A = 17
ENCODER_B = 27

# Motor Specifications
V_MOTOR = 6.8  # Motor operating voltage (V)
I_MAX = 2.0    # Max motor current, measured from regulator

# Wheel/Tire Specifications
WHEEL_DIAMETER = 0.11  # Wheel diameter in meters (11 cm)
CPR = 1024  # Encoder Cycles Per Revolution (modify as per your encoder)

# Set up GPIOs as output for motor
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)

# Set up encoder pins as input
GPIO.setup(ENCODER_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(ENCODER_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Set up PWM on motor control pins (1 kHz frequency)
pwm1 = GPIO.PWM(IN1, 1000)
pwm2 = GPIO.PWM(IN2, 1000)

# Start PWM with 0% duty cycle (motor stopped)
pwm1.start(0)
pwm2.start(0)

# Variables for encoder
encoder_pulse_count = 0
last_encoder_state = 0

# Interrupt callback for encoder counting
def encoder_callback(channel):
    global encoder_pulse_count

    a_state = GPIO.input(ENCODER_A)
    b_state = GPIO.input(ENCODER_B)

    # Determine direction
    if a_state == b_state:
        encoder_pulse_count += 1  # Clockwise
    else:
        encoder_pulse_count -= 1  # Counterclockwise

# Attach interrupt for Encoder A signal
GPIO.add_event_detect(ENCODER_A, GPIO.RISING, callback=encoder_callback)

# Function to estimate mean output current
def estimate_mean_current(duty_cycle):
    """
    Estimates the mean output current based on duty cycle and motor max current.
    Formula: I_mean = I_max * (duty_cycle / 100)
    """
    return I_MAX * (duty_cycle / 100)

# Function to convert RPM to Speed (m/s and km/h)
def rpm_to_speed(rpm, wheel_diameter=WHEEL_DIAMETER):
    """
    Converts RPM to linear speed in meters per second (m/s) and kilometers per hour (km/h).

    :param rpm: Rotations per minute (RPM)
    :param wheel_diameter: Diameter of the wheel in meters (default = 0.11m for 11 cm tire)
    :return: Tuple (speed_mps, speed_kph)
    """
    radius = wheel_diameter / 2  # Convert diameter to radius (m)
    speed_mps = (2 * math.pi * radius * rpm) / 60  # Speed in meters per second
    speed_kph = speed_mps * 3.6  # Convert to km/h
    return speed_mps, speed_kph

# Function to set motor speed and direction
def set_motor_speed(speed, direction):
    """
    Controls motor speed and direction using PWM.
    
    speed: 0 to 100 (percentage)
    direction: 'clockwise' or 'counterclockwise'
    """
    if direction == "clockwise":
        pwm1.ChangeDutyCycle(speed)  # PWM on IN1
        pwm2.ChangeDutyCycle(0)      # IN2 off
    elif direction == "counterclockwise":
        pwm1.ChangeDutyCycle(0)      # IN1 off
        pwm2.ChangeDutyCycle(speed)  # PWM on IN2
    else:
        pwm1.ChangeDutyCycle(0)  # Stop motor
        pwm2.ChangeDutyCycle(0)  # Stop motor

# Function to calculate RPM
def calculate_rpm():
    global encoder_pulse_count
    pulses = encoder_pulse_count
    encoder_pulse_count = 0  # Reset count after reading
    rpm = (pulses / CPR) * 60  # Convert pulses to RPM
    return rpm

# Rotate motor and measure RPM, Speed & Current
try:
    print("Motor running clockwise at 50% speed")
    set_motor_speed(50, "clockwise")
    
    for _ in range(5):  # Measure for 5 seconds
        time.sleep(1)
        rpm = calculate_rpm()
        speed_mps, speed_kph = rpm_to_speed(rpm)
        mean_current = estimate_mean_current(50)
        print(f"RPM: {rpm}, Speed: {speed_mps:.2f} m/s ({speed_kph:.2f} km/h), Estimated Current: {mean_current:.2f} A")

    print("Motor running counterclockwise at 75% speed")
    set_motor_speed(75, "counterclockwise")
    
    for _ in range(5):
        time.sleep(1)
        rpm = calculate_rpm()
        speed_mps, speed_kph = rpm_to_speed(rpm)
        mean_current = estimate_mean_current(75)
        print(f"RPM: {rpm}, Speed: {speed_mps:.2f} m/s ({speed_kph:.2f} km/h), Estimated Current: {mean_current:.2f} A")

    # Stop the motor
    print("Stopping motor")
    set_motor_speed(0, "stop")

except KeyboardInterrupt:
    print("Interrupted, stopping motor")

finally:
    # Cleanup
    pwm1.stop()
    pwm2.stop()
    GPIO.cleanup()

