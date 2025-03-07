from motorController import MotorControl
from IMU_reader import IMUReader

# Define Motor Pins
IN1_PIN = 13
IN2_PIN = 19

# Initialize Motor and IMU
motor = MotorControl(IN1_PIN, IN2_PIN)
imu = IMUReader()

def main():
    """
    Simple motor control: W for forward, S for reverse, I for IMU data, Q to quit.
    """
    print("\n🚀 Motor & IMU Control Started!")
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

if __name__ == "__main__":
    main()

