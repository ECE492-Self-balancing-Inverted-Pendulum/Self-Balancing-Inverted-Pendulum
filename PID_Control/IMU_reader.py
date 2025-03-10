import time
import board
import adafruit_icm20x
import math

class IMUReader:
    """
    A class for reading and filtering IMU data from the ICM-20948 sensor.
    Handles inverted (upside-down) mounting of the IMU.
    """

    # Calibration offsets for the accelerometer
    ACCEL_OFFSET_X = 0.002331952416992187
    ACCEL_OFFSET_Y = -0.14494018010253898
    ACCEL_OFFSET_Z = 0.46995493779295927

    # Default Low-Pass Filter Alpha values
    # Higher values = more responsive but more noise
    # Lower values = smoother but slower updates
    DEFAULT_ALPHA = 0.2  # Increased from 0.1 for better responsiveness

    # Flag to indicate IMU is mounted upside down
    MOUNTED_UPSIDE_DOWN = True

    def __init__(self, alpha=None, upside_down=True):
        """
        Initializes the IMU sensor and sets the starting roll reference.
        
        Args:
            alpha: Optional low-pass filter coefficient (0 < alpha < 1)
                 Higher = more responsive, Lower = smoother
            upside_down: Whether the IMU is mounted upside-down
        """
        self.i2c = board.I2C()  # Setup I2C communication
        self.imu = adafruit_icm20x.ICM20948(self.i2c)  # Initialize IMU sensor
        
        # Set alpha for filter responsiveness
        self.ALPHA = alpha if alpha is not None else self.DEFAULT_ALPHA
        # Set mounting orientation
        self.MOUNTED_UPSIDE_DOWN = upside_down
        
        if self.MOUNTED_UPSIDE_DOWN:
            print("IMU configured for upside-down mounting.")

        # First reading (initialize with actual IMU position)
        self.roll, self.angular_velocity = self._get_initial_reading()
        
    def set_alpha(self, alpha):
        """
        Update the low-pass filter alpha value to change responsiveness.
        
        Args:
            alpha: New filter coefficient (0 < alpha < 1)
                 Higher = more responsive, Lower = smoother
        """
        if 0 < alpha < 1:
            self.ALPHA = alpha
            print(f"IMU filter alpha set to {alpha:.2f}")
            return True
        else:
            print(f"Invalid alpha value: {alpha}. Must be between 0 and 1.")
            return False

    def _get_initial_reading(self):
        """
        Gets the first IMU reading and sets it as the initial reference.
        :return: Initial roll and angular velocity values.
        """
        accel_x, accel_y, accel_z = self.imu.acceleration
        gyro_x, gyro_y, gyro_z = self.imu.gyro  # Angular velocity (°/s)

        # Handle calibration offsets based on IMU orientation
        if self.MOUNTED_UPSIDE_DOWN:
            # For upside-down mounting, invert Y and Z axes
            accel_y = -accel_y - self.ACCEL_OFFSET_Y
            accel_z = -accel_z - self.ACCEL_OFFSET_Z
            gyro_x = -gyro_x
        else:
            # Normal mounting - apply offsets normally
            accel_y -= self.ACCEL_OFFSET_Y
            accel_z -= self.ACCEL_OFFSET_Z

        # Compute initial roll angle
        initial_roll = math.atan2(-accel_y, math.sqrt(accel_x**2 + accel_z**2)) * (180 / math.pi)

        return initial_roll, gyro_x  # Initialize angular velocity with X-axis rotation

    def get_imu_data(self):
        """
        Reads IMU data, applies calibration and filtering, and returns processed values.
        Accounts for the IMU being mounted upside-down.

        :return: A dictionary with roll and angular velocity.
        """
        # Read raw IMU values
        accel_x, accel_y, accel_z = self.imu.acceleration
        gyro_x, gyro_y, gyro_z = self.imu.gyro  # Angular velocity (°/s)

        # Handle calibration offsets based on IMU orientation
        if self.MOUNTED_UPSIDE_DOWN:
            # For upside-down mounting, invert Y and Z axes
            accel_y = -accel_y - self.ACCEL_OFFSET_Y
            accel_z = -accel_z - self.ACCEL_OFFSET_Z
            gyro_x = -gyro_x
        else:
            # Normal mounting - apply offsets normally
            accel_y -= self.ACCEL_OFFSET_Y
            accel_z -= self.ACCEL_OFFSET_Z

        # Compute roll angle from accelerometer (degrees)
        roll = math.atan2(-accel_y, math.sqrt(accel_x**2 + accel_z**2)) * (180 / math.pi)

        # Apply low-pass filter to stabilize roll readings
        self.roll = self.ALPHA * roll + (1 - self.ALPHA) * self.roll
        self.angular_velocity = self.ALPHA * gyro_x + (1 - self.ALPHA) * self.angular_velocity

        return {
            "roll": self.roll,
            "angular_velocity": self.angular_velocity
        }

    def print_imu_data(self, delay=0.1):
        """
        Continuously prints the IMU data for debugging.

        :param delay: Time delay between readings (default: 0.1s).
        """
        try:
            print(f"IMU Orientation: {'Upside Down' if self.MOUNTED_UPSIDE_DOWN else 'Normal'}")
            print(f"Accel Offsets: X={self.ACCEL_OFFSET_X}, Y={self.ACCEL_OFFSET_Y}, Z={self.ACCEL_OFFSET_Z}")
            while True:
                imu_data = self.get_imu_data()
                print(f"Roll: {imu_data['roll']:.2f}° | "
                      f"Angular Velocity: {imu_data['angular_velocity']:.2f}°/s")
                time.sleep(delay)
        except KeyboardInterrupt:
            print("\nIMU Reader Stopped.")

# Example usage
if __name__ == "__main__":
    imu_reader = IMUReader(upside_down=True)
    imu_reader.print_imu_data()

