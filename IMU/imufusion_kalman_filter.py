import time
import board
import adafruit_icm20x
import numpy as np
import imufusion
import csv
import json
import sys
from filterpy.kalman import KalmanFilter

# Load calibration values from calibration.json
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

# Initialize Kalman filter for orientation estimation
kf = KalmanFilter(dim_x=3, dim_z=3)  # 3 states (Roll, Pitch, Yaw), 3 measurements
kf.x = np.array([[0.0], [0.0], [0.0]])  # Initial state
kf.F = np.eye(3)  # State transition matrix
kf.H = np.eye(3)  # Measurement function
kf.P *= 1000  # Initial uncertainty
kf.R = np.eye(3) * 5  # Measurement noise covariance (Tune this)
kf.Q = np.eye(3) * 0.01  # Process noise covariance (Tune this)

# Time tracking
prev_time = time.time()

# Open CSV log file
log_file = open("imu_kalman_log.csv", "w", newline="")
csv_writer = csv.writer(log_file)
csv_writer.writerow(["Timestamp", "Roll", "Pitch", "Yaw"])

print("IMU Sensor Fusion Running with Kalman Filter... Press Ctrl+C to stop.")

try:
    while True:
        # Read IMU raw data
        accel = np.array(icm.acceleration) - accel_offset  # Apply calibration
        gyro = np.array(icm.gyro) * 180 / np.pi - gyro_offset  # Convert rad/s → deg/s & Apply calibration
        mag = np.array(icm.magnetic) - mag_offset  # Apply calibration

        # Get time delta
        curr_time = time.time()
        dt = curr_time - prev_time
        prev_time = curr_time

        # Kalman filter prediction
        kf.predict()

        # Get estimated Euler angles
        euler_angles = np.arctan2(accel[:2], accel[2]) * (180 / np.pi)  # Roll & Pitch estimation
        yaw = np.arctan2(mag[1], mag[0]) * (180 / np.pi)  # Yaw estimation

        # Apply Kalman update
        measurement = np.array([[euler_angles[0]], [euler_angles[1]], [yaw]])
        kf.update(measurement)
        filtered_euler = kf.x.flatten()  # Extract filtered values

        # Log data to CSV
        csv_writer.writerow([curr_time, filtered_euler[0], filtered_euler[1], filtered_euler[2]])
        log_file.flush()  # Ensure immediate writing to file

        # CLI Display (Text-based Visualization)
        sys.stdout.write(f"\rFiltered -> Roll: {filtered_euler[0]:.2f}° | Pitch: {filtered_euler[1]:.2f}° | Yaw: {filtered_euler[2]:.2f}°   ")
        sys.stdout.flush()

        time.sleep(1 / SAMPLE_RATE)  # Maintain sampling rate

except KeyboardInterrupt:
    print("\nExiting IMU Fusion Program...")
    log_file.close()  # Close CSV file

