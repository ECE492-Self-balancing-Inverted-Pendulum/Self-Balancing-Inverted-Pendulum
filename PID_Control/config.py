"""
Configuration Module for Self-Balancing Robot

This module handles loading, saving, and providing default configuration parameters
for the self-balancing robot. It centralizes all tunable parameters in one place,
making it easy to adjust the robot's behavior without modifying code.

Key features:
- Loads configuration from JSON file or creates default if none exists
- Provides easy-to-use interface for updating and saving configuration
- Defines default parameters for PID controller, motors, and IMU
- Maintains backward compatibility with older code

The configuration parameters are divided into several categories:
1. PID Controller Parameters - Control the balancing algorithm
2. Motor Parameters - Define motor behavior and limitations
3. IMU Parameters - Configure sensor responsiveness and orientation
4. System Parameters - Define timing and safety limits

Example Usage:
    # Load the configuration (automatically done when importing)
    from config import CONFIG, HARDWARE_CONFIG
    
    # Access configuration parameters
    p_gain = CONFIG['P_GAIN']
    motor_deadband = CONFIG['MOTOR_DEADBAND']
    
    # Update configuration parameters
    CONFIG['P_GAIN'] = 5.5
    
    # Save updated configuration to file
    from config import save_config
    save_config(CONFIG)
"""

import json
import os

# File path for the configuration
CONFIG_FILE = 'robot_config.json'

# Default configuration for the self-balancing robot
DEFAULT_CONFIG = {
    # PID Controller Parameters (easily adjustable)
    'P_GAIN': 5.0,     # Proportional gain (how strongly to react to current error)
    'I_GAIN': 0.1,     # Integral gain (how strongly to react to accumulated error)
    'D_GAIN': 1.0,     # Derivative gain (how strongly to react to rate of change)
    'MAX_I_TERM': 20,  # Maximum integral term to prevent windup
    'SETPOINT': 0.0,   # Target angle (0 = balanced upright)
    
    # Motor parameters
    'MOTOR_DEADBAND': 60,  # Motor doesn't move below this value (0-100)
    'MAX_MOTOR_SPEED': 100, # Maximum motor speed (0-100)
    'SAFE_TILT_LIMIT': 45,  # Safety cutoff angle in degrees
    'DIRECTION_CHANGE_BOOST': 10.0,  # Percentage boost when changing direction (0-100)
    'ZERO_THRESHOLD': 0.1,  # Threshold below which output is considered zero (0-100)
    
    # Loop timing
    'SAMPLE_TIME': 0.01,  # Time between PID updates (seconds)
    
    # IMU parameters
    'IMU_FILTER_ALPHA': 0.2,     # Low-pass filter coefficient (0-1)
    'IMU_UPSIDE_DOWN': True,     # Set to True if IMU is mounted upside down
}

def load_config():
    """
    Load configuration from file or create default if it doesn't exist.
    
    Returns:
        Configuration dictionary
    """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as file:
                config = json.load(file)
                print(f"✅ Configuration loaded from {CONFIG_FILE}")
                return config
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Error loading configuration: {e}")
            print("Using default configuration instead.")
            return DEFAULT_CONFIG.copy()
    else:
        # Create the default config file if it doesn't exist
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

def save_config(config):
    """
    Save configuration to file.
    
    Args:
        config: Configuration dictionary to save
    """
    try:
        with open(CONFIG_FILE, 'w') as file:
            json.dump(config, file, indent=4)
        print(f"✅ Configuration saved to {CONFIG_FILE}")
    except IOError as e:
        print(f"⚠️ Error saving configuration: {e}")

# Load the configuration
CONFIG = load_config()

# Set up hardware configuration for backward compatibility and convenience
HARDWARE_CONFIG = {
    # Hard-coded pin values - not tunable
    'MOTOR_A_IN1_PIN': 12,
    'MOTOR_A_IN2_PIN': 18,
    'MOTOR_B_IN1_PIN': 13,
    'MOTOR_B_IN2_PIN': 19,
 
}

# For backward compatibility
PID_CONFIG = CONFIG

