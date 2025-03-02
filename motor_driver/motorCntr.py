import RPi.GPIO as GPIO
import time

# Use BCM pin numbering
GPIO.setmode(GPIO.BCM)

# Define motor control pins (both PWM capable)
IN1 = 13  # Motor direction and PWM speed control
IN2 = 19  # Motor direction and PWM speed control

# Set up GPIOs as output
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)

# Set up PWM on both pins (1 kHz frequency)
pwm1 = GPIO.PWM(IN1, 1000)
pwm2 = GPIO.PWM(IN2, 1000)

# Start both PWM signals at 0% duty cycle (motor stopped)
pwm1.start(0)
pwm2.start(0)

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
    else:
        pwm1.ChangeDutyCycle(0)  # Stop motor
        pwm2.ChangeDutyCycle(0)  # Stop motor

# Rotate motor clockwise at 50% speed
set_motor_speed(50, "clockwise")
time.sleep(3)

# Rotate motor counterclockwise at 75% speed
set_motor_speed(75, "counterclockwise")
time.sleep(3)

# Stop the motor
set_motor_speed(0, "stop")

# Cleanup
pwm1.stop()
pwm2.stop()
GPIO.cleanup()
