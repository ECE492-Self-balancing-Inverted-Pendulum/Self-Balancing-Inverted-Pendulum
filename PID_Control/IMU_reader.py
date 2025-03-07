import time
import board
import adafruit_icm20x
import math

class IMUReader:
    """
    A class for reading and filtering IMU data from the ICM-20948 sensor.
    """

    # Calibration offsets for the accelerometer
    ACCEL_OFFSET_X = 0.002331952416992187
    ACCEL_OFFSET_Y = -0.14494018010253898
    ACCEL_OFFSET_Z = 0.46995493779295927

    # Low-Pass Filter Alpha (0 < ALPHA < 1, lower = smoother, slower updates)
    ALPHA = 0.1

    def __init__(self):
        """
        Initializes the IMU sensor and sets the starting pitch reference.
        """
        self.i2c = board.I2C()  # Setup I2C communication
        self.imu = adafruit_icm20x.ICM20948(self.i2c)  # Initialize IMU sensor

        # First reading (initialize with actual IMU position)
        self.pitch, self.angular_velocity = self._get_initial_reading()

    def _get_initial_reading(self):
        """
        Gets the first IMU reading and sets it as the initial reference.
        :return: Initial pitch and angular velocity values.
        """
        accel_x, accel_y, accel_z = self.imu.acceleration
        gyro_x, gyro_y, gyro_z = self.imu.gyro  # Angular velocity (°/s)

        # Apply calibration offsets
        accel_x -= self.ACCEL_OFFSET_X
        accel_y -= self.ACCEL_OFFSET_Y
        accel_z -= self.ACCEL_OFFSET_Z

        # Compute initial pitch angle
        initial_pitch = math.atan2(-accel_x, math.sqrt(accel_y**2 + accel_z**2)) * (180 / math.pi)

        return initial_pitch, gyro_y  # Initialize angular velocity as first reading

    def get_imu_data(self):
        """
        Reads IMU data, applies calibration and filtering, and returns processed values.

        :return: A dictionary with pitch and angular velocity.
        """
        # Read raw IMU values
        accel_x, accel_y, accel_z = self.imu.acceleration
        gyro_x, gyro_y, gyro_z = self.imu.gyro  # Angular velocity (°/s)

        # Apply calibration offsets
        accel_x -= self.ACCEL_OFFSET_X
        accel_y -= self.ACCEL_OFFSET_Y
        accel_z -= self.ACCEL_OFFSET_Z

        # Compute pitch angle from accelerometer (degrees)
        pitch = math.atan2(-accel_x, math.sqrt(accel_y**2 + accel_z**2)) * (180 / math.pi)

        # Apply low-pass filter to stabilize pitch readings
        self.pitch = self.ALPHA * pitch + (1 - self.ALPHA) * self.pitch
        self.angular_velocity = self.ALPHA * gyro_y + (1 - self.ALPHA) * self.angular_velocity

        return {
            "pitch": self.pitch,
            "angular_velocity": self.angular_velocity
        }

    def print_imu_data(self, delay=0.1):
        """
        Continuously prints the IMU data for debugging.

        :param delay: Time delay between readings (default: 0.1s).
        """
        try:
            while True:
                imu_data = self.get_imu_data()
                print(f"Pitch: {imu_data['pitch']:.2f}° | "
                      f"Angular Velocity: {imu_data['angular_velocity']:.2f}°/s")
                time.sleep(delay)
        except KeyboardInterrupt:
            print("\nIMU Reader Stopped.")

# Example usage
if __name__ == "__main__":
    imu_reader = IMUReader()
    imu_reader.print_imu_data()

