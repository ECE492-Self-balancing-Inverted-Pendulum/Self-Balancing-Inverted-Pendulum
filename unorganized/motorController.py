import RPi.GPIO as GPIO
import time

# Use BCM pin numbering
GPIO.setmode(GPIO.BCM)

# Define motor control pins (IN1 & IN2 are PWM capable)
IN1 = 13  # Motor direction and PWM speed control
IN2 = 19  # Motor direction and PWM speed control

# Define encoder pins
ENCODER_A = 17  # Encoder Channel A
ENCODER_B = 27  # Encoder Channel B

# Set up GPIOs
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(ENCODER_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(ENCODER_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Set up PWM on both pins (1 kHz frequency)
pwm1 = GPIO.PWM(IN1, 1000)
pwm2 = GPIO.PWM(IN2, 1000)

# Start both PWM signals at 0% duty cycle (motor stopped)
pwm1.start(0)
pwm2.start(0)

# Encoder Variables
encoder_count = 0
CPR = 500  # Encoder Counts Per Revolution (adjust based on datasheet)
wheel_diameter = 0.05  # Example: 5 cm wheel diameter
circumference = wheel_diameter * 3.1416  # Calculate wheel travel per revolution

def encoder_callback(channel):
    """Increments encoder count based on quadrature signals."""
    global encoder_count
    if GPIO.input(ENCODER_A) == GPIO.input(ENCODER_B):
        encoder_count += 1
    else:
        encoder_count -= 1

# Attach interrupt to Encoder
GPIO.add_event_detect(ENCODER_A, GPIO.RISING, callback=encoder_callback)

# Function to control motor speed and direction
def set_motor_speed(speed, direction):
    """
    Set motor speed and direction using PWM.
    
    speed: 0 to 100 (percentage)
    direction: 'forward' or 'backward'
    """
    if direction == "forward":
        pwm1.ChangeDutyCycle(speed)  # PWM on IN1
        pwm2.ChangeDutyCycle(0)      # IN2 off
    elif direction == "backward":
        pwm1.ChangeDutyCycle(0)      # IN1 off
        pwm2.ChangeDutyCycle(speed)  # PWM on IN2
    else:
        pwm1.ChangeDutyCycle(0)  # Stop motor
        pwm2.ChangeDutyCycle(0)  # Stop motor

# Function to calculate motor speed
def get_speed():
    global encoder_count
    rotations = encoder_count / CPR
    speed = rotations * circumference / 1  # Speed in m/s (assuming 1-second intervals)
    encoder_count = 0  # Reset count
    return speed

# Move Forward and Backward 6 Times with Different Speeds
try:
    speeds = [30, 50, 70, 90, 60, 40]  # Speed variation for 6 cycles

    for i, speed in enumerate(speeds):
        print(f"Cycle {i+1}: Moving Forward at {speed}% speed")
        set_motor_speed(speed, "forward")
        time.sleep(2)
        print(f"Speed: {get_speed()} m/s")

        print("Stopping")
        set_motor_speed(0, "stop")
        time.sleep(1)

        print(f"Cycle {i+1}: Moving Backward at {speed}% speed")
        set_motor_speed(speed, "backward")
        time.sleep(2)
        print(f"Speed: {get_speed()} m/s")

        print("Stopping")
        set_motor_speed(0, "stop")
        time.sleep(1)

    print("Motor sequence complete.")

except KeyboardInterrupt:
    print("Exiting...")

finally:
    pwm1.stop()
    pwm2.stop()
    GPIO.cleanup()
    print("Program ended and GPIO cleaned up.")

