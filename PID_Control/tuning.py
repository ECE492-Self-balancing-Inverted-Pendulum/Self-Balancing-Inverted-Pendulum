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
        
        input("\nPress Enter to continue...")
        
        return self.config 
