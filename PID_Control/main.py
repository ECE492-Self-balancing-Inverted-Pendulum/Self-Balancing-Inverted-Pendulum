from motorController import MotorControl, DualMotorControl
from IMU_reader import IMUReader
import time
import threading
import select
import sys
import tty
import termios
import socket

# Import our new modules
from config import CONFIG, HARDWARE_CONFIG
from balance_controller import BalanceController
from tuning import PIDTuner
from pid_controller import PIDController
from webpage import start_server, stop_server, add_data_point, set_pid_params, update_pid_params, set_update_callback

def runtime_parameter_tuning(pid_tuner, balance_controller):
    """
    Self-balancing mode with web dashboard for parameter tuning.
    Shows real-time angle output in the terminal while allowing parameter tuning via web interface.
    
    Args:
        pid_tuner: PID tuner instance
        balance_controller: Balance controller instance
    """
    print("\n🤖 Self-Balancing Mode with Web Dashboard")
    print("Controls:")
    print("  Q: Return to Main Menu")
    
    # Note: We don't need to print the IP here since the web_server module will handle that
    
    # Try a different port if needed - this may help avoid conflicts with other services
    server_port = 8080
    
    # Start the web server - the web_server module will print the URL
    try:
        start_server(port=server_port)
    except Exception as e:
        print(f"❌ Error starting server. Try a different port (current: {server_port}).")
        return
    
    # Initialize the web interface with current PID parameters
    set_pid_params(
        balance_controller.pid.kp,
        balance_controller.pid.ki,
        balance_controller.pid.kd,
        0.0  # Target angle is always 0 for balancing
    )
    
    # Set up callback for when parameters are updated via the web interface
    def params_update_callback(params):
        if 'kp' in params:
            balance_controller.pid.kp = params['kp']
            CONFIG['P_GAIN'] = params['kp']
        if 'ki' in params:
            balance_controller.pid.ki = params['ki']
            CONFIG['I_GAIN'] = params['ki']
        if 'kd' in params:
            balance_controller.pid.kd = params['kd']
            CONFIG['D_GAIN'] = params['kd']
        
        # Print on a separate line with newline to avoid text overlapping
        print(f"\nParameters updated: KP={balance_controller.pid.kp:.2f}, KI={balance_controller.pid.ki:.2f}, KD={balance_controller.pid.kd:.2f}")
    
    # Register the callback
    set_update_callback(params_update_callback)
    
    # Create a debug callback function to send data to the web interface
    # and display angles in the terminal
    def debug_callback(debug_info):
        # Send data to the web interface
        roll = debug_info['roll']
        angular_velocity = debug_info['angular_velocity']
        output = debug_info['output']
        motor_output = debug_info.get('motor_output', abs(output))  # Get motor output percentage
        pid_info = debug_info['pid']
        
        # Display angle in terminal (similar to option 1) 
        # Use carriage return to overwrite the line and prevent text overlap
        if balance_controller.enable_debug:
            # Clear the line completely before writing
            sys.stdout.write("\r" + " " * 80)  # Write 80 spaces to clear the line
            sys.stdout.write(f"\rAngle: {roll:6.2f}° | Output: {output:6.1f} | Motor: {motor_output:3.0f}% | P: {pid_info['p_term']:6.1f} | I: {pid_info['i_term']:6.1f} | D: {pid_info['d_term']:6.1f}")
            sys.stdout.flush()
        
        # Send data to web dashboard
        add_data_point(
            actual_angle=roll,
            target_angle=0.0,  # Target is always 0 for balancing
            error=0.0 - roll,  # Error is target - actual
            p_term=pid_info['p_term'],
            i_term=pid_info['i_term'],
            d_term=pid_info['d_term'],
            pid_output=output,
            motor_output=motor_output  # Add motor output percentage
        )
    
    print("\nStarting balancing. Web dashboard is available for tuning parameters.")
    print("Press 'Q' to return to the menu.")
    
    # Start balancing with the dashboard display
    balance_controller.start_balancing(debug_callback)
    
    # The balance_controller will return when 'Q' is pressed
    # At this point, we just need to ensure the server is stopped properly
    print("\nStopping web server...")
    stop_server()
    print("Returned to main menu.")

def imu_tuning_mode(imu):
    """
    Interactive mode for tuning IMU responsiveness.
    
    Args:
        imu: IMU reader instance
    """
    print("\n📊 IMU Tuning Mode")
    print("------------------")
    print("This mode allows you to adjust the IMU filter settings")
    print("to find the right balance between responsiveness and stability.")
    print("\nCurrent alpha value:", imu.ALPHA)
    print("Higher alpha = more responsive but noisier")
    print("Lower alpha = smoother but slower to respond")
    print("\nCommands:")
    print("+ : Increase alpha by 0.05 (more responsive)")
    print("- : Decrease alpha by 0.05 (smoother)")
    print("r : Reset to default (0.2)")
    print("t : Toggle IMU upside-down setting")
    print("d : Display current values")
    print("q : Exit IMU tuning mode")
    print("\nContinuously displays IMU data. Press any key to access commands.")
    
    # Setup for non-blocking input
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        # Set terminal to raw mode
        tty.setraw(sys.stdin.fileno())
        
        while True:
            # Display IMU data
            imu_data = imu.get_imu_data()
            
            # Clear line and print data
            sys.stdout.write("\r\033[K")  # Clear line
            sys.stdout.write(f"Roll: {imu_data['roll']:.2f}° | Angular Vel: {imu_data['angular_velocity']:.2f}°/s | Alpha: {imu.ALPHA:.2f} | Upside-down: {imu.MOUNTED_UPSIDE_DOWN}")
            sys.stdout.flush()
            
            # Check if key pressed
            if select.select([sys.stdin], [], [], 0.1)[0]:
                key = sys.stdin.read(1)
                
                if key == 'q':
                    print("\nExiting IMU tuning mode.")
                    break
                
                elif key == '+':
                    new_alpha = min(imu.ALPHA + 0.05, 0.95)
                    imu.set_alpha(new_alpha)
                    sys.stdout.write("\r\033[K")  # Clear line
                    print(f"\nIncreased alpha to {imu.ALPHA:.2f}")
                    
                    # Update the config
                    CONFIG['IMU_FILTER_ALPHA'] = imu.ALPHA
                    from config import save_config
                    save_config(CONFIG)
                
                elif key == '-':
                    new_alpha = max(imu.ALPHA - 0.05, 0.05)
                    imu.set_alpha(new_alpha)
                    sys.stdout.write("\r\033[K")  # Clear line
                    print(f"\nDecreased alpha to {imu.ALPHA:.2f}")
                    
                    # Update the config
                    CONFIG['IMU_FILTER_ALPHA'] = imu.ALPHA
                    from config import save_config
                    save_config(CONFIG)
                
                elif key == 'r':
                    imu.set_alpha(imu.DEFAULT_ALPHA)
                    sys.stdout.write("\r\033[K")  # Clear line
                    print(f"\nReset alpha to default ({imu.DEFAULT_ALPHA:.2f})")
                    
                    # Update the config
                    CONFIG['IMU_FILTER_ALPHA'] = imu.ALPHA
                    from config import save_config
                    save_config(CONFIG)
                
                elif key == 't':
                    # Toggle the upside-down setting
                    imu.MOUNTED_UPSIDE_DOWN = not imu.MOUNTED_UPSIDE_DOWN
                    sys.stdout.write("\r\033[K")  # Clear line
                    print(f"\nToggled IMU orientation. Upside-down: {imu.MOUNTED_UPSIDE_DOWN}")
                    
                    # Update the config
                    CONFIG['IMU_UPSIDE_DOWN'] = imu.MOUNTED_UPSIDE_DOWN
                    from config import save_config
                    save_config(CONFIG)
                
                elif key == 'd':
                    sys.stdout.write("\r\033[K")  # Clear line
                    print(f"\nCurrent settings: Alpha: {imu.ALPHA:.2f}, Upside-down: {imu.MOUNTED_UPSIDE_DOWN}")
    
    finally:
        # Restore terminal settings
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        print("\nIMU tuning mode exited.")

def input_available():
    """Check if input is available without blocking."""
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

def dual_motor_test(motors):
    """
    Test mode for independently testing both motors.
    
    Args:
        motors: DualMotorControl instance
    """
    print("\n🔌 Dual Motor Test Mode")
    print("----------------------")
    print("W: Both Motors Forward (100%)")
    print("S: Both Motors Reverse (100%)")
    print("A: Motor A Forward (100%)")
    print("D: Motor B Forward (100%)")
    print("Z: Motor A Reverse (100%)")
    print("X: Motor B Reverse (100%)")
    print("I: Get IMU Data")
    print("Q: Quit to Main Menu")
    print("-------------------------")
    
    try:
        while True:
            command = input("Enter Command: ").lower().strip()
            
            if command == "w":
                motors.set_motors_speed(100, "clockwise")
                print("Both motors running FORWARD at 100%")
                
            elif command == "s":
                motors.set_motors_speed(100, "counterclockwise")
                print("Both motors running REVERSE at 100%")
                
            elif command == "a":
                motors.set_individual_speeds(100, "clockwise", 0, "stop")
                print("Motor A running FORWARD at 100%")
                
            elif command == "d":
                motors.set_individual_speeds(0, "stop", 100, "clockwise")
                print("Motor B running FORWARD at 100%")
                
            elif command == "z":
                motors.set_individual_speeds(100, "counterclockwise", 0, "stop")
                print("Motor A running REVERSE at 100%")
                
            elif command == "x":
                motors.set_individual_speeds(0, "stop", 100, "counterclockwise")
                print("Motor B running REVERSE at 100%")
                
            elif command == "i":
                imu_data = IMU.get_imu_data()
                print(f"Roll: {imu_data['roll']:.2f}° | Angular Velocity: {imu_data['angular_velocity']:.2f}°/s")
                
            elif command == "q":
                print("Exiting dual motor test mode...")
                motors.stop_motors()
                break
                
    except KeyboardInterrupt:
        print("\nTest interrupted.")
        motors.stop_motors()

def main():
    """Main function with menu for different modes."""
    # Initialize IMU with configuration from CONFIG
    # This compensates for the orientation of the IMU (upside-down or normal)
    imu = IMUReader(
        alpha=CONFIG.get('IMU_FILTER_ALPHA', 0.3),
        upside_down=CONFIG.get('IMU_UPSIDE_DOWN', True)
    )
    
    # Initialize motor control - Now using DualMotorControl for both motors
    motors = DualMotorControl(
        motor_a_in1=HARDWARE_CONFIG['MOTOR_A_IN1_PIN'],
        motor_a_in2=HARDWARE_CONFIG['MOTOR_A_IN2_PIN'],
        motor_b_in1=HARDWARE_CONFIG['MOTOR_B_IN1_PIN'],
        motor_b_in2=HARDWARE_CONFIG['MOTOR_B_IN2_PIN']
    )
    
    # Create balance controller and PID tuner
    balance_controller = BalanceController(imu, motors, CONFIG)
    pid_tuner = PIDTuner(CONFIG)
    
    # Make IMU accessible to test functions
    global IMU
    IMU = imu
    
    print("\n🤖 Self-Balancing Robot Control System")
    print("--------------------------------------")
    print("Using dual motors for better stability and control")
    
    try:
        while True:
            print("\nSelect Mode:")
            print("1: Self-Balancing Mode (PID Control)")
            print("2: Dual Motor Test")
            print("3: Tune All PID Parameters")
            print("4: Quick-Tune Core PID Parameters (P, I, D gains)")
            print("5: Self-Balancing Mode with Runtime Parameter Tuning & Web Dashboard")
            print("6: IMU Responsiveness Tuning")
            print("Q: Quit Program")
            
            choice = input("\nEnter choice: ").lower().strip()
            
            if choice == '1':
                # Define a debug callback function to send data to the web interface
                def debug_callback(debug_info):
                    # Send data to the web interface
                    roll = debug_info['roll']
                    angular_velocity = debug_info['angular_velocity']
                    output = debug_info['output']
                    motor_output = debug_info.get('motor_output', abs(output))  # Get motor output percentage
                    pid_info = debug_info['pid']
                    
                    add_data_point(
                        actual_angle=roll,
                        target_angle=0.0,  # Target is always 0 for balancing
                        error=0.0 - roll,  # Error is target - actual
                        p_term=pid_info['p_term'],
                        i_term=pid_info['i_term'],
                        d_term=pid_info['d_term'],
                        pid_output=output,
                        motor_output=motor_output  # Add motor output percentage
                    )
                
                # Start the web server
                print("\nStarting web dashboard...")
                print("Web interface available at http://192.168.0.103:5000")
                start_server(port=5000)
                
                try:
                    # Start balancing with the debug callback
                    balance_controller.start_balancing(debug_callback)
                finally:
                    # Stop the web server when balancing ends
                    stop_server()
                    
            elif choice == '2':
                dual_motor_test(motors)
            elif choice == '3':
                # Update config with tuned parameters
                pid_tuner.tune_parameters()
                # Update the balance controller with the new configuration
                balance_controller = BalanceController(imu, motors, CONFIG)
            elif choice == '4':
                # Quick tuning of just the P, I, and D gains
                pid_tuner.tune_specific_parameters(['P_GAIN', 'I_GAIN', 'D_GAIN', 'IMU_FILTER_ALPHA'])
                # Update the balance controller with the new configuration
                balance_controller = BalanceController(imu, motors, CONFIG)
            elif choice == '5':
                runtime_parameter_tuning(pid_tuner, balance_controller)
            elif choice == '6':
                imu_tuning_mode(imu)
            elif choice == 'q':
                print("Exiting program...")
                motors.cleanup()
                break
    except KeyboardInterrupt:
        print("\nProgram interrupted.")
    finally:
        try:
            motors.cleanup()
            stop_server()  # Ensure web server is stopped when exiting
        except:
            pass
        print("Goodbye!")

if __name__ == "__main__":
    main()
