import time
import board
import adafruit_icm20x
import numpy as np

# Initialize IMU
i2c = board.I2C()
imu = adafruit_icm20x.ICM20948(i2c)

# Storage for accelerometer readings
accel_data = []

print("Recording 10 seconds of accelerometer data for calibration...")
for _ in range(100):  # Collect 100 samples over ~10 sec
    accel_data.append(imu.acceleration)
    time.sleep(0.1)

# Convert to NumPy array for easy calculations
accel_data = np.array(accel_data)

# Compute average offsets
accel_offset_x = np.mean(accel_data[:, 0])  # X-axis bias
accel_offset_y = np.mean(accel_data[:, 1])  # Y-axis bias
accel_offset_z = np.mean(accel_data[:, 2]) - 9.81  # Adjust Z-axis to be exactly 9.81

print(f"Recommended Offsets:")
print(f"X-axis offset: {accel_offset_x:.3f}")
print(f"Y-axis offset: {accel_offset_y:.3f}")
print(f"Z-axis offset: {accel_offset_z:.3f}")

