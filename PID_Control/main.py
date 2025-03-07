from motorController import MotorControl
from IMU_reader import IMUReader
import time
import threading

# Import our new modules
from config import CONFIG, HARDWARE_CONFIG
from balance_controller import BalanceController
from tuning import PIDTuner
from pid_controller import PIDController

def manual_mode(motor, imu):
    """
    Manual motor control mode: W for forward, S for reverse, I for IMU data, Q to quit.
    
    Args:
        motor: Motor controller instance
        imu: IMU reader instance
    """
    print("\n🚀 Manual Control Mode!")
    print("W: Run Motor Forward (100%)")
    print("S: Run Motor Reverse (100%)")
    print("I: Get IMU Data (Pitch & Angular Velocity)")
    print("Q: Quit Program")
    print("-------------------------")

    try:
        while True:
            command = input("Enter Command: ").lower().strip()

            if command == "w":
                motor.set_motor_speed(100, "clockwise")
                print("Motor running FORWARD at 100%")

            elif command == "s":
                motor.set_motor_speed(100, "counterclockwise")
                print("Motor running REVERSE at 100%")

            elif command == "i":
                imu_data = imu.get_imu_data()
                print(f"Pitch: {imu_data['pitch']:.2f}° | Angular Velocity: {imu_data['angular_velocity']:.2f}°/s")

            elif command == "q":
                print("Stopping motor and exiting...")
                motor.stop_motor()
                break

    except KeyboardInterrupt:
        print("\nInterrupted. Stopping motor.")

    finally:
        motor.stop_motor()
        print("Motor Stopped. Exiting.")

def runtime_parameter_tuning(pid_tuner, balance_controller):
    """
    Allows tuning parameters during runtime without interrupting the balancing.
    
    Args:
        pid_tuner: PID tuner instance
        balance_controller: Balance controller instance
    """
    print("\n⚙️ Runtime Parameter Tuning")
    print("You can modify parameters while the robot is balancing.")
    print("Format: <parameter_name>=<value> (e.g. P_GAIN=5.5)")
    print("Special commands:")
    print("  - 'list' - show current parameters")
    print("  - 'imu' - adjust IMU sensitivity")
    print("  - 'exit' - stop tuning")
    
    running = True
    while running and balance_controller.running:
        command = input("Command: ").strip()
        
        if command.lower() == 'exit':
            running = False
            continue
            
        if command.lower() == 'list':
            for key, value in pid_tuner.config.items():
                print(f"{key}: {value}")
            continue
            
        if command.lower() == 'imu':
            try:
                current_alpha = balance_controller.imu.ALPHA
                new_alpha = input(f"Enter new IMU filter alpha (current={current_alpha:.2f}, higher=more responsive): ")
                if new_alpha.strip():
                    balance_controller.imu.set_alpha(float(new_alpha))
            except ValueError:
                print("Invalid input. Please enter a number between 0 and 1.")
            continue
                
        # Parse parameter=value format
        if '=' in command:
            param, value = command.split('=', 1)
            param = param.strip()
            value = value.strip()
            
            if pid_tuner.tune_parameter_runtime(param, value):
                print(f"Updated {param} to {pid_tuner.config[param]}")
                
                # Update balance controller with new config
                # We're using the same config dictionary reference, 
                # so we just need to reinitialize the PID controller
                balance_controller.pid = PIDController(pid_tuner.config)
                print("Balance controller updated with new parameters")
            
        else:
            print("Invalid command. Use format: parameter=value")
    
    print("Runtime tuning exited.")

def imu_tuning_mode(imu):
    """
    Mode for tuning and testing IMU responsiveness.
    
    Args:
        imu: IMU reader instance
    """
    print("\n🔧 IMU Tuning Mode")
    print("Current alpha value: {:.2f}".format(imu.ALPHA))
    print("Commands:")
    print("  - 'a=VALUE' - set new alpha value (0-1, higher = more responsive)")
    print("  - 'test' - continuously show readings")
    print("  - 'exit' - exit mode")
    
    running = True
    testing = False
    last_time = time.time()
    
    try:
        while running:
            if testing:
                # Show IMU data without waiting for input
                current_time = time.time()
                if current_time - last_time >= 0.1:  # Update 10 times per second
                    imu_data = imu.get_imu_data()
                    print(f"Pitch: {imu_data['pitch']:.2f}° | Angular Velocity: {imu_data['angular_velocity']:.2f}°/s", end='\r')
                    last_time = current_time
                
                # Check for input without blocking
                if input_available():
                    command = input("\nCommand: ").lower().strip()
                    if command == 'exit':
                        testing = False
                else:
                    continue
            else:
                command = input("Command: ").lower().strip()
            
            if command == 'exit' and not testing:
                running = False
            elif command == 'test':
                print("Showing continuous readings (type 'exit' to stop)...")
                testing = True
            elif command.startswith('a='):
                try:
                    new_alpha = float(command[2:])
                    if imu.set_alpha(new_alpha):
                        print(f"Alpha set to {new_alpha:.2f}")
                except ValueError:
                    print("Invalid value. Please enter a number between 0 and 1.")
            else:
                print("Invalid command")
                
    except KeyboardInterrupt:
        print("\nIMU tuning interrupted.")
    
    print("IMU tuning mode exited.")

def input_available():
    """Check if input is available without blocking."""
    import sys, select
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

def main():
    """Main function with menu for different modes."""
    # Initialize hardware
    motor = MotorControl(HARDWARE_CONFIG['IN1_PIN'], HARDWARE_CONFIG['IN2_PIN'])
    imu = IMUReader()
    
    # Improve responsiveness by setting a more responsive filter alpha
    imu.ALPHA = 0.3  # Increase from 0.1 to 0.3 for more responsive readings
    
    # Create balance controller and PID tuner
    balance_controller = BalanceController(imu, motor, CONFIG)
    pid_tuner = PIDTuner(CONFIG)
    
    print("\n🤖 Self-Balancing Robot Control System")
    print("--------------------------------------")
    
    try:
        while True:
            print("\nSelect Mode:")
            print("1: Self-Balancing Mode (PID Control)")
            print("2: Manual Motor Control")
            print("3: Tune All PID Parameters")
            print("4: Quick-Tune Core PID Parameters (P, I, D gains)")
            print("5: Self-Balancing Mode with Runtime Parameter Tuning")
            print("6: IMU Responsiveness Tuning")
            print("Q: Quit Program")
            
            choice = input("\nEnter choice: ").lower().strip()
            
            if choice == '1':
                balance_controller.start_balancing()
            elif choice == '2':
                manual_mode(motor, imu)
            elif choice == '3':
                # Update config with tuned parameters
                pid_tuner.tune_parameters()
                # Update the balance controller with the new configuration
                balance_controller = BalanceController(imu, motor, CONFIG)
            elif choice == '4':
                # Quick tuning of just the P, I, and D gains
                pid_tuner.tune_specific_parameters(['P_GAIN', 'I_GAIN', 'D_GAIN'])
                # Update the balance controller with the new configuration
                balance_controller = BalanceController(imu, motor, CONFIG)
            elif choice == '5':
                # Start balancing in a separate thread
                balancing_thread = threading.Thread(
                    target=balance_controller.start_balancing,
                    daemon=True
                )
                balancing_thread.start()
                
                # Start runtime parameter tuning
                try:
                    runtime_parameter_tuning(pid_tuner, balance_controller)
                finally:
                    # Stop balancing when tuning is done
                    balance_controller.stop_balancing()
                    balancing_thread.join(timeout=1.0)
            elif choice == '6':
                # IMU tuning mode
                imu_tuning_mode(imu)
            elif choice == 'q':
                break
            else:
                print("Invalid choice, please try again.")
    
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
    
    finally:
        print("\nShutting down system...")
        motor.cleanup()
        print("System shutdown complete. Goodbye!")


if __name__ == "__main__":
    main()
