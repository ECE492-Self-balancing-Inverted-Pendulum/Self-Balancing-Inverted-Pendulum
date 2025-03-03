import time
import board
import adafruit_icm20x
import numpy as np
import imufusion
import csv
import json
import sys

# Load calibration values from calibration.json
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
    imufusion.CONVENTION_NWU,  # North-West-Up (NWU) convention
    0.5,  # Gain (higher = faster, noisier)
    2000,  # Gyroscope range (deg/s)
    10,  # Acceleration rejection threshold
    10,  # Magnetic rejection threshold
    5 * SAMPLE_RATE,  # Recovery trigger period = 5 seconds
)

# Time tracking
prev_time = time.time()

# Open CSV log file
log_file = open("imu_log.csv", "w", newline="")
csv_writer = csv.writer(log_file)
csv_writer.writerow(["Timestamp", "Roll", "Pitch", "Yaw"])

print("IMU Sensor Fusion Running with Calibration... Press Ctrl+C to stop.")

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

        # Apply offset correction to gyroscope
        gyro = offset.update(gyro)

        # Apply Madgwick filter
        ahrs.update(gyro, accel, mag, dt)

        # Get Euler angles (Roll, Pitch, Yaw)
        euler = ahrs.quaternion.to_euler()

        # Log data to CSV
        csv_writer.writerow([curr_time, euler[0], euler[1], euler[2]])
        log_file.flush()  # Ensure immediate writing to file

        # CLI Display (Text-based Visualization)
        sys.stdout.write(f"\rRoll: {euler[0]:.2f}° | Pitch: {euler[1]:.2f}° | Yaw: {euler[2]:.2f}°   ")
        sys.stdout.flush()

        time.sleep(1 / SAMPLE_RATE)  # Maintain sampling rate

except KeyboardInterrupt:
    print("\nExiting IMU Fusion Program...")
    log_file.close()  # Close CSV file

