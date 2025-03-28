"""
Balance Controller Module for Self-Balancing Robot

This module implements the main balance control logic for the self-balancing robot,
connecting the IMU sensors, PID controller, and motor control components together.

Example Usage:
    from IMU_reader import IMUReader
    from motorController import DualMotorControl
    from config import CONFIG, HARDWARE_CONFIG
    
    # Create required components
    imu = IMUReader()
    motors = DualMotorControl(
        motor_a_in1=HARDWARE_CONFIG['MOTOR_A_IN1_PIN'],
        motor_a_in2=HARDWARE_CONFIG['MOTOR_A_IN2_PIN'],
        motor_b_in1=HARDWARE_CONFIG['MOTOR_B_IN1_PIN'],
        motor_b_in2=HARDWARE_CONFIG['MOTOR_B_IN2_PIN']
    )
    
    # Create balance controller
    controller = BalanceController(imu, motors)
    
    # Start balancing
    controller.start_balancing()
    
    # To stop balancing
    controller.stop_balancing()
"""

import time
from pid_controller import PIDController
from motorController import MotorControl, DualMotorControl
from config import load_config

class BalanceController:
    """
    Main controller for the self-balancing robot.
    
    This class coordinates between the IMU, motor control, and PID controller to maintain balance.
    """
    
    def __init__(self, imu, motor):
        """
        Initialize the balance controller with IMU and motor control.
        
        Args:
            imu: IMU reader instance
            motor: Motor control instance (single or dual)
        """
        self.imu = imu
        self.motor = motor
        self.pid = PIDController()
        self.running = False
        
        # Determine if we're using dual motors
        self.using_dual_motors = isinstance(self.motor, DualMotorControl)
        print(f"Balance controller configured with {'dual' if self.using_dual_motors else 'single'} motor")
    
    def apply_motor_control(self, output):
        """
        Apply the control output to the motors with deadband handling.
        
        Args:
            output: PID controller output (-100 to 100)
            
        Returns:
            tuple: (final_output, speed, direction)
        """
        # Get latest config each time
        config = load_config()
        
        # Get motor parameters from config
        deadband = config.get('MOTOR_DEADBAND', 0)
        max_speed = config.get('MAX_MOTOR_SPEED', 100)
        zero_threshold = config.get('ZERO_THRESHOLD', 0.1)
        
        # Clamp output between -100 and 100
        output = max(-100, min(100, output))
        
        # Determine the direction
        if output > 0:
            direction = "clockwise"
        else:
            direction = "counterclockwise"
        
        # Get absolute speed value
        speed = abs(output)
        
        # Apply zero threshold
        if speed < zero_threshold:
            speed = 0
        # Apply deadband mapping
        elif deadband > 0:
            # Map the speed from [0-100] to [deadband-max_speed]
            speed = (speed / 100.0) * (max_speed - deadband) + deadband
        
        # Ensure speed is within limits
        speed = min(max(0, speed), max_speed)
        
        # Apply to motors
        if self.using_dual_motors:
            self.motor.set_motors_speed(speed, direction)
        else:
            self.motor.set_motor_speed(speed, direction)
        
        return output, speed, direction
    
    def start_balancing(self, debug_callback=None):
        """
        Start the self-balancing control loop.
        
        Args:
            debug_callback: Optional callback function for debug output
        """
        print("\nSelf-Balancing Mode Started!")
        print("Use Ctrl+C to stop balancing")
        print("-------------------------")
        
        # Reset PID controller
        self.pid.reset()
        
        # Set running flag
        self.running = True
        
        try:
            # Initialize timing variables
            last_time = time.time()
            last_print_time = time.time()
            last_debug_time = time.time()  # Initialize this for debug callback
            
            # Main control loop
            while self.running:
                # Calculate time since last loop
                current_time = time.time()
                time_passed = current_time - last_time
                
                # Get latest sample time from config
                config = load_config()
                sample_time = config.get('SAMPLE_TIME', 0.01)
                
                # Ensure we're running at the correct sample rate
                if time_passed < sample_time:
                    time.sleep(0.001)  # Small sleep to prevent CPU hogging
                    temp_imu_date = self.imu.get_imu_data() # This is to keep the IMU active when PID is sleeping
                    continue
                
                # Get IMU data
                imu_data = self.imu.get_imu_data()
                roll = imu_data['roll']
                angular_velocity = imu_data['angular_velocity']
                
                # Calculate PID output
                output = self.pid.compute(
                    current_value=roll,
                    dt=time_passed
                )
                
                # Apply the output to the motor(s)
                result = self.apply_motor_control(output)
                output, motor_speed, direction = result
                
                # Update for next iteration
                last_time = current_time
                
                # Print status on same line (throttled to 2Hz)
                if current_time - last_print_time >= 0.5:
                    print(f"\rRoll: {roll:.2f}° | Angular Vel: {angular_velocity:.2f}°/s | Output: {output:.2f} | Motor: {motor_speed:.2f}% {direction}", end='', flush=True)
                    last_print_time = current_time
                
                # Optional debug callback (throttled to 10Hz)
                if debug_callback and current_time - last_debug_time >= 0.1:
                    # Get PID terms directly from config instead of relying on internal PID state
                    config = load_config()
                    debug_info = {
                        'roll': roll,
                        'angular_velocity': angular_velocity,
                        'output': output,
                        'motor_output': motor_speed,
                        'pid': {
                            'p_gain': config.get('P_GAIN', 0),
                            'i_gain': config.get('I_GAIN', 0),
                            'd_gain': config.get('D_GAIN', 0)
                        }
                    }
                    debug_callback(debug_info)
                    last_debug_time = current_time
                
        except KeyboardInterrupt:
            print("\nBalancing stopped by user (Ctrl+C)")
        except Exception as e:
            print(f"\nError in balancing loop: {e}")
        finally:
            # Make sure motors are stopped
            if self.using_dual_motors:
                self.motor.stop_motors()
            else:
                self.motor.stop_motor()
            print("\nSelf-balancing mode stopped.")
    
    def stop_balancing(self):
        """Stop the balancing control loop."""
        self.running = False
        if self.using_dual_motors:
            self.motor.stop_motors()
        else:
            self.motor.stop_motor()
        print("\nMotor stopped. Balance mode exited.")