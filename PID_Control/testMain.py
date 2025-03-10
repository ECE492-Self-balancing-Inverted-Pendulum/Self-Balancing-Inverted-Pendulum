from motorController import MotorControl
from IMU_reader import IMUReader
from encoder import Encoder
import time

# Define Motor and Encoder Pins
IN1_PIN = 13
IN2_PIN = 19
ENCODER_A_PIN = 23
ENCODER_B_PIN = 24

# Initialize Motor, IMU, and Encoder
motor = MotorControl(IN1_PIN, IN2_PIN)
imu = IMUReader()
encoder = Encoder(ENCODER_A_PIN, ENCODER_B_PIN)

def main():
    """
    Simple motor control: W for forward, S for reverse, I for IMU data,
    E for encoder RPM test, Q to quit.
    """
    print("\n🚀 Motor, IMU & Encoder Control Started!")
    print("W: Run Motor Forward (100%)")
    print("S: Run Motor Reverse (100%)")
    print("I: Get IMU Data (Roll & Angular Velocity)")
    print("E: Measure RPM from Encoder")
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
                print(f"Roll: {imu_data['roll']:.2f}° | Angular Velocity: {imu_data['angular_velocity']:.2f}°/s")

            elif command == "e":
                rpm = encoder.measure_rpm(duration=1)  # Measure RPM for 1 second
                print(f"Measured RPM: {rpm:.2f}")

            elif command == "q":
                print("Stopping motor and exiting...")
                motor.stop_motor()
                break

    except KeyboardInterrupt:
        print("\nInterrupted. Stopping motor.")

    finally:
        motor.stop_motor()
        encoder.cleanup()
        print("Motor & Encoder Stopped. Exiting.")

if __name__ == "__main__":
    main()

