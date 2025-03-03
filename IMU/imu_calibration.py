import time
import board
import adafruit_icm20x
import numpy as np
import json

# Initialize I2C and IMU
i2c = board.I2C()
icm = adafruit_icm20x.ICM20948(i2c)

NUM_SAMPLES = 500  # Number of readings for calibration

# Storage for offsets
gyro_offset = np.zeros(3)
accel_offset = np.zeros(3)
mag_offset = np.zeros(3)

print("Calibrating IMU... Keep the IMU completely still!")

# Collect sensor readings
for i in range(NUM_SAMPLES):
    accel = icm.acceleration
    gyro = icm.gyro
    mag = icm.magnetic
    
    accel_offset += np.array(accel)
    gyro_offset += np.array(gyro)
    mag_offset += np.array(mag)
    
    time.sleep(0.01)

# Compute the average offset
accel_offset /= NUM_SAMPLES
gyro_offset /= NUM_SAMPLES
mag_offset /= NUM_SAMPLES

# Adjust accelerometer Z-axis to account for gravity (9.81 m/s²)
accel_offset[2] -= 9.81

# Create dictionary with calibration values
calibration_data = {
    "gyro_offset": list(gyro_offset),
    "accel_offset": list(accel_offset),
    "mag_offset": list(mag_offset)
}

# Save calibration to a JSON file
with open("calibration.json", "w") as f:
    json.dump(calibration_data, f, indent=4)

print("\nCalibration complete! Values saved to calibration.json")
print(json.dumps(calibration_data, indent=4))

