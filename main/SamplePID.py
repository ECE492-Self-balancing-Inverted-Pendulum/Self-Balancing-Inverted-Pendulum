import time
import numpy as np
from imu_fusion_module import IMUFusion  # Ensure this module is available
from motor_control_module import DualMotorControl  # Ensure this module is available

class PIDController:
    def __init__(self, kp, ki, kd, setpoint=0, sample_time=0.01):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.sample_time = sample_time

        self.prev_error = 0
        self.integral = 0
        self.last_time = time.time()

    def compute(self, input_value):
        current_time = time.time()
        dt = current_time - self.last_time
        if dt < self.sample_time:
            return None  # Maintain sample rate

        error = self.setpoint - input_value
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt if dt > 0 else 0

        output = (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)
        self.prev_error = error
        self.last_time = current_time
        
        return output

class SelfBalancingRobot:
    def __init__(self, kp, ki, kd, motor_pins):
        self.imu = IMUFusion()
        self.motors = DualMotorControl(*motor_pins)
        self.pid = PIDController(kp, ki, kd)

    def run(self):
        try:
            while True:
                roll, pitch, yaw = self.imu.get_angles()  # Get angles
                print(f"Debug: Roll: {roll:.2f}°, Pitch: {pitch:.2f}°, Yaw: {yaw:.2f}°")
                
                correction = self.pid.compute(pitch)
                
                if correction is not None:
                    speed = min(max(abs(correction), 0), 100)
                    direction = "clockwise" if correction > 0 else "counterclockwise"
                    self.motors.set_motors_speed(speed, direction)
                
                time.sleep(1 / self.imu.sample_rate)
        except KeyboardInterrupt:
            self.motors.stop_motors()
            print("Stopping robot...")

if __name__ == "__main__":
    motor_pins = (17, 18, 22, 23)  # Replace with actual motor control GPIO pins
    robot = SelfBalancingRobot(kp=1.0, ki=0.5, kd=0.1, motor_pins=motor_pins)
    robot.run()
