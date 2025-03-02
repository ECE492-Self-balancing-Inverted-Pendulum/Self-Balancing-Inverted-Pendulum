import RPi.GPIO as GPIO
import time

# Use BCM pin numbering
GPIO.setmode(GPIO.BCM)

# Motor Control Pins (PWM)
IN1 = 13  # Motor direction and PWM speed control
IN2 = 19  # Motor direction and PWM speed control

# Encoder Pins (Quadrature A & B)
ENCODER_A = 17
ENCODER_B = 27

# Motor Specifications (Modify for your motor)
V_MOTOR = 6.8  # Motor operating voltage (V). VDC from regulator.
I_MAX = 2.0   # Max motor current, measured from regulator.

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
CPR = 1024  # Encoder Cycles Per Revolution (modify as per your encoder)

# Interrupt callback for encoder counting
def encoder_callback(channel):
    global encoder_pulse_count, last_encoder_state

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

# Rotate motor and measure RPM & Current
try:
    print("Motor running clockwise at 50% speed")
    set_motor_speed(50, "clockwise")
    
    for _ in range(5):  # Measure for 5 seconds
        time.sleep(1)
        rpm = calculate_rpm()
        mean_current = estimate_mean_current(50)
        print(f"RPM: {rpm}, Estimated Current: {mean_current:.2f} A")

    print("Motor running counterclockwise at 75% speed")
    set_motor_speed(75, "counterclockwise")
    
    for _ in range(5):
        time.sleep(1)
        rpm = calculate_rpm()
        mean_current = estimate_mean_current(75)
        print(f"RPM: {rpm}, Estimated Current: {mean_current:.2f} A")

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

