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


class DualMotorControl:
    """
    Controller for two independent motor drivers, ensuring synchronized movement.
    Motor A and Motor B each have their own controller and pins.
    """
    
    def __init__(self, motor_a_in1, motor_a_in2, motor_b_in1, motor_b_in2, pwm_freq=1000):
        """
        Initializes both motor controllers with their respective pins.
        
        :param motor_a_in1: GPIO pin for Motor A IN1
        :param motor_a_in2: GPIO pin for Motor A IN2
        :param motor_b_in1: GPIO pin for Motor B IN1
        :param motor_b_in2: GPIO pin for Motor B IN2
        :param pwm_freq: PWM frequency in Hz (default: 1000Hz)
        """
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        
        # Create individual motor controllers
        self.motor_a = MotorControl(motor_a_in1, motor_a_in2, pwm_freq)
        self.motor_b = MotorControl(motor_b_in1, motor_b_in2, pwm_freq)
        
        print(f"[INFO] Dual motor controller initialized:")
        print(f"  - Motor A: IN1={motor_a_in1}, IN2={motor_a_in2}")
        print(f"  - Motor B: IN1={motor_b_in1}, IN2={motor_b_in2}")
    
    def set_motors_speed(self, speed, direction):
        """
        Sets both motors to the same speed and direction.
        
        :param speed: Desired speed (0 to 100% PWM)
        :param direction: "clockwise" or "counterclockwise"
        """
        # Set both motors to the same direction and speed
        self.motor_a.set_motor_speed(speed, direction)
        self.motor_b.set_motor_speed(speed, direction)
    
    def set_individual_speeds(self, speed_a, direction_a, speed_b, direction_b):
        """
        Sets each motor to different speeds and directions (use with caution).
        
        :param speed_a: Speed for Motor A (0 to 100%)
        :param direction_a: Direction for Motor A
        :param speed_b: Speed for Motor B (0 to 100%)
        :param direction_b: Direction for Motor B
        """
        self.motor_a.set_motor_speed(speed_a, direction_a)
        self.motor_b.set_motor_speed(speed_b, direction_b)
    
    def stop_motors(self):
        """
        Stops both motors immediately.
        """
        self.motor_a.stop_motor()
        self.motor_b.stop_motor()
    
    def cleanup(self):
        """
        Properly cleans up both motor controllers.
        """
        self.stop_motors()
        # Only call GPIO.cleanup() once, otherwise will generate errors
        self.motor_a.pwm1.stop()
        self.motor_a.pwm2.stop()
        self.motor_b.pwm1.stop()
        self.motor_b.pwm2.stop()
        GPIO.cleanup()
        print("[INFO] Dual motor controller cleaned up.")


# Example usage
if __name__ == "__main__":
    # Example using single motor
    # motor = MotorControl(in1=13, in2=19)
    
    # Example using dual motors
    dual_motor = DualMotorControl(
        motor_a_in1=12, motor_a_in2=18,  # Motor A pins
        motor_b_in1=13, motor_b_in2=19   # Motor B pins
    )
    
    try:
        print("Running both motors forward at 50%...")
        dual_motor.set_motors_speed(50, "clockwise")
        time.sleep(3)
        
        print("Running both motors forward at 100%...")
        dual_motor.set_motors_speed(100, "clockwise")
        time.sleep(3)
        
        print("Stopping motors...")
        dual_motor.stop_motors()
    except KeyboardInterrupt:
        print("\nStopping motors.")
    finally:
        dual_motor.cleanup()

