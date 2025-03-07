from motorController import MotorControl
from IMU_reader import IMUReader
import time

# Import our new modules
from config import PID_CONFIG, HARDWARE_CONFIG
from balance_controller import BalanceController
from tuning import PIDTuner

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


def main():
    """Main function with menu for different modes."""
    # Initialize hardware
    motor = MotorControl(HARDWARE_CONFIG['IN1_PIN'], HARDWARE_CONFIG['IN2_PIN'])
    imu = IMUReader()
    
    # Create balance controller and PID tuner
    balance_controller = BalanceController(imu, motor, PID_CONFIG)
    pid_tuner = PIDTuner(PID_CONFIG)
    
    print("\n🤖 Self-Balancing Robot Control System")
    print("--------------------------------------")
    
    try:
        while True:
            print("\nSelect Mode:")
            print("1: Self-Balancing Mode (PID Control)")
            print("2: Manual Motor Control")
            print("3: Tune All PID Parameters")
            print("4: Quick-Tune Core PID Parameters (P, I, D gains)")
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
                balance_controller = BalanceController(imu, motor, PID_CONFIG)
            elif choice == '4':
                # Quick tuning of just the P, I, and D gains
                pid_tuner.tune_specific_parameters(['P_GAIN', 'I_GAIN', 'D_GAIN'])
                # Update the balance controller with the new configuration
                balance_controller = BalanceController(imu, motor, PID_CONFIG)
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
