import time
import board
import adafruit_icm20x

# Initialize I2C connection
i2c = board.I2C()  # Uses Raspberry Pi's SCL (GPIO3) and SDA (GPIO2)
icm = adafruit_icm20x.ICM20948(i2c)

print("Reading ICM-20948 IMU data...")

while True:
    # Read sensor values
    accel = icm.acceleration
    gyro = icm.gyro
    mag = icm.magnetic

    # Display results
    print(f"Acceleration (m/s²): X={accel[0]:.2f}, Y={accel[1]:.2f}, Z={accel[2]:.2f}")
    print(f"Gyro (rad/s): X={gyro[0]:.2f}, Y={gyro[1]:.2f}, Z={gyro[2]:.2f}")
    print(f"Magnetometer (uT): X={mag[0]:.2f}, Y={mag[1]:.2f}, Z={mag[2]:.2f}")
    print("")

    time.sleep(0.5)  # Delay for readability
