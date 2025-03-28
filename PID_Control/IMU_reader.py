"""
IMU Reader Module for Self-Balancing Robot

This module handles communication with the ICM-20948 Inertial Measurement Unit (IMU)
and processes the raw sensor data to provide filtered roll angle and angular velocity
measurements that are essential for balancing the robot.

Key features:
- Supports both normal and upside-down mounting of the IMU
- Implements Madgwick filter for more accurate orientation estimation
- Applies calibration offsets to account for sensor bias
- Integrates with config.py for tunable parameters
- Calculates roll angle and angular velocity for balancing

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
import numpy as np
import imufusion
from config import CONFIG, save_config

class IMUReader:
    """
    A class for reading and filtering IMU data from the ICM-20948 sensor.
    Uses Madgwick filter for improved orientation estimation.
    Handles inverted (upside-down) mounting of the IMU and integrates with config.py.
    """

    # Calibration offsets for the accelerometer
    ACCEL_OFFSET_X = 0.002331952416992187
    ACCEL_OFFSET_Y = -0.14494018010253898
    ACCEL_OFFSET_Z = 0.46995493779295927

    def __init__(self, upside_down=True):
        """
        Initializes the IMU sensor with settings from CONFIG.
        Sets up the Madgwick filter for orientation estimation.
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
        
        # Initialize Madgwick filter components
        self.SAMPLE_RATE = 100  # Hz - assumed sample rate
        self.offset = imufusion.Offset(self.SAMPLE_RATE)
        self.ahrs = imufusion.Ahrs()
        
        # Set Madgwick filter parameters
        self.ahrs.settings = imufusion.Settings(
            imufusion.CONVENTION_NWU,  # North-West-Up convention
            0.8,                       # Lower gain for smoother response
            2000,                      # Gyroscope range (deg/s)
            10,                        # Acceleration rejection threshold
            10,                        # Magnetic rejection threshold
            5 * self.SAMPLE_RATE,      # Recovery trigger period = 5 seconds
        )
        
        # Initialize timing for filter
        self.prev_time = time.time()
        
        # Initialize orientation values
        self.roll = 0.0
        self.angular_velocity = 0.0
        
        # First reading to initialize values
        self._get_initial_reading()
        
    def set_alpha(self, alpha):
        """
        Update the filter gain parameter and save to CONFIG.
        For compatibility with previous code, we still call it alpha.
        
        Args:
            alpha: New filter coefficient (0 < alpha < 1)
                 Higher = more responsive, Lower = smoother
        """
        if 0 < alpha < 1:
            # Import here to ensure we get the most up-to-date CONFIG
            from config import CONFIG, save_config
            
            # Update the alpha value in CONFIG (for compatibility)
            CONFIG['IMU_FILTER_ALPHA'] = alpha
            
            
            save_config(CONFIG)
            print(f"IMU filter parameter set to {alpha:.2f} (gain: {gain:.2f})")
            return True
        else:
            print(f"Invalid alpha value: {alpha}. Must be between 0 and 1.")
            return False
        
    def set_gain(self, gain):
        """
        Update the filter gain parameter and save to CONFIG.
        For compatibility with previous code, we still call it alpha.
        
        Args:
            gain: New filter coefficient (0 < gain < 1)
        """
        if 0 < gain < 1:
            # Update Madgwick filter gain (roughly map alpha to gain)
            # Alpha 0.8 (responsive) -> gain 0.5 (higher)
            # Alpha 0.2 (smooth) -> gain 0.1 (lower)
           
           CONFIG['IMU_FILTER_GAIN'] = gain
           save_config(CONFIG)
           print(f"IMU filter gain set to {gain:.2f}")
           return True
        else:
            print(f"Invalid gain value: {gain}. Must be between 0 and 1.")
            return False

            

    def _get_initial_reading(self):
        """
        Gets the first IMU reading and sets it as the initial reference.
        """
        # Get raw values
        accel_x, accel_y, accel_z = self.imu.acceleration
        gyro_x, gyro_y, gyro_z = self.imu.gyro
        mag_x, mag_y, mag_z = self.imu.magnetic
        
        # Convert to numpy arrays and apply offsets
        accel = np.array([accel_x, accel_y, accel_z])
        gyro = np.array([gyro_x, gyro_y, gyro_z]) * (180 / np.pi)  # Convert rad/s to deg/s
        mag = np.array([mag_x, mag_y, mag_z])
        
        # Apply calibration offsets
        if self.MOUNTED_UPSIDE_DOWN:
            accel[1] = -accel[1] - self.ACCEL_OFFSET_Y
            accel[2] = -accel[2] - self.ACCEL_OFFSET_Z
            gyro[0] = -gyro[0]
        else:
            accel[1] -= self.ACCEL_OFFSET_Y
            accel[2] -= self.ACCEL_OFFSET_Z
        
        # Clip acceleration values to reasonable range
        accel = np.clip(accel, -9.81, 9.81)
        
        # Initialize Madgwick filter with first reading
        self.ahrs.update(gyro, accel, mag, 1.0)  # Use 1.0 as initial dt
        
        # Get initial Euler angles
        euler = self.ahrs.quaternion.to_euler()
        
        # Store initial roll and gyro values
        self.roll = euler[0]
        self.angular_velocity = gyro[0]
        self.prev_time = time.time()

    def get_imu_data(self):
        """
        Reads IMU data, applies Madgwick filter, and returns processed values.
        Accounts for the IMU being mounted upside-down.

        :return: A dictionary with roll and angular velocity.
        """
        # Get alpha from config (for parameter adjustment compatibility)
        self.ALPHA = CONFIG.get('IMU_FILTER_ALPHA', 0.2)
        
        # Read raw IMU values
        accel_x, accel_y, accel_z = self.imu.acceleration
        gyro_x, gyro_y, gyro_z = self.imu.gyro  # rad/s
        mag_x, mag_y, mag_z = self.imu.magnetic
        
        # Convert to numpy arrays
        accel = np.array([accel_x, accel_y, accel_z])
        gyro = np.array([gyro_x, gyro_y, gyro_z]) * (180 / np.pi)  # Convert rad/s to deg/s
        mag = np.array([mag_x, mag_y, mag_z])
        
        # Handle calibration offsets based on IMU orientation
        if self.MOUNTED_UPSIDE_DOWN:
            # For upside-down mounting, invert Y and Z axes
            accel[1] = -accel[1] - self.ACCEL_OFFSET_Y
            accel[2] = -accel[2] - self.ACCEL_OFFSET_Z
            gyro[0] = -gyro[0]
        else:
            # Normal mounting - apply offsets normally
            accel[1] -= self.ACCEL_OFFSET_Y
            accel[2] -= self.ACCEL_OFFSET_Z

        # Prevent extreme acceleration values
        accel = np.clip(accel, -9.81, 9.81)
        
        # Apply pre-filtering to gyro (reduces noise)
        gyro_filtered = self.ALPHA * gyro + (1 - self.ALPHA) * self.offset.update(gyro)
        
        # Get time delta
        curr_time = time.time()
        dt = max(curr_time - self.prev_time, 1e-3)  # Prevent division by zero
        self.prev_time = curr_time
        
        # Apply Madgwick filter
        self.ahrs.update(gyro_filtered, accel, mag, dt)
        
        # Get Euler angles
        euler = self.ahrs.quaternion.to_euler()
        
        # Store roll and angular velocity
        self.roll = euler[0]
        self.angular_velocity = gyro_filtered[0]  # Use X-axis rotation rate
        
        # Clip to reasonable values
        self.roll = np.clip(self.roll, -180, 180)

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

