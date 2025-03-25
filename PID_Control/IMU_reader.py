"""
IMU Reader Module for Self-Balancing Robot

This module handles communication with the ICM-20948 Inertial Measurement Unit (IMU)
and processes the raw sensor data to provide filtered roll angle and angular velocity
measurements that are essential for balancing the robot.

Key features:
- Supports both normal and upside-down mounting of the IMU
- Implements low-pass filtering to reduce noise in sensor readings
- Applies calibration offsets to account for sensor bias
- Integrates with config.py for tunable parameters
- Calculates roll angle from accelerometer data and angular velocity from gyroscope

Example Usage:
    # Initialize the IMU
    from config import CONFIG
    imu = IMUReader()
    
    # Get filtered IMU data in a loop
    while True:
        data = imu.get_imu_data()
        angle = data['roll']
        angular_velocity = data['angular_velocity']
        
        print(f"Roll: {angle:.2f}° | Angular Velocity: {angular_velocity:.2f}°/s")
        time.sleep(0.01)
"""

import time
import math
import busio
import board
import adafruit_icm20x
from config import CONFIG, save_config

class IMUReader:
    """
    A class for reading and filtering IMU data from the ICM-20948 sensor.
    Handles inverted (upside-down) mounting of the IMU and integrates with config.py.
    """

    # Calibration offsets for the accelerometer
    ACCEL_OFFSET_X = 0.002331952416992187
    ACCEL_OFFSET_Y = -0.14494018010253898
    ACCEL_OFFSET_Z = 0.46995493779295927

    def __init__(self, upside_down=True):
        """
        Initializes the IMU sensor with settings from CONFIG.
        """
        # Create I2C interface
        self.i2c = busio.I2C(board.SCL, board.SDA)
        
        # Try to initialize the IMU
        try:
            # This line tries to initialize the IMU with the address 0x0c (one of the possible addresses)
            self.imu = adafruit_icm20x.ICM20948(self.i2c, address=0x0c)
            print("IMU initialized with address 0x0c")
        except ValueError:
            try:
                self.imu = adafruit_icm20x.ICM20948(self.i2c)
                print("IMU initialized with default address")
            except ValueError as e:
                print(f"Error initializing IMU: {e}")
                print("Try checking IMU connections and I2C address (use i2cdetect -y 1)")
                raise
        
        # Set mounting orientation
        self.MOUNTED_UPSIDE_DOWN = upside_down
        

        # First reading (initialize with actual IMU position)
        self.roll, self.angular_velocity = self._get_initial_reading()
        
        
        
    def set_alpha(self, alpha):
        """
        Update the low-pass filter alpha value and save to CONFIG.
        
        Args:
            alpha: New filter coefficient (0 < alpha < 1)
                 Higher = more responsive, Lower = smoother
        """
        if 0 < alpha < 1:
            # Import here to ensure we get the most up-to-date CONFIG
            from config import CONFIG, save_config
            
            # Only update the alpha value in the latest CONFIG
            CONFIG['IMU_FILTER_ALPHA'] = alpha
            save_config(CONFIG)
            
            print(f"IMU filter alpha set to {alpha:.2f}")
            return True
        else:
            print(f"Invalid alpha value: {alpha}. Must be between 0 and 1.")
            return False

    def _get_initial_reading(self):
        """
        Gets the first IMU reading and sets it as the initial reference.
        
        Returns:
            Initial roll and angular velocity values.
        """
        accel_x, accel_y, accel_z = self.imu.acceleration
        gyro_x, gyro_y, gyro_z = self.imu.gyro  # Angular velocity (°/s)
        
        # Get the upside down value from the config
        upside_down = CONFIG.get('IMU_UPSIDE_DOWN', True)

        # Handle calibration offsets based on IMU orientation
        if upside_down:
            accel_y = -accel_y - self.ACCEL_OFFSET_Y
            accel_z = -accel_z - self.ACCEL_OFFSET_Z
            gyro_x = -gyro_x
        else:
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
        # Get alpha from config
        self.ALPHA = CONFIG.get('IMU_FILTER_ALPHA', 0.2)
        
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
        Continuously prints the IMU data for debugging on a single updating line.
        
        Uses carriage return to update values in place without flooding the terminal.

        Args:
            delay: Time delay between readings (default: 0.1s).
        """
        try:
            # Print initial information
            print(f"IMU Orientation: {'Upside Down' if self.MOUNTED_UPSIDE_DOWN else 'Normal'}")
            print(f"Accel Offsets: X={self.ACCEL_OFFSET_X}, Y={self.ACCEL_OFFSET_Y}, Z={self.ACCEL_OFFSET_Z}")
            print("Press Ctrl+C to stop")
            print("Reading data...", flush=True)
            
            # Main loop - update values on same line
            while True:
                imu_data = self.get_imu_data()
                # \r returns cursor to start of line, overwriting previous output
                # end='' prevents adding a newline, flush=True ensures immediate display
                print(f"\rRoll: {imu_data['roll']:+6.2f}° | Angular Velocity: {imu_data['angular_velocity']:+6.2f}°/s", end='', flush=True)
                time.sleep(delay)
                
        except KeyboardInterrupt:
            # Print a newline to ensure next terminal output starts on a new line
            print("\nIMU Reader Stopped.")
        finally:
            # Ensure terminal returns to normal state
            print("", flush=True)

# Example usage
if __name__ == "__main__":
    imu_reader = IMUReader(upside_down=True)
    imu_reader.print_imu_data()

