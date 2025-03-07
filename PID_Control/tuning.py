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
    
    def tune_specific_parameters(self, param_list):
        """
        Tune only specific parameters from the configuration.
        
        Args:
            param_list: List of parameter names to tune
            
        Returns:
            Updated configuration dictionary
        """
        print("\n⚙️ Quick Tuning Mode")
        print("Current Parameter Values:")
        for key in param_list:
            if key in self.config:
                print(f"{key}: {self.config[key]}")
        
        print("\nEnter new value or press Enter to keep current value.")
        
        # Update only the specified parameters
        for key in param_list:
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
        for key in param_list:
            if key in self.config:
                print(f"{key}: {self.config[key]}")
        
        # Save changes to config file
        self.save_changes()
        
        input("\nPress Enter to continue...")
        
        return self.config
        
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
