"""
Simplified IMU Reader Module with Madgwick Filter

This module provides a simple interface to read and process data from the ICM-20948 IMU
using the Madgwick filter algorithm via the imufusion library.
"""

import time
import board
import busio
import adafruit_icm20x
import numpy as np
import imufusion
from config import load_config, save_config

class IMUReader:
    """
    A simplified class for reading IMU data and applying a Madgwick filter.
    """
    
    def __init__(self, upside_down=True, sample_rate=100):
        """
        Initialize the IMU sensor with a Madgwick filter.
        
        Args:
            upside_down: Whether the IMU is mounted upside down
            sample_rate: Sensor sampling rate in Hz
        """
        # Create I2C interface
        self.i2c = busio.I2C(board.SCL, board.SDA)
        
        # Try to initialize the IMU
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
                print("Check IMU connections and I2C address")
                raise
        
        # Load config values
        self.config = load_config()
        
        # Load calibration data from config - only using array format
        self.gyro_offset = np.array(self.config.get('IMU_GYRO_OFFSET', [0, 0, 0]))
        self.accel_offset = np.array(self.config.get('IMU_ACCEL_OFFSET', [0, 0, 0]))
        
        # Load upside_down setting
        self.upside_down = self.config.get('IMU_UPSIDE_DOWN', upside_down)
        print(f"IMU mounted upside down: {self.upside_down}")
        
        # Sensor sampling rate (calculated from SAMPLE_TIME in config)
        sample_time = self.config.get('SAMPLE_TIME', 0.01)  # Default to 0.01s (100Hz)
        self.sample_rate = int(1 / sample_time)
        print(f"IMU sampling rate: {self.sample_rate} Hz (from sample time: {sample_time}s)")
        
        # Flag to track if filter is initialized
        self._filter_initialized = False
        
        # These will be initialized when get_imu_data is first called
        self.offset = None
        self.ahrs = None
        self.roll = 0.0
        self.angular_velocity = 0.0
        self.prev_time = None
    
    def _initialize_filter(self):
        """
        Initialize the filter components. Called on first data request or after reset.
        """
        print("Initializing IMU filter...")
        # Initialize filter components
        self.offset = imufusion.Offset(self.sample_rate)
        self.ahrs = imufusion.Ahrs()
        
        self.ahrs.settings = imufusion.Settings(
            imufusion.CONVENTION_NWU,  # North-West-Up convention
            0.8,                      # Gain for filter
            2000,                      # Gyroscope range (deg/s)
            10,                        # Acceleration rejection threshold
            10,                        # Magnetic rejection threshold
            1 * self.sample_rate       # Recovery trigger period
        )
        print(f"Madgwick filter initialized with gain: {0.8}")
        
        # Time tracking
        self.prev_time = time.time()
        
        # Initialize filter values
        self.roll = 0.0
        self.angular_velocity = 0.0
        
        # Set flag to indicate filter is initialized
        self._filter_initialized = True
    
    def get_imu_data(self):
        """
        Get filtered IMU data.
        
        Returns:
            dict: Dictionary containing 'roll' and 'angular_velocity'
        """
        # Initialize filter if this is the first call or after reset
        if not self._filter_initialized:
            self._initialize_filter()
        
        # Get time delta
        curr_time = time.time()
        dt = max(curr_time - self.prev_time, 1e-3)
        self.prev_time = curr_time
        
        # Read IMU raw data
        accel_raw = self.imu.acceleration
        gyro_raw = self.imu.gyro
        
        # Convert to numpy arrays and apply calibration offsets
        accel = np.array(accel_raw) - self.accel_offset
        gyro = np.array(gyro_raw) * (180 / np.pi) - self.gyro_offset
        
        # Prevent acceleration fluctuations
        accel = np.clip(accel, -9.81, 9.81)
        
        # Apply orientation correction if upside down
        if self.upside_down:
            accel[1] = -accel[1]
            accel[2] = -accel[2]
            gyro[1] = -gyro[1]
            gyro[2] = -gyro[2]
        
        # Apply low-pass filter to gyro
        alpha = 0.15
        gyro_filtered = alpha * gyro + (1 - alpha) * self.offset.update(gyro)
        
        # Apply Madgwick filter without magnetometer
        self.ahrs.update_no_magnetometer(gyro_filtered, accel, dt)
        
        # Get Euler angles
        euler = self.ahrs.quaternion.to_euler()
        
        # Store roll angle and angular velocity
        self.roll = euler[0]
        self.angular_velocity = gyro_filtered[0]
        
        # Return simplified data structure
        return {
            "roll": self.roll,
            "angular_velocity": self.angular_velocity
        }
    
    def reset_filter(self):
        """
        Reset the IMU filter. Next call to get_imu_data will reinitialize the filter.
        """
        print("Resetting IMU filter...")
        self._filter_initialized = False
        
    def set_gain(self, gain):
        """
        Update the Madgwick filter gain parameter.
        
        Args:
            gain: New filter gain (0 < gain < 1)
        """
        if 0 < gain < 1:
            # Initialize filter if not already done
            if not self._filter_initialized:
                self._initialize_filter()
                
            self.ahrs.settings.gain = gain
            
            # Save to config
            self.config = load_config()
            self.config['IMU_FILTER_GAIN'] = gain
            save_config(self.config)
            
            print(f"Madgwick filter gain set to {gain:.2f} and saved to config")
            return True
        else:
            print(f"Invalid gain value: {gain}. Must be between 0 and 1.")
            return False


# Example usage
if __name__ == "__main__":
    imu_reader = IMUReader()
    
    try:
        print("Reading IMU data... Press Ctrl+C to stop")
        while True:
            data = imu_reader.get_imu_data()
            print(f"\rRoll: {data['roll']:.2f}° | Angular Velocity: {data['angular_velocity']:.2f}°/s", end="", flush=True)
            time.sleep(1/100)  # 100Hz refresh rate
    except KeyboardInterrupt:
        print("\nIMU Reader stopped.")
