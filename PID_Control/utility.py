
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