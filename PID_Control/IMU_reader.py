"""
IMU Reader Module for Self-Balancing Robot

This module handles communication with the ICM-20948 Inertial Measurement Unit (IMU)
and processes the raw sensor data to provide filtered roll angle and angular velocity
measurements that are essential for balancing the robot.

Key features:
- Supports both normal and upside-down mounting of the IMU
- Implements low-pass filtering to reduce noise in sensor readings
- Applies calibration offsets to account for sensor bias
- Provides adjustable filtering alpha parameter for tuning responsiveness
- Calculates roll angle from accelerometer data and angular velocity from gyroscope

Example Usage:
    # Initialize the IMU with default settings
    imu = IMUReader(alpha=0.2, upside_down=True)
    
    # Get filtered IMU data in a loop
    while True:
        data = imu.get_imu_data()
        angle = data['roll']
        angular_velocity = data['angular_velocity']
        
        print(f"Roll: {angle:.2f}° | Angular Velocity: {angular_velocity:.2f}°/s")
        time.sleep(0.01)
        
    # For tuning the IMU filter responsiveness
    # Higher alpha = more responsive, lower alpha = smoother
    imu.set_alpha(0.3)  # More responsive
    imu.set_alpha(0.1)  # Smoother
"""

import time
import math
import sys
import select
import tty
import termios

try:
    import board
    import adafruit_icm20x
    HARDWARE_AVAILABLE = True
except ImportError:
    print("Warning: Running with mock IMU - board/adafruit_icm20x modules not available")
    HARDWARE_AVAILABLE = False
    
    # Mock classes for testing without hardware
    class MockICM20948:
        def __init__(self, i2c):
            self._angle = 0.0
            self._angular_vel = 0.0
            self._last_update = time.time()
        
        @property
        def acceleration(self):
            # Simulate acceleration readings
            # Returns (x, y, z) tuple
            t = time.time()
            # Simulate some gentle motion
            self._angle += 0.1 * math.sin(t)
            return (0.0, -9.81 * math.sin(self._angle), 9.81 * math.cos(self._angle))
        
        @property
        def gyro(self):
            # Simulate gyroscope readings
            # Returns (x, y, z) tuple in degrees/second
            t = time.time()
            self._angular_vel = 5.0 * math.cos(t)
            return (self._angular_vel, 0.0, 0.0)
    
    class MockI2C:
        def __init__(self):
            pass
    
    # Mock the board module
    class MockBoard:
        @property
        def I2C(self):
            return MockI2C

    # Create mock instances
    board = MockBoard()
    adafruit_icm20x = type('MockAdafruitICM20X', (), {'ICM20948': MockICM20948})

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

    def imu_tuning_mode(self):
        """
        Interactive mode for tuning IMU responsiveness.
        
        Example:
            imu = IMUReader(alpha=0.2, upside_down=True)
            imu.imu_tuning_mode()
        """
        import select
        import sys
        import tty
        import termios
        
        # Import config here to avoid circular imports
        try:
            from config import CONFIG, save_config
        except ImportError:
            print("Warning: config module not found, settings will not be saved.")
            CONFIG = {}
            
            def save_config(config):
                print("Warning: config module not found, settings will not be saved.")
                pass
        
        print("\nIMU Tuning Mode")
        print("------------------")
        print("This mode allows you to adjust the IMU filter settings")
        print("to find the right balance between responsiveness and stability.")
        print("\nCurrent alpha value:", self.ALPHA)
        print("Higher alpha = more responsive but noisier")
        print("Lower alpha = smoother but slower to respond")
        print("\nCommands:")
        print("+ : Increase alpha by 0.05 (more responsive)")
        print("- : Decrease alpha by 0.05 (smoother)")
        print("r : Reset to default (0.2)")
        print("t : Toggle IMU upside-down setting")
        print("d : Display current values")
        print("q : Exit IMU tuning mode")
        print("\nIMU data will be displayed periodically. Press a key to access commands.")
        
        # Save original terminal settings
        old_settings = termios.tcgetattr(sys.stdin)
        
        try:
            # Set terminal to cbreak mode (better than raw mode)
            tty.setcbreak(sys.stdin.fileno())
            
            last_print_time = time.time()
            
            while True:
                # Display IMU data every 0.5 seconds instead of continuously
                current_time = time.time()
                if current_time - last_print_time >= 0.5:
                    # Display IMU data
                    imu_data = self.get_imu_data()
                    print(f"Roll: {imu_data['roll']:.2f}° | Angular Vel: {imu_data['angular_velocity']:.2f}°/s | Alpha: {self.ALPHA:.2f} | Upside-down: {self.MOUNTED_UPSIDE_DOWN}")
                    last_print_time = current_time
                
                # Check if key pressed with a short timeout
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    key = sys.stdin.read(1)
                    
                    # Handle each keypress
                    if key == 'q':
                        print("\nExiting IMU tuning mode.")
                        break
                    
                    elif key == '+':
                        new_alpha = min(self.ALPHA + 0.05, 0.95)
                        self.set_alpha(new_alpha)
                        print(f"\nIncreased alpha to {self.ALPHA:.2f}")
                        
                        # Update the config
                        CONFIG['IMU_FILTER_ALPHA'] = self.ALPHA
                        save_config(CONFIG)
                    
                    elif key == '-':
                        new_alpha = max(self.ALPHA - 0.05, 0.05)
                        self.set_alpha(new_alpha)
                        print(f"\nDecreased alpha to {self.ALPHA:.2f}")
                        
                        # Update the config
                        CONFIG['IMU_FILTER_ALPHA'] = self.ALPHA
                        save_config(CONFIG)
                    
                    elif key == 'r':
                        self.set_alpha(self.DEFAULT_ALPHA)
                        print(f"\nReset alpha to default ({self.DEFAULT_ALPHA:.2f})")
                        
                        # Update the config
                        CONFIG['IMU_FILTER_ALPHA'] = self.ALPHA
                        save_config(CONFIG)
                    
                    elif key == 't':
                        # Toggle the upside-down setting
                        self.MOUNTED_UPSIDE_DOWN = not self.MOUNTED_UPSIDE_DOWN
                        print(f"\nToggled IMU orientation. Upside-down: {self.MOUNTED_UPSIDE_DOWN}")
                        
                        # Update the config
                        CONFIG['IMU_UPSIDE_DOWN'] = self.MOUNTED_UPSIDE_DOWN
                        save_config(CONFIG)
                    
                    elif key == 'd':
                        print(f"\nCurrent settings: Alpha: {self.ALPHA:.2f}, Upside-down: {self.MOUNTED_UPSIDE_DOWN}")
        
        finally:
            # Proper cleanup: restore terminal settings no matter what
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            print("\nIMU tuning mode exited.")

# Example usage
if __name__ == "__main__":
    imu_reader = IMUReader(upside_down=True)
    imu_reader.print_imu_data()

