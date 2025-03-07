import time
import board
import adafruit_icm20x
import math

# Initialize I2C and IMU
i2c = board.I2C()
imu = adafruit_icm20x.ICM20948(i2c)

# ✅ Use your provided accelerometer offsets
ACCEL_OFFSET_X = 0.002331952416992187
ACCEL_OFFSET_Y = -0.14494018010253898
ACCEL_OFFSET_Z = 0.46995493779295927

# ✅ Low-Pass Filter Parameter (Adjust ALPHA for smoothness vs response)
ALPHA = 0.1  # Lower = more smoothing, but slower updates

# ✅ Initialize filtered pitch and angular velocity
filtered_pitch = 0
filtered_angular_velocity = 0

while True:
    # Read IMU values
    accel_x, accel_y, accel_z = imu.acceleration
    gyro_x, gyro_y, gyro_z = imu.gyro  # Angular velocity in °/s

    # ✅ Apply calibration offsets
    accel_x -= ACCEL_OFFSET_X
    accel_y -= ACCEL_OFFSET_Y
    accel_z -= ACCEL_OFFSET_Z

    # ✅ Compute pitch from accelerometer
    pitch = math.atan2(-accel_x, math.sqrt(accel_y**2 + accel_z**2)) * (180 / math.pi)

    # ✅ Apply Low-Pass Filter to Pitch
    filtered_pitch = ALPHA * pitch + (1 - ALPHA) * filtered_pitch

    # ✅ Apply Low-Pass Filter to Gyroscope Angular Velocity (for smoother motion readings)
    filtered_angular_velocity = ALPHA * gyro_y + (1 - ALPHA) * filtered_angular_velocity

    # ✅ Output Filtered IMU Data
    print(f"Filtered Pitch: {filtered_pitch:.2f}° | Filtered Angular Velocity: {filtered_angular_velocity:.2f}°/s")

    time.sleep(0.1)  # Adjust the sampling rate if needed

