"""
Balance Controller Module for Self-Balancing Robot

This module implements the main balance control logic for the self-balancing robot,
connecting the IMU sensors, PID controller, and motor control components together.

Key features:
- Integrates data from IMU with PID control to determine motor output
- Handles motor control including deadband and maximum speed limits
- Implements safety features to prevent damage during excessive tilt
- Provides real-time debug output of critical balancing parameters
- Supports both single and dual motor configurations

The balance controller is the central component that ties together all the robot's
systems to achieve and maintain balance. It continuously reads sensor data, calculates
the appropriate response using PID control, and applies that control to the motors.

Example Usage:
    # Initialize components
    from IMU_reader import IMUReader
    from motorController import DualMotorControl
    from config import CONFIG, HARDWARE_CONFIG
    
    # Create required components
    imu = IMUReader(alpha=CONFIG['IMU_FILTER_ALPHA'], upside_down=CONFIG['IMU_UPSIDE_DOWN'])
    motors = DualMotorControl(
        motor_a_in1=HARDWARE_CONFIG['MOTOR_A_IN1_PIN'],
        motor_a_in2=HARDWARE_CONFIG['MOTOR_A_IN2_PIN'],
        motor_b_in1=HARDWARE_CONFIG['MOTOR_B_IN1_PIN'],
        motor_b_in2=HARDWARE_CONFIG['MOTOR_B_IN2_PIN']
    )
    
    # Create balance controller
    controller = BalanceController(imu, motors, CONFIG)
    
    # Start balancing
    controller.start_balancing()
    
    # To stop balancing
    controller.stop_balancing()
"""

import time
import sys
import select
import termios
import tty
from pid_controller import PIDController
from motorController import MotorControl, DualMotorControl

class BalanceController:
    """
    Controller for self-balancing robot that uses PID control.
    Handles the interaction between sensors, PID algorithm, and motor control.
    Supports both single motor and dual motor configurations.
    """
    
    def __init__(self, imu, motor, config):
        """
        Initialize the balance controller with an IMU and motor control.
        
        Args:
            imu: IMU reader instance
            motor: Motor control instance
            config: Configuration dictionary
        """
        self.imu = imu
        self.motor = motor
        self.config = config
        
        # Initialize PID controller
        self.pid = PIDController(config)
        
        # Store sample time from config, can be updated at runtime
        self.sample_time = config['SAMPLE_TIME']
        
        # For direction change boosting
        self.last_direction = None
        self.enable_debug = True  # Enable debug output by default
        self.running = False
        
        # Determine if we're using dual motors
        self.using_dual_motors = isinstance(self.motor, DualMotorControl)
        if self.using_dual_motors:
            print("Balance controller configured with dual motors")
        else:
            print("Balance controller configured with single motor")
    
    def _apply_direction_change_boost(self, output):
        """
        Apply a boost when direction changes to overcome inertia.
        
        Args:
            output (float): Original PID output
            
        Returns:
            float: Modified output with boost if direction changed
        """
        # Determine current direction
        current_direction = "stop" if abs(output) < 0.1 else ("clockwise" if output > 0 else "counterclockwise")
        
        # Skip boost if output is very small
        if current_direction == "stop":
            self.last_direction = None
            return output
            
        # Apply boost on direction change if configured
        boost_amount = self.config.get('DIRECTION_CHANGE_BOOST', 0)
        if boost_amount > 0 and self.last_direction is not None and current_direction != self.last_direction:
            # Direction has changed, apply boost
            output = output * (1 + boost_amount)
        
        # Store current direction for next iteration
        self.last_direction = current_direction
        
        return output
        
    def apply_motor_control(self, output):
        """
        Apply the control output to the motors.
        
        Args:
            output (float): PID controller output (-100 to 100)
        """
        # Get deadband and max speed from config
        deadband = self.config.get('MOTOR_DEADBAND', 0)
        max_speed = self.config.get('MAX_MOTOR_SPEED', 100)
        
        # Clamp output between -100 and 100
        output = max(-100, min(100, output))
        
        # Determine the direction
        if output > 0:
            direction = "clockwise"
            direction = "counterclockwise"
        
        # Set the motor speed (absolute value of output)
        speed = abs(output)
        
        # Apply deadband mapping logic
        if speed < 0.1:  # Near-zero threshold
            speed = 0
        elif deadband > 0:
            # Map the speed from [0-100] to [deadband-max_speed]
            # Formula: new_speed = (speed / 100) * (max_speed - deadband) + deadband
            µµ
        
        # Ensure speed is within limits
        speed = min(max(0, speed), max_speed)
        
        # Apply to motors using the motor driver
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
        print("\n🤖 Self-Balancing Mode Started!")
        print("Press 'Q' to return to main menu")
        print("-------------------------")
        
        # Reset PID controller
        self.pid.reset()
        self.last_direction = None
        
        # Set up non-blocking input detection
        self.running = True
        
        # Configure terminal for non-blocking input
        try:
            # Set up terminal for non-blocking input this will allow us to check for key presses without having to press enter
            tty.setcbreak(sys.stdin.fileno())
            
            # Track timing for main control loop
            last_time = time.time()
            last_debug_time = time.time()
            
            # Main control loop
            while self.running:
                # Check for keypress
                if select.select([sys.stdin], [], [], 0)[0]:
                    key = sys.stdin.read(1)
                    
                    if key.lower() == 'q':
                        print("\nStopping self-balancing mode...")
                        break
                
                # Calculate time since last loop
                current_time = time.time()
                time_passed = current_time - last_time
                
                # Ensure we're running at the correct sample rate
                if time_passed < self.sample_time:
                    continue
                
                # Get IMU data
                imu_data = self.imu.get_imu_data()
                roll = imu_data['roll']
                angular_velocity = imu_data['angular_velocity']
                
                # Calculate PID output using compute() instead of calculate()
                output = self.pid.compute(
                    current_value=roll,
                    angular_velocity=angular_velocity,
                    dt=time_passed
                )
                
                # Apply direction change boost if configured
                output = self._apply_direction_change_boost(output)
                
                # Apply the output to the motor(s)
                result = self.apply_motor_control(output)
                output, motor_speed, direction = result
                
                # Update for next iteration
                last_time = current_time
                
                # Clear the current line and print the status
                sys.stdout.write("\r\033[K")  # Clear line
                sys.stdout.write(f"Roll: {roll:.2f}° | Angular Vel: {angular_velocity:.2f}°/s | Output: {output:.2f} | Motor: {motor_speed:.2f}% {direction}")
                sys.stdout.flush()
                
                # Optional debug callback for data visualization or logging
                if debug_callback and current_time - last_debug_time >= 0.1:  # Limit debug to 10Hz
                    debug_info = {
                        'roll': roll,
                        'angular_velocity': angular_velocity,
                        'output': output,
                        'motor_output': motor_speed,
                        'pid': {
                            'p_term': self.pid.p_term,
                            'i_term': self.pid.i_term,
                            'd_term': self.pid.d_term
                        }
                    }
                    debug_callback(debug_info)
                    last_debug_time = current_time
                
        except Exception as e:
            # Print error
            sys.stdout.write("\r" + " " * 80)  # Clear the line
            sys.stdout.write(f"\rError in balancing loop: {e}")
            sys.stdout.flush()
            print()  # Add a newline after the error
        
        finally:
            # Restore terminal settings
            tty.setcbreak(sys.stdin.fileno())
            
            # Make sure motors are stopped
            self.motor.stop_motors() if self.using_dual_motors else self.motor.stop_motor()
            print("\nSelf-balancing mode stopped.")
    
    def stop_balancing(self):
        """Stop the balancing control loop."""
        self.running = False
        if self.using_dual_motors:
            self.motor.stop_motors()
        else:
            self.motor.stop_motor()
        print("Motor stopped. Balance mode exited.")

    def update_from_config(self, config=None):
        """
        Update controller parameters from config file.
        
        Args:
            config: Optional config dict. If None, reloads from file.
        """
        from config import CONFIG, load_config
        
        # If no config provided, reload from file
        if config is None:
            load_config()
            config = CONFIG
        
        # Update PID parameters
        self.pid.kp = config.get('P_GAIN', self.pid.kp)
        self.pid.ki = config.get('I_GAIN', self.pid.ki)
        self.pid.kd = config.get('D_GAIN', self.pid.kd)
        
        # Update other controller settings
        self.sample_time = config.get('SAMPLE_TIME', self.sample_time)
        
        # Update IMU if we have access to it
        if hasattr(self, 'imu') and self.imu:
            self.imu.ALPHA = config.get('IMU_FILTER_ALPHA', self.imu.ALPHA)
        
        return True 
