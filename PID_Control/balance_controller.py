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
        else:
            direction = "counterclockwise"
        
        # Set the motor speed (absolute value of output)
        speed = abs(output)
        
        # Apply deadband - if speed is below deadband, set to 0
        if speed < deadband:
            speed = 0
        
        # Apply max speed limit
        speed = min(speed, max_speed)
        
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
        
        # Save terminal settings
        old_settings = termios.tcgetattr(sys.stdin)
        
        try:
            # Set terminal to raw mode
            tty.setraw(sys.stdin.fileno())
            
            # Set up select for non-blocking input
            last_time = time.time()
            last_debug_time = time.time()
            
            # Main control loop
            while self.running:
                # Check for keypress
                if select.select([sys.stdin], [], [], 0)[0]:
                    key = sys.stdin.read(1)
                    if key.lower() == 'q':
                        # Restore terminal settings
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                        print("\nExiting balance mode...")
                        break
                
                # Calculate time delta
                current_time = time.time()
                dt = current_time - last_time
                
                # Ensure minimum sample time
                if dt < self.sample_time:
                    time.sleep(0.001)  # Small sleep to prevent CPU hogging
                    continue
                
                # Get IMU data
                imu_data = self.imu.get_imu_data()
                roll = imu_data['roll']
                angular_velocity = imu_data['angular_velocity']
                
                # Safety check - stop motors if tilt exceeds safe limit
                if abs(roll) > self.config['SAFE_TILT_LIMIT']:
                    # Restore terminal settings before printing
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                    
                    # Use a single line for the safety message
                    sys.stdout.write("\r" + " " * 80)  # Clear the line
                    sys.stdout.write("\r⚠️ Safety cutoff: Tilt exceeded limit! Motors stopped.")
                    sys.stdout.flush()
                    
                    # Stop motors
                    self.motor.stop_motors() if self.using_dual_motors else self.motor.stop_motor()
                    time.sleep(1)  # Give time to read the message
                    break
                
                # Update PID controller
                pid_update = self.pid.update(0.0 - roll, dt, angular_velocity)  # Pass angular velocity for better D term
                
                # Apply motor control based on PID output
                output, speed, direction = self.apply_motor_control(pid_update)
                
                # Update last time for next iteration
                last_time = current_time
                
                # Call debug callback if provided
                if debug_callback and callable(debug_callback):
                    # Prepare debug info
                    debug_info = {
                        'roll': roll,
                        'angular_velocity': angular_velocity,
                        'output': output,
                        'motor_output': speed,  # Add motor output percentage
                        'pid': {
                            'p_term': self.pid.p_term,
                            'i_term': self.pid.i_term,
                            'd_term': self.pid.d_term
                        }
                    }
                    
                    # Call the debug callback with the info
                    debug_callback(debug_info)
                    
                # Print debug output directly to terminal if no callback and debug is enabled
                elif self.enable_debug:
                    # Limit debug output rate to avoid flooding terminal
                    if current_time - last_debug_time > 0.1:  # Max 10 updates per second
                        # Clear the line completely before writing
                        sys.stdout.write('\r' + ' ' * 80)
                        sys.stdout.write(f"\rAngle: {roll:6.2f}° | Output: {output:6.1f} | P: {self.pid.p_term:6.1f} | I: {self.pid.i_term:6.1f} | D: {self.pid.d_term:6.1f}")
                        sys.stdout.flush()
                        last_debug_time = current_time
        
        except Exception as e:
            # Restore terminal settings before printing error
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            sys.stdout.write("\r" + " " * 80)  # Clear the line
            sys.stdout.write(f"\rError in balancing loop: {e}")
            sys.stdout.flush()
            print()  # Add a newline after the error
        
        finally:
            # Restore terminal settings
            if old_settings:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            
            # Stop motors for safety
            if self.using_dual_motors:
                self.motor.stop_motors()
            else:
                self.motor.stop_motor()
            
            self.running = False
    
    def stop_balancing(self):
        """Stop the balancing control loop."""
        self.running = False
        if self.using_dual_motors:
            self.motor.stop_motors()
        else:
            self.motor.stop_motor()
        print("Motor stopped. Balance mode exited.") 
