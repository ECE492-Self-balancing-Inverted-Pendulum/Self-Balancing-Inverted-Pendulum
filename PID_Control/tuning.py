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
        print("\n⚙️ PID Tuning Mode")
        print("Current PID Parameters:")
        for key, value in self.config.items():
            print(f"{key}: {value}")
        print("\nEnter new value or press Enter to keep current value.")
        
        # Update parameters
        for key in self.config:
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
        
        print("\nUpdated PID Parameters:")
        for key, value in self.config.items():
            print(f"{key}: {value}")
            
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
        print("\n⚙️ Quick PID Tuning Mode")
        print("Current Parameters:")
        for key in params_list:
            if key in self.config:
                print(f"{key}: {self.config[key]}")
        
        print("\nEnter new value or press Enter to keep current value.")
        
        # Update selected parameters
        for key in params_list:
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
        
        print("\nUpdated Parameters:")
        for key in params_list:
            if key in self.config:
                print(f"{key}: {self.config[key]}")
        
        # Save changes to config file
        self.save_changes()
        
        input("\nPress Enter to continue...")
        
        return self.config
        
    def list_current_parameters(self):
        """
        Display current parameter values.
        """
        print("\nCurrent Parameters:")
        for key, value in self.config.items():
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
