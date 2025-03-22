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

    def __init__(self):
        """
        Initializes the IMU sensor with settings from CONFIG.
        """
        # Create I2C interface
        self.i2c = busio.I2C(board.SCL, board.SDA)
        
        # Try to initialize the IMU
        try:
            self.imu = adafruit_icm20x.ICM20948(self.i2c, address=0x0c)
            print("IMU initialized with address 0x0c")
        except ValueError:
            try:
                self.imu = adafruit_icm20x.ICM20948(self.i2c)
                print("IMU initialized with default address")
            except ValueError as e:
                print(f"Error initializing IMU: {e}")
                print("Try checking connections and I2C address (use i2cdetect -y 1)")
                raise
        
        # Get settings from CONFIG
        self.alpha = CONFIG.get('IMU_FILTER_ALPHA', 0.2)
        self.upside_down = CONFIG.get('IMU_UPSIDE_DOWN', True)
        
        print(f"IMU configured with alpha={self.alpha}, upside_down={self.upside_down}")

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
            self.alpha = alpha
            CONFIG['IMU_FILTER_ALPHA'] = alpha
            save_config(CONFIG)
            print(f"IMU filter alpha set to {alpha:.2f}")
            return True
        else:
            print(f"Invalid alpha value: {alpha}. Must be between 0 and 1.")
            return False

    def set_orientation(self, upside_down):
        """
        Update the IMU orientation setting and save to CONFIG.
        
        Args:
            upside_down: Whether the IMU is mounted upside-down
        """
        self.upside_down = upside_down
        CONFIG['IMU_UPSIDE_DOWN'] = upside_down
        save_config(CONFIG)
        print(f"IMU orientation set to upside_down={upside_down}")

    def _get_initial_reading(self):
        """
        Gets the first IMU reading and sets it as the initial reference.
        
        Returns:
            Initial roll and angular velocity values.
        """
        accel_x, accel_y, accel_z = self.imu.acceleration
        gyro_x, gyro_y, gyro_z = self.imu.gyro

        # Handle calibration offsets based on IMU orientation
        if self.upside_down:
            accel_y = -accel_y - self.ACCEL_OFFSET_Y
            accel_z = -accel_z - self.ACCEL_OFFSET_Z
            gyro_x = -gyro_x
        else:
            accel_y -= self.ACCEL_OFFSET_Y
            accel_z -= self.ACCEL_OFFSET_Z

        # Compute initial roll angle
        initial_roll = math.atan2(-accel_y, math.sqrt(accel_x**2 + accel_z**2)) * (180 / math.pi)

        return initial_roll, gyro_x

    def get_imu_data(self):
        """
        Reads IMU data, applies calibration and filtering, and returns processed values.
        
        Returns:
            A dictionary with roll and angular velocity.
        """
        # Read raw IMU values
        accel_x, accel_y, accel_z = self.imu.acceleration
        gyro_x, gyro_y, gyro_z = self.imu.gyro

        # Handle calibration offsets based on IMU orientation
        if self.upside_down:
            accel_y = -accel_y - self.ACCEL_OFFSET_Y
            accel_z = -accel_z - self.ACCEL_OFFSET_Z
            gyro_x = -gyro_x
        else:
            accel_y -= self.ACCEL_OFFSET_Y
            accel_z -= self.ACCEL_OFFSET_Z

        # Compute roll angle from accelerometer (degrees)
        roll = math.atan2(-accel_y, math.sqrt(accel_x**2 + accel_z**2)) * (180 / math.pi)

        # Apply low-pass filter to stabilize readings
        self.roll = self.alpha * roll + (1 - self.alpha) * self.roll
        self.angular_velocity = self.alpha * gyro_x + (1 - self.alpha) * self.angular_velocity

        return {
            "roll": self.roll,
            "angular_velocity": self.angular_velocity
        }

    def print_diagnostic_data(self, samples=10, delay=0.1):
        """
        Prints diagnostic IMU data for a set number of samples.
        
        Args:
            samples: Number of samples to collect and print
            delay: Time delay between readings
        """
        print(f"IMU Diagnostic Data ({samples} samples):")
        print(f"Alpha: {self.alpha}, Upside-down: {self.upside_down}")
        print("-" * 50)
        
        for i in range(samples):
            imu_data = self.get_imu_data()
            print(f"{i+1}/{samples}: Roll: {imu_data['roll']:.2f}° | Angular Velocity: {imu_data['angular_velocity']:.2f}°/s")
            time.sleep(delay)
        
        print("-" * 50)

# Example usage
if __name__ == "__main__":
    imu_reader = IMUReader()
    imu_reader.print_diagnostic_data()

