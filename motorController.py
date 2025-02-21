import RPi.GPIO as GPIO
import time

# Define GPIO Pins for L298N Motor Driver
IN1 = 23  # Motor 1 IN1
IN2 = 24  # Motor 1 IN2
ENA = 18  # Motor 1 Speed (PWM)

IN3 = 27  # Motor 2 IN1
IN4 = 22  # Motor 2 IN2
ENB = 17  # Motor 2 Speed (PWM)

# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(ENA, GPIO.OUT)

GPIO.setup(IN3, GPIO.OUT)
GPIO.setup(IN4, GPIO.OUT)
GPIO.setup(ENB, GPIO.OUT)

# Set up PWM on ENA and ENB pins
pwm1 = GPIO.PWM(ENA, 1000)  # 1kHz PWM frequency for Motor 1
pwm2 = GPIO.PWM(ENB, 1000)  # 1kHz PWM frequency for Motor 2
pwm1.start(0)  # Start with 0% duty cycle (motor off)
pwm2.start(0)

def move_forward(speed):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm1.ChangeDutyCycle(speed)  # Set speed (0-100%)
    pwm2.ChangeDutyCycle(speed)

def move_backward(speed):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    pwm1.ChangeDutyCycle(speed)
    pwm2.ChangeDutyCycle(speed)

def stop_motors():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)
    pwm1.ChangeDutyCycle(0)
    pwm2.ChangeDutyCycle(0)

try:
    while True:
        print("Moving Forward")
        move_forward(75)  # 75% speed
        time.sleep(2)

        print("Stopping")
        stop_motors()
        time.sleep(1)

        print("Moving Backward")
        move_backward(50)  # 50% speed
        time.sleep(2)

        print("Stopping")
        stop_motors()
        time.sleep(1)

except KeyboardInterrupt:
    print("Exiting...")
finally:
    pwm1.stop()
    pwm2.stop()
    GPIO.cleanup()
