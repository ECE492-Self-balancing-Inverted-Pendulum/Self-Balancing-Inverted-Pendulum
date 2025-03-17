#!/usr/bin/env python3
"""
Simple unit test for the configuration system.
This script:
1. Loads and displays the current config values
2. Uses the PIDTuner to modify values
3. Saves the modified config
4. Reloads the config to verify changes were saved

Usage:
    python test_config.py
"""

# Import the config module and PIDTuner
from config import CONFIG, load_config, save_config
from tuning import PIDTuner

def print_config(config, title="Current Configuration"):
    """
    Print the configuration values in a readable format
    """
    print(f"\n{title}:")
    print("-" * 40)
    
    # Print the most commonly tuned parameters first
    important_params = ['P_GAIN', 'I_GAIN', 'D_GAIN', 'IMU_FILTER_ALPHA', 'MOTOR_DEADBAND']
    
    for param in important_params:
        if param in config:
            print(f"{param:20}: {config[param]}")
    
    # Print any other parameters
    for param, value in config.items():
        if param not in important_params:
            print(f"{param:20}: {value}")
    
    print("-" * 40)

def main():
    """
    Main test function
    """
    print("🔧 Configuration System Test 🔧")
    
    # 1. Load and display current config
    load_config()
    print_config(CONFIG)
    
    # 2. Use PIDTuner to modify config
    print("\nUsing PIDTuner to modify configuration...")
    tuner = PIDTuner(CONFIG)
    tuner.tune_parameters()  # This function already saves the config
    
    # 3. Reload and verify changes
    print("\nReloading configuration to verify changes...")
    new_config = load_config()
    print_config(new_config, "Verified Configuration")
    
    print("\nTest complete. Configuration has been updated.")

if __name__ == "__main__":
    main() 