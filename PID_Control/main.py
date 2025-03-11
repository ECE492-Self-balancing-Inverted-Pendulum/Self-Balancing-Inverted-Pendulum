from motorController import MotorControl, DualMotorControl
from IMU_reader import IMUReader
import time
import threading
import select
import sys
import tty
import termios

# Import our new modules
from config import CONFIG, HARDWARE_CONFIG
from balance_controller import BalanceController
from tuning import PIDTuner
from pid_controller import PIDController

def runtime_parameter_tuning(pid_tuner, balance_controller):
    """
    Allows tuning parameters during runtime without interrupting the balancing.
    Uses a simplified keyboard interface for adjusting P, I, D values.
    
    Args:
        pid_tuner: PID tuner instance
        balance_controller: Balance controller instance
    """
    print("\n⚙️ Runtime Parameter Tuning")
    print("You can modify parameters while the robot is balancing.")
    print("Controls:")
    print("  P, I, D: Select parameter to tune (P is default)")
    print("  + / -: Increase/decrease selected parameter by 1.0")
    print("  w / s: Fine adjustment (increase/decrease by 0.1)")
    print("  B: Toggle parameter selection to direction change boost")
    print("  A: Toggle parameter selection to IMU filter alpha")
    print("  L: List all current parameters")
    print("  S: Save current configuration")
    print("  Q: Quit tuning mode")
    
    # Start balancing in a separate thread
    balancing_thread = threading.Thread(
        target=balance_controller.start_balancing,
        daemon=True
    )
    balancing_thread.start()
    
    # Setup for non-blocking input
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        # Set terminal to raw mode
        tty.setraw(sys.stdin.fileno())
        
        # Default parameter to tune
        current_param = "P_GAIN"
        running = True
        
        while running:
            # Display current parameter and value
            sys.stdout.write("\r\033[K")  # Clear line
            
            # Get current parameter value
            if current_param == "P_GAIN":
                current_value = balance_controller.pid.kp
                display_param = "P"
            elif current_param == "I_GAIN":
                current_value = balance_controller.pid.ki
                display_param = "I"
            elif current_param == "D_GAIN":
                current_value = balance_controller.pid.kd
                display_param = "D"
            elif current_param == "DIRECTION_CHANGE_BOOST":
                current_value = CONFIG.get('DIRECTION_CHANGE_BOOST', 20.0)
                display_param = "Boost"
            elif current_param == "IMU_FILTER_ALPHA":
                current_value = balance_controller.imu.ALPHA
                display_param = "Alpha"
            else:
                current_value = CONFIG.get(current_param, 0)
                display_param = current_param
                
            sys.stdout.write(f"Tuning {display_param}: {current_value:.2f} | Press L for list, Q to quit")
            sys.stdout.flush()
            
            # Check if key pressed
            if select.select([sys.stdin], [], [], 0.1)[0]:
                key = sys.stdin.read(1)
                
                if key.lower() == 'q':
                    running = False
                    sys.stdout.write("\r\033[K")  # Clear line
                    print("\nExiting tuning mode.")
                
                elif key.lower() == 'p':
                    current_param = "P_GAIN"
                    sys.stdout.write("\r\033[K")  # Clear line
                    print(f"\nSelected P_GAIN: {balance_controller.pid.kp:.2f}")
                
                elif key.lower() == 'i':
                    current_param = "I_GAIN"
                    sys.stdout.write("\r\033[K")  # Clear line
                    print(f"\nSelected I_GAIN: {balance_controller.pid.ki:.2f}")
                
                elif key.lower() == 'd':
                    current_param = "D_GAIN"
                    sys.stdout.write("\r\033[K")  # Clear line
                    print(f"\nSelected D_GAIN: {balance_controller.pid.kd:.2f}")
                
                elif key.lower() == 'b':
                    current_param = "DIRECTION_CHANGE_BOOST"
                    boost_value = CONFIG.get('DIRECTION_CHANGE_BOOST', 20.0)
                    sys.stdout.write("\r\033[K")  # Clear line
                    print(f"\nSelected DIRECTION_CHANGE_BOOST: {boost_value:.2f}%")
                
                elif key.lower() == 'a':
                    current_param = "IMU_FILTER_ALPHA"
                    sys.stdout.write("\r\033[K")  # Clear line
                    print(f"\nSelected IMU_FILTER_ALPHA: {balance_controller.imu.ALPHA:.2f}")
                
                elif key == '+':
                    # Regular increment (by 1.0)
                    if current_param == "P_GAIN":
                        balance_controller.pid.kp += 1.0
                        CONFIG['P_GAIN'] = balance_controller.pid.kp
                        sys.stdout.write("\r\033[K")  # Clear line
                        print(f"\nIncreased P_GAIN to {balance_controller.pid.kp:.2f}")
                    elif current_param == "I_GAIN":
                        balance_controller.pid.ki += 1.0
                        CONFIG['I_GAIN'] = balance_controller.pid.ki
                        sys.stdout.write("\r\033[K")  # Clear line
                        print(f"\nIncreased I_GAIN to {balance_controller.pid.ki:.2f}")
                    elif current_param == "D_GAIN":
                        balance_controller.pid.kd += 1.0
                        CONFIG['D_GAIN'] = balance_controller.pid.kd
                        sys.stdout.write("\r\033[K")  # Clear line
                        print(f"\nIncreased D_GAIN to {balance_controller.pid.kd:.2f}")
                    elif current_param == "DIRECTION_CHANGE_BOOST":
                        boost_value = CONFIG.get('DIRECTION_CHANGE_BOOST', 20.0) + 5.0
                        boost_value = min(100.0, boost_value)  # Cap at 100%
                        CONFIG['DIRECTION_CHANGE_BOOST'] = boost_value
                        sys.stdout.write("\r\033[K")  # Clear line
                        print(f"\nIncreased DIRECTION_CHANGE_BOOST to {boost_value:.2f}%")
                    elif current_param == "IMU_FILTER_ALPHA":
                        new_alpha = min(balance_controller.imu.ALPHA + 0.1, 1.0)
                        balance_controller.imu.set_alpha(new_alpha)
                        CONFIG['IMU_FILTER_ALPHA'] = new_alpha
                        sys.stdout.write("\r\033[K")  # Clear line
                        print(f"\nIncreased IMU_FILTER_ALPHA to {new_alpha:.2f}")
                
                elif key == '-':
                    # Regular decrement (by 1.0)
                    if current_param == "P_GAIN":
                        balance_controller.pid.kp = max(0.0, balance_controller.pid.kp - 1.0)
                        CONFIG['P_GAIN'] = balance_controller.pid.kp
                        sys.stdout.write("\r\033[K")  # Clear line
                        print(f"\nDecreased P_GAIN to {balance_controller.pid.kp:.2f}")
                    elif current_param == "I_GAIN":
                        balance_controller.pid.ki = max(0.0, balance_controller.pid.ki - 1.0)
                        CONFIG['I_GAIN'] = balance_controller.pid.ki
                        sys.stdout.write("\r\033[K")  # Clear line
                        print(f"\nDecreased I_GAIN to {balance_controller.pid.ki:.2f}")
                    elif current_param == "D_GAIN":
                        balance_controller.pid.kd = max(0.0, balance_controller.pid.kd - 1.0)
                        CONFIG['D_GAIN'] = balance_controller.pid.kd
                        sys.stdout.write("\r\033[K")  # Clear line
                        print(f"\nDecreased D_GAIN to {balance_controller.pid.kd:.2f}")
                    elif current_param == "DIRECTION_CHANGE_BOOST":
                        boost_value = CONFIG.get('DIRECTION_CHANGE_BOOST', 20.0) - 5.0
                        boost_value = max(0.0, boost_value)  # Ensure non-negative
                        CONFIG['DIRECTION_CHANGE_BOOST'] = boost_value
                        sys.stdout.write("\r\033[K")  # Clear line
                        print(f"\nDecreased DIRECTION_CHANGE_BOOST to {boost_value:.2f}%")
                    elif current_param == "IMU_FILTER_ALPHA":
                        new_alpha = max(0.01, balance_controller.imu.ALPHA - 0.1)
                        balance_controller.imu.set_alpha(new_alpha)
                        CONFIG['IMU_FILTER_ALPHA'] = new_alpha
                        sys.stdout.write("\r\033[K")  # Clear line
                        print(f"\nDecreased IMU_FILTER_ALPHA to {new_alpha:.2f}")
                
                elif key.lower() == 'w':  # Fine increment (previously '=')
                    # Fine increment (by 0.1)
                    if current_param == "P_GAIN":
                        balance_controller.pid.kp += 0.1
                        CONFIG['P_GAIN'] = balance_controller.pid.kp
                        sys.stdout.write("\r\033[K")  # Clear line
                        print(f"\nFine increased P_GAIN to {balance_controller.pid.kp:.2f}")
                    elif current_param == "I_GAIN":
                        balance_controller.pid.ki += 0.1
                        CONFIG['I_GAIN'] = balance_controller.pid.ki
                        sys.stdout.write("\r\033[K")  # Clear line
                        print(f"\nFine increased I_GAIN to {balance_controller.pid.ki:.2f}")
                    elif current_param == "D_GAIN":
                        balance_controller.pid.kd += 0.1
                        CONFIG['D_GAIN'] = balance_controller.pid.kd
                        sys.stdout.write("\r\033[K")  # Clear line
                        print(f"\nFine increased D_GAIN to {balance_controller.pid.kd:.2f}")
                    elif current_param == "DIRECTION_CHANGE_BOOST":
                        boost_value = CONFIG.get('DIRECTION_CHANGE_BOOST', 20.0) + 1.0
                        boost_value = min(100.0, boost_value)  # Cap at 100%
                        CONFIG['DIRECTION_CHANGE_BOOST'] = boost_value
                        sys.stdout.write("\r\033[K")  # Clear line
                        print(f"\nFine increased DIRECTION_CHANGE_BOOST to {boost_value:.2f}%")
                    elif current_param == "IMU_FILTER_ALPHA":
                        new_alpha = min(balance_controller.imu.ALPHA + 0.01, 1.0)
                        balance_controller.imu.set_alpha(new_alpha)
                        CONFIG['IMU_FILTER_ALPHA'] = new_alpha
                        sys.stdout.write("\r\033[K")  # Clear line
                        print(f"\nFine increased IMU_FILTER_ALPHA to {new_alpha:.2f}")
                
                elif key.lower() == 's':  # Fine decrement (previously '_')
                    # Fine decrement (by 0.1)
                    if current_param == "P_GAIN":
                        balance_controller.pid.kp = max(0.0, balance_controller.pid.kp - 0.1)
                        CONFIG['P_GAIN'] = balance_controller.pid.kp
                        sys.stdout.write("\r\033[K")  # Clear line
                        print(f"\nFine decreased P_GAIN to {balance_controller.pid.kp:.2f}")
                    elif current_param == "I_GAIN":
                        balance_controller.pid.ki = max(0.0, balance_controller.pid.ki - 0.1)
                        CONFIG['I_GAIN'] = balance_controller.pid.ki
                        sys.stdout.write("\r\033[K")  # Clear line
                        print(f"\nFine decreased I_GAIN to {balance_controller.pid.ki:.2f}")
                    elif current_param == "D_GAIN":
                        balance_controller.pid.kd = max(0.0, balance_controller.pid.kd - 0.1)
                        CONFIG['D_GAIN'] = balance_controller.pid.kd
                        sys.stdout.write("\r\033[K")  # Clear line
                        print(f"\nFine decreased D_GAIN to {balance_controller.pid.kd:.2f}")
                    elif current_param == "DIRECTION_CHANGE_BOOST":
                        boost_value = CONFIG.get('DIRECTION_CHANGE_BOOST', 20.0) - 1.0
                        boost_value = max(0.0, boost_value)  # Ensure non-negative
                        CONFIG['DIRECTION_CHANGE_BOOST'] = boost_value
                        sys.stdout.write("\r\033[K")  # Clear line
                        print(f"\nFine decreased DIRECTION_CHANGE_BOOST to {boost_value:.2f}%")
                    elif current_param == "IMU_FILTER_ALPHA":
                        new_alpha = max(0.01, balance_controller.imu.ALPHA - 0.01)
                        balance_controller.imu.set_alpha(new_alpha)
                        CONFIG['IMU_FILTER_ALPHA'] = new_alpha
                        sys.stdout.write("\r\033[K")  # Clear line
                        print(f"\nFine decreased IMU_FILTER_ALPHA to {new_alpha:.2f}")
                
                elif key.lower() == 'l':
                    # List all parameters
                    sys.stdout.write("\r\033[K")  # Clear line
                    print("\nCurrent parameters:")
                    print(f"P_GAIN: {balance_controller.pid.kp:.2f}")
                    print(f"I_GAIN: {balance_controller.pid.ki:.2f}")
                    print(f"D_GAIN: {balance_controller.pid.kd:.2f}")
                    print(f"DIRECTION_CHANGE_BOOST: {CONFIG.get('DIRECTION_CHANGE_BOOST', 20.0):.2f}%")
                    print(f"IMU_FILTER_ALPHA: {balance_controller.imu.ALPHA:.2f}")
                    print(f"MOTOR_DEADBAND: {CONFIG.get('MOTOR_DEADBAND', 60)}")
                    print(f"MAX_MOTOR_SPEED: {CONFIG.get('MAX_MOTOR_SPEED', 100)}")
                    print(f"SAFE_TILT_LIMIT: {CONFIG.get('SAFE_TILT_LIMIT', 45)}")
                    print(f"MAX_I_TERM: {CONFIG.get('MAX_I_TERM', 20)}")
                
                elif key.lower() == 'v':  # Using 'v' for save since 's' is now used for fine decrement
                    # Save configuration
                    from config import save_config
                    save_config(CONFIG)
                    sys.stdout.write("\r\033[K")  # Clear line
                    print("\nConfiguration saved successfully!")
    
    except Exception as e:
        print(f"\nError in tuning mode: {e}")
        
    finally:
        # Restore terminal settings
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        
        # Ensure balancing stops
        balance_controller.stop_balancing()
        print("Stopping balancing...")
        balancing_thread.join(timeout=1.0)
        print("Runtime tuning exited.")

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
                
                elif key == '-':
                    new_alpha = max(imu.ALPHA - 0.05, 0.05)
                    imu.set_alpha(new_alpha)
                    sys.stdout.write("\r\033[K")  # Clear line
                    print(f"\nDecreased alpha to {imu.ALPHA:.2f}")
                
                elif key == 'r':
                    imu.set_alpha(imu.DEFAULT_ALPHA)
                    sys.stdout.write("\r\033[K")  # Clear line
                    print(f"\nReset alpha to default ({imu.DEFAULT_ALPHA:.2f})")
                
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
            print("5: Self-Balancing Mode with Runtime Parameter Tuning")
            print("6: IMU Responsiveness Tuning")
            print("Q: Quit Program")
            
            choice = input("\nEnter choice: ").lower().strip()
            
            if choice == '1':
                balance_controller.start_balancing()
            elif choice == '2':
                dual_motor_test(motors)
            elif choice == '3':
                # Update config with tuned parameters
                pid_tuner.tune_parameters()
                # Update the balance controller with the new configuration
                balance_controller = BalanceController(imu, motors, CONFIG)
            elif choice == '4':
                # Quick tuning of just the P, I, and D gains
                pid_tuner.tune_specific_parameters(['P_GAIN', 'I_GAIN', 'D_GAIN'])
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
        except:
            pass
        print("Goodbye!")

if __name__ == "__main__":
    main()
