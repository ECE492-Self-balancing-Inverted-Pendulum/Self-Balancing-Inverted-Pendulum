import time
import board
import adafruit_icm20x
import numpy as np
import imufusion
import json
import sys

# Load calibration values
try:
    with open("calibration.json", "r") as f:
        calibration_data = json.load(f)
    print("Loaded calibration values from calibration.json.")
except FileNotFoundError:
    print("Calibration file not found! Using default offsets.")
    calibration_data = {
        "gyro_offset": [0, 0, 0],
        "accel_offset": [0, 0, 9.81],  # Gravity compensation
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

# Initialize `imufusion` AHRS
ahrs = imufusion.Ahrs()
offset = imufusion.Offset(SAMPLE_RATE)

# Set filter parameters
ahrs.settings = imufusion.Settings(
    imufusion.CONVENTION_NWU,  # North-West-Up (NWU) convention
    0.5,  # Gain (higher = faster, noisier)
    2000,  # Gyroscope range (deg/s)
    10,  # Acceleration rejection threshold
    10,  # Magnetic rejection threshold
    5 * SAMPLE_RATE,  # Recovery trigger period = 5 seconds
)

# Time tracking
prev_time = time.time()

print("IMU Sensor Fusion Running... Press Ctrl+C to stop.")

try:
    while True:
        # Read IMU raw data
        accel = np.array(icm.acceleration) - accel_offset  # Remove bias
        gyro = np.array(icm.gyro) * 180 / np.pi - gyro_offset  # Convert rad/s → deg/s & Remove bias
        mag = np.array(icm.magnetic) - mag_offset  # Remove bias

        # Get time delta
        curr_time = time.time()
        dt = curr_time - prev_time
        prev_time = curr_time

        # Apply offset correction to gyroscope
        gyro = offset.update(gyro)

        # Apply `imufusion` for sensor fusion
        ahrs.update(gyro, accel, mag, dt)

        # Extract Euler Angles
        euler = ahrs.quaternion.to_euler()  # [Roll, Pitch, Yaw]
        roll, pitch, yaw = euler

        # Get Angular Velocity (Gyroscope data after filtering)
        angular_velocity = gyro  # [ω_x, ω_y, ω_z] in deg/s

        # Get Linear Acceleration (Removing Gravity)
        gravity_vector = ahrs.gravity # Gravity estimation
        linear_accel = accel - gravity_vector  # Linear acceleration (No gravity)

        # Print values
        sys.stdout.write(f"\rPitch: {pitch:.2f}° | Roll: {roll:.2f}° | Yaw: {yaw:.2f}° "
                         f"| Pitch Rate: {angular_velocity[1]:.2f}°/s | Roll Rate: {angular_velocity[0]:.2f}°/s "
                         f"| Angular Velocities: {angular_velocity} "
                         f"| Linear Acceleration: {linear_accel}  ")
        sys.stdout.flush()

        time.sleep(1 / SAMPLE_RATE)  # Maintain sampling rate

        #time.sleep(1)  # Maintain sampling rate
except KeyboardInterrupt:
    print("\nExiting IMU Fusion Program...")

