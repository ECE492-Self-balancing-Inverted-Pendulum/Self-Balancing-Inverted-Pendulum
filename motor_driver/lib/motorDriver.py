# motor_control.py
import RPi.GPIO as GPIO
import time

class MotorControl:
    def __init__(self, in1, in2):
        self.IN1 = in1
        self.IN2 = in2
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.IN1, GPIO.OUT)
        GPIO.setup(self.IN2, GPIO.OUT)
        
        self.pwm1 = GPIO.PWM(self.IN1, 1000)
        self.pwm2 = GPIO.PWM(self.IN2, 1000)
        
        self.pwm1.start(0)
        self.pwm2.start(0)

    def set_motor_speed(self, speed, direction):
        """
        Set motor speed and direction using PWM.
        speed: 0 to 100 (percentage)
        direction: 'clockwise' or 'counterclockwise'
        """
        if direction == "clockwise":
            self.pwm1.ChangeDutyCycle(speed)
            self.pwm2.ChangeDutyCycle(0)
        elif direction == "counterclockwise":
            self.pwm1.ChangeDutyCycle(0)
            self.pwm2.ChangeDutyCycle(speed)
        elif direction == "brake":
            self.pwm1.ChangeDutyCycle(80)
            self.pwm2.ChangeDutyCycle(80)
        else:
            self.pwm1.ChangeDutyCycle(0)
            self.pwm2.ChangeDutyCycle(0)

    def stop_motor(self):
        self.set_motor_speed(0, "stop")
        self.pwm1.stop()
        self.pwm2.stop()
        GPIO.cleanup()
        
    def brake(self):
        self.pwm1.ChangeDutyCycle(100)
        self.pwm2.ChangeDutyCycle(100)
        time.sleep(0.025)

