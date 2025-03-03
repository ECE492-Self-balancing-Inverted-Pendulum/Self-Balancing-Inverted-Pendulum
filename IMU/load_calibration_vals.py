import time
import board
import adafruit_icm20x
import numpy as np
import json

# Load calibration values
try:
    with open("calibration.json", "r") as f:
        calibration_data = json.load(f)
    print("Loaded calibration values from file.")
except FileNotFoundError:
    print("Calibration file not found! Run the calibration script first.")
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

while True:
    # Read sensor values
    accel = np.array(icm.acceleration) - accel_offset
    gyro = np.array(icm.gyro) - gyro_offset
    mag = np.array(icm.magnetic) - mag_offset

    # Display results
    print(f"Corrected Acceleration: X={accel[0]:.2f}, Y={accel[1]:.2f}, Z={accel[2]:.2f} m/s²")
    print(f"Corrected Gyro: X={gyro[0]:.2f}, Y={gyro[1]:.2f}, Z={gyro[2]:.2f} rad/s")
    print(f"Corrected Magnetometer: X={mag[0]:.2f}, Y={mag[1]:.2f}, Z={mag[2]:.2f} uT")
    print("")

    time.sleep(0.5)

