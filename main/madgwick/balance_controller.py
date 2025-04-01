import time
import board
import adafruit_icm20x
import numpy as np
import imufusion
import json
from pid_controller import PIDController
from motorController import DualMotorControl

# Initialize PID controller
pid = PIDController()

# Initialize motor controller (adjust GPIO pins as needed)
motors = DualMotorControl(
    motor_a_in1=17, 
    motor_a_in2=18, 
    motor_b_in1=22, 
    motor_b_in2=23, 
    pwm_freq=1000
)

# Load calibration values
try:
    with open("calibration.json", "r") as f:
        calibration_data = json.load(f)
    print("Loaded calibration values from calibration.json.")
except FileNotFoundError:
    print("Calibration file not found! Using default offsets.")
    calibration_data = {
        "gyro_offset": [0, 0, 0],
        "accel_offset": [0, 0, 0],
        "mag_offset": [0, 0, 0]
    }

# Convert calibration data to NumPy arrays
gyro_offset = np.array(calibration_data["gyro_offset"])
accel_offset = np.array(calibration_data["accel_offset"])
mag_offset = np.array(calibration_data["mag_offset"])

# Initialize I2C and IMU
i2c = board.I2C()
icm = adafruit_icm20x.ICM20948(i2c)

# Sensor sampling rate
SAMPLE_RATE = 100  # Hz

# Initialize sensor fusion (Madgwick filter)
offset = imufusion.Offset(SAMPLE_RATE)
ahrs = imufusion.Ahrs()

# Set Madgwick filter parameters
ahrs.settings = imufusion.Settings(
    imufusion.CONVENTION_NWU,  # North-West-Up convention
    0.8,  # Reduced gain for better stability
    2000,  # Gyroscope range (deg/s)
    10,  # Acceleration rejection threshold
    10,  # Magnetic rejection threshold
    1 * SAMPLE_RATE  # Recovery trigger period
)

# Time tracking
prev_time = time.time()

print("Balance Controller Running... Press Ctrl+C to stop.")

try:
    while True:
        # Read IMU raw data
        accel = np.array(icm.acceleration) - accel_offset
        gyro = np.array(icm.gyro) * (180 / np.pi) - gyro_offset
        
        # Prevent acceleration fluctuations
        accel = np.clip(accel, -9.81, 9.81)
        
        # Apply low-pass filter to gyro
        alpha = 0.8
        gyro = alpha * gyro + (1 - alpha) * offset.update(gyro)
        
        # Get time delta
        curr_time = time.time()
        dt = max(curr_time - prev_time, 1e-3)
        prev_time = curr_time
        
        # Apply Madgwick filter without magnetometer
        ahrs.update_no_magnetometer(gyro, accel, dt)
        
        # Get Euler angles
        euler = ahrs.quaternion.to_euler()
        
        # Use pitch angle for balancing (adjust based on your robot orientation)
        roll = euler[0]
        pitch = euler[1]
        current_angle = roll  # Pitch angle
        
        # Compute PID output
        pid_output = pid.compute(current_angle, dt)
        
        # Convert PID output to motor commands
        motor_speed = abs(pid_output)
        
        # Determine direction based on PID output sign
        if pid_output > 0:
            # Robot needs to move forward
            motors.set_motors_speed(motor_speed, "clockwise")
        else:
            # Robot needs to move backward
            motors.set_motors_speed(motor_speed, "counterclockwise")
        
        # Display current status
        print(f"\Current (Roll) Angle: {current_angle:.2f}° | Pitch Angle: {pitch:.2f}° | PID Output: {pid_output:.2f} | Motor Speed: {motor_speed:.2f}", end="")
        
        # Maintain sampling rate
        time.sleep(1 / SAMPLE_RATE)

except KeyboardInterrupt:
    print("\nStopping Balance Controller...")
    motors.stop_motors()
    motors.cleanup()
