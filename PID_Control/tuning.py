"""
PID Tuning Module for Self-Balancing Robot

This module provides interfaces for interactively tuning the PID parameters
and other configuration settings of the self-balancing robot. It offers multiple
tuning modes from comprehensive parameter adjustment to quick adjustments of
critical parameters.

Key features:
- Interactive console-based parameter tuning
- Selective tuning of specific parameter groups
- Runtime parameter adjustments during balancing
- Automatic saving of tuned parameters to configuration file
- Display of current parameter values for reference

Tuning is a critical part of making a self-balancing robot work effectively,
as the ideal PID parameters vary depending on the physical characteristics of
the robot, such as weight distribution, motor power, and sensor placement.

Example Usage:
    # Full parameter tuning
    from tuning import PIDTuner
    from config import CONFIG
    
    tuner = PIDTuner(CONFIG)
    
    # Interactive tuning of all parameters
    tuner.tune_parameters()
    
    # Quick tuning of just the core PID gains
    tuner.tune_specific_parameters(['P_GAIN', 'I_GAIN', 'D_GAIN'])
    
    # Display current parameter values
    tuner.list_current_parameters()
    
    # Runtime adjustment of a single parameter
    tuner.tune_parameter_runtime('P_GAIN', 5.5)
"""

import sys
import config

class PIDTuner:
    """
    Interface for tuning PID parameters interactively.
    """
    
    def __init__(self, config_dict):
        """
        Initialize PID tuner with a configuration dictionary.
        
        Args:
            config_dict: Dictionary containing PID and other parameters
        """
        self.config = config_dict
    
    def save_changes(self):
        """
        Save current configuration to file.
        """
        config.save_config(self.config)
        print("Changes have been saved to the configuration file.")
    
    def tune_parameters(self):
        """
        Interactive tuning of PID parameters.
        
        Returns:
            Updated configuration dictionary
        """
        print("\nPID Tuning Mode")
        print("Current PID Parameters:")
        print("-" * 40)
        
        # Display parameters in a more organized way
        for key, value in self.config.items():
            print(f"{key:20}: {value}")
        
        print("-" * 40)
        print("\nEnter new value or press Enter to keep current value.")
        print("Parameters will appear one by one.\n")
        
        # Update parameters
        for key in self.config:
            try:
                # Print on a new line each time
                print(f"\n{key} [{self.config[key]}]")
                new_value = input("New value: ")
                
                if new_value.strip():
                    # Convert to the same type as the current value
                    if isinstance(self.config[key], float):
                        self.config[key] = float(new_value)
                        print(f"Updated to: {self.config[key]}")
                    elif isinstance(self.config[key], int):
                        self.config[key] = int(new_value)
                        print(f"Updated to: {self.config[key]}")
                    elif isinstance(self.config[key], bool):
                        # Handle boolean values
                        if new_value.lower() in ('true', 'yes', '1'):
                            self.config[key] = True
                        else:
                            self.config[key] = False
                        print(f"Updated to: {self.config[key]}")
                    else:
                        # Handle strings and other types
                        self.config[key] = new_value
                        print(f"Updated to: {self.config[key]}")
                else:
                    print("Kept current value.")
            except ValueError as e:
                print(f"Invalid input for {key}, keeping current value. Error: {e}")
        
        print("\nUpdated PID Parameters:")
        print("-" * 40)
        for key, value in self.config.items():
            print(f"{key:20}: {value}")
        print("-" * 40)
        
        # Save changes to config file
        self.save_changes()
        
        input("\nPress Enter to continue...")
        
        return self.config
    
    def tune_specific_parameters(self, params_list):
        """
        Interactive tuning of specific parameters.
        
        Args:
            params_list: List of parameter names to tune
            
        Returns:
            Updated configuration dictionary
        """
        # Add MOTOR_DEADBAND and MAX_MOTOR_SPEED to the list of parameters that can be tuned
        all_params = params_list + ['MOTOR_DEADBAND', 'MAX_MOTOR_SPEED']
        
        print("\nQuick PID Tuning Mode")
        print("Current Parameters:")
        for key in all_params:
            if key in self.config:
                print(f"{key}: {self.config[key]}")
        
        print("\nEnter new value or press Enter to keep current value.")
        
        # Update parameters
        for key in all_params:
            if key in self.config:
                try:
                    new_value = input(f"{key} [{self.config[key]}]: ")
                    if new_value.strip():
                        # Convert to the same type as the current value
                        if isinstance(self.config[key], float):
                            self.config[key] = float(new_value)
                        elif isinstance(self.config[key], int):
                            self.config[key] = int(new_value)
                except ValueError:
                    print(f"Invalid input for {key}, keeping current value.")
        
        # Save changes
        self.save_changes()
        
        return self.config
        
    def list_current_parameters(self):
        """
        Display current parameter values.
        """
        print("\nCurrent Parameters:")
        for key, value in self.config.items():
            if key not in ['SETPOINT', 'IN1_PIN', 'IN2_PIN']:
                print(f"{key}: {value}")
        
        # Group parameters by type for better readability
        print("\nGrouped by category:")
        
        print("\nPID Controller:")
        print(f"P_GAIN: {self.config.get('P_GAIN', 'N/A')}")
        print(f"I_GAIN: {self.config.get('I_GAIN', 'N/A')}")
        print(f"D_GAIN: {self.config.get('D_GAIN', 'N/A')}")
        print(f"MAX_I_TERM: {self.config.get('MAX_I_TERM', 'N/A')}")
        
        print("\nMotor Configuration:")
        print(f"MOTOR_DEADBAND: {self.config.get('MOTOR_DEADBAND', 'N/A')}")
        print(f"MAX_MOTOR_SPEED: {self.config.get('MAX_MOTOR_SPEED', 'N/A')}")
        print(f"DIRECTION_CHANGE_BOOST: {self.config.get('DIRECTION_CHANGE_BOOST', 'N/A')}")
        
        print("\nIMU Configuration:")
        print(f"IMU_FILTER_ALPHA: {self.config.get('IMU_FILTER_ALPHA', 'N/A')}")
        print(f"IMU_UPSIDE_DOWN: {self.config.get('IMU_UPSIDE_DOWN', 'N/A')}")
        
        print("\nSafety Settings:")
        print(f"SAFE_TILT_LIMIT: {self.config.get('SAFE_TILT_LIMIT', 'N/A')}")
        
        print("\nTiming:")
        print(f"SAMPLE_TIME: {self.config.get('SAMPLE_TIME', 'N/A')}")
    
    def tune_parameter_runtime(self, parameter, value):
        """
        Tune a single parameter during runtime.
        
        Args:
            parameter: Name of the parameter to tune
            value: New value for the parameter
            
        Returns:
            Updated configuration dictionary
        """
        if parameter in self.config:
            try:
                # Convert to the same type as the current value
                if isinstance(self.config[parameter], float):
                    self.config[parameter] = float(value)
                elif isinstance(self.config[parameter], int):
                    self.config[parameter] = int(value)
                
                # Save changes to config file
                self.save_changes()
                return True
            except ValueError:
                print(f"Invalid value for {parameter}")
                return False
        else:
            print(f"Parameter {parameter} not found in configuration")
            return False 
