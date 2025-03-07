import RPi.GPIO as GPIO
import time

class MotorControl:
    """
    A simple motor control class for PWM-based DC motors using a motor driver.
    """

    def __init__(self, in1, in2, pwm_freq=1000):
        """
        Initializes the motor controller.

        :param in1: GPIO pin for motor IN1
        :param in2: GPIO pin for motor IN2
        :param pwm_freq: PWM frequency in Hz (default: 1000Hz)
        """
        GPIO.setwarnings(False)  # ✅ Disable "channel already in use" warning
        GPIO.setmode(GPIO.BCM)

        self.IN1 = in1
        self.IN2 = in2
        self.pwm_freq = pwm_freq

        GPIO.setup(self.IN1, GPIO.OUT)
        GPIO.setup(self.IN2, GPIO.OUT)

        self.pwm1 = GPIO.PWM(self.IN1, self.pwm_freq)
        self.pwm2 = GPIO.PWM(self.IN2, self.pwm_freq)
        self.pwm1.start(0)
        self.pwm2.start(0)

    def set_motor_speed(self, speed, direction):
        """
        Sets motor speed and direction.

        :param speed: Desired speed (0 to 100% PWM)
        :param direction: "clockwise" or "counterclockwise"
        """
        speed = max(0, min(100, speed))

        if direction not in ["clockwise", "counterclockwise", "stop"]:
            print("[ERROR] Invalid direction. Use 'clockwise', 'counterclockwise', or 'stop'.")
            return

        if direction == "clockwise":
            self.pwm1.ChangeDutyCycle(speed)
            self.pwm2.ChangeDutyCycle(0)
        elif direction == "counterclockwise":
            self.pwm1.ChangeDutyCycle(0)
            self.pwm2.ChangeDutyCycle(speed)
        elif direction == "stop":
            self.pwm1.ChangeDutyCycle(0)
            self.pwm2.ChangeDutyCycle(0)

    def stop_motor(self):
        """
        Stops the motor immediately.
        """
        self.set_motor_speed(0, "stop")

    def cleanup(self):
        """
        Cleans up GPIO settings.
        """
        self.stop_motor()
        self.pwm1.stop()
        self.pwm2.stop()
        GPIO.cleanup()
        print("[INFO] GPIO cleanup completed.")

# Example usage
if __name__ == "__main__":
    motor = MotorControl(in1=13, in2=19)
    
    try:
        motor.set_motor_speed(50, "clockwise")  # Start motor at 50% speed
        time.sleep(3)
        motor.set_motor_speed(100, "clockwise")  # Increase speed to 100%
        time.sleep(3)
        motor.stop_motor()  # Stop the motor
    except KeyboardInterrupt:
        print("\nStopping motor.")
    finally:
        motor.cleanup()

