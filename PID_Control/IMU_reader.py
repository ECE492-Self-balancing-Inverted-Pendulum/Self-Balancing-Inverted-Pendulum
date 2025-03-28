"""
IMU Reader Module for Self-Balancing Robot (Modified for Consistency)

This module handles communication with the ICM-20948 IMU and processes data
using a pre-filter followed by a Madgwick filter (no magnetometer),
attempting to replicate the behavior of the provided standalone script.

WARNING: This implementation retains the flawed approach of pre-filtering
gyro data before the Madgwick filter. For a more correct implementation,
the pre-filter should be removed, and Madgwick gain adjusted.

Key features:
- Supports both normal and upside-down mounting of the IMU (Orientation logic retained, but calibration simplified for consistency)
- Implements pre-filter + Madgwick filter (no magnetometer)
- Applies calibration offsets
- Integrates with config.py

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
# Ensure config.py exists and is accessible
try:
    from config import CONFIG, save_config, load_config
    DEFAULT_CONFIG = load_config()
except ImportError:
    print("Warning: config.py not found. Using default settings.")
    # Define default CONFIG if not found, adjust as needed
    DEFAULT_CONFIG = {
        'IMU_ACCEL_OFFSET_X': 0.0, 'IMU_ACCEL_OFFSET_Y': 0.0, 'IMU_ACCEL_OFFSET_Z': 0.0,
        'IMU_GYRO_OFFSET_X': 0.0, 'IMU_GYRO_OFFSET_Y': 0.0, 'IMU_GYRO_OFFSET_Z': 0.0,
        'IMU_FILTER_ALPHA': 0.2, # Default alpha to match standalone script
        'IMU_FILTER_GAIN': 0.8,  # Default gain to match standalone script
        'IMU_UPSIDE_DOWN': True
    }
    # def save_config(cfg):
    #     print("Warning: save_config is a dummy function.")
    #     pass


class IMUReader:
    """
    A class for reading and filtering IMU data from the ICM-20948 sensor.
    Uses a pre-filter + Madgwick filter (no magnetometer) for consistency
    with the standalone script. Handles inverted mounting.
    """

    def __init__(self, upside_down=None): # Allow override of config
        """
        Initializes the IMU sensor with settings from CONFIG.
        Sets up the pre-filter and Madgwick filter.
        """
        # Create I2C interface
        self.i2c = busio.I2C(board.SCL, board.SDA)

        # Try to initialize the IMU (Match standalone script's implicit default usage)
        try:
            # Try default address 0x68 first
            self.imu = adafruit_icm20x.ICM20948(self.i2c, address=0x68)
            print("IMU initialized with address 0x68")
        except ValueError:
            try:
                 # Try alternative address 0x69
                self.imu = adafruit_icm20x.ICM20948(self.i2c, address=0x69)
                print("IMU initialized with address 0x69")
            except ValueError as e:
                print(f"Error initializing IMU: {e}")
                print("Try checking IMU connections and I2C address (use i2cdetect -y 1)")
                raise

        # Get calibration values from config (use defaults if not found)
        self.ACCEL_OFFSET_X = DEFAULT_CONFIG.get('IMU_ACCEL_OFFSET_X', 0.0)
        self.ACCEL_OFFSET_Y = DEFAULT_CONFIG.get('IMU_ACCEL_OFFSET_Y', 0.0)
        self.ACCEL_OFFSET_Z = DEFAULT_CONFIG.get('IMU_ACCEL_OFFSET_Z', 0.0)
        self.GYRO_OFFSET_X = DEFAULT_CONFIG.get('IMU_GYRO_OFFSET_X', 0.0)
        self.GYRO_OFFSET_Y = DEFAULT_CONFIG.get('IMU_GYRO_OFFSET_Y', 0.0)
        self.GYRO_OFFSET_Z = DEFAULT_CONFIG.get('IMU_GYRO_OFFSET_Z', 0.0)

        # Combine offsets into arrays for easier subtraction (like standalone script)
        self.accel_offset_vector = np.array([self.ACCEL_OFFSET_X, self.ACCEL_OFFSET_Y, self.ACCEL_OFFSET_Z])
        self.gyro_offset_vector = np.array([self.GYRO_OFFSET_X, self.GYRO_OFFSET_Y, self.GYRO_OFFSET_Z])

        # Set mounting orientation from config, allow override
        if upside_down is None:
            self.MOUNTED_UPSIDE_DOWN = DEFAULT_CONFIG.get('IMU_UPSIDE_DOWN', True)
        else:
            self.MOUNTED_UPSIDE_DOWN = upside_down
            DEFAULT_CONFIG['IMU_UPSIDE_DOWN'] = upside_down # Update config if overridden
        
        print(self.MOUNTED_UPSIDE_DOWN)
        if self.MOUNTED_UPSIDE_DOWN is False:
            self.MOUNTED_UPSIDE_DOWN = True
        

        # Initialize Madgwick filter components
        # self.SAMPLE_RATE = 100  # Hz - assumed sample rate
        self.SAMPLE_RATE = 1/DEFAULT_CONFIG.get('SAMPLE_TIME') # Allow config override
        print(self.SAMPLE_RATE)
        self.SAMPLE_RATE = int(self.SAMPLE_RATE)
        self.offset = imufusion.Offset(self.SAMPLE_RATE) # Keep for pre-filter
        self.ahrs = imufusion.Ahrs()

        # --- Consistency Change: Match standalone script's initial gain ---
        initial_gain = DEFAULT_CONFIG.get('MADGWICK_FILTER_GAIN', 0.8) # Default to 0.8

        # Set Madgwick filter parameters (Match standalone script)
        self.ahrs.settings = imufusion.Settings(
            imufusion.CONVENTION_NWU,  # North-West-Up convention
            initial_gain,              # Match standalone script's gain (0.8)
            2000,                      # Gyroscope range (deg/s)
            10,                        # Acceleration rejection threshold
            10,                        # Magnetic rejection threshold (Not used by update_no_magnetometer)
            1 * self.SAMPLE_RATE,      # Match standalone script's recovery period (1 second)
        )
        print(f"Madgwick filter initialized with gain: {initial_gain:.2f}")

        # --- Consistency Change: Match standalone script's alpha ---
        self.ALPHA = DEFAULT_CONFIG.get('IMU_FILTER_ALPHA', 0.2) # Default to 0.8
        print(f"Pre-filter alpha set to: {self.ALPHA:.2f}")


        # Initialize timing for filter
        self.prev_time = time.time()

        # Initialize orientation values
        self.roll = 0.0
        self.angular_velocity = 0.0

        # First reading to initialize values
        self._get_initial_reading() # Keep initial reading logic

    def set_gain(self, gain):
        """
        Update the Madgwick filter gain parameter and save to CONFIG.
        (Corrected implementation)

        Args:
            gain: New filter gain (0 < gain < 1)
        """
        if 0 < gain < 1:
            # --- Fix: Only update the gain attribute ---
            self.ahrs.settings.gain = gain

            # Save to CONFIG
            DEFAULT_CONFIG['MADGWICK_FILTER_GAIN'] = gain
            save_config(DEFAULT_CONFIG)

            print(f"IMU filter gain set to {gain:.2f}")
            return True
        else:
            print(f"Invalid gain value: {gain}. Must be between 0 and 1.")
            return False

    # Removed set_alpha as it's redundant if we fix ALPHA for consistency

    def _get_initial_reading(self):
        """
        Gets the first IMU reading, applies simplified calibration,
        and initializes the filters.
        """
        # Allow a short time for sensor to stabilize and get first dt
        time.sleep(1.0 / self.SAMPLE_RATE)
        curr_time = time.time()
        dt = max(curr_time - self.prev_time, 1e-4)
        self.prev_time = curr_time

        # Get raw values
        accel_raw = self.imu.acceleration
        gyro_raw = self.imu.gyro
        # mag_raw = self.imu.magnetic # Not needed for update_no_magnetometer

        # Convert to numpy arrays
        accel = np.array(accel_raw)
        gyro = np.array(gyro_raw) * (180 / np.pi)  # Convert rad/s to deg/s

        # --- Consistency Change: Apply offsets simply like standalone script ---
        # Apply offsets BEFORE potential orientation changes
        accel = accel - self.accel_offset_vector
        gyro = gyro - self.gyro_offset_vector

        # Apply orientation logic (kept from original class, may need testing)
        if self.MOUNTED_UPSIDE_DOWN:
            accel[1] = -accel[1]
            accel[2] = -accel[2]
            # gyro[0] = -gyro[0] # Still likely incorrect, keep commented
            gyro[1] = -gyro[1]
            gyro[2] = -gyro[2]

        # Clip acceleration values (like standalone script)
        accel = np.clip(accel, -9.81, 9.81)

        # Apply pre-filter (using the fixed self.ALPHA)
        gyro_filtered = self.ALPHA * gyro + (1 - self.ALPHA) * self.offset.update(gyro)

        # Initialize Madgwick filter (Match standalone script)
        self.ahrs.update_no_magnetometer(gyro_filtered, accel, dt) # Use dt, not 1.0

        # Get initial Euler angles
        euler = self.ahrs.quaternion.to_euler()

        # Store initial roll and gyro values (Match standalone script's source)
        self.roll = euler[0]
        self.angular_velocity = gyro_filtered[0] # Use pre-filtered gyro


    def get_imu_data(self):
        """
        Reads IMU data, applies pre-filter + Madgwick filter (no magnetometer),
        and returns processed values, aiming for consistency with standalone script.

        :return: A dictionary with 'roll' and 'angular_velocity'.
        """
        # Get time delta
        curr_time = time.time()
        dt = max(curr_time - self.prev_time, 1e-4)
        self.prev_time = curr_time

        # Read raw IMU values
        accel_raw = self.imu.acceleration
        gyro_raw = self.imu.gyro  # rad/s
        # mag_raw = self.imu.magnetic # Not needed

        # Convert to numpy arrays
        accel = np.array(accel_raw)
        gyro = np.array(gyro_raw) * (180 / np.pi)  # Convert rad/s to deg/s

        # --- Consistency Change: Apply offsets simply like standalone script ---
        # Apply offsets BEFORE potential orientation changes
        accel = accel - self.accel_offset_vector
        gyro = gyro - self.gyro_offset_vector

        # Apply orientation logic (kept from original class, may need testing)
        if self.MOUNTED_UPSIDE_DOWN:
            accel[1] = -accel[1]
            accel[2] = -accel[2]
            # gyro[0] = -gyro[0] # Still likely incorrect, keep commented
            gyro[1] = -gyro[1]
            gyro[2] = -gyro[2]

        # Clip acceleration values (like standalone script)
        accel = np.clip(accel, -9.81, 9.81)

        # Apply pre-filtering to gyro (using the fixed self.ALPHA = 0.8)
        gyro_filtered = self.ALPHA * gyro + (1 - self.ALPHA) * self.offset.update(gyro)

        # Apply Madgwick filter (Match standalone script)
        self.ahrs.update_no_magnetometer(gyro_filtered, accel, dt)

        # Get Euler angles
        euler = self.ahrs.quaternion.to_euler()

        # Store roll and angular velocity (Match standalone script's source)
        self.roll = euler[0]
        self.angular_velocity = gyro_filtered[0]  # Use pre-filtered gyro X-axis rate

        # Clip roll angle (like standalone script)
        self.roll = np.clip(self.roll, -180, 180)

        return {
            "roll": self.roll,
            "angular_velocity": self.angular_velocity # Return the pre-filtered value
        }

    #  Not being called by main. Needs to be in utility.py
    def print_imu_data(self, delay=0.1):
        """
        Continuously prints the IMU data for debugging on a single updating line.
        """
        try:
            print(f"IMU Orientation: {'Upside Down' if self.MOUNTED_UPSIDE_DOWN else 'Normal'}")
            print(f"Accel Offsets: X={self.ACCEL_OFFSET_X:.4f}, Y={self.ACCEL_OFFSET_Y:.4f}, Z={self.ACCEL_OFFSET_Z:.4f}")
            print(f"Gyro Offsets: X={self.GYRO_OFFSET_X:.4f}, Y={self.GYRO_OFFSET_Y:.4f}, Z={self.GYRO_OFFSET_Z:.4f}")
            print(f"Madgwick Gain: {self.ahrs.settings.gain:.2f}")
            print(f"Pre-filter Alpha: {self.ALPHA:.2f}")
            print("Press Ctrl+C to stop")
            print("Reading data...", flush=True)

            while True:
                imu_data = self.get_imu_data()
                print(f"\rRoll: {imu_data['roll']:+7.2f}° | AngVel: {imu_data['angular_velocity']:+7.2f}°/s", end='', flush=True)
                time.sleep(delay)

        except KeyboardInterrupt:
            print("\nIMU Reader Stopped.")
        finally:
            print("", flush=True)

# Example usage
if __name__ == "__main__":
    imu_reader = IMUReader() # Let config handle upside_down default or override here
    imu_reader.print_imu_data()
